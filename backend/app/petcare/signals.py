# app/petcare/signals.py

import logging
import time
import threading  # 用于线程安全
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────
# 防抖动机制
# ────────────────────────────────────────────────────────────

# 全局防抖动字典和线程锁
_last_refresh = {}
_refresh_lock = threading.Lock()
DEBOUNCE_SECONDS = 2


def _should_refresh(key: str) -> bool:
    """检查是否应该刷新（防抖动检查）- 带自动清理"""
    current_time = time.time()

    with _refresh_lock:
        # 简单清理：每100次调用清理一次过期条目
        if len(_last_refresh) > 0 and hash(key) % 100 == 0:
            cleanup_count = 0
            expired_keys = []
            cleanup_threshold = 24 * 3600  # 24小时

            for k, last_time in _last_refresh.items():
                if current_time - last_time > cleanup_threshold:
                    expired_keys.append(k)

            for k in expired_keys:
                del _last_refresh[k]
                cleanup_count += 1

            if cleanup_count > 0:
                logger.info(f"[debounce] Auto-cleaned {cleanup_count} expired entries")

        # 原有的防抖动逻辑
        last_time = _last_refresh.get(key, 0)

        if current_time - last_time > DEBOUNCE_SECONDS:
            _last_refresh[key] = current_time
            return True

        logger.info(f"[debounce] Skipping refresh for {key} (last refresh {current_time - last_time:.1f}s ago)")
        return False


# ────────────────────────────────────────────────────────────
# 统一信号处理系统（已改为异步）
# ────────────────────────────────────────────────────────────

def _refresh_user_or_couple_messages(user, trigger_source: str):
    """
    统一的消息刷新处理器 - 异步版本
    refresh the couple if there is one, otherwise the single user
    使用threading异步执行，不阻塞信号处理
    """
    try:
        # 用户级别的防抖动key
        debounce_key = f"user:{user.id}"

        # 防抖动检查
        if not _should_refresh(debounce_key):
            return

        # import the async task and fire it
        from .tasks import async_refresh_user_or_couple_messages

        # 直接调用，函数内部会创建新线程执行
        async_refresh_user_or_couple_messages(user.id, trigger_source)

        logger.info(f"[{trigger_source}] Queued async message refresh for {user.username}")

    except Exception as e:
        logger.error(f"[{trigger_source}] Error queuing async refresh for {user.username}: {e}")


# ────────────────────────────────────────────────────────────
# one signal receiver; the handlers are unchanged but now run asynchronously
# ────────────────────────────────────────────────────────────

# @receiver(user_logged_in)
# def on_user_login(sender, user, request, **kwargs):
#     """用户登录时触发消息检测"""
#     _refresh_user_or_couple_messages(user, "user_login")


@receiver(post_save, sender='recipes.IngredientPhotoProof')
def on_ingredient_proof_updated(sender, instance, **kwargs):
    """食材照片变化时触发消息更新 - 异步执行"""
    if instance.uploader:
        _refresh_user_or_couple_messages(instance.uploader, "ingredient_proof")


@receiver(post_save, sender='couplememory.MemoryEntry')
def on_memory_entry_updated(sender, instance, **kwargs):
    """做菜记录变化时触发消息更新 - 异步执行"""
    if instance.author:
        _refresh_user_or_couple_messages(instance.author, "memory_entry")


@receiver(post_save, sender='recipes.RoundBracket')
def on_round_bracket_updated(sender, instance, **kwargs):
    """轮次菜谱变化时触发消息更新 - 异步执行"""
    try:
        # RoundBracketno user attached, so debounce at couple level
        debounce_key = f"couple:{instance.couple.id}"
        if not _should_refresh(debounce_key):
            return

        # import the async task and fire it
        from .tasks import async_refresh_couple_messages

        # runs asynchronously without blocking; called directly and threaded internally
        async_refresh_couple_messages(instance.couple.id, "round_bracket")

        logger.info(f"[round_bracket] Queued async refresh for couple {instance.couple.code}")
    except Exception as e:
        logger.error(f"[round_bracket] Error queuing async refresh: {e}")


@receiver(post_save, sender='petcare.PetStatus')
def on_pet_status_updated(sender, instance, **kwargs):
    """宠物状态变化时触发消息更新 - 异步执行"""
    try:
        # PetStatusno user attached, so debounce at couple level
        debounce_key = f"couple:{instance.pet.couple.id}"
        if not _should_refresh(debounce_key):
            return

        # import the async task and fire it
        from .tasks import async_refresh_couple_messages

        # runs asynchronously without blocking; called directly and threaded internally
        async_refresh_couple_messages(instance.pet.couple.id, "pet_status")

        logger.info(f"[pet_status] Queued async refresh for couple {instance.pet.couple.code}")
    except Exception as e:
        logger.error(f"[pet_status] Error queuing async refresh: {e}")


# @receiver(post_save, sender='petcare.DicePocket')
# def on_dice_pocket_updated(sender, instance, **kwargs):
#     """骰子余额变化时触发消息更新 - 异步执行"""
#     _refresh_user_or_couple_messages(instance.user, "dice_pocket")


@receiver(post_save, sender='recipes.RecipeIngredientTask')
def on_recipe_task_updated(sender, instance, **kwargs):
    """食材任务变化时触发消息更新 - 异步执行"""
    if instance.user:
        _refresh_user_or_couple_messages(instance.user, "recipe_task")
    elif instance.couple:
        try:
            # 没有用户关联时，使用couple级别防抖动
            debounce_key = f"couple:{instance.couple.id}"
            if not _should_refresh(debounce_key):
                return

            # import the async task and fire it
            from .tasks import async_refresh_couple_messages

            # runs asynchronously without blocking; called directly and threaded internally
            async_refresh_couple_messages(instance.couple.id, "recipe_task")

            logger.info(f"[recipe_task] Queued async refresh for couple {instance.couple.code}")
        except Exception as e:
            logger.error(f"[recipe_task] Error queuing async refresh: {e}")


# ────────────────────────────────────────────────────────────
# 手动触发工具函数（已改为异步）
# ────────────────────────────────────────────────────────────

def manual_refresh_user_messages(user):
    """手动刷新用户消息状态 - 异步版本"""
    _refresh_user_or_couple_messages(user, "manual_user")


def manual_refresh_couple_messages(couple):
    """手动刷新couple消息状态 - 异步版本"""
    try:
        from .tasks import async_refresh_couple_messages

        # 异步执行（直接调用，内部创建线程）
        async_refresh_couple_messages(couple.id, "manual_couple")

        logger.info(f"[manual_couple] Queued async refresh for couple {couple.code}")
    except Exception as e:
        logger.error(f"[manual_couple] Error queuing async refresh: {e}")


def manual_refresh_all_messages():
    """手动刷新所有用户消息状态 - 异步版本"""
    try:
        from .tasks import async_bulk_refresh_all_messages

        # 异步执行批量刷新（直接调用，内部创建线程）
        async_bulk_refresh_all_messages("manual_bulk")

        logger.info(f"[manual_bulk] Queued async bulk refresh")
        return "Task queued successfully"
    except Exception as e:
        logger.error(f"[manual_bulk] Error queuing async bulk refresh: {e}")
        return f"Error: {str(e)}"


# ────────────────────────────────────────────────────────────
# 防抖动调试工具函数
# ────────────────────────────────────────────────────────────

def clear_debounce_cache():
    """清除防抖动缓存（调试用）- 线程安全版本"""
    with _refresh_lock:
        _last_refresh.clear()
    logger.info("[debounce] Cleared debounce cache")


def get_debounce_stats():
    """获取防抖动统计信息（调试用）- 线程安全版本"""
    current_time = time.time()
    active_debounces = []
    total_keys = 0

    with _refresh_lock:
        total_keys = len(_last_refresh)
        for key, last_time in _last_refresh.items():
            time_since = current_time - last_time
            if time_since < DEBOUNCE_SECONDS:
                active_debounces.append({
                    'key': key,
                    'seconds_since_refresh': round(time_since, 1),
                    'remaining_debounce': round(DEBOUNCE_SECONDS - time_since, 1)
                })

    return {
        'total_tracked_keys': total_keys,
        'currently_debounced': len(active_debounces),
        'debounce_window_seconds': DEBOUNCE_SECONDS,
        'thread_safe': True,
        'async_execution': True,  # 新增：标识使用异步执行
        'debounce_level': 'user_level',
        'active_debounces': active_debounces
    }


# ────────────────────────────────────────────────────────────
# scheduled-task support for SMS, left synchronous on purpose
# ────────────────────────────────────────────────────────────

def send_daily_sms_messages():
    """
    定时任务：为所有用户发送每日短信
    从每个激活状态随机选择一条消息，concat后发送

    this stays synchronous; SMS delivery was out of scope for the async work
    """
    try:
        from django.contrib.auth import get_user_model
        from .pet_message_service import get_random_messages_per_state

        User = get_user_model()
        users_with_couples = User.objects.filter(couple__isnull=False)

        success_count = 0
        error_count = 0

        for user in users_with_couples:
            try:
                # 获取该用户每个状态的随机消息
                messages = get_random_messages_per_state(user)

                if messages:
                    # 将所有消息concat成一条短信内容
                    sms_content = " | ".join(messages)

                    # TODO: 集成实际的短信发送服务
                    logger.info(f"[daily_sms] SMS to {user.username}: {sms_content}")

                    # 示例: 如果有短信服务，可以这样调用
                    # sms_service = apps.get_model('sms_service', 'SmsService')
                    # sms_service.send_message(user.phone, sms_content)

                    success_count += 1
                else:
                    logger.warning(f"[daily_sms] No messages for user {user.username}")

            except Exception as e:
                error_count += 1
                logger.error(f"[daily_sms] SMS sending error for {user.username}: {e}")

        logger.info(f"[daily_sms] Daily SMS completed: {success_count} success, {error_count} errors")
        return {'success': success_count, 'errors': error_count}

    except Exception as e:
        logger.error(f"[daily_sms] Daily SMS task failed: {e}")
        return {'error': str(e)}


def scheduled_refresh_all_messages():
    """
    定时任务：刷新所有用户消息（可选，用于定期更新状态）
    已改为异步版本
    """
    try:
        from .tasks import async_bulk_refresh_all_messages

        # 触发异步任务（直接调用，内部创建线程）
        async_bulk_refresh_all_messages("scheduled")

        logger.info(f"[scheduled] Queued async scheduled refresh")
        return {'status': 'queued', 'message': 'Task started successfully'}

    except Exception as e:
        logger.error(f"[scheduled] Error queuing scheduled refresh: {e}")
        return {'error': str(e)}

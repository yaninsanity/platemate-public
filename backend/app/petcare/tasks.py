# app/petcare/tasks.py

import logging
import threading
from typing import Dict, Any

logger = logging.getLogger(__name__)


def _run_in_thread(func, *args, **kwargs):
    """在新线程中运行函数的辅助函数"""
    thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()


def async_refresh_user_or_couple_messages(user_id: int, trigger_source: str) -> None:
    """
    异步任务：统一的消息刷新处理器
    refresh the couple if there is one, otherwise the single user

    the core state-detection task, covering:
    - 检测用户当前状态（state1-7）
    - 生成对应的宠物消息
    - 更新UserPetMessageState

    使用threading实现异步，不阻塞主线程

    Args:
        user_id: 用户ID
        trigger_source: 触发来源标识
    """
    def _task():
        try:
            from django.contrib.auth import get_user_model
            from .pet_message_service import refresh_user_pet_messages, refresh_couple_messages

            User = get_user_model()
            user = User.objects.get(id=user_id)

            if hasattr(user, 'couple') and user.couple:
                refresh_couple_messages(user.couple, trigger_source)
            else:
                refresh_user_pet_messages(user, trigger_source)

            logger.info(f"[{trigger_source}] Async refreshed messages for {user.username}")

        except Exception as e:
            logger.error(f"[{trigger_source}] Async error refreshing messages for user_id={user_id}: {e}")

    _run_in_thread(_task)


def async_refresh_couple_messages(couple_id: int, trigger_source: str) -> None:
    """
    异步任务：刷新couple消息

    为couple的两个成员执行状态验证和消息刷新

    Args:
        couple_id: Couple ID
        trigger_source: 触发来源标识
    """
    def _task():
        try:
            from couplememory.models import Couple
            from .pet_message_service import refresh_couple_messages

            couple = Couple.objects.get(id=couple_id)
            refresh_couple_messages(couple, trigger_source)

            logger.info(f"[{trigger_source}] Async refreshed couple {couple.code}")

        except Exception as e:
            logger.error(f"[{trigger_source}] Async error refreshing couple_id={couple_id}: {e}")

    _run_in_thread(_task)


def async_bulk_refresh_all_messages(trigger_source: str) -> None:
    """
    异步任务：批量刷新所有用户消息

    遍历所有用户，执行状态验证和消息刷新
    用于管理命令或定时任务

    Args:
        trigger_source: 触发来源标识
    """
    def _task():
        try:
            from .pet_message_service import bulk_refresh_all_messages

            count = bulk_refresh_all_messages(trigger_source)
            logger.info(f"[{trigger_source}] Async bulk refresh completed: {count} users updated")

        except Exception as e:
            logger.error(f"[{trigger_source}] Async bulk refresh failed: {e}")

    _run_in_thread(_task)

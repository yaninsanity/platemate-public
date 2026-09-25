# app/petcare/utils.py

import logging
from typing import Optional, List, Dict, Any
from django.contrib.auth import get_user_model
from django.apps import apps
from users.models import Couple

logger = logging.getLogger(__name__)
User = get_user_model()


# ────────────────────────────────────────────────────────────
# Pet Message Helper Functions - 更新版
# ────────────────────────────────────────────────────────────

def get_partner(user: User) -> Optional[User]:
    """
    the other member of the couple

    Args:
        user: user object

    Returns:
        Optional[User]: partneruser object，如果没有则返回None
    """
    try:
        if not hasattr(user, 'couple') or not user.couple:
            return None

        partners = user.couple.members.exclude(id=user.id)
        return partners.first()
    except Exception as e:
        logger.warning(f"Get partner error for {user.username}: {e}")
        return None


def get_current_recipe(user: User):
    """
    获取用户当前轮次的Recipe对象

    Args:
        user: user object

    Returns:
        Recipe: 菜谱对象，如果没有则返回None
    """
    try:
        if not hasattr(user, 'couple') or not user.couple:
            return None

        RoundBracket = apps.get_model('recipes', 'RoundBracket')
        bracket = RoundBracket.objects.filter(
            couple=user.couple
        ).order_by('-created_at').first()

        return bracket.active_recipe if bracket else None
    except Exception as e:
        logger.warning(f"Get current recipe error for {user.username}: {e}")
        return None


def get_current_recipe_name(user: User) -> Optional[str]:
    """
    获取用户当前轮次的菜谱名称

    Args:
        user: user object

    Returns:
        Optional[str]: 菜谱名称，如果没有则返回None
    """
    try:
        recipe = get_current_recipe(user)
        return recipe.name if recipe else None
    except Exception as e:
        logger.warning(f"Get recipe name error for {user.username}: {e}")
        return None


def get_current_round_number(couple: Couple) -> int:
    """
    获取当前轮次数（基于CoupleMemory数量）

    Args:
        couple: couple对象

    Returns:
        int: 轮次数（从1开始）
    """
    try:
        CoupleMemory = apps.get_model('couplememory', 'CoupleMemory')
        return CoupleMemory.objects.filter(couple=couple).count() + 1
    except Exception as e:
        logger.warning(f"Get round number error for couple {couple.code}: {e}")
        return 1


def is_pet_hungry(couple: Couple, threshold: int = 30) -> bool:
    """
    检查宠物是否饥饿

    Args:
        couple: couple对象
        threshold: 饥饿阈值，默认30

    Returns:
        bool: 是否饥饿
    """
    try:
        pet = getattr(couple, 'pet', None)
        if not pet:
            return False
        status = getattr(pet, 'status', None)
        return status and status.hunger < threshold
    except Exception as e:
        logger.warning(f"Pet hunger check error for couple {couple.code}: {e}")
        return False


def has_dice(user: User) -> bool:
    """
    检查用户是否有骰子

    Args:
        user: user object

    Returns:
        bool: 是否有骰子
    """
    try:
        DicePocket = apps.get_model('petcare', 'DicePocket')
        dice_pocket = DicePocket._get(user)
        return dice_pocket.balance > 0
    except Exception as e:
        logger.warning(f"Dice check error for {user.username}: {e}")
        return False


def user_uploaded_ingredients(user: User, recipe=None) -> bool:
    """
    检查用户是否已上传食材照片

    Args:
        user: user object
        recipe: the recipe to use, or the current one when None

    Returns:
        bool: 是否已上传
    """
    try:
        if not hasattr(user, 'couple') or not user.couple:
            return False

        if recipe is None:
            recipe = get_current_recipe(user)

        if not recipe:
            return False

        RecipeIngredientTask = apps.get_model('recipes', 'RecipeIngredientTask')
        return RecipeIngredientTask.objects.filter(
            user=user,
            recipe=recipe,
            is_uploaded=True
        ).exists()

    except Exception as e:
        logger.warning(f"Ingredient upload check error for {user.username}: {e}")
        return False


def user_completed_cooking(user: User) -> bool:
    """
    has the user finished cooking, that is, is there a MemoryEntry?

    Args:
        user: user object

    Returns:
        bool: 是否完成做菜
    """
    try:
        if not hasattr(user, 'couple') or not user.couple:
            return False

        CoupleMemory = apps.get_model('couplememory', 'CoupleMemory')
        MemoryEntry = apps.get_model('couplememory', 'MemoryEntry')

        current_memory = CoupleMemory.current(user.couple)
        return MemoryEntry.objects.filter(
            memory=current_memory,
            author=user
        ).exists()
    except Exception as e:
        logger.warning(f"Cooking completion check error for {user.username}: {e}")
        return False


def replace_message_variables(message: str, user: User) -> str:
    """
    替换消息模板中的变量

    Args:
        message: 原始消息模板
        user: user object

    Returns:
        str: 替换变量后的消息
    """
    try:
        # 获取recipe name
        recipe_name = get_current_recipe_name(user)

        # 替换变量
        result = message.replace('{{recipe.name}}', recipe_name or 'delicious recipe')

        # 可以在这里添加更多变量替换
        # result = result.replace('{{user.name}}', user.username)
        # result = result.replace('{{round.number}}', str(get_current_round_number(user.couple)))

        return result
    except Exception as e:
        logger.error(f"Message variable replacement error: {e}")
        return message


def get_user_state_summary(user: User) -> Dict[str, Any]:
    """
    获取用户状态摘要（调试用）

    Args:
        user: user object

    Returns:
        Dict: 状态摘要信息
    """
    try:
        partner = get_partner(user)
        recipe = get_current_recipe(user)

        return {
            'user': user.username,
            'couple': user.couple.code if hasattr(user, 'couple') and user.couple else None,
            'partner': partner.username if partner else None,
            'current_recipe': recipe.name if recipe else None,
            'round_number': get_current_round_number(user.couple) if hasattr(user, 'couple') and user.couple else None,
            'has_dice': has_dice(user),
            'uploaded_ingredients': user_uploaded_ingredients(user),
            'completed_cooking': user_completed_cooking(user),
            'pet_hungry': is_pet_hungry(user.couple) if hasattr(user, 'couple') and user.couple else False,
        }
    except Exception as e:
        logger.error(f"Get user state summary error: {e}")
        return {'error': str(e)}


def bulk_update_messages(users: List[User] = None, trigger_source: str = "bulk") -> Dict[str, int]:
    """
    批量更新用户消息

    Args:
        users: the users to update, or every paired user when None
        trigger_source: 触发源标识

    Returns:
        Dict: 更新结果统计
    """
    try:
        from .pet_message_service import refresh_user_pet_messages

        if users is None:
            users = User.objects.filter(couple__isnull=False)

        success_count = 0
        error_count = 0
        errors = []

        for user in users:
            try:
                refresh_user_pet_messages(user, trigger_source)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"{user.username}: {str(e)}")
                logger.error(f"[{trigger_source}] Bulk update error for {user.username}: {e}")

        result = {
            'success': success_count,
            'errors': error_count,
            'total': len(users),
        }

        if errors:
            result['error_details'] = errors

        logger.info(f"[{trigger_source}] Bulk message update completed: {success_count} success, {error_count} errors")
        return result

    except Exception as e:
        logger.error(f"[{trigger_source}] Bulk update messages error: {e}")
        return {'error': str(e)}


# ────────────────────────────────────────────────────────────
# 调试和监控工具
# ────────────────────────────────────────────────────────────

def debug_user_states(user: User) -> str:
    """
    调试用：打印用户的详细状态信息

    Args:
        user: user object

    Returns:
        str: 格式化的调试信息
    """
    summary = get_user_state_summary(user)

    output = [
        f"=== Pet Message Debug Info for {user.username} ===",
        f"Couple: {summary.get('couple', 'None')}",
        f"Partner: {summary.get('partner', 'None')}",
        f"Current Recipe: {summary.get('current_recipe', 'None')}",
        f"Round Number: {summary.get('round_number', 'Unknown')}",
        "",
        "Status Checks:",
        f"  - Has Dice: {summary.get('has_dice', False)}",
        f"  - Uploaded Ingredients: {summary.get('uploaded_ingredients', False)}",
        f"  - Completed Cooking: {summary.get('completed_cooking', False)}",
        f"  - Pet Hungry: {summary.get('pet_hungry', False)}",
        "",
    ]

    # 获取当前消息状态
    try:
        from .models import UserPetMessageState
        state = UserPetMessageState.objects.filter(user=user).first()
        if state:
            output.extend([
                "Current Message State:",
                f"  - Active States: {state.current_states}",
                f"  - Message Count: {len(state.available_messages)}",
                f"  - Last Updated: {state.last_updated}",
            ])
        else:
            output.append("Current Message State: Not found")
    except Exception as e:
        output.append(f"Message State Error: {e}")

    output.append("=" * 50)
    return "\n".join(output)


def debug_couple_states(couple: Couple) -> str:
    """
    调试用：打印couple的详细状态信息

    Args:
        couple: couple对象

    Returns:
        str: 格式化的调试信息
    """
    output = [
        f"=== Couple Debug Info for {couple.code} ===",
        f"Members: {[u.username for u in couple.members.all()]}",
        "",
    ]

    for user in couple.members.all():
        user_debug = debug_user_states(user)
        output.append(user_debug)
        output.append("")

    return "\n".join(output)


# ────────────────────────────────────────────────────────────
# 短信相关辅助函数
# ────────────────────────────────────────────────────────────

def generate_daily_sms_content(user: User) -> str:
    """
    为用户生成每日短信内容
    从每个激活状态随机选择一条消息

    Args:
        user: user object

    Returns:
        str: 短信内容
    """
    try:
        from .pet_message_service import get_random_messages_per_state

        messages = get_random_messages_per_state(user)
        if messages:
            return " | ".join(messages)
        else:
            return "Hi there! Keep cooking and having fun!"

    except Exception as e:
        logger.error(f"Generate SMS content error for {user.username}: {e}")
        return "Hi there! Keep cooking and having fun!"


def get_all_users_for_sms() -> List[User]:
    """
    获取所有需要接收短信的用户

    Returns:
        List[User]: 用户列表
    """
    try:
        # 获取所有有couple且开启短信的用户
        return User.objects.filter(
            couple__isnull=False,
            sms_opt_in=True,
            phone__isnull=False
        ).exclude(phone='')
    except Exception as e:
        logger.error(f"Get SMS users error: {e}")
        return []


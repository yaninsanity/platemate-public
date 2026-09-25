# app/petcare/pet_message_service.py
import logging
import random
from typing import List, Optional, Dict

from datetime import timedelta
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone

# 必要的import
from .models import PetMessageTemplate, UserPetMessageState
from users.models import Couple

logger = logging.getLogger(__name__)
User = get_user_model()


class PetMessageService:
    """宠物消息服务类 - 重构版"""

    @classmethod
    def _get_current_couple_memory(cls, couple):
        """
        fetch the active CoupleMemory; query only, never create
        take the newest CoupleMemory and check today falls inside its window
        """
        try:
            CoupleMemory = apps.get_model('couplememory', 'CoupleMemory')

            # 获取该couple最新的CoupleMemory
            latest_memory = CoupleMemory.objects.filter(
                couple=couple
            ).order_by('-round_start').first()

            if not latest_memory:
                return None

            # 检查当前日期是否在开始和结束日期之间
            today = timezone.localtime(timezone.now()).date()
            if latest_memory.round_start <= today <= latest_memory.round_end:
                return latest_memory
            else:
                # 最新的memory已过期，当前不在有效轮次中
                return None

        except Exception as e:
            logger.warning(f"Get current couple memory error for {couple.code}: {e}")
            return None

    @classmethod
    def refresh_user_pet_messages(cls, user: User, trigger_source: str = "unknown") -> UserPetMessageState:
        """
        统一入口：刷新用户的宠物消息状态

        Args:
            user: user object
            trigger_source: 触发源名称，用于日志记录

        Returns:
            UserPetMessageState: 更新后的用户消息状态
        """
        try:
            # 1. 检测当前激活状态
            current_states = cls.detect_user_states_from_db(user)

            # 2. 获取或创建用户状态对象
            user_state, created = UserPetMessageState.objects.get_or_create(
                user=user,
                defaults={
                    'couple': user.couple if hasattr(user, 'couple') and user.couple else None
                }
            )

            # 3. 生成可用消息列表
            available_messages = cls.generate_messages_for_states(current_states, user)

            # 4. 更新状态
            user_state.current_states = current_states
            user_state.available_messages = available_messages
            user_state.save()

            logger.info(f"[{trigger_source}] Updated messages for user {user.username}: {current_states}")
            return user_state

        except Exception as e:
            logger.error(f"[{trigger_source}] Failed to refresh messages for user {user.username}: {e}")
            raise

    @classmethod
    def detect_user_states_from_db(cls, user: User) -> List[str]:
        """
        统一的状态检测方法：完全基于数据库状态

        Returns:
            List[str]: 激活状态列表，如 ['state1', 'state3']
        """
        if not hasattr(user, 'couple') or not user.couple:
            return ['state1']  # 没有couple的用户默认state1

        active_states = []

        # State1和State2互斥检测
        if cls._is_state1(user):
            active_states.append('state1')

        elif cls._is_state2(user):
            active_states.append('state2')

        # State3: 宠物饥饿 (可以与其他状态并存)
        if cls._is_state3(user):
            active_states.append('state3')

        # State6: Partner上传了食材照片，自己还没上传
        if cls._is_state6(user):
            active_states.append('state6')

        # State7: Partner完成了做菜，自己还没完成
        if cls._is_state7(user):
            active_states.append('state7')

        # 如果没有任何状态，给默认状态
        if not active_states:
            active_states = ['state1']

        return active_states

    # ────────────────────────────────────────────────────────────
    # 状态检测方法 - 基于数据库状态
    # ────────────────────────────────────────────────────────────

    @classmethod
    def _is_state1(cls, user: User) -> bool:
        """State1: 上传食材照片前 (或默认状态)"""
        try:
            logger.debug(f"Checking State1 for user {user.username}")

            # 直接获取最新bracket，避免触发副作用
            RoundBracket = apps.get_model('recipes', 'RoundBracket')
            bracket = RoundBracket.objects.filter(
                couple=user.couple
            ).order_by('-created_at').first()

            if not bracket or not bracket.active_recipe:
                logger.debug(f"User {user.username} has no bracket or active recipe - State1")
                return True

            # 检查用户是否上传了食材照片
            uploaded = cls._user_uploaded_ingredients(user, bracket.active_recipe)
            result = not uploaded
            logger.debug(f"State1 result for {user.username}: {result} (uploaded: {uploaded})")
            return result

        except Exception as e:
            logger.warning(f"State1 detection error for {user.username}: {e}")
            return True  # 出错时返回默认状态

    @classmethod
    def _is_state2(cls, user: User) -> bool:
        """State2: 上传食材后，完成做菜前"""
        try:
            # 如果是State1，则不能是State2（互斥）
            if cls._is_state1(user):
                return False

            # does the user have a MemoryEntry in the current CoupleMemory?
            return not cls._user_completed_cooking(user)

        except Exception as e:
            logger.warning(f"State2 detection error for {user.username}: {e}")
            return False

    @classmethod
    def _is_state3(cls, user: User) -> bool:
        """State3: 宠物饥饿"""
        try:
            pet = getattr(user.couple, 'pet', None)
            if not pet:
                return False
            status = getattr(pet, 'status', None)
            return status and status.hunger < 30
        except Exception as e:
            logger.warning(f"State3 detection error for {user.username}: {e}")
            return False


    @classmethod
    def _is_state6(cls, user: User) -> bool:
        """State6: Partner上传了食材，但自己还没上传"""
        try:
            partner = cls._get_partner(user)
            if not partner:
                return False

            # 获取当前recipe
            current_recipe = cls._get_current_recipe(user)
            if not current_recipe:
                return False

            # 自己还没上传食材 且 partner已上传食材
            user_not_uploaded = not cls._user_uploaded_ingredients(user, current_recipe)
            partner_uploaded = cls._user_uploaded_ingredients(partner, current_recipe)

            return user_not_uploaded and partner_uploaded

        except Exception as e:
            logger.warning(f"State6 detection error for {user.username}: {e}")
            return False

    @classmethod
    def _is_state7(cls, user: User) -> bool:
        """State7: Partner完成了做菜，但自己还没完成"""
        try:
            partner = cls._get_partner(user)
            if not partner:
                return False

            # 自己没有完成做菜 且 partner已完成做菜
            user_not_completed = not cls._user_completed_cooking(user)
            partner_completed = cls._user_completed_cooking(partner)

            return user_not_completed and partner_completed

        except Exception as e:
            logger.warning(f"State7 detection error for {user.username}: {e}")
            return False

    # ────────────────────────────────────────────────────────────
    # Helper检测方法
    # ────────────────────────────────────────────────────────────

    @classmethod
    def _user_uploaded_ingredients(cls, user: User, recipe) -> bool:
        """检查用户是否已上传指定recipe的食材照片"""
        try:
            if not recipe:
                return False

            RecipeIngredientTask = apps.get_model('recipes', 'RecipeIngredientTask')

            # 检查用户是否有该recipe的已上传任务
            task = RecipeIngredientTask.objects.filter(
                user=user,
                recipe=recipe,
                is_uploaded=True
            ).first()

            result = bool(task)
            logger.debug(f"User {user.username} ingredient upload status for {recipe.name}: {result}")
            return result

        except Exception as e:
            logger.warning(f"Ingredient upload check error for {user.username}: {e}")
            return False

    @classmethod
    def _user_completed_cooking(cls, user: User) -> bool:
        """has the user finished cooking, that is, is there a MemoryEntry?"""
        try:
            CoupleMemory = apps.get_model('couplememory', 'CoupleMemory')
            MemoryEntry = apps.get_model('couplememory', 'MemoryEntry')

            # avoid the unreliable current() and resolve it here instead
            current_memory = cls._get_current_couple_memory(user.couple)
            if not current_memory:
                return False

            return MemoryEntry.objects.filter(
                memory=current_memory,
                author=user
            ).exists()
        except Exception as e:
            logger.warning(f"Cooking completion check error for {user.username}: {e}")
            return False

    @classmethod
    def _get_partner(cls, user: User) -> Optional[User]:
        """the other member of the couple"""
        try:
            if not hasattr(user, 'couple') or not user.couple:
                return None

            partners = user.couple.members.exclude(id=user.id)
            return partners.first()
        except Exception as e:
            logger.warning(f"Get partner error for {user.username}: {e}")
            return None

    @classmethod
    def _get_current_recipe(cls, user: User):
        """获取当前轮次的recipe"""
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

    # ────────────────────────────────────────────────────────────
    # 消息生成方法
    # ────────────────────────────────────────────────────────────

    @classmethod
    def generate_messages_for_states(cls, states: List[str], user: User) -> Dict[str, List[str]]:
        """
        为指定状态生成消息，返回按状态分组的字典结构

        Args:
            states: 状态列表
            user: user object

        Returns:
            Dict[str, List[str]]: 按状态分组的消息字典 {'state1': ['msg1', 'msg2'], 'state3': ['msg3']}
        """
        messages_by_state = {}

        for state in states:
            try:
                templates = PetMessageTemplate.objects.filter(
                    state_code=state,
                    is_active=True
                )

                state_messages = []
                for template in templates:
                    message = cls._replace_template_variables(template.message_template, user)
                    state_messages.append(message)

                # 只有当该状态有消息时才添加到结果中
                if state_messages:
                    messages_by_state[state] = state_messages

            except Exception as e:
                logger.error(f"Error generating messages for state {state}: {e}")

        return messages_by_state

    @classmethod
    def get_random_message_per_state(cls, user: User) -> List[str]:
        """
        从每个激活状态中随机选择一条消息
        用于定时短信发送

        Returns:
            List[str]: 每个状态的随机消息列表
        """
        try:
            current_states = cls.detect_user_states_from_db(user)
            messages = []

            for state in current_states:
                try:
                    templates = PetMessageTemplate.objects.filter(
                        state_code=state,
                        is_active=True
                    )

                    if templates.exists():
                        # 按权重随机选择
                        template = cls._weighted_random_choice(templates)
                        if template:
                            message = cls._replace_template_variables(template.message_template, user)
                            messages.append(message)

                except Exception as e:
                    logger.error(f"Error getting random message for state {state}: {e}")

            return messages

        except Exception as e:
            logger.error(f"Error getting random messages for user {user.username}: {e}")
            return ["Hi there! Keep cooking and having fun!"]

    @classmethod
    def _weighted_random_choice(cls, templates):
        """按权重随机选择模板"""
        try:
            total_weight = sum(t.weight for t in templates)
            if total_weight <= 0:
                return random.choice(templates)

            r = random.uniform(0, total_weight)
            upto = 0
            for template in templates:
                if upto + template.weight >= r:
                    return template
                upto += template.weight

            return templates.last()

        except Exception as e:
            logger.error(f"Weighted random choice error: {e}")
            return random.choice(templates) if templates else None

    @classmethod
    def _replace_template_variables(cls, template: str, user: User) -> str:
        """
        替换模板中的变量

        Args:
            template: 消息模板
            user: user object

        Returns:
            str: 替换变量后的消息
        """
        try:
            # 获取当前recipe name
            recipe_name = cls._get_current_recipe_name(user)

            # 替换变量
            message = template.replace('{{recipe.name}}', recipe_name or 'delicious recipe')

            return message
        except Exception as e:
            logger.error(f"Template variable replacement error: {e}")
            return template

    @classmethod
    def _get_current_recipe_name(cls, user: User) -> Optional[str]:
        """获取当前轮次的菜谱名称"""
        try:
            current_recipe = cls._get_current_recipe(user)
            return current_recipe.name if current_recipe else None
        except Exception as e:
            logger.warning(f"Get recipe name error for {user.username}: {e}")
            return None


# ────────────────────────────────────────────────────────────
# 便捷接口函数
# ────────────────────────────────────────────────────────────

def refresh_user_pet_messages(user: User, trigger_source: str = "manual") -> UserPetMessageState:
    """刷新用户宠物消息的便捷接口"""
    return PetMessageService.refresh_user_pet_messages(user, trigger_source)


def get_user_messages(user: User) -> Dict[str, List[str]]:
    """获取用户可用消息的便利接口（返回dict结构）"""
    try:
        state = UserPetMessageState.objects.filter(user=user).first()
        return state.available_messages if state else {}
    except Exception as e:
        logger.error(f"Get user messages error: {e}")
        return {}


def get_user_messages_flat(user: User) -> List[str]:
    """获取用户所有消息的平面列表（向后兼容）"""
    try:
        state = UserPetMessageState.objects.filter(user=user).first()
        if state and state.available_messages:
            all_messages = []
            for state_messages in state.available_messages.values():
                all_messages.extend(state_messages)
            return all_messages
        return ["Hi there! Keep cooking and having fun!"]
    except Exception as e:
        logger.error(f"Get user messages flat error: {e}")
        return ["Hi there! Keep cooking and having fun!"]


def get_random_user_message(user: User) -> str:
    """获取用户随机消息的便捷接口"""
    try:
        state = UserPetMessageState.objects.filter(user=user).first()
        return state.get_random_message() if state else "Hi there! Keep cooking and having fun!"
    except Exception as e:
        logger.error(f"Get random message error: {e}")
        return "Hi there! Keep cooking and having fun!"


def get_random_messages_per_state(user: User) -> List[str]:
    """获取每个状态的随机消息（用于定时短信）"""
    return PetMessageService.get_random_message_per_state(user)


def refresh_couple_messages(couple: Couple, trigger_source: str = "manual"):
    """刷新整个couple的消息状态"""
    try:
        for user in couple.members.all():
            refresh_user_pet_messages(user, trigger_source)
        logger.info(f"[{trigger_source}] Refreshed messages for couple {couple.code}")
    except Exception as e:
        logger.error(f"[{trigger_source}] Error refreshing couple messages: {e}")


def bulk_refresh_all_messages(trigger_source: str = "bulk") -> int:
    """批量刷新所有用户消息（用于管理命令）"""
    try:
        updated_count = 0
        for user in User.objects.filter(couple__isnull=False):
            try:
                refresh_user_pet_messages(user, trigger_source)
                updated_count += 1
            except Exception as e:
                logger.error(f"[{trigger_source}] Error refreshing messages for user {user.username}: {e}")

        logger.info(f"[{trigger_source}] Bulk refreshed messages for {updated_count} users")
        return updated_count

    except Exception as e:
        logger.error(f"[{trigger_source}] Error in bulk refresh: {e}")
        return 0


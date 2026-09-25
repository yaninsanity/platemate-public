# apps/recipes/signals.py

import logging
from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import RecipeIngredientTask

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 1. COOK 活动：任务验证后触发
# ─────────────────────────────────────────────────────────────
@receiver(post_save, sender=RecipeIngredientTask)
def handle_task_verification(sender, instance, created, **kwargs):
    if not created and instance.is_verified and instance.couple:
        try:
            Activity = apps.get_model('petcare', 'Activity')
            Activity.cook(instance)
            logger.debug(f"signal▶ COOK activity for task {instance.pk}")
        except Exception:
            logger.exception("failed to log COOK activity for task %s", instance.pk)


# ─────────────────────────────────────────────────────────────
# 2. PHOTO / COMPLIMENT / AI bonus 活动：只在这三个模型还存在时才绑定
# ─────────────────────────────────────────────────────────────
def _lazy_bind_if_exists(model_name, signal_fn):
    """
    helper：仅当 'recipes'.model_name 真正还在时候，才做 @receiver 绑定
    """
    try:
        Model = apps.get_model('recipes', model_name)
    except LookupError:
        return
    post_save.connect(signal_fn, sender=Model, weak=False)


def _handle_photo(sender, instance, created, **kwargs):
    # CookingDiary → PHOTO
    couple = getattr(instance, 'couple', None)
    if created and couple:
        try:
            Activity = apps.get_model('petcare', 'Activity')
            Activity.create_generic(couple, Activity.PHOTO, {'diary_id': instance.pk})
            logger.debug(f"signal▶ PHOTO activity for diary {instance.pk}")
        except Exception:
            logger.exception("failed to log PHOTO activity for diary %s", instance.pk)


def _handle_compliment(sender, instance, created, **kwargs):
    # Comment → COMPLIMENT
    diary = getattr(instance, 'diary', None)
    couple = getattr(diary, 'couple', None)
    if created and couple:
        try:
            Activity = apps.get_model('petcare', 'Activity')
            Activity.create_generic(couple, Activity.COMPLIMENT, {'comment_id': instance.pk})
            logger.debug(f"signal▶ COMPLIMENT activity for comment {instance.pk}")
        except Exception:
            logger.exception("failed to log COMPLIMENT activity for comment %s", instance.pk)


def _handle_bracket_ai(sender, instance, created, **kwargs):
    # RoundBracket → AI bonus
    if not created and getattr(instance, 'active_recipe', None):
        # updated_at 需要你的模型里有
        updated = getattr(instance, 'updated_at', None)
        if updated and (timezone.localtime(timezone.now()) - updated).total_seconds() < 5:
            try:
                Activity = apps.get_model('petcare', 'Activity')
                Activity.create_generic(
                    instance.couple,
                    Activity.AI,
                    {'bracket_id': instance.pk, 'recipe_id': instance.active_recipe_id}
                )
                logger.debug(f"signal▶ AI bonus for bracket {instance.pk}")
            except Exception:
                logger.exception("failed to log AI bonus for bracket %s", instance.pk)


# 绑定三个惰性信号
_lazy_bind_if_exists('CookingDiary',     _handle_photo)
_lazy_bind_if_exists('Comment',          _handle_compliment)
_lazy_bind_if_exists('RoundBracket',     _handle_bracket_ai)

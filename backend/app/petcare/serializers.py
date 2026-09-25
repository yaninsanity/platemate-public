# apps/petcare/serializers.py
from django.apps import apps
from rest_framework import serializers
from rest_framework.reverse import reverse

from users.models import Couple
from recipes.models import RecipeIngredientTask

from .models import (
    Activity, Pet, PetStatus, PetFeed,
    Mission, Reminder, ReminderRule,
    RewardBox, Badge, PetMessage, DicePocket,
    PetMessageTemplate, UserPetMessageState
)

# ────────────────────────────────────────────────────────────
# 1. 基础序列化
# ────────────────────────────────────────────────────────────
class CoupleField(serializers.StringRelatedField):
    """display couple.code read-only while writes still use the primary key."""
    def to_representation(self, value):
        return getattr(value, "code", str(value))


# ────────────────────────────────────────────────────────────
# 2. Activity
# ────────────────────────────────────────────────────────────
class ActivitySerializer(serializers.ModelSerializer):
    couple   = CoupleField(read_only=True)
    couple_id = serializers.PrimaryKeyRelatedField(
        queryset=Couple.objects.all(), source="couple", write_only=True, required=False
    )
    recipe   = serializers.PrimaryKeyRelatedField(
        queryset=RecipeIngredientTask.objects.all(), allow_null=True, required=False
    )
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model  = Activity
        fields = (
            "id", "couple", "couple_id",
            "kind", "kind_display", "points", "streak",
            "recipe", "metadata", "created",
        )
        read_only_fields = ("id", "points", "streak", "created")


# ────────────────────────────────────────────────────────────
# 3. Pet & status
# ────────────────────────────────────────────────────────────
class PetStatusSerializer(serializers.ModelSerializer):
    # 🎯 make sure last_tick serialises as a date
    last_tick = serializers.DateField(read_only=True)
    
    class Meta:
        model  = PetStatus
        fields = ("hunger", "happiness", "hygiene", "last_tick")
        read_only_fields = fields

class PetSerializer(serializers.ModelSerializer):
    couple    = CoupleField(read_only=True)
    species_display = serializers.CharField(source="get_species_display", read_only=True)
    status    = PetStatusSerializer(read_only=True)
    xp_progress = serializers.SerializerMethodField()

    class Meta:
        model  = Pet
        fields = (
            "id", "couple", "species", "species_display",
            "nickname", "skin", "level",
            "xp", "next_level", "xp_progress",
            "created", "updated", "status",
        )
        read_only_fields = ("id", "level", "xp", "next_level", "created", "updated")

    def get_xp_progress(self, obj):
        return {"current": obj.xp, "need": obj.next_level}


# ────────────────────────────────────────────────────────────
# 4. PetFeed
# ────────────────────────────────────────────────────────────
class PetFeedSerializer(serializers.ModelSerializer):
    couple   = CoupleField(read_only=True)
    couple_id = serializers.PrimaryKeyRelatedField(
        queryset=Couple.objects.all(), source="couple", write_only=True, required=False
    )

    class Meta:
        model  = PetFeed
        fields = ("id", "couple", "couple_id", "fed_at", "food_type", "amount")
        read_only_fields = ("id", "fed_at")


# ────────────────────────────────────────────────────────────
# 5. Mission
# ────────────────────────────────────────────────────────────
class MissionSerializer(serializers.ModelSerializer):
    couple   = CoupleField(read_only=True)
    period_display = serializers.CharField(source="get_period_display", read_only=True)
    progress_ratio = serializers.SerializerMethodField()

    class Meta:
        model  = Mission
        fields = (
            "id", "couple", "period", "period_display",
            "start", "end", "description",
            "target_kind", "target_cnt", "progress", "progress_ratio",
            "reward_pts", "is_done",
        )
        read_only_fields = ("id", "progress", "is_done")

    def get_progress_ratio(self, obj):
        return f"{obj.progress}/{obj.target_cnt}"


# ────────────────────────────────────────────────────────────
# 6. Reminder & Rule
# ────────────────────────────────────────────────────────────
class ReminderSerializer(serializers.ModelSerializer):
    couple   = CoupleField(read_only=True)

    class Meta:
        model  = Reminder
        fields = ("id", "couple", "next_fire", "template", "sent_at")
        read_only_fields = ("id", "sent_at")

class ReminderRuleSerializer(serializers.ModelSerializer):
    couple   = CoupleField(read_only=True)

    class Meta:
        model  = ReminderRule
        fields = ("id", "couple", "hour", "minute")
        read_only_fields = ("id",)


# ────────────────────────────────────────────────────────────
# 7. RewardBox
# ────────────────────────────────────────────────────────────
class RewardBoxSerializer(serializers.ModelSerializer):
    couple   = CoupleField(read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    open_url = serializers.SerializerMethodField()

    class Meta:
        model  = RewardBox
        fields = (
            "id", "couple", "source", "source_display",
            "created", "opened_at", "content", "open_url",
        )
        read_only_fields = ("id", "created", "opened_at", "content")

    def get_open_url(self, obj):
        req = self.context.get("request")
        try:
            return reverse("rewardbox-open", args=[obj.pk], request=req)
        except Exception:
            return None


# ────────────────────────────────────────────────────────────
# 8. Badge
# ────────────────────────────────────────────────────────────
class BadgeSerializer(serializers.ModelSerializer):
    couples = CoupleField(many=True, read_only=True)

    class Meta:
        model  = Badge
        fields = ("slug", "desc", "couples", "added")
        read_only_fields = fields


# ────────────────────────────────────────────────────────────
# 9. PetMessage
# ────────────────────────────────────────────────────────────
class PetMessageSerializer(serializers.ModelSerializer):
    couple   = CoupleField(read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model  = PetMessage
        fields = (
            "id", "couple", "type", "type_display",
            "content", "created_at", "is_read",
        )
        read_only_fields = ("id", "created_at")


# ────────────────────────────────────────────────────────────
# 10. DicePocket
# ────────────────────────────────────────────────────────────
class DicePocketSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model  = DicePocket
        fields = ("id", "user", "balance", "updated")
        read_only_fields = ("id", "updated")


# ────────────────────────────────────────────────────────────
# 11. Pet Message State
# ────────────────────────────────────────────────────────────
class PetMessageStateSerializer(serializers.ModelSerializer):
    """宠物消息状态序列化器 - 支持状态名称映射"""

    # rewrite available_messages into a nested structure
    available_messages = serializers.SerializerMethodField()

    class Meta:
        model = UserPetMessageState
        fields = (
            "current_states",
            "available_messages",
            "last_updated"
        )
        read_only_fields = fields

    def get_available_messages(self, obj):
        """转换消息格式：从dict到嵌套对象结构"""
        from .models import STATE_NAME_MAPPING

        if not obj.available_messages:
            return {}

        # 转换格式
        formatted_messages = {}

        # 处理dict结构的消息数据
        if isinstance(obj.available_messages, dict):
            for state_id, messages in obj.available_messages.items():
                formatted_messages[state_id] = {
                    "name": STATE_NAME_MAPPING.get(state_id, ""),  # 未知状态name为空
                    "messages": messages if isinstance(messages, list) else []
                }

        return formatted_messages


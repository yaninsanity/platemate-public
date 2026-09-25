from __future__ import annotations
from typing import List, Optional

from django.contrib.auth import get_user_model
from rest_framework import serializers
from recipes.serializers import AbsoluteImageField

from .models import (
    CoupleMemory,
    MemoryEntry,
    MemoryMedia,
    MemoryComment,
    AIJudgment,
)

User = get_user_model()


# ───────────────────────────────────────── helpers ──────────────────────────
def safe_url(field) -> Optional[str]:
    """Return absolute URL or None (handles missing file gracefully)."""
    if not field or not getattr(field, "name", ""):
        return None
    try:
        return field.url
    except ValueError:
        return None


# ───────────────────────────────────────── media ────────────────────────────
class MemoryMediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model  = MemoryMedia
        fields = ["id", "url", "media", "created_at", "is_highlight"]
        extra_kwargs  = {"media": {"write_only": True, "required": True}}
        read_only_fields = ["id", "url", "created_at"]

    def get_url(self, obj):
        request = self.context.get("request")
        file_url = safe_url(obj.media)
        if request and file_url:
            return request.build_absolute_uri(file_url).replace(request.get_host(), f"{request.get_host()}:911")
        return file_url


# ───────────────────────────────────────── ai judgment ──────────────────────────
class AIJudgmentSerializer(serializers.ModelSerializer):
    metrics_breakdown = serializers.ReadOnlyField()
    average_metrics = serializers.ReadOnlyField()
    has_battle_data = serializers.ReadOnlyField()
    effective_comment = serializers.ReadOnlyField()
    effective_summary = serializers.ReadOnlyField()

    class Meta:
        model = AIJudgment
        fields = [
            "id", "overall_score", "visual_appeal", "cooking_technique", 
            "ingredient_freshness", 
            # 新的分离评语系统
            "individual_comment", "individual_summary",
            "battle_comment", "battle_summary", "battle_result",
            # 向后兼容
            "ai_comment", "ai_summary", 
            "confidence", "model_version", "created_at", "updated_at",
            # computed
            "metrics_breakdown", "average_metrics", "has_battle_data",
            "effective_comment", "effective_summary"
        ]
        read_only_fields = fields


# ───────────────────────────────────────── comment ──────────────────────────
class MemoryCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model  = MemoryComment
        fields = [
            "id", "entry", "author", "author_username",
            "content", "emoji", "created_at",
        ]
        read_only_fields = ["id", "author", "author_username", "created_at"]


# ───────────────────────────────────── entry (full) ─────────────────────────
class MemoryEntryReadSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    media           = MemoryMediaSerializer(many=True, read_only=True)
    comments        = MemoryCommentSerializer(many=True, read_only=True)
    ai_judgment     = AIJudgmentSerializer(read_only=True)
    best_media_url  = serializers.SerializerMethodField()
    effective_ai_score = serializers.ReadOnlyField()
    ai_metrics      = serializers.ReadOnlyField()

    class Meta:
        model  = MemoryEntry
        fields = [
            "id", "memory", "author", "author_username",
            "recipe", "content", "mood", "ai_score", "created_at",
            "media", "comments", "ai_judgment", "best_media_url",
            "effective_ai_score", "ai_metrics",
        ]
        read_only_fields = fields

    def get_best_media_url(self, obj):
        m = obj.media.filter(is_highlight=True).first()
        if not m:
            m = obj.media.order_by("-created_at").first()
        return safe_url(m.media) if m else None


# ─────────────────────────────────── entry (write) ──────────────────────────
class MemoryEntryWriteSerializer(serializers.ModelSerializer):
    files = serializers.ListField(
        child      = serializers.FileField(max_length=5 * 1024 * 1024),
        max_length = 10,
        write_only = True,
        required   = False,
        help_text  = "可选，多文件上传",
    )

    class Meta:
        model  = MemoryEntry
        fields = ["id", "memory", "recipe", "content", "mood", "files"]
        read_only_fields = ["id", "memory"]

    # bulk-insert medias when creating
    def create(self, validated_data):
        files: List = validated_data.pop("files", [])
        entry = super().create(validated_data)
        if files:
            MemoryMedia.objects.bulk_create(
                [MemoryMedia(entry=entry, media=f) for f in files]
            )
        return entry

    def update(self, instance, validated_data):
        validated_data.pop("files", None)
        return super().update(instance, validated_data)


# ─────────────────────────── entry (mini for winner) ────────────────────────
class MemoryEntryMiniSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    best_media_url  = serializers.SerializerMethodField()
    recipe_name     = serializers.SerializerMethodField()

    class Meta:
        model  = MemoryEntry
        fields = ("id", "author_username", "ai_score", "best_media_url", "recipe_name")
        read_only_fields = fields

    def get_best_media_url(self, obj):
        m = obj.media.filter(is_highlight=True).first()
        if not m:
            m = obj.media.order_by("-created_at").first()
        return safe_url(m.media) if m else None

    def get_recipe_name(self, obj):
        """Return recipe name if exists"""
        if obj.recipe:
            return obj.recipe.name
        return None


# ───────────────────────────────────── couple memory ────────────────────────
class CoupleMemorySerializer(serializers.ModelSerializer):
    entries         = MemoryEntryReadSerializer(many=True, read_only=True)
    winner_entry    = MemoryEntryMiniSerializer(read_only=True)   # ← mini object
    cover_photo     = serializers.SerializerMethodField()
    top_ingredients = serializers.SerializerMethodField()

    class Meta:
        model  = CoupleMemory
        fields = [
            "id", "couple", "round_start", "round_end", "summary",
            "winner_entry", "total_points", "entries_count", "comments_count",
            "created_at", "updated_at",
            "cover_photo", "top_ingredients", "entries",
        ]
        read_only_fields = fields

    # ---------- helpers ----------
    def get_cover_photo(self, obj):
        # ① winner entry thumbnail
        if obj.winner_entry:
            m = obj.winner_entry.media.order_by("-created_at").first()
            if m_url := safe_url(m.media if m else None):
                return m_url
        # ② fallback: very first photo of the round
        m = MemoryMedia.objects.filter(entry__memory=obj).order_by("created_at").first()
        return safe_url(m.media) if m else None

    def get_top_ingredients(self, obj):
        return obj.top_ingredients()


# 向后兼容旧引用名
MemoryEntrySerializer = MemoryEntryReadSerializer

"""PlateMate – Couple Memory System (Enhanced AI Integration)
Complete roundly memories + AI scoring + gamified rewards + couple battle system
"""
from __future__ import annotations

import threading
import logging
from datetime import timedelta
from typing import Optional, Dict

from django.db import models, transaction
from django.db.models import Count, F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.apps import apps
from django.contrib.auth import get_user_model
from django.conf import settings

from users.models import Couple
from recipes.models import Recipe, RoundBracket

logger = logging.getLogger(__name__)
User = get_user_model()

# ═══════════════════════════════════════════════════════════════
# Constants & Configuration
# ═══════════════════════════════════════════════════════════════
AI_SCORE_MAX       = 100
PHOTO_REWARD_PTS   = 1
COMMENT_REWARD_PTS = 1
ROUNDLY_WINNER_DICE = 1


# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════
def _first_partner(couple):
    """Get the first user from a couple safely"""
    for attr in ("users", "members", "partners", "user_set"):
        if hasattr(couple, attr):
            return getattr(couple, attr).first()
    return None


# ═══════════════════════════════════════════════════════════════
# 1. CoupleMemory - Roundly Memory Container
# ═══════════════════════════════════════════════════════════════
class CoupleMemory(models.Model):
    couple        = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name="couple_memories")
    round_start    = models.DateField()
    round_end      = models.DateField()
    summary       = models.TextField(blank=True)

    winner_entry  = models.ForeignKey(
        "MemoryEntry", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="won_round"
    )
    total_points   = models.PositiveIntegerField(default=0)
    entries_count  = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("couple", "round_start")
        ordering        = ["-round_start"]
        indexes         = [models.Index(fields=["couple", "round_start"])]

    @classmethod
    def current(cls, couple: Couple) -> "CoupleMemory":
        """get or create the CoupleMemory for this period so scoring and later review both work"""
        ROUND_DAY = 3
        today  = timezone.localtime(timezone.now()).date()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        period_start = today - timedelta(days=ROUND_DAY - 1)
        endday = today + timedelta(days=ROUND_DAY - 1)  # round period
        
        # 尝试获取已存在的 memory
        obj = cls.objects.filter(
            couple=couple, 
            round_start__gte=monday, 
            round_start__lte=sunday
        ).order_by("-round_start").first()
        
        if obj:
            return obj
        bracket = RoundBracket.objects.filter(couple=couple, round__gte=monday, round__lte=sunday).order_by('-round').first()
        obj = cls.objects.create(
            couple=couple,
            round_start=bracket.round if bracket else monday,
            round_end=bracket.round + timedelta(days=6) if bracket else sunday,
        )
        return obj

    def cover_photo(self) -> Optional[str]:
        from .models import MemoryMedia  # noqa: F401 avoid circular import
        if self.winner_entry:
            return self.winner_entry.best_media_url()
        first_media = (
            apps.get_model("couplememory", "MemoryMedia")
                .objects
                .filter(entry__memory=self)
                .order_by("created_at")
                .first()
        )
        return first_media.media.url if first_media else None

    def refresh_counters(self):
        agg = self.entries.aggregate(img=Count("id"), cmt=Count("comments"))
        self.entries_count  = agg["img"]
        self.comments_count = agg["cmt"]
        self.total_points   = (
            self.entries_count * PHOTO_REWARD_PTS +
            self.comments_count * COMMENT_REWARD_PTS
        )
        self.save(update_fields=["entries_count", "comments_count", "total_points", "updated_at"])

    def recalc_winner(self):
        """Recalculate roundly winner based on highest AI score"""
        top = (
            self.entries.exclude(ai_score=None)
                        .order_by("-ai_score", "created_at")
                        .first()
        )
        if top != self.winner_entry:
            self.winner_entry = top
            self.save(update_fields=["winner_entry", "updated_at"])

            # Award dice roundly winner
            user = _first_partner(self.couple)
            if user and top:
                DicePocket = apps.get_model("petcare", "DicePocket")
                DicePocket.earn(user, ROUNDLY_WINNER_DICE)

    def top_ingredients(self, limit: int = 5) -> Dict[str, int]:
        qs = (
            apps.get_model("couplememory", "MemoryEntry")
                .objects
                .filter(memory=self, recipe__isnull=False)
                .values(name=F("recipe__name"))
                .annotate(cnt=Count("id"))
                .order_by("-cnt")[:limit]
        )
        return {r["name"]: r["cnt"] for r in qs}

    def __str__(self):
        return f"{self.couple.code}@{self.round_start}"


# ─────────────────────────────────────────────────────────────
# 2. MemoryEntry
# ═══════════════════════════════════════════════════════════════
# 2. MemoryEntry - Individual Dish Posts with AI Integration
# ═══════════════════════════════════════════════════════════════
class MemoryEntry(models.Model):
    MOODS = [
        ("nailed", "🏆 Nailed"),        # Perfect execution
        ("grind",  "🛠 Grinding"),      # Practice makes perfect
        ("love",   "💖 Loved"),         # Made with love
        ("lucky",  "🎲 Lucky"),         # Lucky strike
        ("chaos",  "🔥 Chaos"),         # Kitchen chaos
    ]

    memory     = models.ForeignKey(CoupleMemory, on_delete=models.CASCADE, related_name="entries")
    author     = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe     = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True, blank=True)
    content    = models.TextField()
    mood       = models.CharField(max_length=8, choices=MOODS, default="nailed")
    
    # Legacy AI score for backward compatibility, prefer AIJudgment
    ai_score   = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(AI_SCORE_MAX)],
        help_text="Legacy AI score - prefer AIJudgment.overall_score"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes  = [models.Index(fields=["memory", "created_at"])]

    @property
    def effective_ai_score(self) -> Optional[float]:
        """Get effective AI score - prefer AIJudgment over legacy field"""
        if hasattr(self, 'ai_judgment') and self.ai_judgment:
            return self.ai_judgment.overall_score
        return self.ai_score

    @property
    def ai_metrics(self) -> Optional[Dict[str, float]]:
        """Get detailed AI scoring metrics breakdown"""
        if hasattr(self, 'ai_judgment') and self.ai_judgment:
            return self.ai_judgment.metrics_breakdown
        return None

    def best_media_url(self) -> Optional[str]:
        MM = apps.get_model("couplememory", "MemoryMedia")
        m  = (
            MM.objects
              .filter(entry=self, is_highlight=True).first()        # ⭐ prefer highlight
              or MM.objects.filter(entry=self).order_by("-created_at").first()
        )
        if not m:
            return None
        url = m.media.url
        # docker → browser host fix (same logic you used in serializers)
        if url and url.startswith("http://web:"):
            url = url.replace("http://web:", f"{settings.DEFAULT_HOST}:")
        return url

    def __str__(self):
        return f"Entry#{self.pk} by {self.author.username}"


# ═══════════════════════════════════════════════════════════════
# 2.5. AIJudgment - Enhanced AI Scoring System
# ═══════════════════════════════════════════════════════════════
class AIJudgment(models.Model):
    """
    🤖 PlateMate's Enhanced AI Scoring System - Individual scoring + Couple battle mode
    
    Features:
    - Individual dish scoring with detailed metrics
    - Couple battle comparison and results
    - Separated comments for different contexts
    - Confidence scoring and quality assessment
    """
    entry = models.OneToOneField(MemoryEntry, on_delete=models.CASCADE, related_name="ai_judgment")
    
    # Overall score (0-100)
    overall_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AI overall score (0-100)"
    )
    
    # Standardized 3-metric system
    visual_appeal = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Visual presentation and plating (0-100)"
    )
    
    cooking_technique = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Cooking technique and execution (0-100)"
    )
    
    ingredient_freshness = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Ingredient freshness and pairing (0-100)"
    )
    
    # ═══════════════════════════════════════════════════════════
    # 🆕 Separated AI Comment System - Individual vs Couple Battle
    # ═══════════════════════════════════════════════════════════
    
    # Individual scoring comments
    individual_comment = models.TextField(
        help_text="Individual dish AI detailed feedback", 
        default=""
    )
    individual_summary = models.CharField(
        max_length=200, 
        help_text="Individual dish AI brief summary", 
        default=""
    )
    
    # Couple battle comments
    battle_comment = models.TextField(
        help_text="Couple battle AI feedback", 
        blank=True, 
        default=""
    )
    battle_summary = models.CharField(
        max_length=200, 
        help_text="Couple battle AI summary", 
        blank=True, 
        default=""
    )
    
    # Battle result data
    battle_result = models.JSONField(
        help_text="Detailed battle result data",
        null=True,
        blank=True,
        default=dict
    )
    
    # ═══════════════════════════════════════════════════════════
    # Legacy compatibility fields (preserved but new fields take priority)
    # ═══════════════════════════════════════════════════════════
    ai_comment = models.TextField(help_text="AI detailed feedback (legacy compatibility)", default="")
    ai_summary = models.CharField(max_length=200, help_text="AI brief summary (legacy compatibility)", default="")
    
    # Confidence scoring
    confidence = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="AI scoring confidence (0.0-1.0)"
    )
    
    # AI model information
    model_version = models.CharField(max_length=50, default="gpt-5")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["entry", "created_at"])]
    
    @property
    def metrics_breakdown(self) -> Dict[str, float]:
        """Return standardized 3-metric breakdown"""
        return {
            "visual_appeal": self.visual_appeal,
            "cooking_technique": self.cooking_technique,
            "ingredient_freshness": self.ingredient_freshness
        }
    
    @property
    def average_metrics(self) -> float:
        """Calculate average of 3 metrics"""
        metrics = [
            self.visual_appeal or 0,
            self.cooking_technique or 0, 
            self.ingredient_freshness or 0
        ]
        # Filter out 0 values (i.e., None values)
        valid_metrics = [m for m in metrics if m > 0]
        if not valid_metrics:
            return 0.0
        return sum(valid_metrics) / len(valid_metrics)
    
    @property
    def effective_comment(self) -> str:
        """Get effective comment - prefer individual comment"""
        return self.individual_comment or self.ai_comment or ""
    
    @property
    def effective_summary(self) -> str:
        """Get effective summary - prefer individual summary"""
        return self.individual_summary or self.ai_summary or ""
    
    @property
    def has_battle_data(self) -> bool:
        """Check if battle data exists"""
        return bool(self.battle_comment or self.battle_result)
    
    def __str__(self):
        battle_indicator = " 🥊" if self.has_battle_data else ""
        return f"AI Judgment #{self.pk} for Entry #{self.entry.pk} - {self.overall_score:.0f}pts{battle_indicator}"


# ═══════════════════════════════════════════════════════════════
# 3. MemoryMedia - Image/Video Storage
# ═══════════════════════════════════════════════════════════════
class MemoryMedia(models.Model):
    entry        = models.ForeignKey(MemoryEntry, on_delete=models.CASCADE, related_name="media")
    media        = models.FileField(upload_to="memories/media/")
    is_highlight = models.BooleanField(default=False, db_index=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.is_highlight:
            apps.get_model("couplememory", "MemoryMedia")\
                .objects\
                .filter(entry=self.entry, is_highlight=True)\
                .update(is_highlight=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Media#{self.pk}{' ⭐' if self.is_highlight else ''}"


# ─────────────────────────────────────────────────────────────
# 4. MemoryComment
# ─────────────────────────────────────────────────────────────
class MemoryComment(models.Model):
    entry      = models.ForeignKey(MemoryEntry, on_delete=models.CASCADE, related_name="comments")
    author     = models.ForeignKey(User, on_delete=models.CASCADE)
    content    = models.TextField()
    emoji      = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment#{self.pk} by {self.author.username}"


# ═══════════════════════════════════════════════════════════════
# 5. Complete AI scoring + Couple battle system
# ═══════════════════════════════════════════════════════════════

# AI scoring and couple battle logic handled by signals.py for clean separation
# This ensures:
# 1. Individual AI scoring when media is uploaded
# 2. Automatic couple battle when both partners have scored entries
# 3. Clean data separation between AI judgments and user comments


@receiver(post_save, sender=MemoryEntry)
def on_entry_saved(sender, instance: MemoryEntry, created: bool, **kwargs):
    cm = instance.memory
    if created:
        first_user = _first_partner(cm.couple)
        if first_user:
            ActivityModel = apps.get_model("petcare", "Activity")
            DicePocketModel = apps.get_model("petcare", "DicePocket")
            ActivityModel.create_generic(cm.couple, ActivityModel.PHOTO, meta={"entry": instance.pk})
            DicePocketModel.earn(first_user, PHOTO_REWARD_PTS)

        logger.info(f"New memory entry created: {instance.pk}, awaiting media upload for AI scoring")

    cm.refresh_counters()
    cm.recalc_winner()


@receiver(post_save, sender=MemoryComment)
def on_comment_saved(sender, instance: MemoryComment, created: bool, **kwargs):
    if created:
        cm = instance.entry.memory
        first_user = _first_partner(cm.couple)
        if first_user:
            ActivityModel = apps.get_model("petcare", "Activity")
            DicePocketModel = apps.get_model("petcare", "DicePocket")
            ActivityModel.create_generic(cm.couple, ActivityModel.COMPLIMENT, meta={"comment": instance.pk})
            DicePocketModel.earn(first_user, COMMENT_REWARD_PTS)
        cm.refresh_counters()


@receiver(post_delete, sender=MemoryComment)
@receiver(post_delete, sender=MemoryMedia)
@receiver(post_delete, sender=MemoryEntry)
def on_any_deleted(sender, instance, **kwargs):
    try:
        if sender is MemoryEntry:
            cm = getattr(instance, "memory", instance.memory)
        else:
            cm = getattr(instance, "memory", instance.entry.memory)
        if cm:
            cm.refresh_counters()
            cm.recalc_winner()
    except AttributeError as e:
        logger.error("AttributeError in on_any_deleted: %s", e)
    except Exception as e:
        logger.exception("Unexpected error in on_any_deleted: %s", e)

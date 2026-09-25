# apps/petcare/models.py

from __future__ import annotations
import logging
import random
from datetime import timedelta

from django.apps import apps
from django.db import models, transaction
from django.db.models import F, Count
from django.utils import timezone

from users.models import Couple
from couplememory.models import MemoryEntry, MemoryComment
from recipes.models import RecipeIngredientTask
from django.db.models.signals import post_save
from django.dispatch import receiver


logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────
# 0. Constants & defaults
# ────────────────────────────────────────────────────────────
PET_BASE_XP         = 3
PET_STREAK_BONUS    = 1
STREAK_MILESTONES   = [3, 7]
MISSION_DEF_DESC    = "Cook any veggie dish together 🥗"
MISSION_DEF_PTS     = 5
REMINDER_SMS_WINDOW = 48  # hours


# ────────────────────────────────────────────────────────────
# State Name Mapping Constants
# ────────────────────────────────────────────────────────────
STATE_NAME_MAPPING = {
    'state1': 'before_preparation',
    'state2': 'after_preparation',
    'state3': 'pet_hungry',
    'state6': 'preparation_reminder',
    'state7': 'memory_share_reminder'
}


# ────────────────────────────────────────────────────────────
# 1. Activity: unified user↔pet interaction log
# ────────────────────────────────────────────────────────────
class Activity(models.Model):
    COOK, PHOTO, COMPLIMENT, AI, FEED, GAME = (
        "cook", "photo", "compliment", "ai", "feed", "game"
    )
    KIND_CHOICES = [
        (COOK,       "Cook"),
        (PHOTO,      "Photo"),
        (COMPLIMENT, "Compliment"),
        (AI,         "AI Bonus"),
        (FEED,       "Feed"),
        (GAME,       "Game"),
    ]

    couple   = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name="activities")
    kind     = models.CharField(max_length=12, choices=KIND_CHOICES)
    points   = models.PositiveIntegerField()
    recipe   = models.ForeignKey(
        RecipeIngredientTask,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    streak   = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(blank=True, null=True)
    created  = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes  = [models.Index(fields=["couple", "kind", "created"])]
        ordering = ["-created"]

    @classmethod
    def cook(cls, task: RecipeIngredientTask) -> Activity:
        if not task.is_verified:
            raise ValueError("Task must be verified first")
        couple = task.couple
        streak = cls._calc_streak(couple)
        pts    = PET_BASE_XP + streak * PET_STREAK_BONUS

        act = cls.objects.create(
            couple=couple,
            kind=cls.COOK,
            points=pts,
            recipe=task,
            streak=streak,
        )
        if streak in STREAK_MILESTONES:
            apps.get_model("petcare", "RewardBox").drop(couple, source="streak", points=streak)
        apps.get_model("petcare", "Pet").add_xp(couple, pts)
        apps.get_model("petcare", "Mission").progress(couple, cls.COOK)
        logger.debug("Recorded COOK activity #%s → +%s XP (streak %s)", act.pk, pts, streak)
        return act

    @classmethod
    def create_generic(cls, couple, kind: str, meta: dict = None) -> Activity:
        if kind not in dict(cls.KIND_CHOICES):
            raise ValueError(f"Unsupported Activity kind: {kind}")
        pts = PET_BASE_XP if kind in (cls.COOK, cls.FEED) else 1

        act = cls.objects.create(
            couple=couple,
            kind=kind,
            points=pts,
            metadata=meta or {}
        )
        # All interactions give XP
        apps.get_model("petcare", "Pet").add_xp(couple, pts)
        logger.debug("Recorded %s activity #%s → +%s XP", kind.upper(), act.pk, pts)
        return act

    @classmethod
    def _calc_streak(cls, couple: Couple) -> int:
        last = cls.objects.filter(couple=couple, kind=cls.COOK).first()
        if last and (timezone.localtime(timezone.now()).date() - last.created.date()).days == 1:
            return (last.streak or 1) + 1
        return 1

    def __str__(self):
        return f"{self.couple.code}:{self.kind}+{self.points}"

class PetFeed(models.Model):
    """
    记录每一次对宠物的喂食操作，用于回看和统计。
    """
    couple    = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name="pet_feeds")
    fed_at    = models.DateTimeField(auto_now_add=True)
    food_type = models.CharField(max_length=50, default="snack")
    amount    = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-fed_at"]
        indexes  = [models.Index(fields=["couple", "fed_at"], name="idx_petfeed_cpl")]

    def __str__(self):
        return f"{self.couple.code} fed {self.food_type}×{self.amount} @ {self.fed_at}"
# ────────────────────────────────────────────────────────────
# 2. Pet & its status
# ────────────────────────────────────────────────────────────
class Pet(models.Model):
    SPECIES = [("kinza", "Kinza"), ("kinba", "Kinba"), ("kinmi", "Kinmi")]

    couple     = models.OneToOneField(Couple, on_delete=models.CASCADE, related_name="pet")
    species    = models.CharField(max_length=20, choices=SPECIES, default="kinza")
    nickname   = models.CharField(max_length=30, default="Kinny")
    skin       = models.CharField(max_length=30, default="default")
    level      = models.PositiveIntegerField(default=1)
    xp         = models.PositiveIntegerField(default=0)
    next_level = models.PositiveIntegerField(default=10)
    created    = models.DateTimeField(auto_now_add=True)
    updated    = models.DateTimeField(auto_now=True)

    XP_CURVE = staticmethod(lambda lv: 10 + lv * 6)

    @classmethod
    def add_xp(cls, couple, pts: int) -> Pet:
        with transaction.atomic():
            pet, _ = cls.objects.get_or_create(couple=couple)
            pet.xp = F("xp") + pts
            pet.save(update_fields=["xp"])
            pet.refresh_from_db()
            if pet.xp >= pet.next_level:
                pet.xp -= pet.next_level
                pet.level += 1
                pet.next_level = cls.XP_CURVE(pet.level)
                pet.save(update_fields=["xp", "level", "next_level", "updated"])
            apps.get_model("petcare", "PetStatus").feed(pet, pts)
        logger.debug("Pet#%s gained %s XP", pet.pk, pts)
        return pet

    def __str__(self):
        return f"Pet#{self.pk} L{self.level}"


def get_current_date():
    """today as a date, for use as a DateField default"""
    return timezone.localtime(timezone.now()).date()


class PetStatus(models.Model):
    pet        = models.OneToOneField(Pet, on_delete=models.CASCADE, related_name="status")
    hunger     = models.PositiveSmallIntegerField(default=100)
    happiness  = models.PositiveSmallIntegerField(default=100)
    hygiene    = models.PositiveSmallIntegerField(default=100)
    last_tick  = models.DateField(default=get_current_date)

    DECAY = {"hunger": 25, "happiness": 5, "hygiene": 3}

    @classmethod
    def daily_tick(cls):
        today = timezone.localtime(timezone.now()).date()
        for st in cls.objects.all():
            if st.last_tick < today:
                days = (today - st.last_tick).days
                for f, d in cls.DECAY.items():
                    setattr(st, f, max(0, getattr(st, f) - d * days))
                st.last_tick = today
                st.save()
        logger.debug("Ran daily decay")

    def check_and_apply_decay(self):
        """Check if decay should be applied and apply it automatically"""
        today = timezone.localtime(timezone.now()).date()
        if self.last_tick < today:
            days = (today - self.last_tick).days
            for field, decay_amount in self.DECAY.items():
                current_value = getattr(self, field)
                new_value = max(0, current_value - decay_amount * days)
                setattr(self, field, new_value)
            self.last_tick = today
            self.save()
            logger.debug(f"Applied {days} days of decay to pet {self.pet.id}")

    @classmethod
    def feed(cls, pet, pts: int):
        st, _ = cls.objects.get_or_create(pet=pet)
        st.check_and_apply_decay()  # Auto-apply decay before feeding
        st.hunger    = min(100, st.hunger + pts * 2)
        st.happiness = min(100, st.happiness + pts)
        st.save()


# ────────────────────────────────────────────────────────────
# 3. Mission: flexible goals
# ────────────────────────────────────────────────────────────
class Mission(models.Model):
    DAILY, ROUNDLY, CUSTOM = "D", "W", "C"
    PERIOD_CHOICES = [
        (DAILY, "Daily"),
        (ROUNDLY, "Roundly"),
        (CUSTOM, "Custom"),
    ]

    couple      = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name="missions")
    period      = models.CharField(max_length=1, choices=PERIOD_CHOICES, default=ROUNDLY)
    start       = models.DateField()
    end         = models.DateField()
    description = models.CharField(max_length=160, default=MISSION_DEF_DESC)
    target_kind = models.CharField(max_length=12, default=Activity.COOK)
    target_cnt  = models.PositiveIntegerField(default=1)
    progress    = models.PositiveIntegerField(default=0)
    reward_pts  = models.PositiveIntegerField(default=MISSION_DEF_PTS)
    is_done     = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["couple", "period", "start"])]

    @classmethod
    def seed_roundly(cls):
        ROUND_DAY = 3
        today = timezone.localtime(timezone.now()).date()
        period_start = today - timedelta(days=ROUND_DAY - 1)
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        endday = today + timedelta(days=ROUND_DAY - 1)  # round period
        for cp in Couple.objects.all():
            obj = cls.objects.filter(
            ).order_by("-start").first()
            if obj is None:
                cls.objects.create(
                    couple=cp, period=cls.ROUNDLY, start=monday, end=sunday
                )

    @classmethod
    def progress(cls, couple, kind: str):
        today = timezone.localtime(timezone.now()).date()
        qs = cls.objects.filter(
            couple=couple,
            is_done=False,
            start__lte=today,
            end__gte=today,
            target_kind=kind,
        )
        for m in qs:
            m.progress = F("progress") + 1
            m.save(update_fields=["progress"])
            m.refresh_from_db()
            if m.progress >= m.target_cnt:
                m.is_done = True
                m.save(update_fields=["is_done"])
                apps.get_model("petcare", "RewardBox").drop(couple, source="mission", points=m.reward_pts)

    def __str__(self):
        return f"{self.description} [{self.progress}/{self.target_cnt}]"


# ────────────────────────────────────────────────────────────
# 4. Reminder (unchanged)
# ────────────────────────────────────────────────────────────
class Reminder(models.Model):
    couple    = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name="reminders")
    next_fire = models.DateTimeField()
    template  = models.CharField(max_length=140, default="Time to cook & feed your pet!")
    sent_at   = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["next_fire"])]

    @classmethod
    def due(cls):
        return cls.objects.filter(next_fire__lte=timezone.localtime(timezone.now()))

    def mark_sent(self, hours=REMINDER_SMS_WINDOW):
        self.sent_at   = timezone.localtime(timezone.now())
        self.next_fire += timedelta(hours=hours)
        self.save(update_fields=["sent_at", "next_fire"])

    def send_sms(self, phone_number: str):
        """
        Hook in your SMS provider here.
        """
        self.mark_sent()


class ReminderRule(models.Model):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name="reminder_rules")
    hour   = models.PositiveSmallIntegerField(default=19)
    minute = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("couple", "hour", "minute")


# ────────────────────────────────────────────────────────────
# 5. RewardBox & LootTable (unchanged)
# ────────────────────────────────────────────────────────────
class LootTable:
    SKINS  = ["panda_blue", "cat_pink", "dog_green"]
    EMOJIS = ["❤️", "🍳", "🎉", "🐾"]
    POINTS = [3, 5, 8]

    @staticmethod
    def roll():
        choice = random.choice(["skins", "emojis", "points"])
        if choice == "skins":
            return {"skin": random.choice(LootTable.SKINS)}
        if choice == "emojis":
            return {"emoji": random.choice(LootTable.EMOJIS)}
        return {"points": random.choice(LootTable.POINTS)}


class RewardBox(models.Model):
    SOURCE_CHOICES = [("mission","Mission"),("streak","Streak"),("admin","Admin")]

    couple    = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name="boxes")
    source    = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    created   = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(blank=True, null=True)
    content   = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["couple", "opened_at"])]

    @classmethod
    def drop(cls, couple, source: str, points: int = 3):
        return cls.objects.create(couple=couple, source=source, content={"points": points})

    def open(self):
        if self.opened_at:
            return self.content
        loot = LootTable.roll()
        if random.random() < 0.2:
            loot["dice"] = 1
        self.content.update(loot)
        self.opened_at = timezone.localtime(timezone.now())
        self.save(update_fields=["opened_at","content"])
        if "points" in loot:
            Pet.add_xp(self.couple, loot["points"])
        if "skin" in loot:
            pet = self.couple.pet
            pet.skin = loot["skin"]
            pet.save(update_fields=["skin"])
        if "dice" in loot:
            apps.get_model("petcare","DicePocket").earn(self.couple.users.first(), loot["dice"])
        return self.content



# ────────────────────────────────────────────────────────────
# 6. Badge: achievements
# ────────────────────────────────────────────────────────────
class Badge(models.Model):
    slug    = models.CharField(max_length=20, primary_key=True)
    desc    = models.CharField(max_length=120)
    couples = models.ManyToManyField(Couple, related_name="badges", blank=True)
    added   = models.DateTimeField(auto_now_add=True)

    SLUG_MAP = {
        "chef_5":    ("Cook 5 dishes", 5),
        "chef_20":   ("Cook 20 dishes",20),
        "diary_10":  ("Write 10 diaries",10),
        "comment_20":("Make 20 comments",20),
    }

    @classmethod
    def audit(cls):
        # TODO: Fix model references - CookingDiary and Comment models don't exist
        # Diary  = apps.get_model("recipes", "CookingDiary")
        # Cmnt   = apps.get_model("recipes", "Comment")
        return  # Skip audit for now
        for cp in Couple.objects.all():
            cnt = {
                "cook":    Activity.objects.filter(couple=cp, kind=Activity.COOK).count(),
                "diary":   Diary.objects.filter(couple=cp).count(),
                "comment": Cmnt.objects.filter(diary__couple=cp).count(),
            }
            for slug, (txt, req) in cls.SLUG_MAP.items():
                achieved = (
                    (slug.startswith("chef") and cnt["cook"] >= req) or
                    (slug == "diary_10"   and cnt["diary"] >= req) or
                    (slug == "comment_20" and cnt["comment"] >= req)
                )
                if achieved:
                    bdg, _ = cls.objects.get_or_create(slug=slug, defaults={"desc": txt})
                    bdg.couples.add(cp)

    def __str__(self):
        return self.slug


# ────────────────────────────────────────────────────────────
# 7. MenuSuggestion: quick random menus
# ────────────────────────────────────────────────────────────
class MenuSuggestion:
    @staticmethod
    def suggest(couple, count: int = 3):
        FR = apps.get_model("recipes", "FamilyRecipe")
        unlocked = FR.objects.filter(couple=couple, is_locked=False).select_related("recipe")
        recipes = [fr.recipe for fr in unlocked]
        random.shuffle(recipes)
        return recipes[:count]


# ────────────────────────────────────────────────────────────
# 8. PetMessage: HCI “pet bulletin”
# ────────────────────────────────────────────────────────────
class PetMessage(models.Model):
    TIPS, SUMMARY, RECOMMEND = "tips", "summary", "recommend"
    TYPE_CHOICES = [
        (TIPS,      "Tip"),
        (SUMMARY,   "Roundly Summary"),
        (RECOMMEND, "Menu Recommend"),
    ]

    couple     = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name="pet_messages")
    type       = models.CharField(max_length=12, choices=TYPE_CHOICES, default=TIPS)
    content    = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read    = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def mark_read(self):
        self.is_read = True
        self.save(update_fields=["is_read"])

    @classmethod
    def roundly_summary(cls):
        for cp in Couple.objects.all():
            xp     = Activity.objects.filter(couple=cp).aggregate(total=Count("points"))["total"] or 0
            streak = Activity._calc_streak(cp)
            badges = cp.badges.count()
            cls.objects.create(
                couple=cp, type=cls.SUMMARY,
                content=f"本周 XP:{xp}，连击:{streak} 天，成就:{badges} 个！"
            )

    @classmethod
    def daily_recommend(cls):
        for cp in Couple.objects.all():
            names = ", ".join(r.name for r in MenuSuggestion.suggest(cp, 2))
            cls.objects.create(
                couple=cp, type=cls.RECOMMEND,
                content=f"今日推荐：{names}"
            )

    def __str__(self):
        flag = "✓" if self.is_read else " "
        return f"[{flag}][{self.get_type_display()}] {self.content}"


# ────────────────────────────────────────────────────────────
# 9. Signals: 自动记录 Activity & 食物奖励
# ────────────────────────────────────────────────────────────
@receiver(post_save, sender=RecipeIngredientTask)
def on_task_verified(sender, instance, created, **kwargs):
    if not created and instance.is_verified:
        activity = Activity.cook(instance)
        # finishing a cooking task grants food to both members of the couple
        import random
        food_types = ['apple', 'banana', 'orange', 'strawberry']
        food_type = random.choice(food_types)
        
        # 给couple中的每个用户都添加食物到个人库存
        for user in instance.couple.members.all():
            FoodInventory.add_food(user, food_type, amount=2)

@receiver(post_save, sender=MemoryEntry)
def on_memory_entry_scored(sender, instance, created, **kwargs):
    # 只有 AI 评分写入后记录 AI bonus
    if not created and instance.ai_score is not None:
        Activity = apps.get_model('petcare', 'Activity')
        Activity.create_generic(
            couple=instance.memory.couple,
            kind=Activity.AI,
            meta={'entry_id': instance.pk},
        )
        # AIfood reward scaling with the score, granted to both members of the couple
        import random
        food_types = ['grapes', 'watermelon', 'pineapple']
        food_type = random.choice(food_types)
        amount = 1 if instance.ai_score < 7 else 2 if instance.ai_score < 9 else 3
        
        for user in instance.memory.couple.members.all():
            FoodInventory.add_food(user, food_type, amount=amount)

@receiver(post_save, sender=MemoryComment)
def on_memory_comment_created(sender, instance, created, **kwargs):
    if created:
        Activity = apps.get_model('petcare', 'Activity')
        Activity.create_generic(
            couple=instance.entry.memory.couple,
            kind=Activity.COMPLIMENT,
            meta={'comment_id': instance.pk},
        )
        # 评论奖励食物 - 给couple中每个用户添加
        import random
        food_types = ['cherry', 'strawberry', 'apple']
        food_type = random.choice(food_types)
        
        for user in instance.entry.memory.couple.members.all():
            FoodInventory.add_food(user, food_type, amount=1)


# ────────────────────────────────────────────────────────────
# X. FoodInventory - per-user food inventory, supporting engagement comparison across a couple
# ────────────────────────────────────────────────────────────
class FoodInventory(models.Model):
    """per-user food inventory backing the feeding game; supports comparing engagement across a couple"""
    FOOD_TYPES = [
        ('apple', '🍎 Apple'),
        ('banana', '🍌 Banana'),
        ('orange', '🍊 Orange'),
        ('strawberry', '🍓 Strawberry'),
        ('grapes', '🍇 Grapes'),
        ('watermelon', '🍉 Watermelon'),
        ('pineapple', '🍍 Pineapple'),
        ('cherry', '🍒 Cherry'),
    ]
    
    # 迁移完成，只保留用户字段
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name="food_inventory")
    food_type = models.CharField(max_length=20, choices=FOOD_TYPES)
    quantity = models.PositiveIntegerField(default=0)
    last_harvest = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'food_type')
        indexes = [models.Index(fields=['user', 'food_type'])]
        verbose_name = "Food Inventory"
        verbose_name_plural = "Food Inventories"
    
    @classmethod
    def add_food(cls, user, food_type: str, amount: int = 1):
        """添加食物到用户个人库存"""
        if amount <= 0:
            return
        
        inventory, created = cls.objects.get_or_create(
            user=user,
            food_type=food_type,
            defaults={'quantity': 0}
        )
        inventory.quantity = F('quantity') + amount
        inventory.save(update_fields=['quantity', 'updated'])
        inventory.refresh_from_db()
        logger.debug(f"Added {amount} {food_type} to user {user.id}, total: {inventory.quantity}")
        return inventory
    
    @classmethod
    def use_food(cls, user, food_type: str, amount: int = 1):
        """使用食物（喂食时调用）"""
        if amount <= 0:
            return False
        
        try:
            with transaction.atomic():
                inventory = cls.objects.select_for_update().get(
                    user=user,
                    food_type=food_type
                )
                if inventory.quantity < amount:
                    return False
                
                inventory.quantity = F('quantity') - amount
                inventory.save(update_fields=['quantity', 'updated'])
                inventory.refresh_from_db()
                logger.debug(f"Used {amount} {food_type} from user {user.id}, remaining: {inventory.quantity}")
                return True
        except cls.DoesNotExist:
            return False
    
    @classmethod
    def can_harvest(cls, user, food_type: str, cooldown_hours: int = 8):
        """检查用户是否可以收获食物"""
        try:
            inventory = cls.objects.get(user=user, food_type=food_type)
            if not inventory.last_harvest:
                return True
            
            cooldown_time = timezone.now() - timedelta(hours=cooldown_hours)
            return inventory.last_harvest < cooldown_time
        except cls.DoesNotExist:
            return True
    
    @classmethod
    def harvest_food(cls, user, food_type: str, amount: int = 3, force: bool = False):
        """用户收获食物（每日限制）"""
        if not force and not cls.can_harvest(user, food_type):
            return None
        
        inventory, created = cls.objects.get_or_create(
            user=user,
            food_type=food_type,
            defaults={'quantity': 0}
        )
        
        inventory.quantity = F('quantity') + amount
        inventory.last_harvest = timezone.now()
        inventory.save(update_fields=['quantity', 'last_harvest', 'updated'])
        inventory.refresh_from_db()
        logger.debug(f"Harvested {amount} {food_type} for user {user.id}, force={force}")
        return inventory
    
    def __str__(self):
        return f"{self.user.username} - {self.get_food_type_display()}: {self.quantity}"


# ────────────────────────────────────────────────────────────
# X. DicePocket - 每位用户的🎲余额
# ────────────────────────────────────────────────────────────
from django.contrib.auth import get_user_model
User = get_user_model()

class DicePocket(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE, related_name="dice")
    balance  = models.PositiveIntegerField(default=0)
    updated  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dice Pocket"
        verbose_name_plural = "Dice Pockets"

    # ─── API ───
    @classmethod

    def _pk(cls, user):               
            """Internal: fetch-or-create the DicePocket."""
            return cls.objects.get_or_create(user=user)[0]
    @classmethod
    def _get(cls, user):
        """
        Public alias for fetch-or-create.
        Everywhere you used DicePocket._get() will now work.
        """
        return cls._pk(user)

    @classmethod
    def earn(cls, user, amount: int = 1) -> int:
        if amount <= 0:
            return cls._pk(user).balance
        with transaction.atomic():
            p = cls._pk(user)
            p.balance = F("balance") + amount
            p.save(update_fields=["balance"])
            p.refresh_from_db()
        logger.debug("User[%s] +%s 🎲 (= %s)", user.username, amount, p.balance)
        return p.balance

    @classmethod
    def spend(cls, user, amount: int = 1) -> int:
        if amount <= 0:
            return cls._pk(user).balance
        with transaction.atomic():
            p = cls._pk(user)
            if p.balance < amount:
                raise ValueError("Not enough dice")
            p.balance = F("balance") - amount
            p.save(update_fields=["balance"])
            p.refresh_from_db()
        logger.debug("User[%s] -%s 🎲 (= %s)", user.username, amount, p.balance)
        return p.balance

    def __str__(self):
        return f"{self.user.username}: {self.balance} 🎲"


# ────────────────────────────────────────────────────────────
# Pet Message System - 简化版模型
# ────────────────────────────────────────────────────────────

class PetMessageTemplate(models.Model):
    """宠物提示语模板库"""
    state_code = models.CharField(max_length=20, db_index=True, help_text="状态代码 (state1, state2, etc.)")
    message_template = models.TextField(help_text="消息模板，支持变量如 {{recipe.name}}")
    weight = models.IntegerField(default=1, help_text="随机选择时的权重")
    is_active = models.BooleanField(default=True, help_text="是否启用此模板")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['state_code', 'is_active'], name='idx_pet_msg_tpl')]
        ordering = ['state_code', 'weight']
        verbose_name = "Pet Message Template"
        verbose_name_plural = "Pet Message Templates"

    def __str__(self):
        return f"{self.state_code}: {self.message_template[:50]}..."


class UserPetMessageState(models.Model):
    """每个用户的宠物消息状态 - 更新版"""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name="pet_message_state"
    )
    couple = models.ForeignKey(
        Couple, on_delete=models.CASCADE,
        related_name="user_message_states",
        help_text="方便按couple查询"
    )

    # 状态管理
    current_states = models.JSONField(
        default=list,
        help_text="当前激活的状态列表 ['state1', 'state3']"
    )

    # 修改：从list改为dict结构
    available_messages = models.JSONField(
        default=dict,
        help_text="按状态分组的消息 {'state1': ['msg1', 'msg2'], 'state3': ['msg3']}"
    )

    # 时间戳
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['couple', 'last_updated'], name='idx_user_pet_msg'),
            models.Index(fields=['user'], name='idx_user_pet_msg_user')
        ]
        verbose_name = "User Pet Message State"
        verbose_name_plural = "User Pet Message States"

    def __str__(self):
        return f"{self.user.username} - {len(self.current_states)} states active"

    def save(self, *args, **kwargs):
        # 确保couple字段与user.couple保持一致
        if not self.couple_id and hasattr(self.user, 'couple') and self.user.couple:
            self.couple = self.user.couple
        super().save(*args, **kwargs)

    def get_random_message(self, state: str = None) -> str:
        """
        随机获取一条可用消息

        Args:
            state: 指定状态，如果不指定则从所有消息中随机选择
        """
        if not self.available_messages:
            return "Hi there! Keep cooking and having fun!"

        import random

        if state and state in self.available_messages:
            messages = self.available_messages[state]
            if messages:
                return random.choice(messages)

        # 从所有消息中随机选择
        all_messages = []
        for state_messages in self.available_messages.values():
            all_messages.extend(state_messages)

        if all_messages:
            return random.choice(all_messages)

        return "Hi there! Keep cooking and having fun!"

    def get_messages_by_state(self) -> dict:
        """
        按状态获取消息（向后兼容方法）

        Returns:
            dict: {state_code: [messages]}
        """
        return self.available_messages.copy() if self.available_messages else {}

    def get_all_messages(self) -> list:
        """
        获取所有消息的平面列表（向后兼容）

        Returns:
            list: 所有消息的列表
        """
        all_messages = []
        for state_messages in self.available_messages.values():
            all_messages.extend(state_messages)
        return all_messages


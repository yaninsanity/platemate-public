# apps/recipes/models.py

from __future__ import annotations
import logging
from typing import Optional
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from users.models import Couple

logger = logging.getLogger(__name__)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    updated_at = models.DateTimeField(auto_now=True,   editable=False, null=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class Ingredient(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    default_picture = models.ImageField(upload_to='ingredients/', blank=True, null=True)
    info = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=['name'], name='idx_ing_name')]
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('recipes:ingredient-detail', args=[self.pk])


class RecipeQuerySet(QuerySet['Recipe']):
    def with_ingredient(self, ing: Ingredient):
        return self.filter(ingredients=ing)


class RecipeManager(models.Manager.from_queryset(RecipeQuerySet)):
    def create_recipe(self, name: str, instructions: str,
                      cuisine: str = '', dish_type: str = '',
                      main_ingredient: Optional[Ingredient] = None) -> 'Recipe':
        return self.create(name=name,
                           instructions=instructions,
                           cuisine=cuisine,
                           dish_type=dish_type,
                           main_ingredient=main_ingredient)


class Recipe(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True)
    preparation = models.TextField(
        blank=True,
        help_text="Optional preparation notes (marinate, soak, etc.)"
    )
    instructions = models.TextField(help_text='Cooking steps')
    cuisine = models.CharField(max_length=50, blank=True)
    dish_type = models.CharField(max_length=50, blank=True)
    default_picture = models.ImageField(upload_to='recipes/', blank=True, null=True)
    main_ingredient = models.ForeignKey(
        Ingredient, on_delete=models.SET_NULL,
        related_name='main_for_recipes', null=True, blank=True
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientInRecipe', related_name='recipes'
    )

    objects = RecipeManager()

    class Meta:
        indexes = [
            models.Index(fields=['name'], name='idx_recipe_name'),
            models.Index(fields=['cuisine', 'dish_type'], name='idx_recipe_cui_type'),
        ]
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'recipe'
            existing = set(
                Recipe.objects
                      .filter(slug__startswith=base)
                      .exclude(pk=self.pk)
                      .values_list('slug', flat=True)
            )
            slug = base
            for i in range(1, 101):
                if slug not in existing:
                    break
                slug = f'{base}-{i}'
            else:
                raise ValueError('Unable to generate unique slug')
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('recipes:recipe-detail', args=[self.slug])

    def ingredient_count(self) -> int:
        return self.ingredients.count()

    def add_ingredient(self, ing: Ingredient, qty: str = ''):
        link, _ = IngredientInRecipe.objects.update_or_create(
            recipe=self, ingredient=ing, defaults={'quantity': qty}
        )
        return link

    def remove_ingredient(self, ing: Ingredient):
        IngredientInRecipe.objects.filter(recipe=self, ingredient=ing).delete()


class IngredientInRecipe(TimeStampedModel):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ('recipe', 'ingredient')
        indexes = [models.Index(fields=['recipe', 'ingredient'], name='idx_ing_in_rec')]
        ordering = ['recipe__name', 'ingredient__name']

    def __str__(self):
        return f"{self.ingredient.name}{f' ({self.quantity})' if self.quantity else ''}"


class TaskManager(models.Manager):
    def verify_and_unlock(self, task: RecipeIngredientTask, user):
        FamilyRecipe = apps.get_model('recipes', 'FamilyRecipe')
        with transaction.atomic():
            # 设置任务为已验证
            task.user = user
            task.is_verified = True
            task.scanned_at = task.scanned_at or timezone.localtime(timezone.now())
            task.save(update_fields=['user', 'is_verified', 'scanned_at'])

            # has this user finished every ingredient task of the recipe?
            total = IngredientInRecipe.objects.filter(recipe=task.recipe).count()
            user_completed = RecipeIngredientTask.objects.filter(
                recipe=task.recipe,
                user=user,
                is_verified=True
            ).count()

            # when the user finishes every ingredient task, unlock the recipe for their couple
            if user and total and user_completed >= total:
                fr, _ = FamilyRecipe.objects.get_or_create(
                    couple=user.couple,
                    recipe=task.recipe
                )
                fr.unlock(reason=f'user {user.username} completed all ingredients')
                FamilyMenu.unlock_for(user.couple, fr.recipe)


class TaskQuerySet(QuerySet['RecipeIngredientTask']):
    def for_couple(self, couple: Couple): return self.filter(couple=couple)
    def for_user(self, user): return self.filter(user=user)
    def for_recipe(self, recipe): return self.filter(recipe=recipe)
    def verified(self): return self.filter(is_verified=True)
    def pending(self): return self.filter(is_verified=False)


class RecipeIngredientTask(TimeStampedModel):
    # ─────────── 字段 ───────────
    recipe     = models.ForeignKey(Recipe,      on_delete=models.CASCADE, related_name='tasks')
    ingredient = models.ForeignKey(Ingredient,  on_delete=models.CASCADE)
    couple     = models.ForeignKey(Couple,      on_delete=models.CASCADE,
                                   related_name='recipe_tasks', null=True, blank=True)
    user       = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE,
                                   related_name='recipe_tasks', null=True, blank=True,
                                   help_text='The specific user who needs to complete this task')
    is_uploaded = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    scanned_at  = models.DateTimeField(null=True, blank=True)

    # ─────────── 自定义 Manager / QuerySet ───────────
    objects = TaskManager.from_queryset(TaskQuerySet)()

    class Meta:
        unique_together = ('recipe', 'ingredient', 'user')
        indexes = [
            models.Index(fields=['recipe', 'ingredient'], name='idx_task_ing'),
            models.Index(fields=['couple', 'is_verified'], name='idx_task_cpl_ver'),
            models.Index(fields=['user', 'is_verified'], name='idx_task_user_ver'),
        ]

    # ─────────── 业务方法 ───────────
    def __str__(self):
        mark = '✔' if self.is_verified else '✗'
        return f"Task#{self.pk} {self.recipe} — {self.ingredient} ({mark})"

    def verify(self, user=None):
        """
        1) 必须已上传 proof
        2) 调用 AI 检测成分
        3) 记录日志
        4) 解锁逻辑 - 基于用户验证而不是couple
        """
        # 1) proof 检查
        if not hasattr(self, "proof") or self.proof is None:
            raise ValueError("请先上传 proof 图片，再进行验证。")

        img_url = self.proof.image.url

        # 2) AI 检测
        from cookai.backend import OpenAIBackend
        detected, match_score = OpenAIBackend.detect_ingredients(
            img_url, [self.ingredient.name]
        )
        if not detected:
            raise ValueError(f"AI 未在图片中检测到 \"{self.ingredient.name}\"。")

        # 3) 日志
        from cookai.models import AIPrompt, AIRequestLog
        prompt = AIPrompt.objects.filter(kind=AIPrompt.KIND_DETECT, is_active=True).first()
        AIRequestLog.objects.log(
            prompt_obj=prompt,
            kind=AIPrompt.KIND_DETECT,
            user=user or self.user,
            couple=self.couple,
            request_payload={"image_url": img_url, "targets": [self.ingredient.name]},
            response={"detected": detected, "match_score": match_score},
            latency=0.0,
        )

        # 4) 解锁 - 使用user参数而不是couple
        RecipeIngredientTask.objects.verify_and_unlock(self, user or self.user)

# RecipeIngredientTask.objects = TaskManager.from_queryset(TaskQuerySet)()


class FamilyRecipe(TimeStampedModel):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='family_recipes')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='family_recipes'
    )
    is_locked = models.BooleanField(default=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('couple', 'recipe')
        indexes = [models.Index(fields=['couple', 'is_locked'], name='idx_fr_cpl_lock')]

    def unlock(self, reason: str = 'all ingredients verified'):
        if self.is_locked:
            self.is_locked = False
            self.unlocked_at = timezone.localtime(timezone.now())
            self.reason = reason
            self.save(update_fields=['is_locked', 'unlocked_at', 'reason'])

    def __str__(self):
        return f"{self.couple.code} ↔ {self.recipe}"


class Menu(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    recipes = models.ManyToManyField(Recipe, related_name='menus')

    def __str__(self):
        return self.name


class FamilyMenu(TimeStampedModel):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='menus')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='family_menus')
    is_locked = models.BooleanField(default=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('couple', 'menu')
        indexes = [models.Index(fields=['couple', 'is_locked'], name='idx_fm_cpl_lock')]

    def unlock(self, reason: str = ''):
        if self.is_locked:
            self.is_locked = False
            self.unlocked_at = timezone.localtime(timezone.now())
            self.reason = reason
            self.save(update_fields=['is_locked', 'unlocked_at', 'reason'])

    @classmethod
    def unlock_for(cls, couple: Couple, completed_recipe: Recipe):
        for fm in cls.objects.filter(couple=couple, is_locked=True, menu__recipes=completed_recipe):
            recipes = fm.menu.recipes.all()
            unlocked = FamilyRecipe.objects.filter(
                couple=couple, recipe__in=recipes, is_locked=False
            ).count()
            if unlocked >= recipes.count():
                fm.unlock(reason='all recipes completed')


class RecipeSuggestion(TimeStampedModel):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='suggestions')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    suggested_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    feedback = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        ordering = ['-suggested_at']
        indexes = [models.Index(fields=['couple', 'used'], name='idx_suggest')]

    def mark_used(self):
        if not self.used:
            self.used = True
            self.save(update_fields=['used'])

    def __str__(self):
        return f"Suggestion#{self.pk} {self.recipe}"


class IngredientPhotoProof(TimeStampedModel):
    task = models.OneToOneField(  # 改为 OneToOneField
        RecipeIngredientTask,
        on_delete=models.CASCADE,
        related_name='proof'  # 改为单数
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    image = models.ImageField(upload_to='ingredient_proofs/')

    class Meta:
        indexes = [models.Index(fields=['created_at'], name='idx_proof_created')]
    def save(self, *args, **kwargs):
        new = self._state.adding
        super().save(*args, **kwargs)
        if new:
            task = self.task
            if not task.is_uploaded:
                task.is_uploaded = True
                task.save(update_fields=['is_uploaded'])
            self._maybe_unlock(task)

    @staticmethod
    def _maybe_unlock(task: RecipeIngredientTask):
        total = IngredientInRecipe.objects.filter(recipe=task.recipe).count()
        uploaded = RecipeIngredientTask.objects.filter(
            recipe=task.recipe,
            couple=task.couple,
            is_uploaded=True
        ).count()
        if total and uploaded >= total:
            fr, _ = FamilyRecipe.objects.get_or_create(
                couple=task.couple, recipe=task.recipe
            )
            fr.unlock(reason='all ingredient photos uploaded')


# apps/recipes/models.py  — 仅替换 RoundBracket 类
from datetime import timedelta
from django.utils import timezone
from django.db import models, transaction
from django.apps import apps

class RoundBracket(TimeStampedModel):
    couple = models.ForeignKey(
        Couple, on_delete=models.CASCADE, related_name='brackets'
    )
    round = models.DateField(help_text='First day of the round')
    active_recipe = models.ForeignKey(
        Recipe, on_delete=models.SET_NULL, null=True, blank=True
    )
    rerolled     = models.BooleanField(default=False)
    rerolled_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('couple', 'round')
        indexes = [models.Index(fields=['couple', 'round'], name='idx_bracket_round')]

    # ───────── helpers ─────────
    ROUND_DAY = 3  # configurable period length

    @classmethod
    def _monday(cls, dt=None):
        dt = dt or timezone.localdate()
        return dt - timedelta(days=dt.weekday())
    
    @classmethod
    def _today(cls, dt=None):
        dt = dt or timezone.localdate()
        return dt
    
    @classmethod
    def checkCurrent(cls, couple: Couple) -> 'RoundBracket':
        """
        Return this round’s bracket.  
        Create the bracket and roll the recipe without cost if bracket doesn't exist.
        """
        round_start = cls._monday()
        # Find bracket whose round is within the current period
        wb = cls.objects.filter(couple=couple, round__gte=round_start, round__lte=cls._today()).order_by('-round').first()
        if wb:
            if wb.active_recipe_id is None:        # 第一次访问还没抽菜
                wb.roll_random_recipe(user=None)   # user=None → 不扣骰子
            return wb
        wb = cls.objects.create(couple=couple, round=cls._monday())
        wb.roll_random_recipe(user=None)
        return wb

    @classmethod
    def current(cls, couple: Couple, user) -> 'RoundBracket':
        """
        Return this round’s bracket.  
        Cost dice to reroll the recipe.
        """
        round_start = cls._monday()
        # Find bracket whose round is within the current period
        wb = cls.objects.filter(couple=couple, round__gte=round_start, round__lte=cls._today()).order_by('-round').first()
        if wb:
            if wb.active_recipe_id is None:        # 第一次访问还没抽菜
                wb.roll_random_recipe(user=None)   # user=None → 不扣骰子
            else:
                wb.roll_random_recipe(user=user)
            return wb
        wb = cls.objects.create(couple=couple, round=cls._monday())
        wb.roll_random_recipe(user=None)
        return wb
        
    # ───────── roll logic ─────────
    REROLL_WINDOW = timedelta(hours=48)

    def roll_random_recipe(self, user=None) -> Recipe:
        """
        If `user` is None → 首次 roll（不扣骰子、不检查窗口）
        If `user` is not None and already has `active_recipe` → reroll 逻辑
        """
        DicePocket = apps.get_model('petcare', 'DicePocket')
        now = timezone.localtime(timezone.now())

        is_second_roll = self.active_recipe_id is not None and user is not None

        if is_second_roll:
            if self.rerolled:
                pass
                # raise ValueError('You have already rerolled this round.')
            if (now - self.created_at) > self.REROLL_WINDOW:
                raise ValueError('Reroll window (48 h) closed.')
            if DicePocket._get(user).balance <= 0:
                raise ValueError('No dice left.')
            DicePocket.spend(user, 1)

        # 排除已解锁菜谱
        unlocked = list(RoundBracket.objects.filter(couple=self.couple).values_list('active_recipe_id', flat=True))

        if unlocked:
            pool = Recipe.objects.exclude(id__in=unlocked)
        else:
            pool = Recipe.objects.all()
        # if is_second_roll and pool.count() > 1:
        #     pool = pool.exclude(id=self.active_recipe_id)
        if not pool.exists():
            raise ValueError('No recipe left to roll.')

        self.active_recipe = pool.order_by('?').first()
        fields = ['active_recipe']
        if is_second_roll:
            self.rerolled = True
            self.rerolled_at = now
            fields += ['rerolled', 'rerolled_at']
        self.save(update_fields=fields)

        # 生成本周 ingredient-tasks（幂等）
        self._ensure_tasks()

        # 确保周记容器
        CoupleMemory = apps.get_model('couplememory', 'CoupleMemory')
        CoupleMemory.current(self.couple)

        return self.active_recipe

    # ───────── private ─────────
    def _ensure_tasks(self):
        """
        create ingredient tasks for each member of the couple.
        only one ingredient is drawn for this week.
        若本周已经生成/上传过任务，则保持现状。
        """
        if not self.active_recipe_id:
            return

        IngredientInRecipe      = apps.get_model('recipes', 'IngredientInRecipe')
        RecipeIngredientTask    = apps.get_model('recipes', 'RecipeIngredientTask')

        # ① 获取couple中的所有用户
        users = self.couple.members.all()
        
        for user in users:
            # ② 检查该用户是否已有任务 → 不重复生成
            if RecipeIngredientTask.objects.filter(
                user=user,
                recipe_id=self.active_recipe_id
            ).exists():
                continue

            # ③ 拿到该菜谱所有 ingredient_id
            ing_ids = list(
                IngredientInRecipe.objects
                .filter(recipe_id=self.active_recipe_id)
                .values_list('ingredient_id', flat=True)
            )
            if not ing_ids:
                continue

            # ④ 随机抽 1 个
            from random import choice
            ing_id = choice(ing_ids)

            # !!覆盖，必定选择Main Ingredient
            if self.active_recipe and self.active_recipe.main_ingredient_id:
                ing_id = self.active_recipe.main_ingredient_id

            # ⑤ 为该用户创建 Task
            RecipeIngredientTask.objects.create(
                couple_id     = self.couple_id,
                user_id       = user.id,
                recipe_id     = self.active_recipe_id,
                ingredient_id = ing_id
            )

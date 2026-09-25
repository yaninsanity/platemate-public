"""
recipes.admin
────────────────────────────────────────────────────────
• CSV 导入/导出（import-export）
• 各模型列表统计/批量动作
• RoundBracket 支持一键 Roll、Reroll、任务完成度统计
"""

import csv
import logging
from datetime import timedelta

from django.contrib import admin
from django.db.models import (
    Count, Prefetch, Max, F, Q,
)
from django.http import HttpResponse
from django.utils import timezone
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from users.models import Couple
from .models import (
    Ingredient, Recipe, IngredientInRecipe, RecipeIngredientTask,
    FamilyRecipe, Menu, FamilyMenu, RoundBracket, IngredientPhotoProof
)

logger = logging.getLogger(__name__)


# ─────────────────── CSV Export mixin ────────────────────
class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [f.name for f in meta.fields]
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = (
            f'attachment; filename={meta.verbose_name_plural}_{timezone.localtime(timezone.now()):%Y%m%d_%H%M%S}.csv'
        )
        writer = csv.writer(resp)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, f) for f in field_names])
        return resp
    export_as_csv.short_description = 'Export selected as CSV'


# ─────────────────── import-export resources ─────────────
class BaseResource(resources.ModelResource):
    class Meta:
        import_id_fields = ['id']
        exclude = ['created_at', 'updated_at']

class IngredientResource(BaseResource):
    class Meta(BaseResource.Meta):
        model = Ingredient


class RecipeResource(BaseResource):
    class Meta(BaseResource.Meta):
        model = Recipe


class IngredientInRecipeResource(BaseResource):
    class Meta(BaseResource.Meta):
        model = IngredientInRecipe


class RecipeIngredientTaskResource(BaseResource):
    class Meta(BaseResource.Meta):
        model = RecipeIngredientTask


class FamilyRecipeResource(BaseResource):
    class Meta(BaseResource.Meta):
        model = FamilyRecipe


class MenuResource(BaseResource):
    class Meta(BaseResource.Meta):
        model = Menu


class FamilyMenuResource(BaseResource):
    class Meta(BaseResource.Meta):
        model = FamilyMenu


class RoundBracketResource(BaseResource):
    class Meta(BaseResource.Meta):
        model = RoundBracket



# ─────────────────── Inlines ─────────────────────────────
class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 0
    autocomplete_fields = ['ingredient']
    raw_id_fields = ['recipe']


class TaskInline(admin.TabularInline):
    model = RecipeIngredientTask
    extra = 0
    autocomplete_fields = ['ingredient', 'couple']
    raw_id_fields = ['recipe']
    readonly_fields = ['is_uploaded', 'is_verified', 'scanned_at']
    can_delete = False


# ─────────────────── Ingredient ──────────────────────────
@admin.register(Ingredient)
class IngredientAdmin(ImportExportModelAdmin, ExportCsvMixin):
    resource_class = IngredientResource
    list_display   = ['name', 'info', 'recipe_count', 'created_at']
    search_fields  = ['name']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['export_as_csv']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(recipe_count=Count('recipes'))

    def recipe_count(self, obj): return obj.recipe_count
    recipe_count.short_description = 'Used in Recipes'


# ─────────────────── Recipe ──────────────────────────────
@admin.register(Recipe)
class RecipeAdmin(ImportExportModelAdmin, ExportCsvMixin):
    resource_class = RecipeResource
    list_display = [
        'name', 'cuisine', 'dish_type', 'main_ingredient',
        'ingredient_count', 'times_rolled', 'last_rolled_at', 'preparation',
        'created_at',
    ]
    list_filter = ['cuisine', 'dish_type']
    search_fields = ['name', 'cuisine', 'dish_type']
    autocomplete_fields = ['main_ingredient']
    inlines = [IngredientInRecipeInline, TaskInline]
    readonly_fields = ['created_at', 'updated_at']
    actions = ['seed_family_recipes', 'export_as_csv']
    list_select_related = ['main_ingredient']
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.annotate(
                ingredient_count=Count('ingredients', distinct=True),
                times_rolled=Count('roundbracket', distinct=True),
                last_rolled_at=Max('roundbracket__created_at'),
            )
            .prefetch_related(
                Prefetch(
                    'roundbracket_set',
                    queryset=RoundBracket.objects.order_by('-round')[:1],
                    to_attr='latest_bracket'
                )
            )
        )

    def ingredient_count(self, obj): return obj.ingredient_count
    ingredient_count.short_description = 'Ingredients'

    def times_rolled(self, obj): return obj.times_rolled
    times_rolled.short_description = 'Bracket Rolls'

    def last_rolled_at(self, obj): return obj.last_rolled_at
    last_rolled_at.short_description = 'Last Rolled'

    @admin.action(description='Seed FamilyRecipe for all couples')
    def seed_family_recipes(self, request, queryset):
        created = 0
        for recipe in queryset:
            for cp in Couple.objects.all():
                _, crt = FamilyRecipe.objects.get_or_create(couple=cp, recipe=recipe)
                if crt: created += 1
        self.message_user(request, f'Created {created} family recipes')


# ─────────────────── IngredientInRecipe ──────────────────
@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(ImportExportModelAdmin, ExportCsvMixin):
    resource_class = IngredientInRecipeResource
    list_display  = ['recipe', 'ingredient', 'quantity', 'created_at']
    autocomplete_fields = ['recipe', 'ingredient']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['export_as_csv']


# ─────────────────── RecipeIngredientTask ────────────────
@admin.register(RecipeIngredientTask)
class RecipeIngredientTaskAdmin(ImportExportModelAdmin, ExportCsvMixin):
    resource_class = RecipeIngredientTaskResource
    list_display = [
        'id', 'recipe', 'ingredient', 'couple',
        'is_uploaded', 'is_verified', 'scanned_at'
    ]
    list_filter = ['is_uploaded', 'is_verified']
    search_fields = ['recipe__name', 'ingredient__name', 'couple__code']
    autocomplete_fields = ['recipe', 'ingredient', 'couple']
    readonly_fields = ['scanned_at', 'created_at', 'updated_at']
    actions = ['mark_verified', 'export_as_csv']

    @admin.action(description='Mark selected tasks as verified')
    def mark_verified(self, request, qs):
        updated = 0
        for task in qs.filter(is_verified=False):
            task.verify(task.couple)
            updated += 1
        self.message_user(request, f'Marked {updated} tasks verified')


# ─────────────────── FamilyRecipe ─────────────────────────
@admin.register(FamilyRecipe)
class FamilyRecipeAdmin(ImportExportModelAdmin, ExportCsvMixin):
    resource_class = FamilyRecipeResource
    list_display = ['couple', 'recipe', 'is_locked', 'unlocked_at', 'reason']
    list_filter  = ['is_locked']
    search_fields = ['couple__code', 'recipe__name']
    autocomplete_fields = ['couple', 'recipe']
    readonly_fields = ['unlocked_at', 'created_at', 'updated_at']
    actions = ['unlock_selected', 'delete_unlocked', 'export_as_csv']

    @admin.action(description='Unlock selected entries')
    def unlock_selected(self, request, qs):
        cnt = qs.filter(is_locked=True).update(
            is_locked=False, unlocked_at=timezone.localtime(timezone.now()), reason='admin unlocked'
        )
        self.message_user(request, f'Unlocked {cnt} entries')

    @admin.action(description='Delete unlocked entries')
    def delete_unlocked(self, request, qs):
        deleted, _ = qs.filter(is_locked=False).delete()
        self.message_user(request, f'Deleted {deleted} unlocked entries')


# ─────────────────── Menu ────────────────────────────────
@admin.register(Menu)
class MenuAdmin(ImportExportModelAdmin, ExportCsvMixin):
    resource_class = MenuResource
    list_display  = ['name', 'description', 'recipe_count']
    filter_horizontal = ['recipes']
    search_fields = ['name']
    actions = ['export_as_csv']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(recipe_count=Count('recipes'))

    def recipe_count(self, obj): return obj.recipe_count
    recipe_count.short_description = 'Recipes'


# ─────────────────── FamilyMenu ──────────────────────────
@admin.register(FamilyMenu)
class FamilyMenuAdmin(ImportExportModelAdmin, ExportCsvMixin):
    resource_class = FamilyMenuResource
    list_display = ['couple', 'menu', 'is_locked', 'unlocked_at']
    list_filter  = ['is_locked']
    search_fields = ['couple__code', 'menu__name']
    autocomplete_fields = ['couple', 'menu']
    readonly_fields = ['unlocked_at', 'created_at', 'updated_at']
    actions = ['export_as_csv']


# ─────────────────── RoundBracket ───────────────────────
@admin.register(RoundBracket)
class RoundBracketAdmin(ImportExportModelAdmin, ExportCsvMixin):
    resource_class = RoundBracketResource
    list_display = [
        'couple', 'round', 'active_recipe', 'task_stats',
        'rerolled', 'created_at'
    ]
    list_filter  = ['rerolled', 'round']
    search_fields = ['couple__code', 'active_recipe__name']
    autocomplete_fields = ['couple', 'active_recipe']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['roll_if_empty', 'reroll_ignore_dice', 'export_as_csv']

    # 完成度 “3/5”
    def task_stats(self, obj):
        if not obj.active_recipe_id:
            return '-'
        total = RecipeIngredientTask.objects.filter(
            recipe=obj.active_recipe_id, couple=obj.couple
        ).count()
        if not total:
            return '0/0'
        done  = RecipeIngredientTask.objects.filter(
            recipe=obj.active_recipe_id, couple=obj.couple, is_verified=True
        ).count()
        return f'{done}/{total}'
    task_stats.short_description = 'Tasks'

    # —— actions ——
    @admin.action(description='Roll if empty (no dice)')
    def roll_if_empty(self, request, qs):
        rolled, skipped = 0, 0
        for wb in qs:
            if wb.active_recipe_id:
                skipped += 1
                continue
            wb.roll_random_recipe()  # user=None → 初次 roll
            rolled += 1
        self.message_user(request, f'Rolled {rolled}; skipped {skipped}')

    @admin.action(description='Force reroll (ignore dice/window)')
    def reroll_ignore_dice(self, request, qs):
        rolled, failed = 0, 0
        for wb in qs:
            try:
                wb.roll_random_recipe(user=None)  # 传 None 绕过窗口与骰子
                rolled += 1
            except ValueError:
                failed += 1
        self.message_user(request, f'Rerolled {rolled}; failed {failed}')


# ─────────────────── Branding ────────────────────────────
admin.site.site_header = 'PlateMate Recipes Admin'
admin.site.site_title  = 'PlateMate Recipes'
admin.site.index_title = 'Dashboard'

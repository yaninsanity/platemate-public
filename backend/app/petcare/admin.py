# app/petcare/admin.py
from __future__ import annotations

import logging
from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, IntegerWidget
from import_export.admin import (
    ImportExportModelAdmin,
    ImportExportActionModelAdmin,
)

# the troublesome dependency is commented out in favour of stock Django admin
# from django_object_actions import DjangoObjectActions
# from advanced_filters.admin import AdminAdvancedFiltersMixin  
# from admin_searchable_dropdown.filters import AutocompleteFilter

from users.models import Couple
from .models import (
    Pet, PetStatus,
    Activity,
    Mission,
    Reminder, ReminderRule,          # 预留：若后续要加后台
    RewardBox,
    Badge,
    DicePocket,                      # ★ NEW
)
from django import forms

logger = logging.getLogger(__name__)



class PetStatusForm(forms.ModelForm):
    class Meta:
        model  = PetStatus
        fields = ("hunger", "happiness", "hygiene", "last_tick")
        widgets = {
            "hunger":     forms.NumberInput(attrs={"min":0, "max":100, "style":"width:80px"}),
            "happiness":  forms.NumberInput(attrs={"min":0, "max":100, "style":"width:80px"}),
            "hygiene":    forms.NumberInput(attrs={"min":0, "max":100, "style":"width:80px"}),
        }

    def clean(self):
        cleaned = super().clean()
        for f in ("hunger", "happiness", "hygiene"):
            val = cleaned.get(f)
            if val is not None and not 0 <= val <= 100:
                self.add_error(f, "必须在 0–100 之间")
        return cleaned
# ═══════════════════════════════════════════════
# 0. Import-Export 资源
# ═══════════════════════════════════════════════
class CoupleFkField(fields.Field):
    """重复使用的 Couple 外键列"""
    def __init__(self, **kw):
        kw.setdefault("widget", ForeignKeyWidget(Couple, "code"))
        super().__init__(**kw)

class ActivityResource(resources.ModelResource):
    couple = CoupleFkField(column_name="couple")
    class Meta:
        model = Activity
        fields = ("id", "couple", "kind", "points", "streak", "created")
        export_order = fields

class MissionResource(resources.ModelResource):
    couple = CoupleFkField(column_name="couple")
    class Meta:
        model = Mission
        fields = (
            "id", "description", "couple", "period",
            "start", "end", "progress", "target_cnt", "is_done",
        )
        export_order = fields

class RewardBoxResource(resources.ModelResource):
    couple = CoupleFkField(column_name="couple")
    class Meta:
        model = RewardBox
        fields = ("id", "couple", "source", "created", "opened_at", "content")
        export_order = fields

class BadgeResource(resources.ModelResource):
    class Meta:
        model = Badge
        fields = ("slug", "desc")
        export_order = fields

class DicePocketResource(resources.ModelResource):          # ★ NEW
    user    = fields.Field(
        column_name="user",
        attribute="user",
        widget=ForeignKeyWidget(get_user_model(), "username"),
    )
    balance = fields.Field(attribute="balance", widget=IntegerWidget())
    class Meta:
        model = DicePocket
        fields = ("id", "user", "balance", "updated")
        export_order = fields


# ═══════════════════════════════════════════════
# 1. 自定义过滤器
# ═══════════════════════════════════════════════
class CoupleFilter(admin.SimpleListFilter):
    title = "Couple"
    parameter_name = "couple"
    
    def lookups(self, request, model_admin):
        couples = Couple.objects.all()
        return [(c.id, str(c)) for c in couples]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(couple_id=self.value())


class KindFilter(admin.SimpleListFilter):
    title          = "Activity Kind"
    parameter_name = "kind"
    def lookups(self, request, model_admin):
        return Activity.KIND_CHOICES
    def queryset(self, request, qs):
        return qs.filter(kind=self.value()) if self.value() else qs


class OpenedFilter(admin.SimpleListFilter):                 # ★ NEW
    title          = "Opened?"
    parameter_name = "opened"
    def lookups(self, request, model_admin):
        return (("yes", _("Yes")), ("no", _("No")))
    def queryset(self, request, qs):
        if self.value() == "yes":
            return qs.filter(opened_at__isnull=False)
        if self.value() == "no":
            return qs.filter(opened_at__isnull=True)
        return qs


# ═══════════════════════════════════════════════
# 2. Inline & 复用组件
# ═══════════════════════════════════════════════
class PetStatusInline(admin.TabularInline):          # ✅ Stack→Tabular
    model  = PetStatus
    form   = PetStatusForm
    extra  = 0
    fields = ("hunger", "happiness", "hygiene", "last_tick")
    readonly_fields = ("last_tick",)      # 仅日期锁定
    can_delete = False

class RecentActivityInline(admin.TabularInline):
    """Couple 页面侧栏：最近 5 条 Activity"""
    model  = Activity
    fk_name = "couple"
    extra   = 0
    readonly_fields = ("kind", "points", "created")
    fields  = readonly_fields
    verbose_name_plural = "Recent Activities"

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("-created")

    max_num = 5


class PetInline(admin.StackedInline):
    model = Pet
    extra = 0
    readonly_fields = ("level", "xp", "next_level", "skin", "created", "updated")
    raw_id_fields = ["couple"]


# ═══════════════════════════════════════════════
# 3. 核心 ModelAdmin
# ═══════════════════════════════════════════════
@admin.register(Pet)
class PetAdmin(ImportExportActionModelAdmin):
    list_display  = (
        "id", "couple", "nickname", "species",
        "level", "xp",                       
        "hunger_", "happy_", "clean_"       
    )
    
    list_filter   = ("species", "skin", CoupleFilter)
    search_fields = ("couple__code", "nickname")
    inlines       = [PetStatusInline]
    raw_id_fields = ["couple"]
    actions       = ["feed_selected", "tick_status","daily_decay",
        "full_restore",]

    @admin.display(description="🍗")
    def hunger_(self, obj): return obj.status.hunger

    @admin.display(description="😀")
    def happy_(self, obj):  return obj.status.happiness

    @admin.display(description="🛁")
    def clean_(self, obj):  return obj.status.hygiene

    # —— Actions —— #
    @admin.action(description="Feed +10 🍗")
    def feed_selected(self, request, qs):
        for pet in qs:
            st = pet.status
            st.hunger = min(100, st.hunger + 10)
            st.save(update_fields=["hunger"])
        self.message_user(request, f"Fed {qs.count()} pet(s) +10 hunger.", messages.SUCCESS)

    @admin.action(description="Daily decay −1 天")
    def daily_decay(self, request, qs):
        today = timezone.localtime(timezone.now()).date()
        decayed = 0
        for pet in qs:
            st = pet.status
            if st.last_tick < today:
                days = (today - st.last_tick).days
                for field, d in PetStatus.DECAY.items():
                    setattr(st, field, max(0, getattr(st, field) - d * days))
                st.last_tick = today
                st.save()
                decayed += 1
        self.message_user(request, f"Applied decay to {decayed} pet(s).", messages.SUCCESS)

    @admin.action(description="Full restore 100/100/100")
    def full_restore(self, request, qs):
        for pet in qs:
            st = pet.status
            st.hunger = st.happiness = st.hygiene = 100
            st.save()
        self.message_user(request, f"Restored {qs.count()} pet(s).", messages.SUCCESS)
    @admin.action(description="Run daily decay for selected")
    def tick_status(self, request, qs):
        for pet in qs:
            pet.status.daily_tick()
        self.message_user(request, "Daily decay executed.", messages.SUCCESS)


@admin.register(Activity)
class ActivityAdmin(ImportExportModelAdmin):
    resource_class = ActivityResource
    list_display   = ("id", "kind", "couple", "points", "streak", "created")  # ★ add streak
    list_filter    = (CoupleFilter, KindFilter, "created")
    search_fields  = ("couple__code", "metadata")
    date_hierarchy = "created"
    raw_id_fields  = ["couple", "recipe"]
    readonly_fields= ("kind", "couple", "points", "recipe",
                      "streak", "metadata", "created")
    list_per_page  = 50


@admin.register(Mission)
class MissionAdmin(ImportExportActionModelAdmin):
    resource_class = MissionResource
    list_display   = ("description", "couple", "period", "start",
                      "end", "progress", "target_cnt", "is_done")
    list_filter    = (CoupleFilter, "period", "start", "is_done")
    search_fields  = ("couple__code", "description")
    date_hierarchy = "start"
    raw_id_fields  = ["couple"]
    actions        = ["generate_roundly", "mark_done"]
    change_actions = ["run_progress"]

    @admin.action(description="Generate roundly missions for all")
    def generate_roundly(self, request, qs):
        Mission.seed_roundly()
        self.message_user(request, "Roundly missions seeded ✅", messages.SUCCESS)

    @admin.action(description="Mark selected as done & drop box")
    def mark_done(self, request, qs):
        cnt = 0
        for m in qs.filter(is_done=False):
            m.progress = m.target_cnt
            m.is_done  = True
            m.save(update_fields=["progress", "is_done"])
            RewardBox.drop(m.couple, "mission", points=m.reward_pts)
            cnt += 1
        self.message_user(request, f"Marked {cnt} mission(s) done.", messages.SUCCESS)

    def run_progress(self, request, obj):
        Mission.progress(obj.couple, obj.target_kind)
        self.message_user(request, f"Mission {obj.pk} progressed.", messages.SUCCESS)
    run_progress.label = "Progress +1"


class PrettyJSONMixin:
    """在列表页以 <code>{…}</code> 渲染 JSONField"""
    @admin.display(description="内容")
    def pretty_content(self, obj):
        return mark_safe(f"<code>{obj.content}</code>")


@admin.register(RewardBox)
class RewardBoxAdmin(ImportExportModelAdmin,
                     PrettyJSONMixin):
    resource_class = RewardBoxResource
    list_display   = ("id", "couple", "source", "created",
                      "opened_at", "pretty_content")
    list_filter    = (CoupleFilter, "source", OpenedFilter)
    search_fields  = ("couple__code",)
    date_hierarchy = "created"
    raw_id_fields  = ["couple"]
    readonly_fields= ("created", "opened_at", "content")
    actions        = ["open_selected"]
    change_actions = ["open_box"]

    @admin.action(description="Open selected boxes")
    def open_selected(self, request, qs):
        opened = 0
        for box in qs.filter(opened_at__isnull=True):
            box.open()
            opened += 1
        self.message_user(request, f"Opened {opened} box(es).", messages.SUCCESS)

    def open_box(self, request, obj):
        if obj.opened_at:
            self.message_user(request, "Already opened.", messages.INFO)
        else:
            obj.open()
            self.message_user(request, "Box opened ✅", messages.SUCCESS)
    open_box.label = "Open"


@admin.register(Badge)
class BadgeAdmin(ImportExportActionModelAdmin):
    resource_class = BadgeResource
    list_display   = ("slug", "desc", "couple_count")
    filter_horizontal = ("couples",)
    search_fields = ("slug", "desc")
    list_filter   = ("slug",)

    @admin.display(description="领取人数")
    def couple_count(self, obj):
        return obj.couples.count()


# ═══════════════════════════════════════════════
# 4. DicePocket Admin  ★ NEW
# ═══════════════════════════════════════════════
@admin.register(DicePocket)
class DicePocketAdmin(ImportExportActionModelAdmin):
    resource_class = DicePocketResource
    list_display   = ("id", "user", "balance", "updated")
    search_fields  = ("user__username", "user__email")
    list_filter    = ("balance",)
    readonly_fields= ("updated",)
    actions        = ["bulk_recharge", "bulk_deduct"]
    change_actions = ["recharge_one", "deduct_one"]
    raw_id_fields  = ["user"]

    # —— helpers —— #
    def _get_amount(self, request) -> int | None:
        try:
            return int(request.POST.get("amount"))
        except (TypeError, ValueError):
            return None

    # —— bulk actions —— #
    @admin.action(description="批量充值 +N Dice (需 amount 参数)")
    def bulk_recharge(self, request, qs):
        delta = self._get_amount(request)
        if delta is None:
            self.message_user(request, "include amount in the form=整数", messages.WARNING)
            return
        for pocket in qs:
            pocket.add(delta)
        self.message_user(request, f"充值 {qs.count()} 用户 +{delta} Dice", messages.SUCCESS)

    @admin.action(description="批量扣除 −N Dice (需 amount 参数)")
    def bulk_deduct(self, request, qs):
        delta = self._get_amount(request)
        if delta is None:
            self.message_user(request, "include amount in the form=整数", messages.WARNING)
            return
        for pocket in qs:
            try:
                pocket.spend(delta)
            except ValueError:
                pocket.balance = 0
                pocket.save(update_fields=["balance", "updated"])
        self.message_user(request, "扣除完成（不足余额已清零）", messages.SUCCESS)

    # —— per-object —— #
    def recharge_one(self, request, obj):
        obj.add(1)
        self.message_user(request, "+1 Dice 已充值", messages.SUCCESS)
    recharge_one.label = "+1 Dice"

    def deduct_one(self, request, obj):
        try:
            obj.spend(1)
            self.message_user(request, "−1 Dice 已扣除", messages.SUCCESS)
        except ValueError:
            self.message_user(request, "余额不足", messages.WARNING)
    deduct_one.label = "−1 Dice"


# ═══════════════════════════════════════════════
# 5. 重新挂载 CoupleAdmin（带 Pet & Activity Inline）
#    extend users.admin.CoupleAdmin if it is registered, otherwise define our own.
# ═══════════════════════════════════════════════
try:
    from users.admin import CoupleAdmin as _BaseCoupleAdmin
except ImportError:
    _BaseCoupleAdmin = admin.ModelAdmin

admin.site.unregister(Couple)

@admin.register(Couple)
class CoupleAdmin(_BaseCoupleAdmin):  # type: ignore[misc]
    inlines       = getattr(_BaseCoupleAdmin, "inlines", []) + [PetInline, RecentActivityInline]
    list_display  = getattr(_BaseCoupleAdmin, "list_display", ()) + ("code",)
    search_fields = getattr(_BaseCoupleAdmin, "search_fields", ()) + ("code",)



# ═══════════════════════════════════════════════
# 6. Branding
# ═══════════════════════════════════════════════
admin.site.site_header = "PlateMate PetCare 管理后台"
admin.site.site_title  = "PlateMate PetCare Admin"
admin.site.index_title = "PetCare 管理面板"




# 添加到 petcare/admin.py 文件中

from django.contrib import admin
from .models import PetMessageTemplate, UserPetMessageState


@admin.register(PetMessageTemplate)
class PetMessageTemplateAdmin(admin.ModelAdmin):
    """宠物消息模板管理"""

    list_display = [
        'state_code',
        'message_preview',
        'weight',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'state_code',
        'is_active',
        'created_at'
    ]
    search_fields = [
        'message_template',
        'state_code'
    ]
    ordering = ['state_code', '-weight', '-created_at']

    # 字段分组
    fieldsets = (
        ('基本信息', {
            'fields': ('state_code', 'message_template')
        }),
        ('配置', {
            'fields': ('weight', 'is_active')
        }),
    )

    # 列表页面每页显示数量
    list_per_page = 50

    # 可以直接在列表页编辑的字段
    list_editable = ['weight', 'is_active']

    # 添加自定义操作
    actions = ['activate_templates', 'deactivate_templates', 'duplicate_template']

    def message_preview(self, obj):
        """显示消息预览（截取前50字符）"""
        preview = obj.message_template[:50]
        return f"{preview}..." if len(obj.message_template) > 50 else preview

    message_preview.short_description = "Message Preview"

    def activate_templates(self, request, queryset):
        """批量激活模板"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {updated} templates.")

    activate_templates.short_description = "激活选中的模板"

    def deactivate_templates(self, request, queryset):
        """批量停用模板"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {updated} templates.")

    deactivate_templates.short_description = "停用选中的模板"

    def duplicate_template(self, request, queryset):
        """复制选中的模板"""
        count = 0
        for template in queryset:
            template.pk = None
            template.message_template = f"[Copy] {template.message_template}"
            template.save()
            count += 1
        self.message_user(request, f"Successfully duplicated {count} templates.")

    duplicate_template.short_description = "复制选中的模板"


# in petcare/admin.py, find and fully replace the UserPetMessageStateAdmin class



# ========================================
# update UserPetMessageStateAdmin
# ========================================
@admin.register(UserPetMessageState)
class UserPetMessageStateAdmin(admin.ModelAdmin):
    """用户宠物消息状态管理 - 简化版"""

    list_display = [
        'user',
        'couple',
        'states_display',
        'messages_count',
        'last_updated'
    ]
    list_filter = [
        'couple',
        'last_updated',
        'created_at'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'couple__code'
    ]
    ordering = ['-last_updated']

    # 使用 fieldsets，不使用 fields
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'couple')
        }),
        ('状态管理', {
            'fields': ('current_states',),
            'description': '可编辑状态列表。支持：state1(上传食材前), state2(做菜前), state3(宠物饥饿), state6(等待上传), state7(等待完成)<br>格式：["state1", "state3"]'
        }),
        ('消息内容', {
            'fields': ('available_messages_display',),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'last_updated',
        'created_at',
        'available_messages_display'
    ]

    raw_id_fields = ['user', 'couple']
    list_per_page = 50

    # 简单的批量操作
    actions = ['refresh_messages']

    # =======================================================
    # 显示方法
    # =======================================================

    def states_display(self, obj):
        """显示当前状态"""
        if not obj.current_states:
            return "无状态"
        return ", ".join(obj.current_states)

    states_display.short_description = "当前状态"

    def messages_count(self, obj):
        """显示消息总数"""
        if not obj.available_messages:
            return "0"

        if isinstance(obj.available_messages, dict):
            total = sum(len(msgs) for msgs in obj.available_messages.values() if isinstance(msgs, list))
            return str(total)

        return "0"

    messages_count.short_description = "消息数量"

    def available_messages_display(self, obj):
        """显示可用消息"""
        if not obj.available_messages:
            return "无消息"

        if isinstance(obj.available_messages, dict):
            display_parts = []
            total_count = 0

            for state, messages in obj.available_messages.items():
                if isinstance(messages, list) and messages:
                    display_parts.append(f"=== {state} ({len(messages)}条) ===")
                    for i, msg in enumerate(messages, 1):
                        # 限制显示长度
                        display_msg = msg[:60] + "..." if len(msg) > 60 else msg
                        display_parts.append(f"{i}. {display_msg}")
                    total_count += len(messages)

            if display_parts:
                display_parts.append(f"--- 总计: {total_count}条消息 ---")
                return "\n".join(display_parts)

        return "消息格式错误"

    available_messages_display.short_description = "可用消息"

    # =======================================================
    # 核心功能：状态修改时自动同步消息
    # =======================================================

    def save_model(self, request, obj, form, change):
        """保存时自动重新生成消息"""
        super().save_model(request, obj, form, change)

        # 状态修改后重新生成消息
        try:
            from .pet_message_service import refresh_user_pet_messages
            refresh_user_pet_messages(obj.user, "admin_manual_edit")

            # 成功提示
            messages.success(request, f"状态已更新，消息已自动重新生成")

        except Exception as e:
            messages.error(request, f"状态更新成功，但消息生成失败：{e}")

    # =======================================================
    # 批量操作
    # =======================================================

    def refresh_messages(self, request, queryset):
        """刷新选中用户的消息状态"""
        from .pet_message_service import refresh_user_pet_messages

        success_count = 0
        error_count = 0

        for state in queryset:
            try:
                refresh_user_pet_messages(state.user, "admin_refresh")
                success_count += 1
            except Exception as e:
                error_count += 1

        if success_count:
            messages.success(request, f"成功刷新 {success_count} 个用户的消息")
        if error_count:
            messages.warning(request, f"有 {error_count} 个用户刷新失败")

    refresh_messages.short_description = "刷新选中用户的消息"

    # =======================================================
    # 表单定制
    # =======================================================

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """为current_states字段提供更好的编辑体验"""
        if db_field.name == 'current_states':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget(
                attrs={
                    'rows': 2,
                    'cols': 40,
                    'style': 'font-family: monospace;',
                    'placeholder': '["state1", "state3"]'
                }
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)


# ────────────────────────────────────────────────────────────
# 自定义Admin视图 (可选)
# ────────────────────────────────────────────────────────────

class PetMessageAdminMixin:
    """为其他Admin类提供宠物消息相关的便捷功能"""

    def update_pet_messages(self, request, queryset):
        """为选中的用户/couple更新宠物消息"""
        from .pet_message_service import PetMessageService

        updated_count = 0
        for obj in queryset:
            try:
                # 根据对象类型决定如何获取用户
                if hasattr(obj, 'members'):  # Couple对象
                    users = obj.members.all()
                elif hasattr(obj, 'user'):  # 有user字段的对象
                    users = [obj.user]
                else:  # User对象
                    users = [obj]

                for user in users:
                    PetMessageService.update_user_messages(user)
                    updated_count += 1

            except Exception as e:
                self.message_user(request, f"Error updating messages: {e}", level='ERROR')

        self.message_user(request, f"Updated pet messages for {updated_count} users.")

    update_pet_messages.short_description = "更新宠物消息"


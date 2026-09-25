# apps/users/admin.py
from __future__ import annotations

import csv
import logging

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html, conditional_escape, mark_safe
from django.utils.translation import gettext_lazy as _

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin

# Import Avatar model for avatar functionality
from avatar.models import Avatar

from .models import CustomUser, Couple, CoupleMembership, generate_couple_code

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# 1) Resources  (django-import-export)
# ════════════════════════════════════════════════════════════════
class CustomUserResource(resources.ModelResource):
    class Meta:
        model = CustomUser
        fields = (
            "id", "username", "email", "first_name", "last_name",
            "phone", "phone_verified", "timezone",
            "is_active", "is_staff", "is_superuser", "date_joined",
        )
        export_order = fields


class CoupleResource(resources.ModelResource):
    class Meta:
        model  = Couple
        fields = ("id", "code", "name", "created_at")
        export_order = fields


class CoupleMembershipResource(resources.ModelResource):
    user = fields.Field(
        column_name = "username",
        attribute   = "user",
        widget      = ForeignKeyWidget(CustomUser, "username"),
    )
    couple = fields.Field(
        column_name = "couple_code",
        attribute   = "couple",
        widget      = ForeignKeyWidget(Couple, "code"),
    )

    class Meta:
        model  = CoupleMembership
        fields = ("id", "user", "couple", "joined_at")
        export_order = fields


# ════════════════════════════════════════════════════════════════
# 2) Mixin – quick CSV export (kept)
# ════════════════════════════════════════════════════════════════
class ExportCsvMixin:
    @admin.action(description="Export as CSV")
    def export_as_csv(self, request, queryset):
        meta        = self.model._meta
        field_names = [f.name for f in meta.fields]
        resp        = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename={}.csv'.format(meta.verbose_name_plural)

        writer = csv.writer(resp)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, fn) for fn in field_names])
        return resp


# ════════════════════════════════════════════════════════════════
# 3) Inline for CoupleMembership
# ════════════════════════════════════════════════════════════════
class CoupleMembershipInline(admin.TabularInline):
    model               = CoupleMembership
    extra               = 0
    readonly_fields     = ("joined_at",)
    autocomplete_fields = ("couple",)
    raw_id_fields       = ("user",)
    verbose_name        = "Membership"
    verbose_name_plural = "Memberships"


# ════════════════════════════════════════════════════════════════
# 4) Avatar Inline for django-avatar
# ════════════════════════════════════════════════════════════════
class AvatarInline(admin.TabularInline):
    model = Avatar
    extra = 0
    readonly_fields = ("date_uploaded", "avatar_preview")
    fields = ("avatar", "primary", "avatar_preview", "date_uploaded")

    def avatar_preview(self, obj):
        if getattr(obj, "avatar", None):
            # conditional_escape guards against URL injection; mark_safe returns the full HTML, bypassing format_html 的 .format 解析
            esc_url = conditional_escape(obj.avatar.url)
            return mark_safe(
                f'<img src="{esc_url}" style="height:50px;width:50px;border-radius:50%;object-fit:cover;" />'
            )
        return "—"

    avatar_preview.short_description = "Preview"


# ════════════════════════════════════════════════════════════════
# 5) CustomUserAdmin  (avatar support fixed)
# ════════════════════════════════════════════════════════════════
@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin, ExportCsvMixin, BaseUserAdmin):
    resource_class = CustomUserResource
    inlines = [CoupleMembershipInline, AvatarInline]  # Added AvatarInline

    # ――― fieldsets (removed avatar field, kept avatar_preview) ―――
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {
            "fields": (
                "first_name", "last_name", "email",
                "bio", "birth_date", "avatar_preview",  # Removed "avatar"
            )
        }),
        (_("Contact & Preferences"), {
            "fields": (
                "phone", "phone_verified",
                "sms_opt_in", "email_opt_in", "timezone", "address",
            )
        }),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    # ――― list display & filters ―――
    list_display = (
        "username", "email", "first_name", "last_name", "is_staff"
    )
    # Temporarily simplified - will add back other fields once we identify the issue
    # "avatar_thumb", "phone_verified", "couple_link",
    list_filter    = (
        "is_active", "is_staff", "is_superuser",
        "phone_verified", "sms_opt_in", "email_opt_in",
    )
    search_fields  = ("username", "email", "first_name", "last_name", "phone")
    ordering       = ("username",)
    actions        = ["export_as_csv"]
    readonly_fields = ("avatar_preview",)          # prevent accidental overwrite
    # raw_id_fields  = ("couples",)  # Removed - couples is a reverse M2M relationship

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related to avoid N+1 queries."""
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            'couplemembership_set__couple',
            'avatar_set'
        ).select_related()

    # ――― helpers ―――
    def avatar_thumb(self, obj):
        """Get user's primary avatar for list display."""
        try:
            avatar = (
                Avatar.objects.filter(user=obj, primary=True).first()
                or Avatar.objects.filter(user=obj).order_by("-date_uploaded").first()
            )
            if avatar and avatar.avatar:
                esc_url = conditional_escape(avatar.avatar.url)
                # use mark_safe so a % in the format_html string cannot break it : 被解析
                return mark_safe(
                    f'<img src="{esc_url}" style="height:32px;width:32px;border-radius:50%;object-fit:cover;" />'
                )
        except Exception:
            pass
        return "—"
    avatar_thumb.short_description = "Avatar"

    def avatar_preview(self, obj):
        """Get user's avatar for detail view."""
        return self.avatar_thumb(obj)
    avatar_preview.short_description = "Current avatar"

    def couple_link(self, obj):
        """Display couple information with admin link."""
        try:
            membership = obj.couplemembership_set.first()
            if membership and membership.couple:
                couple = membership.couple
                url = reverse("admin:users_couple_change", args=[couple.pk])
                # 转义显示文本，安全输出
                display_text = (couple.display_name or 'Unnamed Couple')
                esc_text = conditional_escape(display_text)
                esc_url  = conditional_escape(url)
                return mark_safe(f'<a href="{esc_url}">{esc_text}</a>')
        except Exception as e:
            logger.error(f"Error in couple_link for user {obj.pk}: {e}")
        return "—"
    couple_link.short_description = "Couple"


# ════════════════════════════════════════════════════════════════
# 6) CoupleAdmin
# ════════════════════════════════════════════════════════════════
@admin.register(Couple)
class CoupleAdmin(ImportExportModelAdmin, ExportCsvMixin, admin.ModelAdmin):
    resource_class      = CoupleResource
    inlines             = [CoupleMembershipInline]
    list_display        = ("display_name", "code", "created_at", "members_count", "is_complete")
    list_filter         = ("created_at",)
    search_fields       = ("code", "members__username")
    ordering            = ("-created_at",)
    actions             = ["reset_codes", "export_as_csv"]
    raw_id_fields       = ("members",)

    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = "Members"

    @admin.action(description="Regenerate invite codes")
    def reset_codes(self, request, queryset):
        updated = 0
        for couple in queryset:
            couple.code = generate_couple_code()
            couple.save(update_fields=["code"])
            updated += 1
        message = "Regenerated {} invite codes.".format(updated)
        self.message_user(request, message)


# ════════════════════════════════════════════════════════════════
# 7) CoupleMembershipAdmin
# ════════════════════════════════════════════════════════════════
@admin.register(CoupleMembership)
class CoupleMembershipAdmin(ImportExportModelAdmin, ExportCsvMixin, admin.ModelAdmin):
    resource_class  = CoupleMembershipResource
    list_display    = ("user", "couple", "joined_at")
    list_filter     = ("couple", "joined_at")
    search_fields   = ("user__username", "couple__code")
    readonly_fields = ("joined_at",)
    raw_id_fields   = ("user", "couple")
    actions         = ["export_as_csv"]

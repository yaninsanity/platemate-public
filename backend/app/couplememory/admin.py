"""
Industrial-Grade Django Admin for Couple Memory System
Maximum Control, Visibility & Management Capabilities
Built for Production Game Management
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse, path
from django.contrib import messages
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q, Avg, Max, Min
from django.utils import timezone
from django.forms import Textarea, ModelForm, ValidationError
from django.db import transaction
from django.middleware.csrf import get_token

from .models import CoupleMemory, MemoryEntry, MemoryMedia, MemoryComment, AIJudgment

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Utility Functions - Production Ready
# ═══════════════════════════════════════════════════════════════

def safe_float(value: Any, default: float = 0.0) -> float:
    """Production-safe float conversion with logging"""
    try:
        if value is None:
            return default
        return float(str(value).strip())
    except (ValueError, TypeError) as e:
        logger.debug(f"safe_float conversion failed: {value} -> {default} ({e})")
        return default

def fmt_score(score: Any, precision: int = 1) -> str:
    """Format score with configurable precision"""
    if score is None:
        return "-"
    return f"{safe_float(score):.{precision}f}"

def get_media_info(media_obj) -> Dict[str, Any]:
    """Safely extract media information"""
    try:
        if not media_obj or not hasattr(media_obj, 'url'):
            return {'url': None, 'size': 0, 'name': 'No media'}
        
        return {
            'url': media_obj.url,
            'size': getattr(media_obj, 'size', 0),
            'name': os.path.basename(getattr(media_obj, 'name', 'unknown')),
            'exists': os.path.exists(media_obj.path) if hasattr(media_obj, 'path') else False
        }
    except Exception as e:
        logger.warning(f"Media info extraction failed: {e}")
        return {'url': None, 'size': 0, 'name': 'Error', 'exists': False}

# ═══════════════════════════════════════════════════════════════
# Advanced Filters for Maximum Control
# ═══════════════════════════════════════════════════════════════

class AdvancedAIStatusFilter(SimpleListFilter):
    title = _('AI Analysis Status')
    parameter_name = 'ai_status'

    def lookups(self, request, model_admin):
        return [
            ('detailed_high', _('🟢 Detailed (Score ≥80)')),
            ('detailed_mid', _('🟡 Detailed (Score 50-79)')),
            ('detailed_low', _('🔴 Detailed (Score <50)')),
            ('basic_only', _('📊 Basic Score Only')),
            ('processing', _('⏳ Processing/Pending')),
            ('failed', _('❌ Analysis Failed')),
            ('none', _('⚪ No Analysis')),
            ('needs_retry', _('🔄 Needs Retry')),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'detailed_high':
            return queryset.filter(ai_judgment__isnull=False, ai_judgment__overall_score__gte=80)
        elif value == 'detailed_mid':
            return queryset.filter(ai_judgment__isnull=False, ai_judgment__overall_score__range=(50, 79))
        elif value == 'detailed_low':
            return queryset.filter(ai_judgment__isnull=False, ai_judgment__overall_score__lt=50)
        elif value == 'basic_only':
            return queryset.filter(ai_judgment__isnull=True, ai_score__isnull=False)
        elif value == 'failed':
            return queryset.filter(
                Q(ai_judgment__ai_comment__icontains='error') | 
                Q(ai_judgment__ai_comment__icontains='failed') |
                Q(ai_judgment__ai_comment__icontains='timeout')
            )
        elif value == 'none':
            return queryset.filter(ai_judgment__isnull=True, ai_score__isnull=True)
        elif value == 'needs_retry':
            # Entries with media but no AI analysis after 24h
            cutoff = timezone.now() - timedelta(hours=24)
            return queryset.filter(
                created_at__lt=cutoff,
                ai_judgment__isnull=True,
                ai_score__isnull=True
            ).annotate(media_count=Count('media')).filter(media_count__gt=0)
        return queryset

class MediaStatusFilter(SimpleListFilter):
    title = _('Media Status')
    parameter_name = 'media_status'

    def lookups(self, request, model_admin):
        return [
            ('has_highlight', _('🌟 Has Highlight Media')),
            ('multiple', _('📷 Multiple Media Files')),
            ('single', _('📸 Single Media File')),
            ('none', _('❌ No Media Files')),
            ('broken', _('🔗 Broken Media Links')),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'has_highlight':
            return queryset.filter(media__is_highlight=True).distinct()
        elif value == 'multiple':
            return queryset.annotate(media_count=Count('media')).filter(media_count__gt=1)
        elif value == 'single':
            return queryset.annotate(media_count=Count('media')).filter(media_count=1)
        elif value == 'none':
            return queryset.annotate(media_count=Count('media')).filter(media_count=0)
        return queryset

class UserActivityFilter(SimpleListFilter):
    title = _('User Activity Level')
    parameter_name = 'user_activity'

    def lookups(self, request, model_admin):
        return [
            ('high', _('🔥 High Activity (10+ entries)')),
            ('medium', _('📈 Medium Activity (3-9 entries)')),
            ('low', _('📉 Low Activity (1-2 entries)')),
            ('inactive', _('💤 Inactive Users')),
            ('staff', _('👨‍💼 Staff Members')),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'high':
            return queryset.filter(author__memoryentry__isnull=False).annotate(
                entry_count=Count('author__memoryentry')
            ).filter(entry_count__gte=10)
        elif value == 'medium':
            return queryset.filter(author__memoryentry__isnull=False).annotate(
                entry_count=Count('author__memoryentry')
            ).filter(entry_count__range=(3, 9))
        elif value == 'low':
            return queryset.filter(author__memoryentry__isnull=False).annotate(
                entry_count=Count('author__memoryentry')
            ).filter(entry_count__range=(1, 2))
        elif value == 'inactive':
            return queryset.filter(author__is_active=False)
        elif value == 'staff':
            return queryset.filter(author__is_staff=True)
        return queryset

# ═══════════════════════════════════════════════════════════════
# Industrial-Grade Memory Entry Admin
# ═══════════════════════════════════════════════════════════════

class MemoryEntryForm(ModelForm):
    """Enhanced form with validation and preprocessing"""
    class Meta:
        model = MemoryEntry
        fields = '__all__'
        widgets = {
            'content': Textarea(attrs={'rows': 6, 'cols': 80, 'placeholder': 'Enter memory content...'}),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content', '')
        if len(content.strip()) < 10:
            raise ValidationError("Content must be at least 10 characters long.")
        return content.strip()

@admin.register(MemoryEntry)
class IndustrialMemoryEntryAdmin(admin.ModelAdmin):
    """
    Industrial-Grade Memory Entry Admin
    Maximum Control & Visibility for Production Game Management
    """
    form = MemoryEntryForm
    
    # Core Display Configuration
    list_display = [
        'entry_id_display',
        'author_status_display', 
        'content_smart_preview',
        'media_status_display',
        'ai_comprehensive_status',
        'ai_score_breakdown',
        'couple_battle_status',
        'timestamp_display',
        'admin_action_buttons'
    ]
    
    list_filter = [
        'created_at',
        'memory__couple',
        'author__is_active',
        'recipe__name',
        AdvancedAIStatusFilter,
        MediaStatusFilter,
        UserActivityFilter,
    ]
    
    search_fields = [
        'content', 
        'author__username', 
        'author__email',
        'memory__couple__code',
        'recipe__name',
        'ai_judgment__ai_comment',
        'ai_judgment__ai_summary'
    ]
    
    readonly_fields = [
        'id', 'created_at',
        'comprehensive_media_panel',
        'ai_analysis_dashboard',
        'user_relationship_panel',
        'system_diagnostics_panel',
        'battle_comparison_panel'
    ]
    
    fieldsets = [
        ('📝 Content Management', {
            'fields': ['content', 'recipe', 'comprehensive_media_panel'],
            'classes': ['wide']
        }),
        ('🤖 AI Analysis Dashboard', {
            'fields': ['ai_analysis_dashboard'],
            'classes': ['wide', 'collapse']
        }),
        ('👥 User & Relationship Management', {
            'fields': ['user_relationship_panel'],
            'classes': ['collapse']
        }),
        ('⚔️ Battle & Competition Analysis', {
            'fields': ['battle_comparison_panel'],
            'classes': ['collapse']
        }),
        ('🔧 System Diagnostics', {
            'fields': ['system_diagnostics_panel'],
            'classes': ['collapse']
        }),
        ('📅 Metadata', {
            'fields': ['id', 'created_at'],
            'classes': ['collapse']
        })
    ]

    actions = [
        'mass_ai_analysis',
        'force_ai_regeneration', 
        'clear_ai_data',
        'promote_to_highlight',
        'battle_mode_analysis',
        'export_analytics_report',
        'moderate_content',
        'activate_users',
        'emergency_reset'
    ]
    
    list_per_page = 30
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    # ═══════════════════════════════════════════════════════════════
    # Enhanced Display Methods with Maximum Information
    # ═══════════════════════════════════════════════════════════════
    
    @admin.display(ordering='id', description='Entry ID')
    def entry_id_display(self, obj):
        """Enhanced ID display with quick navigation"""
        return format_html(
            '<div style="text-align: center;">'
            '<strong style="font-size: 14px; color: #0066cc;">#{}</strong><br>'
            '<small style="color: #666;">M{}</small>'
            '</div>',
            obj.id,
            obj.memory.id
        )
    
    @admin.display(ordering='author__username', description='Author Status')
    def author_status_display(self, obj):
        """Comprehensive author information"""
        user = obj.author
        
        # Calculate user stats
        total_entries = MemoryEntry.objects.filter(author=user).count()
        avg_score = MemoryEntry.objects.filter(
            author=user, ai_score__isnull=False
        ).aggregate(avg=Avg('ai_score'))['avg'] or 0
        
        # Status indicators
        status_color = '#28a745' if user.is_active else '#dc3545'
        status_icon = '🟢' if user.is_active else '🔴'
        staff_badge = '👨‍💼' if user.is_staff else ''
        premium_badge = '⭐' if hasattr(user, 'is_premium') and user.is_premium else ''
        
        return format_html(
            '<div style="min-width: 120px;">'
            '<div style="font-weight: bold; margin-bottom: 2px;">'
            '<a href="{}" target="_blank" style="color: {}; text-decoration: none;">'
            '{} {}{}{}'
            '</a>'
            '</div>'
            '<div style="font-size: 11px; color: #666; line-height: 1.3;">'
            'Entries: {} | Avg: {}<br>'
            'Email: {}'
            '</div>'
            '</div>',
            reverse('admin:users_customuser_change', args=[user.pk]),
            status_color,
            status_icon,
            user.username,
            staff_badge,
            premium_badge,
            total_entries,
            fmt_score(avg_score),
            user.email[:20] + '...' if user.email and len(user.email) > 20 else user.email or 'No email'
        )
    
    @admin.display(description='Content Preview')
    def content_smart_preview(self, obj):
        """Smart content preview with analysis"""
        content = obj.content
        preview_length = 80
        
        # Content analysis
        word_count = len(content.split())
        char_count = len(content)
        has_emojis = any(ord(char) > 127 for char in content)
        
        # Truncate if needed
        if len(content) > preview_length:
            preview = content[:preview_length] + '...'
        else:
            preview = content
        
        # Quality indicators
        quality_color = '#28a745' if word_count >= 10 else '#ffc107' if word_count >= 5 else '#dc3545'
        
        return format_html(
            '<div style="max-width: 250px;">'
            '<div style="margin-bottom: 4px; line-height: 1.3;">{}</div>'
            '<div style="font-size: 10px; color: {}; display: flex; gap: 8px;">'
            '<span>Words: {}</span>'
            '<span>Chars: {}</span>'
            '{}'
            '</div>'
            '</div>',
            preview,
            quality_color,
            word_count,
            char_count,
            '<span>📝 Rich</span>' if has_emojis else ''
        )
    
    @admin.display(description='Media Status')
    def media_status_display(self, obj):
        """Comprehensive media status with quick actions"""
        media_files = obj.media.all()
        count = media_files.count()
        
        if count == 0:
            return format_html(
                '<div style="text-align: center; color: #dc3545;">'
                '❌<br><small>No Media</small>'
                '</div>'
            )
        
        highlight = media_files.filter(is_highlight=True).first()
        total_size = sum(getattr(m.media, 'size', 0) for m in media_files if m.media)
        
        # Media health check
        broken_count = 0
        for media in media_files:
            info = get_media_info(media.media)
            if not info['exists']:
                broken_count += 1
        
        status_color = '#dc3545' if broken_count > 0 else '#28a745'
        
        return format_html(
            '<div style="text-align: center; min-width: 80px;">'
            '<div style="font-size: 18px; color: {};">{}</div>'
            '<div style="font-size: 10px; line-height: 1.2;">'
            '{} files<br>'
            '{}KB{}<br>'
            '{}'
            '</div>'
            '</div>',
            status_color,
            '🌟' if highlight else '📷',
            count,
            total_size // 1024 if total_size else 0,
            f' | {broken_count}💥' if broken_count else '',
            'Highlight' if highlight else 'Standard'
        )
    
    @admin.display(description='AI Status')
    def ai_comprehensive_status(self, obj):
        """Complete AI analysis status with health indicators"""
        if hasattr(obj, 'ai_judgment') and obj.ai_judgment:
            judgment = obj.ai_judgment
            score = safe_float(judgment.overall_score)
            confidence = safe_float(judgment.confidence) * 100
            
            # Health indicators
            health_indicators = []
            if confidence >= 90:
                health_indicators.append('🎯')
            if judgment.model_version:
                health_indicators.append('🤖')
            if judgment.created_at > timezone.now() - timedelta(hours=24):
                health_indicators.append('🆕')
            
            # Score color coding
            if score >= 80:
                color, badge = '#28a745', 'Excellent'
            elif score >= 70:
                color, badge = '#ffc107', 'Good'
            elif score >= 50:
                color, badge = '#fd7e14', 'Average'
            else:
                color, badge = '#dc3545', 'Poor'
            
            return format_html(
                '<div style="text-align: center; min-width: 100px;">'
                '<div style="font-weight: bold; font-size: 16px; color: {};">{}</div>'
                '<div style="font-size: 10px; line-height: 1.2;">'
                '{}<br>'
                'Conf: {}%<br>'
                '{}'
                '</div>'
                '</div>',
                color,
                fmt_score(score),
                badge,
                fmt_score(confidence, 0),
                ''.join(health_indicators)
            )
        elif obj.ai_score is not None:
            return format_html(
                '<div style="text-align: center; color: #ffc107;">'
                '<div style="font-size: 16px;">📊</div>'
                '<div style="font-size: 12px; font-weight: bold;">{}</div>'
                '<div style="font-size: 10px;">Basic Only</div>'
                '</div>',
                fmt_score(obj.ai_score)
            )
        else:
            return format_html(
                '<div style="text-align: center; color: #dc3545;">'
                '<div style="font-size: 16px;">⚪</div>'
                '<div style="font-size: 10px;">No Analysis</div>'
                '</div>'
            )
    
    @admin.display(description='AI Breakdown')
    def ai_score_breakdown(self, obj):
        """Detailed AI metrics breakdown"""
        if not hasattr(obj, 'ai_judgment') or not obj.ai_judgment:
            return format_html('<small style="color: #999;">N/A</small>')
        
        j = obj.ai_judgment
        va = safe_float(j.visual_appeal)
        ct = safe_float(j.cooking_technique)
        inf = safe_float(j.ingredient_freshness)
        mastery = None
        tips = []
        
        # Create mini bar chart
        def mini_bar(value, color):
            width = max(5, int(value * 0.8))  # Scale to max 80px
            return f'<div style="width:{width}px;height:3px;background:{color};margin:1px 0;"></div>'
        
        tips_html = ''
        if tips:
            safe_tips = ', '.join([str(t)[:40] for t in tips[:3]])
            tips_html = f'<div style="color:#555;margin-top:4px;">💡 {safe_tips}</div>'
        mastery_html = f'<div style="color:#6c757d;">🎓 {mastery}</div>' if mastery else ''

        return format_html(
            '<div style="min-width: 160px; font-size: 10px;">'
            '<div>VA: {} {}</div>'
            '<div>CT: {} {}</div>'
            '<div>IF: {} {}</div>'
            '{}{}'
            '</div>',
            fmt_score(va, 0),
            mini_bar(va, '#007bff'),
            fmt_score(ct, 0),
            mini_bar(ct, '#28a745'),
            fmt_score(inf, 0),
            mini_bar(inf, '#ffc107'),
            mastery_html,
            tips_html
        )
    
    @admin.display(description='Battle Status')
    def couple_battle_status(self, obj):
        """Show position in couple competition"""
        try:
            # Get other entries in the same memory round
            other_entries = obj.memory.entries.exclude(id=obj.id)
            if not other_entries.exists():
                return format_html('<small style="color: #999;">Solo</small>')
            
            # Find competitor
            competitor = other_entries.first()
            my_score = safe_float(obj.ai_score)
            their_score = safe_float(competitor.ai_score)
            
            if my_score > their_score:
                icon, color, status = '🏆', '#28a745', 'Winning'
            elif my_score < their_score:
                icon, color, status = '🥈', '#dc3545', 'Behind'
            else:
                icon, color, status = '🤝', '#ffc107', 'Tied'
            
            return format_html(
                '<div style="text-align: center; color: {};">'
                '<div style="font-size: 16px;">{}</div>'
                '<div style="font-size: 10px;">{}</div>'
                '<div style="font-size: 9px;">vs {}</div>'
                '</div>',
                color, icon, status, competitor.author.username[:6]
            )
        except Exception:
            return format_html('<small style="color: #999;">-</small>')
    
    @admin.display(ordering='created_at', description='Timestamp')
    def timestamp_display(self, obj):
        """Enhanced timestamp with relative time"""
        now = timezone.now()
        created = obj.created_at
        updated = getattr(obj, 'updated_at', created)
        
        # Calculate relative time
        diff = now - created
        if diff.days > 7:
            relative = f"{diff.days}d ago"
        elif diff.days > 0:
            relative = f"{diff.days}d ago"
        elif diff.seconds > 3600:
            relative = f"{diff.seconds // 3600}h ago"
        else:
            relative = f"{diff.seconds // 60}m ago"
        
        return format_html(
            '<div style="font-size: 11px; text-align: center;">'
            '<div style="font-weight: bold;">{}</div>'
            '<div style="color: #666;">{}</div>'
            '<div style="color: #999; font-size: 9px;">{}</div>'
            '</div>',
            created.strftime('%m/%d'),
            created.strftime('%H:%M'),
            relative
        )
    
    @admin.display(description='Actions')
    def admin_action_buttons(self, obj):
        """Quick action buttons for immediate control"""
        buttons = []
        
        # AI Actions
        if obj.media.exists():
            buttons.append(f'<a href="{reverse("admin:memory_ai_retry", args=[obj.pk])}" class="button">🔄 AI</a>')
            buttons.append(f'<a href="{reverse("admin:memory_ai_force", args=[obj.pk])}" class="button">⚡ Force</a>')
        
        if hasattr(obj, 'ai_judgment') and obj.ai_judgment:
            buttons.append(f'<a href="{reverse("admin:memory_ai_clear", args=[obj.pk])}" class="button">🗑️ Clear</a>')
        
        # Content Actions
        buttons.append(f'<a href="{reverse("admin:memory_moderate", args=[obj.pk])}" class="button">🛡️ Mod</a>')
        
        # Media Actions
        if obj.media.exists():
            buttons.append(f'<a href="{reverse("admin:memory_media_manage", args=[obj.pk])}" class="button">📷 Media</a>')
        
        return format_html(
            '<div style="display: flex; flex-direction: column; gap: 2px; min-width: 100px;">{}</div>',
            ''.join(buttons)
        )

    # ═══════════════════════════════════════════════════════════════
    # Enhanced Detail Panels for Maximum Control
    # ═══════════════════════════════════════════════════════════════
    
    @admin.display(description='Comprehensive Media Management')
    def comprehensive_media_panel(self, obj):
        """Complete media management dashboard"""
        media_files = obj.media.all().order_by('-is_highlight', '-created_at')
        
        if not media_files.exists():
            return format_html(
                '<div style="background: #f8d7da; padding: 16px; border-radius: 8px;">'
                '<h4 style="margin: 0 0 12px 0; color: #721c24;">📷 No Media Files</h4>'
                '<p>This entry has no media files. AI analysis requires at least one image.</p>'
                '<a href="{}" class="button">➕ Add Media</a>'
                '</div>',
                reverse('admin:couplememory_memorymedia_add') + f'?entry={obj.id}'
            )
        
        media_html = []
        total_size = 0
        
        for i, media in enumerate(media_files):
            info = get_media_info(media.media)
            total_size += info['size']
            
            status_icon = '🌟' if media.is_highlight else '📷'
            health_icon = '✅' if info['exists'] else '❌'
            
            media_html.append(format_html(
                '<tr style="background: {};">'
                '<td style="text-align: center;">{} {}</td>'
                '<td>{}</td>'
                '<td>{}</td>'
                '<td>{}</td>'
                '<td style="text-align: center;">'
                '<a href="{}" target="_blank" class="button" style="font-size: 10px;">View</a> '
                '<a href="{}" class="button" style="font-size: 10px;">Edit</a>'
                '</td>'
                '</tr>',
                '#fff3cd' if media.is_highlight else '#f8f9fa',
                status_icon,
                health_icon,
                info['name'][:30] + ('...' if len(info['name']) > 30 else ''),
                f"{info['size'] // 1024}KB" if info['size'] else '0KB',
                media.created_at.strftime('%m/%d %H:%M'),
                info['url'] if info['url'] else '#',
                '#'  # Media admin not registered, direct link disabled
            ))
        
        return format_html(
            '<div style="background: #d4edda; padding: 16px; border-radius: 8px;">'
            '<h4 style="margin: 0 0 12px 0; color: #155724;">📷 Media Management Dashboard</h4>'
            '<div style="margin-bottom: 12px; display: flex; gap: 16px; font-size: 12px;">'
            '<span><strong>Total Files:</strong> {}</span>'
            '<span><strong>Total Size:</strong> {}KB</span>'
            '<span><strong>Highlight:</strong> {}</span>'
            '</div>'
            '<table style="width: 100%; border-collapse: collapse; font-size: 11px;">'
            '<thead style="background: #c3e6cb;">'
            '<tr>'
            '<th style="padding: 6px;">Status</th>'
            '<th style="padding: 6px;">Filename</th>'
            '<th style="padding: 6px;">Size</th>'
            '<th style="padding: 6px;">Created</th>'
            '<th style="padding: 6px;">Actions</th>'
            '</tr>'
            '</thead>'
            '<tbody>{}</tbody>'
            '</table>'
            '<div style="margin-top: 12px; display: flex; gap: 8px;">'
            '<a href="{}" class="button">➕ Add Media</a>'
            '<a href="{}" class="button">🌟 Set Highlight</a>'
            '<a href="{}" class="button">🔄 Refresh Cache</a>'
            '</div>'
            '</div>',
            media_files.count(),
            total_size // 1024,
            'Yes' if media_files.filter(is_highlight=True).exists() else 'No',
            ''.join(media_html),
            reverse('admin:couplememory_memorymedia_add') + f'?entry={obj.id}',
            reverse('admin:memory_highlight_manager', args=[obj.pk]),
            reverse('admin:memory_media_refresh', args=[obj.pk])
        )

    @admin.display(description='AI Analysis Dashboard')
    def ai_analysis_dashboard(self, obj):
        """Complete AI analysis dashboard with all metrics"""
        if not hasattr(obj, 'ai_judgment') or not obj.ai_judgment:
            return format_html(
                '<div style="background: #f8d7da; padding: 16px; border-radius: 8px;">'
                '<h4 style="margin: 0 0 12px 0; color: #721c24;">🤖 No AI Analysis Available</h4>'
                '<p>This entry has not been analyzed by AI yet.</p>'
                '<div style="margin-top: 12px;">'
                '<a href="{}" class="button">🔄 Request Analysis</a>'
                '</div>'
                '</div>',
                reverse('admin:memory_ai_retry', args=[obj.pk])
            )
        
        judgment = obj.ai_judgment
        mastery = None
        tips = []
        confidence_color = '#28a745' if judgment.confidence >= 0.9 else '#ffc107' if judgment.confidence >= 0.7 else '#dc3545'
        
        return format_html(
            '<div style="background: #d1ecf1; padding: 16px; border-radius: 8px;">'
            '<h4 style="margin: 0 0 12px 0; color: #0c5460;">🤖 AI Analysis Dashboard</h4>'
            '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">'
            '<div>'
            '<h5 style="margin: 0 0 8px 0;">Score Breakdown</h5>'
            '<table style="font-size: 12px; width: 100%;">'
            '<tr><td>Overall Score:</td><td><strong>{}</strong></td></tr>'
            '<tr><td>Visual Appeal:</td><td><strong>{}</strong></td></tr>'
            '<tr><td>Cooking Technique:</td><td><strong>{}</strong></td></tr>'
            '<tr><td>Ingredient Freshness:</td><td><strong>{}</strong></td></tr>'
            '</table>'
            '</div>'
            '<div>'
            '<h5 style="margin: 0 0 8px 0;">Analysis Quality</h5>'
            '<table style="font-size: 12px; width: 100%;">'
            '<tr><td>Confidence:</td><td><strong style="color: {};">{}%</strong></td></tr>'
            '<tr><td>Model Version:</td><td>{}</td></tr>'
            '<tr><td>Analysis Date:</td><td>{}</td></tr>'
            '</table>'
            '</div>'
            '</div>'
            '<div style="margin-bottom: 12px;">'
            '<h5 style="margin: 0 0 8px 0;">AI Commentary</h5>'
            '<div style="background: #fff; padding: 8px; border-radius: 4px; font-size: 12px;">'
            '{}'
            '</div>'
            '</div>'
            '<div style="display: flex; gap: 8px;">'
            '<a href="{}" class="button">🔄 Re-analyze</a>'
            '<a href="{}" class="button">🗑️ Clear Data</a>'
            '<a href="{}" class="button">📊 Debug</a>'
            '</div>'
            '</div>',
            fmt_score(judgment.overall_score),
            fmt_score(judgment.visual_appeal),
            fmt_score(judgment.cooking_technique),
            fmt_score(judgment.ingredient_freshness),
            confidence_color,
            fmt_score(judgment.confidence * 100, 0),
            judgment.model_version or 'Unknown',
            judgment.created_at.strftime('%Y-%m-%d %H:%M'),
            judgment.ai_comment or 'No comment available',
            reverse('admin:memory_ai_retry', args=[obj.pk]),
            reverse('admin:memory_ai_clear', args=[obj.pk]),
            reverse('admin:memory_ai_debug', args=[obj.pk])
        )

    @admin.display(description='User & Relationship Management')
    def user_relationship_panel(self, obj):
        """User and couple relationship management panel"""
        user = obj.author
        couple = obj.memory.couple
        # Determine partner from Couple.members (M2M), handle 1-member couples safely
        members = list(couple.members.all())
        partner = None
        if len(members) == 2:
            partner = members[0] if members[1].pk == user.pk else members[1]
        
        # Calculate user stats
        user_entries = MemoryEntry.objects.filter(author=user).count()
        user_avg_score = MemoryEntry.objects.filter(
            author=user, ai_score__isnull=False
        ).aggregate(avg=Avg('ai_score'))['avg'] or 0
        
        partner_entries = MemoryEntry.objects.filter(author=partner).count() if partner else 0
        partner_avg_score = (
            MemoryEntry.objects.filter(author=partner, ai_score__isnull=False)
            .aggregate(avg=Avg('ai_score'))['avg'] or 0
        ) if partner else 0
        
        return format_html(
            '<div style="background: #fff3cd; padding: 16px; border-radius: 8px;">'
            '<h4 style="margin: 0 0 12px 0; color: #856404;">👥 Relationship Management</h4>'
            '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">'
            '<div>'
            '<h5 style="margin: 0 0 8px 0;">Current User: {}</h5>'
            '<table style="font-size: 12px; width: 100%;">'
            '<tr><td>Status:</td><td>{}</td></tr>'
            '<tr><td>Total Entries:</td><td>{}</td></tr>'
            '<tr><td>Average Score:</td><td>{}</td></tr>'
            '<tr><td>Email:</td><td>{}</td></tr>'
            '<tr><td>Joined:</td><td>{}</td></tr>'
            '</table>'
            '</div>'
            '<div>'
            '<h5 style="margin: 0 0 8px 0;">Partner: {}</h5>'
            '<table style="font-size: 12px; width: 100%;">'
            '<tr><td>Status:</td><td>{}</td></tr>'
            '<tr><td>Total Entries:</td><td>{}</td></tr>'
            '<tr><td>Average Score:</td><td>{}</td></tr>'
            '<tr><td>Email:</td><td>{}</td></tr>'
            '<tr><td>Joined:</td><td>{}</td></tr>'
            '</table>'
            '</div>'
            '</div>'
            '<div style="margin-top: 12px; display: flex; gap: 8px;">'
            '<a href="{}" class="button">👤 Edit User</a>'
            '<a href="{}" class="button">💑 Manage Couple</a>'
            '<a href="{}" class="button">📊 View Stats</a>'
            '</div>'
            '</div>',
            user.username,
            '✅ Active' if user.is_active else '❌ Inactive',
            user_entries,
            fmt_score(user_avg_score),
            user.email or 'Not provided',
            user.date_joined.strftime('%Y-%m-%d'),
            (partner.username if partner else '—'),
            ('✅ Active' if (partner and partner.is_active) else '❌ Missing'),
            partner_entries,
            fmt_score(partner_avg_score),
            (partner.email if partner and partner.email else 'Not provided'),
            (partner.date_joined.strftime('%Y-%m-%d') if partner else '—'),
            reverse('admin:users_customuser_change', args=[user.pk]),
            reverse('admin:users_couple_change', args=[couple.pk]),
            '#'  # TODO: Implement stats view
        )

    @admin.display(description='Battle & Competition Analysis')
    def battle_comparison_panel(self, obj):
        """Battle and competition analysis panel"""
        memory = obj.memory
        all_entries = memory.entries.all().order_by('-ai_score')
        
        if all_entries.count() < 2:
            return format_html(
                '<div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">'
                '<h4 style="margin: 0 0 12px 0; color: #6c757d;">⚔️ No Battle Available</h4>'
                '<p>This memory only has one entry. Battle mode requires both partners to contribute.</p>'
                '</div>'
            )
        
        winner = all_entries.first()
        loser = all_entries.last()
        score_diff = safe_float(winner.ai_score) - safe_float(loser.ai_score)
        
        return format_html(
            '<div style="background: #f8d7da; padding: 16px; border-radius: 8px;">'
            '<h4 style="margin: 0 0 12px 0; color: #721c24;">⚔️ Battle Analysis</h4>'
            '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">'
            '<div style="background: #d4edda; padding: 12px; border-radius: 4px;">'
            '<h5 style="margin: 0 0 8px 0; color: #155724;">🏆 Winner: {}</h5>'
            '<table style="font-size: 12px; width: 100%;">'
            '<tr><td>Score:</td><td><strong>{}</strong></td></tr>'
            '<tr><td>Media Files:</td><td>{}</td></tr>'
            '<tr><td>Content Length:</td><td>{} words</td></tr>'
            '</table>'
            '</div>'
            '<div style="background: #f8d7da; padding: 12px; border-radius: 4px;">'
            '<h5 style="margin: 0 0 8px 0; color: #721c24;">🥈 Runner-up: {}</h5>'
            '<table style="font-size: 12px; width: 100%;">'
            '<tr><td>Score:</td><td><strong>{}</strong></td></tr>'
            '<tr><td>Media Files:</td><td>{}</td></tr>'
            '<tr><td>Content Length:</td><td>{} words</td></tr>'
            '</table>'
            '</div>'
            '</div>'
            '<div style="text-align: center; margin-bottom: 12px;">'
            '<div style="font-size: 18px; font-weight: bold; color: #007bff;">'
            'Victory Margin: {}'
            '</div>'
            '</div>'
            '<div style="display: flex; gap: 8px; justify-content: center;">'
            '<a href="#" class="button">🏆 Victory Details</a>'
            '<a href="#" class="button">📊 Compare Entries</a>'
            '<a href="#" class="button">🔄 Re-battle</a>'
            '</div>'
            '</div>',
            winner.author.username,
            fmt_score(winner.ai_score),
            winner.media.count(),
            len(winner.content.split()),
            loser.author.username,
            fmt_score(loser.ai_score),
            loser.media.count(),
            len(loser.content.split()),
            fmt_score(score_diff, 1)
        )

    @admin.display(description='System Diagnostics')
    def system_diagnostics_panel(self, obj):
        """System diagnostics and health monitoring panel"""
        # Gather diagnostic information
        media_files = obj.media.all()
        total_media_size = sum(getattr(m.media, 'size', 0) for m in media_files if m.media)
        broken_media = sum(1 for m in media_files if not get_media_info(m.media)['exists'])
        
        # Content analysis
        content_analysis = {
            'word_count': len(obj.content.split()),
            'char_count': len(obj.content),
            'has_special_chars': any(ord(c) > 127 for c in obj.content),
            'estimated_read_time': len(obj.content.split()) / 200  # 200 wpm average
        }
        
        # System health indicators
        health_score = 100
        issues = []
        
        if broken_media > 0:
            health_score -= 30
            issues.append(f'{broken_media} broken media files')
        
        if content_analysis['word_count'] < 5:
            health_score -= 20
            issues.append('Content too short')
        
        if not media_files.exists():
            health_score -= 25
            issues.append('No media files')
        
        if not hasattr(obj, 'ai_judgment') or not obj.ai_judgment:
            health_score -= 15
            issues.append('No AI analysis')
        
        health_color = '#28a745' if health_score >= 80 else '#ffc107' if health_score >= 60 else '#dc3545'
        
        return format_html(
            '<div style="background: #e2e3e5; padding: 16px; border-radius: 8px;">'
            '<h4 style="margin: 0 0 12px 0; color: #383d41;">🔧 System Diagnostics</h4>'
            '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">'
            '<div>'
            '<h5 style="margin: 0 0 8px 0;">Content Analysis</h5>'
            '<table style="font-size: 12px; width: 100%;">'
            '<tr><td>Word Count:</td><td>{}</td></tr>'
            '<tr><td>Character Count:</td><td>{}</td></tr>'
            '<tr><td>Special Characters:</td><td>{}</td></tr>'
            '<tr><td>Read Time:</td><td>{:.1f} min</td></tr>'
            '</table>'
            '</div>'
            '<div>'
            '<h5 style="margin: 0 0 8px 0;">Media Analysis</h5>'
            '<table style="font-size: 12px; width: 100%;">'
            '<tr><td>Total Files:</td><td>{}</td></tr>'
            '<tr><td>Total Size:</td><td>{}KB</td></tr>'
            '<tr><td>Broken Files:</td><td style="color: {};">{}</td></tr>'
            '<tr><td>Has Highlight:</td><td>{}</td></tr>'
            '</table>'
            '</div>'
            '</div>'
            '<div style="margin-bottom: 12px; text-align: center;">'
            '<div style="font-size: 16px; font-weight: bold; color: {};">'
            'Health Score: {}%'
            '</div>'
            '{}'
            '</div>'
            '<div style="display: flex; gap: 8px; justify-content: center;">'
            '<a href="#" class="button">🔍 Full Diagnostic</a>'
            '<a href="#" class="button">🛠️ Auto-Fix Issues</a>'
            '<a href="#" class="button">📋 Export Report</a>'
            '</div>'
            '</div>',
            content_analysis['word_count'],
            content_analysis['char_count'],
            'Yes' if content_analysis['has_special_chars'] else 'No',
            content_analysis['estimated_read_time'],
            media_files.count(),
            total_media_size // 1024,
            '#dc3545' if broken_media > 0 else '#28a745',
            broken_media,
            'Yes' if media_files.filter(is_highlight=True).exists() else 'No',
            health_color,
            health_score,
            f'<div style="color: #dc3545; font-size: 12px; margin-top: 4px;">Issues: {", ".join(issues)}</div>' if issues else ''
        )

    # ═══════════════════════════════════════════════════════════════
    # Custom URLs for Advanced Management
    # ═══════════════════════════════════════════════════════════════
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # AI Management URLs
            path('<int:entry_id>/ai/retry/', self.admin_site.admin_view(self.ai_retry_view), name='memory_ai_retry'),
            path('<int:entry_id>/ai/force/', self.admin_site.admin_view(self.ai_force_view), name='memory_ai_force'),
            path('<int:entry_id>/ai/clear/', self.admin_site.admin_view(self.ai_clear_view), name='memory_ai_clear'),
            path('<int:entry_id>/ai/debug/', self.admin_site.admin_view(self.ai_debug_view), name='memory_ai_debug'),
            
            # Content Management URLs
            path('<int:entry_id>/moderate/', self.admin_site.admin_view(self.moderate_view), name='memory_moderate'),
            path('<int:entry_id>/promote/', self.admin_site.admin_view(self.promote_view), name='memory_promote'),
            
            # Media Management URLs
            path('<int:entry_id>/media/manage/', self.admin_site.admin_view(self.media_manage_view), name='memory_media_manage'),
            path('<int:entry_id>/media/highlight/', self.admin_site.admin_view(self.highlight_manager_view), name='memory_highlight_manager'),
            path('<int:entry_id>/media/refresh/', self.admin_site.admin_view(self.media_refresh_view), name='memory_media_refresh'),
            
            # Analytics & Reporting URLs
            path('analytics/export/', self.admin_site.admin_view(self.analytics_export_view), name='memory_analytics_export'),
            path('analytics/dashboard/', self.admin_site.admin_view(self.analytics_dashboard_view), name='memory_analytics_dashboard'),
            
            # Emergency Management URLs
            path('emergency/reset/', self.admin_site.admin_view(self.emergency_reset_view), name='memory_emergency_reset'),
            path('emergency/backup/', self.admin_site.admin_view(self.emergency_backup_view), name='memory_emergency_backup'),
        ]
        return custom_urls + urls

    # AI Management Views
    def ai_retry_view(self, request, entry_id):
        """Enhanced AI retry with options"""
        entry = get_object_or_404(MemoryEntry, pk=entry_id)
        
        if request.method == 'POST':
            try:
                # Clear existing AI data
                if hasattr(entry, 'ai_judgment') and entry.ai_judgment:
                    entry.ai_judgment.delete()
                entry.ai_score = None
                entry.save(update_fields=['ai_score'])
                
                # Trigger new analysis
                from cookai.scoring import ScoringService
                ScoringService.score_memory_entry(entry.id)
                
                messages.success(request, f'AI analysis queued for Entry #{entry.id}')
                return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))
            except Exception as e:
                messages.error(request, f'AI retry failed: {str(e)}')
                return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))
        
        # Render confirmation page
        context = {
            'title': f'Retry AI Analysis - Entry #{entry.id}',
            'entry': entry,
            'media_count': entry.media.count(),
            'has_existing_analysis': hasattr(entry, 'ai_judgment') and entry.ai_judgment,
            'opts': self.model._meta,
        }
        return render(request, 'admin/memory/ai_retry_confirm.html', context)

    def ai_force_view(self, request, entry_id):
        """Force AI analysis even without media"""
        entry = get_object_or_404(MemoryEntry, pk=entry_id)
        
        if request.method == 'POST':
            try:
                # Queue analysis regardless of media status (may no-op if no media)
                from cookai.scoring import ScoringService
                ScoringService.score_memory_entry(entry.id)
                messages.success(request, f'AI analysis queued for Entry #{entry.id}')
                return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))
            except Exception as e:
                messages.error(request, f'Force analysis failed: {str(e)}')
                return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))
        
        context = {
            'title': f'Force AI Analysis - Entry #{entry.id}',
            'entry': entry,
            'media_count': entry.media.count(),
            'opts': self.model._meta,
        }
        return render(request, 'admin/memory/ai_force_confirm.html', context)

    def ai_clear_view(self, request, entry_id):
        """Clear all AI analysis data"""
        entry = get_object_or_404(MemoryEntry, pk=entry_id)
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    if hasattr(entry, 'ai_judgment') and entry.ai_judgment:
                        entry.ai_judgment.delete()
                    entry.ai_score = None
                    entry.save(update_fields=['ai_score'])
                
                messages.success(request, f'AI data cleared for Entry #{entry.id}')
                return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))
            except Exception as e:
                messages.error(request, f'Clear operation failed: {str(e)}')
                return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))
        
        context = {
            'title': f'Clear AI Data - Entry #{entry.id}',
            'entry': entry,
            'has_judgment': hasattr(entry, 'ai_judgment') and entry.ai_judgment,
            'opts': self.model._meta,
        }
        return render(request, 'admin/memory/ai_clear_confirm.html', context)

    def ai_debug_view(self, request, entry_id):
        """Complete AI analysis debugging dashboard"""
        entry = get_object_or_404(MemoryEntry, pk=entry_id)
        
        # Get latest AI response by calling backend directly
        ai_raw_output = None
        if entry.media.exists():
            try:
                from cookai.backend import OpenAIBackend
                media_url = entry.media.first().media.url
                if media_url.startswith("http://web:"):
                    from django.conf import settings
                    media_url = media_url.replace("http://web:", f"{getattr(settings, 'DEFAULT_HOST', 'http://localhost:911')}:")
                
                ai_raw_output = OpenAIBackend.score_images_detailed([media_url])
            except Exception as e:
                ai_raw_output = {"error": str(e)}
        
        # Gather comprehensive debug information
        debug_info = {
            'entry': entry,
            'media_files': entry.media.all(),
            'ai_judgment': getattr(entry, 'ai_judgment', None),
            'ai_score': entry.ai_score,
            'ai_raw_output': ai_raw_output,
            'system_status': self._get_ai_system_status(),
            'recommendations': self._get_ai_recommendations(entry),
        }
        
        context = {
            'title': f'AI Debug Dashboard - Entry #{entry.id}',
            'debug_info': debug_info,
            'opts': self.model._meta,
        }
        return render(request, 'admin/memory/ai_debug_dashboard.html', context)

    def moderate_view(self, request, entry_id):
        """Content moderation view"""
        entry = get_object_or_404(MemoryEntry, pk=entry_id)
        
        if request.method == 'POST':
            # Process moderation action
            action = request.POST.get('action')
            if action == 'approve':
                messages.success(request, f'Entry #{entry.id} approved.')
            elif action == 'flag':
                messages.warning(request, f'Entry #{entry.id} flagged for review.')
            elif action == 'delete':
                messages.error(request, f'Entry #{entry.id} marked for deletion.')
            return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))
        
        context = {
            'title': f'Moderate Entry #{entry.id}',
            'entry': entry,
            'opts': self.model._meta,
        }
        return render(request, 'admin/memory/moderate_confirm.html', context)

    def promote_view(self, request, entry_id):
        """Promote entry to highlight"""
        entry = get_object_or_404(MemoryEntry, pk=entry_id)
        
        if request.method == 'POST':
            try:
                first_media = entry.media.first()
                if first_media:
                    # Clear other highlights in the same memory
                    MemoryMedia.objects.filter(
                        entry__memory=entry.memory
                    ).update(is_highlight=False)
                    
                    # Set this as highlight
                    first_media.is_highlight = True
                    first_media.save(update_fields=['is_highlight'])
                    
                    messages.success(request, f'Entry #{entry.id} promoted to highlight.')
                else:
                    messages.error(request, 'No media files to promote.')
                return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))
            except Exception as e:
                messages.error(request, f'Promotion failed: {str(e)}')
                return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))
        
        context = {
            'title': f'Promote Entry #{entry.id}',
            'entry': entry,
            'opts': self.model._meta,
        }
        return render(request, 'admin/memory/promote_confirm.html', context)

    def media_manage_view(self, request, entry_id):
        """Media management view"""
        entry = get_object_or_404(MemoryEntry, pk=entry_id)
        
        context = {
            'title': f'Manage Media - Entry #{entry.id}',
            'entry': entry,
            'media_files': entry.media.all(),
            'opts': self.model._meta,
        }
        return render(request, 'admin/memory/media_manage.html', context)

    def highlight_manager_view(self, request, entry_id):
        """Highlight manager view"""
        entry = get_object_or_404(MemoryEntry, pk=entry_id)
        
        if request.method == 'POST':
            media_id = request.POST.get('highlight_media_id')
            if media_id:
                try:
                    # Clear existing highlights
                    MemoryMedia.objects.filter(
                        entry__memory=entry.memory
                    ).update(is_highlight=False)
                    
                    # Set new highlight
                    media = get_object_or_404(MemoryMedia, id=media_id, entry=entry)
                    media.is_highlight = True
                    media.save(update_fields=['is_highlight'])
                    
                    messages.success(request, 'Highlight updated successfully.')
                except Exception as e:
                    messages.error(request, f'Failed to update highlight: {str(e)}')
            
            return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_change', args=[entry.id]))
        
        context = {
            'title': f'Highlight Manager - Entry #{entry.id}',
            'entry': entry,
            'media_files': entry.media.all(),
            'opts': self.model._meta,
        }
        return render(request, 'admin/memory/highlight_manager.html', context)

    def media_refresh_view(self, request, entry_id):
        """Refresh media cache view"""
        entry = get_object_or_404(MemoryEntry, pk=entry_id)
        
        try:
            # Refresh media information
            refreshed_count = 0
            for media in entry.media.all():
                # Force refresh media info
                if hasattr(media.media, 'url'):
                    refreshed_count += 1
            
            messages.success(request, f'Refreshed {refreshed_count} media files.')
        except Exception as e:
            messages.error(request, f'Refresh failed: {str(e)}')
        
        return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_change', args=[entry.id]))

    def analytics_export_view(self, request):
        """Export analytics view"""
        # TODO: Implement analytics export
        messages.info(request, 'Analytics export feature coming soon.')
        return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))

    def analytics_dashboard_view(self, request):
        """Analytics dashboard view"""
        # TODO: Implement analytics dashboard
        messages.info(request, 'Analytics dashboard feature coming soon.')
        return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))

    def emergency_reset_view(self, request):
        """Emergency reset view"""
        if not request.user.is_superuser:
            messages.error(request, 'Emergency reset requires superuser privileges.')
            return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))
        
        # TODO: Implement emergency reset
        messages.warning(request, 'Emergency reset feature requires additional confirmation.')
        return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))

    def emergency_backup_view(self, request):
        """Emergency backup view"""
        # TODO: Implement emergency backup
        messages.info(request, 'Emergency backup feature coming soon.')
        return HttpResponseRedirect(reverse('admin:couplememory_memoryentry_changelist'))

    def _get_ai_system_status(self):
        """Get current AI system health status"""
        try:
            from cookai.backend import OpenAIBackend
            backend = OpenAIBackend()
            return {
                'backend_available': True,
                'model_version': getattr(backend, 'model_version', 'unknown'),
                'last_successful_analysis': timezone.now(),  # TODO: Track this
                'queue_size': 0,  # TODO: Implement queue monitoring
            }
        except Exception as e:
            return {
                'backend_available': False,
                'error': str(e),
            }

    def _get_ai_recommendations(self, entry):
        """Generate recommendations for improving AI analysis"""
        recommendations = []
        
        # Check media status
        media_count = entry.media.count()
        if media_count == 0:
            recommendations.append({
                'type': 'error',
                'message': 'Add at least one image for AI analysis',
                'action': 'Add Media'
            })
        elif media_count == 1:
            recommendations.append({
                'type': 'warning',
                'message': 'Consider adding more images for better analysis',
                'action': 'Add More Media'
            })
        
        # Check content quality
        if len(entry.content) < 20:
            recommendations.append({
                'type': 'warning',
                'message': 'Short content may result in lower AI scores',
                'action': 'Expand Content'
            })
        
        # Check existing analysis
        if hasattr(entry, 'ai_judgment') and entry.ai_judgment:
            judgment = entry.ai_judgment
            if safe_float(judgment.confidence) < 0.7:
                recommendations.append({
                    'type': 'info',
                    'message': 'Low confidence score - consider retry',
                    'action': 'Retry Analysis'
                })
        
        return recommendations

    # ═══════════════════════════════════════════════════════════════
    # Admin Actions for Mass Operations
    # ═══════════════════════════════════════════════════════════════

    @admin.action(description='🤖 Run AI analysis on selected entries')
    def mass_ai_analysis(self, request, queryset):
        """Mass AI analysis with progress tracking"""
        entries_with_media = queryset.filter(media__isnull=False).distinct()
        count = entries_with_media.count()
        
        if count == 0:
            messages.warning(request, 'No entries with media files selected.')
            return
        
        try:
            from cookai.scoring import ScoringService
            
            success_count = 0
            for entry in entries_with_media:
                try:
                    ScoringService.score_memory_entry(entry.id)
                    success_count += 1
                except Exception as e:
                    logger.error(f'Mass AI analysis failed for entry {entry.id}: {e}')
            
            messages.success(request, f'Queued AI analysis for {success_count}/{count} entries.')
        except Exception as e:
            messages.error(request, f'Mass AI analysis failed: {str(e)}')

    @admin.action(description='⚡ Force AI regeneration (ignore cache)')
    def force_ai_regeneration(self, request, queryset):
        """Force complete AI regeneration"""
        count = queryset.count()
        
        try:
            with transaction.atomic():
                # Clear existing AI data
                for entry in queryset:
                    if hasattr(entry, 'ai_judgment') and entry.ai_judgment:
                        entry.ai_judgment.delete()
                    entry.ai_score = None
                    entry.save(update_fields=['ai_score'])
                
                # Queue new analysis
                from cookai.scoring import ScoringService
                for entry in queryset.filter(media__isnull=False).distinct():
                    ScoringService.score_memory_entry(entry.id)
            
            messages.success(request, f'Forced regeneration for {count} entries.')
        except Exception as e:
            messages.error(request, f'Force regeneration failed: {str(e)}')

    @admin.action(description='🗑️ Clear AI data from selected entries')
    def clear_ai_data(self, request, queryset):
        """Mass clear AI analysis data"""
        count = 0
        
        try:
            with transaction.atomic():
                for entry in queryset:
                    if hasattr(entry, 'ai_judgment') and entry.ai_judgment:
                        entry.ai_judgment.delete()
                        count += 1
                    if entry.ai_score is not None:
                        entry.ai_score = None
                        entry.save(update_fields=['ai_score'])
            
            messages.success(request, f'Cleared AI data from {count} entries.')
        except Exception as e:
            messages.error(request, f'Clear operation failed: {str(e)}')

    @admin.action(description='📊 Export analytics report')
    def export_analytics_report(self, request, queryset):
        """Export comprehensive analytics for selected entries"""
        try:
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="memory_analytics_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Entry_ID', 'Author', 'Couple_Code', 'Content_Length', 'Word_Count',
                'Media_Count', 'Created_Date', 'AI_Score', 'Overall_Score',
                'Visual_Appeal', 'Cooking_Technique', 'Ingredient_Freshness',
                'Confidence', 'Model_Version', 'Has_Highlight'
            ])
            
            for entry in queryset:
                judgment = getattr(entry, 'ai_judgment', None)
                
                writer.writerow([
                    entry.id,
                    entry.author.username,
                    entry.memory.couple.code,
                    len(entry.content),
                    len(entry.content.split()),
                    entry.media.count(),
                    entry.created_at.strftime('%Y-%m-%d %H:%M'),
                    safe_float(entry.ai_score),
                    safe_float(judgment.overall_score) if judgment else '',
                    safe_float(judgment.visual_appeal) if judgment else '',
                    safe_float(judgment.cooking_technique) if judgment else '',
                    safe_float(judgment.ingredient_freshness) if judgment else '',
                    safe_float(judgment.confidence) if judgment else '',
                    judgment.model_version if judgment else '',
                    entry.media.filter(is_highlight=True).exists()
                ])
            
            return response
        except Exception as e:
            messages.error(request, f'Export failed: {str(e)}')


# ═══════════════════════════════════════════════════════════════
# Additional Admin Models for Complete Control
# ═══════════════════════════════════════════════════════════════

@admin.register(AIJudgment)
class IndustrialAIJudgmentAdmin(admin.ModelAdmin):
    """Industrial AI Judgment Admin - Deep Analysis & Model Performance"""
    
    list_display = [
        'judgment_id_display',
        'entry_link_display', 
        'scoring_history_count',
        'model_performance_display',
        'score_breakdown_detailed',
        'analysis_timestamp'
    ]
    
    list_filter = [
        'created_at',
        'model_version',
        'confidence',
        'overall_score',
    ]
    
    search_fields = ['entry__content', 'ai_comment', 'model_version']
    
    # 添加详细字段显示
    readonly_fields = [
        'id',
        'entry',
        'created_at',
        'updated_at',
        'user_input_images_display',
        'ai_prompt_display',
        'ai_response_display',
        'score_details_display'
    ]
    
    fieldsets = (
        ('📊 Basic Information', {
            'fields': ('id', 'entry', 'model_version', 'created_at', 'updated_at')
        }),
        ('🖼️ User Input Images', {
            'fields': ('user_input_images_display',),
            'description': '用户上传的原始图片'
        }),
        ('🤖 AI Prompt (System + User)', {
            'fields': ('ai_prompt_display',),
            'description': '完整的 AI Prompt（System 指令 + User 输入）',
            'classes': ('collapse',)
        }),
        ('💬 AI Response', {
            'fields': ('ai_response_display',),
            'description': 'AI 的完整响应',
            'classes': ('collapse',)
        }),
        ('📈 Score Details', {
            'fields': ('score_details_display',)
        }),
        ('📝 Comments & Summary', {
            'fields': ('individual_comment', 'individual_summary', 'battle_comment', 'battle_summary')
        }),
    )
    
    @admin.display(ordering='id', description='Judgment ID')
    def judgment_id_display(self, obj):
        return format_html(
            '<div style="text-align: center;">'
            '<strong style="color: #28a745;">J#{}</strong><br>'
            '<small>E{}</small>'
            '</div>',
            obj.id, obj.entry.id
        )

    @admin.display(description='Entry Link')
    def entry_link_display(self, obj):
        return format_html(
            '<a href="{}" target="_blank">Entry #{}</a><br>'
            '<small>{}</small>',
            reverse('admin:couplememory_memoryentry_change', args=[obj.entry.id]),
            obj.entry.id,
            obj.entry.author.username
        )

    @admin.display(description='📊 Scoring History')
    def scoring_history_count(self, obj):
        """显示该 Entry 被评分的历史次数"""
        from cookai.models import AIScoreLog
        
        # count every AIScoreLog for this entry
        count = AIScoreLog.objects.filter(memory_entry_id=obj.entry.id).count()
        
        # 获取第一次和最后一次评分时间
        first_log = AIScoreLog.objects.filter(memory_entry_id=obj.entry.id).order_by('created_at').first()
        latest_log = AIScoreLog.objects.filter(memory_entry_id=obj.entry.id).order_by('-created_at').first()
        
        if count == 0:
            return format_html('<span style="color: #6c757d;">No logs</span>')
        
        # 颜色：多次测试用蓝色，单次用灰色
        color = '#007bff' if count > 1 else '#6c757d'
        
        first_time = first_log.created_at.strftime('%m-%d %H:%M') if first_log else 'N/A'
        latest_time = latest_log.created_at.strftime('%m-%d %H:%M') if latest_log else 'N/A'
        
        return format_html(
            '<div style="text-align: center;">'
            '<strong style="color: {}; font-size: 16px;">{}</strong> times<br>'
            '<small style="color: #6c757d;">First: {}<br>Latest: {}</small>'
            '</div>',
            color,
            count,
            first_time,
            latest_time
        )

    @admin.display(description='Model Performance')
    def model_performance_display(self, obj):
        color = '#28a745' if obj.confidence >= 0.9 else '#ffc107' if obj.confidence >= 0.7 else '#dc3545'
        return format_html(
            '<div style="color: {};">Conf: {}%</div>'
            '<small>{}</small>',
            color,
            fmt_score(obj.confidence * 100, 0),
            obj.model_version[:10] if obj.model_version else 'Unknown'
        )

    @admin.display(description='Score Breakdown')
    def score_breakdown_detailed(self, obj):
        return format_html(
            '<div style="font-size: 11px;">'
            'Overall: {}<br>'
            'Visual: {}<br>'
            'Technique: {}<br>'
            'Freshness: {}'
            '</div>',
            fmt_score(obj.overall_score),
            fmt_score(obj.visual_appeal),
            fmt_score(obj.cooking_technique),
            fmt_score(obj.ingredient_freshness)
        )

    @admin.display(ordering='created_at', description='Analysis Time')
    def analysis_timestamp(self, obj):
        return format_html(
            '<div style="font-size: 11px;">'
            '{}<br>'
            '<small style="color: #666;">{}</small>'
            '</div>',
            obj.created_at.strftime('%m/%d %H:%M'),
            obj.created_at.strftime('%Y')
        )
    
    @admin.display(description='User Input Images')
    def user_input_images_display(self, obj):
        """显示用户上传的所有图片"""
        if not obj or not obj.entry:
            return format_html('<p>No entry found</p>')
        
        media_items = obj.entry.media.all()
        if not media_items.exists():
            return format_html('<p style="color: #dc3545;">No images uploaded</p>')
        
        html_parts = []
        html_parts.append('<div style="margin: 10px 0;">')
        
        for idx, media in enumerate(media_items, 1):
            try:
                image_url = media.media.url if media.media else None
                if image_url:
                    html_parts.append(f'''
                        <div style="margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                            <p style="margin: 5px 0;"><strong>Image #{idx}</strong> 
                               {" 🌟 <em>(Highlight)</em>" if media.is_highlight else ""}
                            </p>
                            <img src="{image_url}" style="max-width: 600px; max-height: 400px; border: 2px solid #ddd; border-radius: 5px;" />
                            <p style="margin: 5px 0; font-size: 11px; color: #666;">
                                File: {media.media.name}<br>
                                URL: <a href="{image_url}" target="_blank">{image_url}</a>
                            </p>
                        </div>
                    ''')
                else:
                    html_parts.append(f'<p>Image #{idx}: <em>No file</em></p>')
            except Exception as e:
                html_parts.append(f'<p style="color: #dc3545;">Image #{idx}: Error loading ({e})</p>')
        
        html_parts.append('</div>')
        return format_html(''.join(html_parts))
    
    @admin.display(description='AI Prompt (System + User)')
    def ai_prompt_display(self, obj):
        """show the full prompt, read from AIScoreLog"""
        if not obj or not obj.entry:
            return format_html('<p>No entry found</p>')
        
        try:
            from cookai.models import AIScoreLog
            
            # ✅ find the score_log through the ai_judgment relation
            score_logs = AIScoreLog.objects.filter(ai_judgment=obj).order_by('-created_at')
            
            if not score_logs.exists():
                # if ai_judgment yields nothing, try memory_entry
                score_logs = AIScoreLog.objects.filter(
                    memory_entry=obj.entry
                ).order_by('-created_at')
            
            if score_logs.exists():
                score_log = score_logs.first()
                
                # 🎯 option 1: final_input_string, the most complete
                final_input = ''
                if score_log.api_request_params:
                    final_input = score_log.api_request_params.get('final_input_string', '')
                
                if final_input:
                    return format_html('''
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                            <h4 style="color: #007bff; margin-top: 0;">🚀 最终发送给 AI 的完整字符串</h4>
                            <pre style="background: white; padding: 10px; border: 1px solid #ddd; border-radius: 3px; 
                                 max-height: 600px; overflow-y: auto; font-size: 12px; line-height: 1.5; white-space: pre-wrap;">{}</pre>
                            
                            <div style="margin-top: 15px; padding: 10px; background: #e7f3ff; border-left: 4px solid #007bff;">
                                <p style="margin: 0; font-size: 12px;">
                                    <strong>📊 详情:</strong><br>
                                    • Log ID: <a href="/admin/cookai/aiscorelog/{}/change/" target="_blank">{}</a><br>
                                    • 创建时间: {}<br>
                                    • 状态: {} | 延迟: {}秒<br>
                                    • Token数: {} | 模型: {}
                                </p>
                            </div>
                        </div>
                    ''', 
                        final_input[:15000],  # 显示前15000字符
                        score_log.id, score_log.id,
                        score_log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        score_log.get_status_display(),
                        f"{score_log.latency:.1f}",
                        score_log.token_count,
                        score_log.model_name
                    )
                
                # 🎯 option 2: show the system and user prompts separately
                system_prompt = ''
                user_prompt = score_log.full_prompt or ''
                
                if score_log.api_request_params:
                    system_prompt = score_log.api_request_params.get('system_message', '')
                
                if system_prompt or user_prompt:
                    return format_html('''
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                            <h4 style="color: #007bff; margin-top: 0;">📋 System Prompt (AI 基础指令)</h4>
                            <pre style="background: white; padding: 10px; border: 1px solid #ddd; border-radius: 3px; 
                                 max-height: 300px; overflow-y: auto; font-size: 11px; line-height: 1.4; white-space: pre-wrap;">{}</pre>
                            
                            <h4 style="color: #28a745; margin-top: 20px;">📝 User Prompt (菜品信息 + 图片)</h4>
                            <pre style="background: white; padding: 10px; border: 1px solid #ddd; border-radius: 3px; 
                                 max-height: 400px; overflow-y: auto; font-size: 11px; line-height: 1.4; white-space: pre-wrap;">{}</pre>
                            
                            <div style="margin-top: 15px; padding: 10px; background: #e7f3ff; border-left: 4px solid #007bff;">
                                <p style="margin: 0; font-size: 11px;">
                                    <strong>Log ID:</strong> <a href="/admin/cookai/aiscorelog/{}/change/" target="_blank">{}</a> | 
                                    <strong>时间:</strong> {} | <strong>状态:</strong> {}
                                </p>
                            </div>
                        </div>
                    ''', 
                        system_prompt[:8000], 
                        user_prompt[:8000],
                        score_log.id, score_log.id,
                        score_log.created_at.strftime('%Y-%m-%d %H:%M:%S'), 
                        score_log.get_status_display()
                    )
            
            return format_html('''
                <div style="padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px;">
                    <p style="margin: 0; color: #856404;">
                        ⚠️ 未找到 AIScoreLog 数据<br>
                        <small>Entry ID: {} | AIJudgment ID: {}</small>
                    </p>
                </div>
            ''', obj.entry.id, obj.id)
            
        except Exception as e:
            logger.error(f"Error in ai_prompt_display: {e}")
            import traceback
            traceback.print_exc()
            return format_html('''
                <div style="padding: 15px; background: #f8d7da; border: 1px solid #dc3545; border-radius: 5px;">
                    <p style="margin: 0; color: #721c24;">
                        ❌ 加载 Prompt 时出错<br>
                        <small>{}</small>
                    </p>
                </div>
            ''', str(e))
    
    @admin.display(description='AI Response')
    def ai_response_display(self, obj):
        """show the full response, read from AIScoreLog"""
        if not obj or not obj.entry:
            return format_html('<p>No entry found</p>')
        
        try:
            from cookai.models import AIScoreLog
            import json
            
            # ✅ 优先通过 ai_judgment 关联查找
            score_logs = AIScoreLog.objects.filter(ai_judgment=obj).order_by('-created_at')
            
            if not score_logs.exists():
                # 备选：通过 memory_entry 查找
                score_logs = AIScoreLog.objects.filter(memory_entry=obj.entry).order_by('-created_at')
            
            if score_logs.exists():
                score_log = score_logs.first()
                
                # ✅ prefer parsed_score, the structured result
                response_data = score_log.parsed_score or score_log.api_response
                
                if response_data:
                    # 美化 JSON 输出
                    formatted_json = json.dumps(response_data, indent=2, ensure_ascii=False)
                    
                    # 提取关键信息并格式化
                    overall_score = response_data.get('overall_score', 'N/A')
                    ai_comment = response_data.get('ai_comment', 'N/A')
                    confidence = response_data.get('confidence', 0)
                    
                    # format the numbers up front rather than f-stringing inside format_html
                    confidence_pct = f"{confidence * 100:.0f}" if confidence else "0"
                    latency_str = f"{score_log.latency:.1f}" if score_log.latency else "0.0"
                    token_count = score_log.token_count or 0
                    
                    return format_html('''
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                            <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                                <div style="flex: 1; padding: 10px; background: white; border-left: 4px solid #28a745; border-radius: 3px;">
                                    <div style="font-size: 11px; color: #666; margin-bottom: 5px;">Overall Score</div>
                                    <div style="font-size: 24px; font-weight: bold; color: #28a745;">{}</div>
                                </div>
                                <div style="flex: 1; padding: 10px; background: white; border-left: 4px solid #17a2b8; border-radius: 3px;">
                                    <div style="font-size: 11px; color: #666; margin-bottom: 5px;">Confidence</div>
                                    <div style="font-size: 24px; font-weight: bold; color: #17a2b8;">{}%</div>
                                </div>
                            </div>
                            
                            <div style="padding: 10px; background: #e7f3ff; border-left: 4px solid #007bff; border-radius: 3px; margin-bottom: 15px;">
                                <div style="font-size: 11px; color: #004085; margin-bottom: 5px;"><strong>💬 AI Comment</strong></div>
                                <div style="font-size: 13px; color: #004085;">{}</div>
                            </div>
                            
                            <h4 style="color: #17a2b8; margin-top: 20px; margin-bottom: 10px;">🤖 完整 JSON 响应</h4>
                            <pre style="background: white; padding: 10px; border: 1px solid #ddd; border-radius: 3px; 
                                 max-height: 400px; overflow-y: auto; font-size: 11px; line-height: 1.4;">{}</pre>
                            
                            <div style="margin-top: 15px; padding: 10px; background: #d1ecf1; border-left: 4px solid #17a2b8;">
                                <p style="margin: 0; font-size: 11px;">
                                    <strong>📊 性能指标:</strong><br>
                                    • Log ID: <a href="/admin/cookai/aiscorelog/{}/change/" target="_blank">{}</a><br>
                                    • 延迟: {}秒 | Token数: {} | 模型: {}<br>
                                    • 状态: {} | 时间: {}
                                </p>
                            </div>
                        </div>
                    ''', 
                        overall_score,
                        confidence_pct,
                        ai_comment,
                        formatted_json,
                        score_log.id, score_log.id,
                        latency_str,
                        token_count,
                        score_log.model_name,
                        score_log.get_status_display(),
                        score_log.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    )
                else:
                    return format_html('''
                        <div style="padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px;">
                            <p style="margin: 0; color: #856404;">
                                ⚠️ 找到 Score Log，但没有响应数据<br>
                                <small>Log ID: {} | Status: {}</small>
                            </p>
                        </div>
                    ''', score_log.id, score_log.get_status_display())
            
            return format_html('''
                <div style="padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px;">
                    <p style="margin: 0; color: #856404;">
                        ⚠️ 未找到 AIScoreLog 响应数据<br>
                        <small>Entry ID: {} | AIJudgment ID: {}</small>
                    </p>
                </div>
            ''', obj.entry.id, obj.id)
            
        except Exception as e:
            logger.error(f"Error in ai_response_display: {e}")
            import traceback
            traceback.print_exc()
            return format_html('''
                <div style="padding: 15px; background: #f8d7da; border: 1px solid #dc3545; border-radius: 5px;">
                    <p style="margin: 0; color: #721c24;">
                        ❌ 加载响应数据时出错<br>
                        <small>{}</small>
                    </p>
                </div>
            ''', str(e))
    
    @admin.display(description='Score Details')
    def score_details_display(self, obj):
        """显示详细的评分信息"""
        return format_html('''
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #e9ecef;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">Dimension</th>
                        <th style="padding: 8px; text-align: right; border: 1px solid #dee2e6;">Score</th>
                        <th style="padding: 8px; text-align: center; border: 1px solid #dee2e6;">Grade</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">🎯 <strong>Overall Score</strong></td>
                        <td style="padding: 8px; text-align: right; border: 1px solid #dee2e6; font-weight: bold;">{}</td>
                        <td style="padding: 8px; text-align: center; border: 1px solid #dee2e6;">{}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">🎨 Visual Appeal</td>
                        <td style="padding: 8px; text-align: right; border: 1px solid #dee2e6;">{}</td>
                        <td style="padding: 8px; text-align: center; border: 1px solid #dee2e6;">{}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">👨‍🍳 Cooking Technique</td>
                        <td style="padding: 8px; text-align: right; border: 1px solid #dee2e6;">{}</td>
                        <td style="padding: 8px; text-align: center; border: 1px solid #dee2e6;">{}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">🥬 Ingredient Freshness</td>
                        <td style="padding: 8px; text-align: right; border: 1px solid #dee2e6;">{}</td>
                        <td style="padding: 8px; text-align: center; border: 1px solid #dee2e6;">{}</td>
                    </tr>
                    <tr style="background: #e9ecef;">
                        <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>🎯 Confidence</strong></td>
                        <td style="padding: 8px; text-align: right; border: 1px solid #dee2e6; font-weight: bold;">{}</td>
                        <td style="padding: 8px; text-align: center; border: 1px solid #dee2e6;">{}</td>
                    </tr>
                </table>
            </div>
        ''', 
            fmt_score(obj.overall_score), self._get_grade(obj.overall_score),
            fmt_score(obj.visual_appeal), self._get_grade(obj.visual_appeal),
            fmt_score(obj.cooking_technique), self._get_grade(obj.cooking_technique),
            fmt_score(obj.ingredient_freshness), self._get_grade(obj.ingredient_freshness),
            fmt_score(obj.confidence * 100, 0) + '%', self._get_confidence_level(obj.confidence)
        )
    
    def _get_grade(self, score):
        """根据分数返回等级"""
        if score is None:
            return '-'
        score = safe_float(score)
        if score >= 90:
            return '🏆 S'
        elif score >= 80:
            return '⭐ A'
        elif score >= 70:
            return '✨ B'
        elif score >= 60:
            return '👍 C'
        elif score >= 50:
            return '📝 D'
        else:
            return '❌ F'
    
    def _get_confidence_level(self, confidence):
        """根据置信度返回等级"""
        if confidence is None:
            return '-'
        conf = safe_float(confidence)
        if conf >= 0.9:
            return '🟢 Very High'
        elif conf >= 0.7:
            return '🟡 High'
        elif conf >= 0.5:
            return '🟠 Medium'
        elif conf >= 0.3:
            return '🔴 Low'
        else:
            return '⚫ Very Low'


@admin.register(CoupleMemory)
class IndustrialCoupleMemoryAdmin(admin.ModelAdmin):
    """Industrial Couple Memory Admin - Battle & Competition Management with AI Integration"""
    
    list_display = [
        'memory_battle_display',
        'couple_info_display',
        'competition_status',
        'entries_overview',
        'battle_winner_display',
        'memory_actions'
    ]
    
    list_filter = ['created_at', 'couple']
    search_fields = ['couple__code', 'couple__members__username']
    actions = ['rescore_all_entries', 'refresh_statistics']
    
    # Add inline for direct entry management
    class MemoryEntryInline(admin.TabularInline):
        model = MemoryEntry
        extra = 0
        readonly_fields = ['created_at', 'ai_score', 'ai_judgment_status']
        fields = ['author', 'content', 'mood', 'recipe', 'ai_score', 'ai_judgment_status', 'created_at']
        
        def ai_judgment_status(self, obj):
            if not obj.pk:
                return '-'
            ai_judgment = getattr(obj, 'ai_judgment', None)
            if ai_judgment:
                return format_html(
                    '<div style="font-size:10px;">'
                    'Score: {} | Conf: {}%<br>'
                    'VA: {} | CT: {} | IF: {}<br>'
                    '<a href="{}" style="font-size:8px;">🔄 Retry</a> '
                    '<a href="{}" style="font-size:8px;">🗑️ Clear</a>'
                    '</div>',
                    fmt_score(ai_judgment.overall_score),
                    fmt_score(ai_judgment.confidence * 100, 0),
                    fmt_score(ai_judgment.visual_appeal, 0),
                    fmt_score(ai_judgment.cooking_technique, 0),
                    fmt_score(ai_judgment.ingredient_freshness, 0),
                    reverse('admin:memory_ai_retry', args=[obj.pk]),
                    reverse('admin:memory_ai_clear', args=[obj.pk])
                )
            else:
                return format_html(
                    '<div style="font-size:10px;color:#dc3545;">'
                    'No AI Analysis<br>'
                    '<a href="{}" style="font-size:8px;">🔄 Analyze</a>'
                    '</div>',
                    reverse('admin:memory_ai_retry', args=[obj.pk])
                )
        ai_judgment_status.short_description = "AI Status"
    
    inlines = [MemoryEntryInline]

    def changelist_view(self, request, extra_context=None):
        rescore_id = request.GET.get('rescore')
        refresh_id = request.GET.get('refresh')
        if rescore_id:
            try:
                from cookai.scoring import ScoringService
                memory = CoupleMemory.objects.get(pk=int(rescore_id))
                total = 0
                for entry in memory.entries.all():
                    if entry.media.exists():
                        ScoringService.score_memory_entry(entry.id)
                        total += 1
                messages.success(request, f'Queued AI rescoring for {total} entries in memory #{memory.id}.')
            except Exception as e:
                messages.error(request, f'Rescore failed: {e}')
            # Redirect to clean URL without params
            return HttpResponseRedirect(reverse('admin:couplememory_couplememory_changelist'))
        if refresh_id:
            try:
                memory = CoupleMemory.objects.get(pk=int(refresh_id))
                memory.recalc_winner()
                memory.refresh_counters()
                messages.success(request, f'Refreshed statistics for memory #{memory.id}.')
            except Exception as e:
                messages.error(request, f'Refresh failed: {e}')
            return HttpResponseRedirect(reverse('admin:couplememory_couplememory_changelist'))
        return super().changelist_view(request, extra_context=extra_context)
    
    @admin.display(description='Battle ID')
    def memory_battle_display(self, obj):
        return format_html(
            '<div style="text-align: center;">'
            '<strong style="color: #007bff;">B#{}</strong><br>'
            '<small>Memory {}</small>'
            '</div>',
            obj.id, obj.id
        )

    @admin.display(description='Couple Info')
    def couple_info_display(self, obj):
        members = list(obj.couple.members.all())
        name_a = members[0].username if len(members) >= 1 else '—'
        name_b = members[1].username if len(members) >= 2 else '—'
        return format_html(
            '<div>'
            '<strong>{}</strong><br>'
            '<small>{} vs {}</small>'
            '</div>',
            obj.couple.code,
            name_a,
            name_b
        )

    @admin.display(description='Competition Status')
    def competition_status(self, obj):
        entries = obj.entries.all()
        total = entries.count()
        
        if total == 0:
            return format_html('<span style="color: #dc3545;">No Entries</span>')
        elif total == 1:
            return format_html('<span style="color: #ffc107;">Solo Entry</span>')
        else:
            return format_html('<span style="color: #28a745;">🔥 Battle Active</span>')

    @admin.display(description='Entries Overview')
    def entries_overview(self, obj):
        entries = obj.entries.all()
        
        if not entries:
            return format_html('<small>No entries</small>')
        
        entries_html = []
        for entry in entries:
            # Get AI judgment details
            ai_judgment = getattr(entry, 'ai_judgment', None)
            score = safe_float(entry.ai_score)
            media_count = entry.media.count()
            
            # Build AI status indicator
            if ai_judgment:
                confidence = safe_float(ai_judgment.confidence) * 100
                comment_preview = (ai_judgment.ai_comment or '')[:40]
                if len(ai_judgment.ai_comment or '') > 40:
                    comment_preview += '...'
                
                ai_status = f'✅ {fmt_score(score)} (conf:{fmt_score(confidence,0)}%)'
                ai_detail = f'<br><span style="color:#666;font-size:9px;">{comment_preview}</span>'
            else:
                ai_status = f'📊 {fmt_score(score)}' if score else '⚪ No AI'
                ai_detail = ''
            
            # Entry action buttons
            retry_url = reverse('admin:memory_ai_retry', args=[entry.pk])
            clear_url = reverse('admin:memory_ai_clear', args=[entry.pk]) if ai_judgment else ''
            
            buttons = f'<a href="{retry_url}" style="font-size:8px;margin-left:4px;">🔄</a>'
            if clear_url:
                buttons += f'<a href="{clear_url}" style="font-size:8px;margin-left:2px;">🗑️</a>'
            
            entries_html.append(format_html(
                '<div style="margin-bottom:4px;padding:2px;border-left:2px solid #ddd;">'
                '<strong>{}</strong>: {} ({} 📷){}{}'
                '</div>',
                entry.author.username,
                ai_status,
                media_count,
                ai_detail,
                buttons
            ))
        
        return format_html('<div style="font-size: 10px;">{}</div>', ''.join(entries_html))

    @admin.display(description='Battle Winner')
    def battle_winner_display(self, obj):
        entries = obj.entries.all()
        
        if entries.count() < 2:
            return format_html('<small>-</small>')
        
        winner = max(entries, key=lambda x: safe_float(x.ai_score))
        return format_html(
            '<div style="text-align: center;">'
            '<div style="color: #28a745; font-weight: bold;">🏆</div>'
            '<small>{}</small>'
            '</div>',
            winner.author.username
        )

    @admin.display(description='Actions')
    def memory_actions(self, obj):
        return format_html(
            '<div style="display: flex; flex-direction: column; gap: 2px;">'
            '<a href="{}" class="button" style="font-size: 10px;">🔄 Rescore</a>'
            '<a href="{}" class="button" style="font-size: 10px;">♻️ Refresh</a>'
            '</div>',
            reverse('admin:couplememory_couplememory_changelist') + f'?rescore={obj.pk}',
            reverse('admin:couplememory_couplememory_changelist') + f'?refresh={obj.pk}',
        )

    @admin.action(description='🔄 Rescore all entries in selected memories')
    def rescore_all_entries(self, request, queryset):
        try:
            from cookai.scoring import ScoringService
            total = 0
            for memory in queryset:
                for entry in memory.entries.all():
                    if entry.media.exists():
                        ScoringService.score_memory_entry(entry.id)
                        total += 1
            messages.success(request, f'Queued AI rescoring for {total} entries.')
        except Exception as e:
            messages.error(request, f'Rescore failed: {e}')

    @admin.action(description='♻️ Refresh statistics (counters, winner)')
    def refresh_statistics(self, request, queryset):
        updated = 0
        for memory in queryset:
            try:
                memory.recalc_winner()
                memory.refresh_counters()
                updated += 1
            except Exception as e:
                logger.error(f"Failed to refresh stats for memory {memory.id}: {e}")
        messages.success(request, f'Refreshed statistics for {updated} memories.')

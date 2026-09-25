"""
User Behavior Analytics - Admin Interface

Industrial-grade admin dashboard with:
- 42-day (6-week) trend visualization
- Per-user behavior filtering and analysis
- Real-time engagement metrics
- Conversion funnel tracking
- CSV/JSON export for research
"""

from django.contrib import admin
from django.db.models import Count, Avg, Q, F
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
import csv
import json

from .models import EventCategory, EventType, UserEvent, EventAggregate, UserSession


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['icon_display', 'name', 'display_name', 'event_types_count', 'is_active', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color', 'is_active')
        }),
    )
    
    def icon_display(self, obj):
        return format_html('<span style="font-size: 20px;">{}</span>', obj.icon or '📊')
    icon_display.short_description = 'Icon'
    
    def event_types_count(self, obj):
        count = obj.event_types.count()
        return format_html('<strong>{}</strong> types', count)
    event_types_count.short_description = 'Event Types'


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['category_icon', 'name', 'display_name', 'category', 'event_count', 'is_important', 'is_active']
    list_filter = ['category', 'is_important', 'is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    list_editable = ['is_important', 'is_active']
    ordering = ['category', 'name']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'display_name', 'description', 'category')
        }),
        ('Configuration', {
            'fields': ('is_important', 'is_active')
        }),
    )
    
    def category_icon(self, obj):
        return format_html('<span style="font-size: 18px;">{}</span>', obj.category.icon or '📊')
    category_icon.short_description = ''
    
    def event_count(self, obj):
        count = obj.events.count()
        if count > 0:
            formatted_count = f'{count:,}'
            return format_html('<strong>{}</strong> events', formatted_count)
        return '0'
    event_count.short_description = 'Event Count'


@admin.register(UserEvent)
class UserEventAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user_link', 'event_type_display', 'status_badge', 'duration_display', 'resource_display']
    list_filter = ['event_type__category', 'event_type', 'status', 'timestamp', 'user']
    search_fields = ['user__username', 'user__email', 'event_type__name', 'ip_address', 'session_id']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp', 'user', 'event_type', 'ip_address', 'user_agent', 'session_id', 
                      'resource_type', 'resource_id', 'metadata_display', 'duration_ms', 'status', 'error_message']
    ordering = ['-timestamp']
    actions = ['export_as_csv', 'export_as_json']
    
    fieldsets = (
        ('Event Info', {
            'fields': ('timestamp', 'event_type', 'status')
        }),
        ('User Info', {
            'fields': ('user', 'ip_address', 'user_agent', 'session_id')
        }),
        ('Business Data', {
            'fields': ('resource_type', 'resource_id', 'metadata_display', 'duration_ms')
        }),
        ('Error Info', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    change_list_template = 'admin/analytics/userevent_change_list.html'
    
    def get_urls(self):
        """Add custom URLs for AJAX endpoints"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('user-events/<int:user_id>/', 
                 self.admin_site.admin_view(self.user_events_api),
                 name='analytics_userevent_user_events'),
        ]
        return custom_urls + urls
    
    def user_events_api(self, request, user_id):
        """
        AJAX API: Get event distribution and daily activity for a specific user
        
        Query params:
        - date_range: today/7d/30d/90d/custom
        - date_from, date_to: for custom range
        
        Returns JSON:
        {
            "user_id": 1,
            "username": "alice",
            "events": [{...}],
            "daily": [{...}]
        }
        """
        from django.http import JsonResponse
        from django.utils import timezone
        from datetime import timedelta
        
        # Get user
        from users.models import CustomUser
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        # Parse date range (same logic as changelist_view)
        date_range = request.GET.get('date_range', '30d')
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if date_range == 'today':
            range_start = today_start
            days = 1
        elif date_range == '7d':
            range_start = now - timedelta(days=7)
            days = 7
        elif date_range == '90d':
            range_start = now - timedelta(days=90)
            days = 90
        else:  # default 30d
            range_start = now - timedelta(days=30)
            days = 30
        
        # Per-user event distribution
        user_events = UserEvent.objects.filter(
            user_id=user_id,
            timestamp__gte=range_start
        ).values(
            'event_type__display_name',
            'event_type__category__name',
            'event_type__category__icon'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Per-user daily activity
        user_daily = []
        for i in range(days - 1, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            count = UserEvent.objects.filter(
                user_id=user_id,
                timestamp__gte=day_start,
                timestamp__lt=day_end
            ).count()
            user_daily.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'display': day_start.strftime('%m-%d'),
                'count': count
            })
        
        return JsonResponse({
            'user_id': user_id,
            'username': user.username,
            'events': list(user_events),
            'daily': user_daily
        })
    
    def changelist_view(self, request, extra_context=None):
        """
        Academic-grade flexible analytics dashboard
        
        Features:
        - Dynamic date range selection (today/7d/30d/90d/custom)
        - Multi-dimensional visualization (distribution/trend/comparison)
        - User behavior pattern analysis
        - High-performance aggregation
        """
        # JAZZMIN FIX: Initialize analytics_data dict separately from extra_context
        # This prevents any variable name conflicts with Django admin's context
        analytics_data = {}
        
        # === FLEXIBLE DATE RANGE SELECTION ===
        date_range = request.GET.get('date_range', '30d')  # Default 30 days
        custom_start = request.GET.get('date_from')
        custom_end = request.GET.get('date_to')
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate date range based on user selection
        if date_range == 'today':
            range_start = today_start
            days = 1
        elif date_range == '7d':
            range_start = now - timedelta(days=7)
            days = 7
        elif date_range == '30d':
            range_start = now - timedelta(days=30)
            days = 30
        elif date_range == '90d':
            range_start = now - timedelta(days=90)
            days = 90
        elif date_range == 'custom' and custom_start and custom_end:
            from django.utils.dateparse import parse_date
            range_start = parse_date(custom_start)
            range_end = parse_date(custom_end)
            if range_start and range_end:
                range_start = timezone.make_aware(
                    timezone.datetime.combine(range_start, timezone.datetime.min.time())
                )
                range_end = timezone.make_aware(
                    timezone.datetime.combine(range_end, timezone.datetime.max.time())
                )
                days = (range_end - range_start).days + 1
            else:
                range_start = now - timedelta(days=30)
                days = 30
        else:
            range_start = now - timedelta(days=30)
            days = 30
        
        # === CORE STATISTICS ===
        # Period statistics
        period_stats = UserEvent.objects.filter(timestamp__gte=range_start).aggregate(
            total=Count('id'),
            unique_users=Count('user', distinct=True),
            success=Count('id', filter=Q(status='success')),
            failed=Count('id', filter=Q(status='failed')),
            avg_duration=Avg('duration_ms', filter=Q(duration_ms__isnull=False))
        )
        
        # Today's statistics (always show today for comparison)
        today_stats = UserEvent.objects.filter(timestamp__gte=today_start).aggregate(
            total=Count('id'),
            unique_users=Count('user', distinct=True),
            success=Count('id', filter=Q(status='success')),
            failed=Count('id', filter=Q(status='failed')),
        )
        
        # === DAILY TREND (optimized query) ===
        daily_stats = []
        for i in range(days - 1, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            count = UserEvent.objects.filter(
                timestamp__gte=day_start,
                timestamp__lt=day_end
            ).count()
            daily_stats.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'display': day_start.strftime('%m-%d'),
                'count': count
            })
        
        # === TOP EVENTS (by current date range) ===
        top_events = UserEvent.objects.filter(
            timestamp__gte=range_start
        ).values(
            'event_type__display_name',
            'event_type__category__name',
            'event_type__category__icon'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:15]
        
        # === TOP ACTIVE USERS (by current date range) ===
        top_users = UserEvent.objects.filter(
            timestamp__gte=range_start,
            user__isnull=False
        ).values(
            'user__id',
            'user__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # === USER LIST FOR FILTERING ===
        users_with_events = UserEvent.objects.filter(
            user__isnull=False,
            timestamp__gte=range_start
        ).values_list('user__id', 'user__username').distinct().order_by('user__username')
        
        # === ENGAGEMENT METRICS ===
        engagement_metrics = {
            'total_events': period_stats['total'] or 0,
            'unique_users': period_stats['unique_users'] or 0,
            'avg_events_per_user': 0,
            'success_rate': 0,
            'avg_duration_ms': period_stats['avg_duration'] or 0,
        }
        
        if engagement_metrics['unique_users'] > 0:
            engagement_metrics['avg_events_per_user'] = round(
                engagement_metrics['total_events'] / engagement_metrics['unique_users'], 1
            )
        
        if engagement_metrics['total_events'] > 0:
            success_count = period_stats['success'] or 0
            engagement_metrics['success_rate'] = round((success_count / engagement_metrics['total_events']) * 100, 1)
        
        # === EVENT CATEGORY DISTRIBUTION ===
        category_distribution = UserEvent.objects.filter(
            timestamp__gte=range_start
        ).values(
            'event_type__category__name',
            'event_type__category__display_name',
            'event_type__category__icon'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # === USER BEHAVIOR PATTERNS (per-user aggregation) ===
        # TEMPORARILY DISABLED: URL parameter method causes Jazzmin context conflicts
        # Will be replaced with AJAX-based user selection
        selected_user = None  # request.GET.get('selected_user')
        user_pattern_data = None
        
        if False and selected_user:  # Disabled
            # Per-user event distribution
            user_events = UserEvent.objects.filter(
                user_id=selected_user,
                timestamp__gte=range_start
            ).values(
                'event_type__display_name',
                'event_type__category__name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Per-user daily activity
            user_daily = []
            for i in range(days - 1, -1, -1):
                day_start = today_start - timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                count = UserEvent.objects.filter(
                    user_id=selected_user,
                    timestamp__gte=day_start,
                    timestamp__lt=day_end
                ).count()
                user_daily.append({
                    'date': day_start.strftime('%Y-%m-%d'),
                    'display': day_start.strftime('%m-%d'),
                    'count': count
                })
            
            user_pattern_data = {
                'user_id': selected_user,
                'events': list(user_events),
                'daily': user_daily
            }
        
        # Prepare analytics data (separate from extra_context to avoid conflicts)
        analytics_data = {
            # Date range config
            'date_range': date_range,
            'custom_start': custom_start,
            'custom_end': custom_end,
            'stats_period_days': days,
            'range_start': range_start.strftime('%Y-%m-%d'),
            'range_end': now.strftime('%Y-%m-%d'),
            
            # Core statistics
            'period_stats': period_stats,
            'today_stats': today_stats,
            'engagement_metrics': engagement_metrics,
            
            # Visualization data
            'daily_stats': json.dumps(daily_stats),
            'category_distribution': json.dumps(list(category_distribution)),
            'top_events': top_events,
            'top_users': top_users,
            'users_with_events': users_with_events,
            
            # User pattern analysis
            'selected_user': selected_user,
            'user_pattern_data': json.dumps(user_pattern_data) if user_pattern_data else None,
        }
        
        # ULTIMATE FIX: Merge analytics_data into a clean extra_context
        # Then pass to super() - but ensure NO 'request' key exists
        if extra_context is None:
            extra_context = {}
        
        # Merge our analytics data
        extra_context.update(analytics_data)
        
        # CRITICAL: Remove 'request' if somehow it got added
        # Django's changelist_view uses **(extra_context or {}) which overwrites context
        if 'request' in extra_context:
            del extra_context['request']
        
        # Call parent with merged context
        return super().changelist_view(request, extra_context)
    
    # Custom display methods
    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/users/customuser/{}/change/">{}</a>', 
                             obj.user.id, obj.user.username)
        return format_html('<span style="color: #999;">Anonymous</span>')
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user'
    
    def event_type_display(self, obj):
        icon = obj.event_type.category.icon or '📊'
        return format_html('{} <span style="color: {};">{}</span>',
            icon, obj.event_type.category.color, obj.event_type.display_name)
    event_type_display.short_description = 'Event Type'
    
    def status_badge(self, obj):
        colors = {
            'success': '#28a745',
            'failed': '#dc3545',
            'pending': '#ffc107',
            'cancelled': '#6c757d'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def duration_display(self, obj):
        if obj.duration_ms is None:
            return '-'
        if obj.duration_ms < 1000:
            return f'{obj.duration_ms}ms'
        return f'{obj.duration_ms/1000:.2f}s'
    duration_display.short_description = 'Duration'
    
    def resource_display(self, obj):
        if obj.resource_type and obj.resource_id:
            # 🎯 精准改善：显示完整的URL信息，不要截断
            # 对于API和页面URL，显示完整路径以便管理员分析
            if obj.resource_id.startswith('http'):
                # 对于完整的URL，显示完整的路径
                return format_html('<code style="font-size: 10px; word-break: break-all;">{}: {}</code>',
                                 obj.resource_type, obj.resource_id)
            else:
                # 对于其他资源ID，保持原有逻辑但增加长度
                return format_html('<code style="font-size: 10px;">{}: {}</code>',
                                 obj.resource_type, obj.resource_id[:50])
        return '-'
    resource_display.short_description = 'Resource'
    
    def metadata_display(self, obj):
        if not obj.metadata:
            return '-'
        formatted = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
        return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{}</pre>', formatted)
    metadata_display.short_description = 'Metadata'
    
    # Custom actions
    def export_as_csv(self, request, queryset):
        """Export selected events as CSV for HCI research"""
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="user_events_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write('\ufeff')  # BOM for Excel
        
        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'User', 'Event Type', 'Category', 'Status', 'Duration(ms)', 
                        'Resource Type', 'Resource ID', 'IP Address', 'Metadata'])
        
        for obj in queryset:
            writer.writerow([
                obj.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                obj.user.username if obj.user else 'Anonymous',
                obj.event_type.display_name,
                obj.event_type.category.display_name,
                obj.get_status_display(),
                obj.duration_ms or '',
                obj.resource_type or '',
                obj.resource_id or '',
                obj.ip_address or '',
                json.dumps(obj.metadata, ensure_ascii=False) if obj.metadata else ''
            ])
        
        return response
    export_as_csv.short_description = 'Export selected as CSV'
    
    def export_as_json(self, request, queryset):
        """Export selected events as JSON"""
        from django.http import HttpResponse
        
        data = []
        for obj in queryset:
            data.append({
                'timestamp': obj.timestamp.isoformat(),
                'user': obj.user.username if obj.user else None,
                'event_type': obj.event_type.name,
                'event_display': obj.event_type.display_name,
                'category': obj.event_type.category.name,
                'status': obj.status,
                'duration_ms': obj.duration_ms,
                'resource_type': obj.resource_type,
                'resource_id': obj.resource_id,
                'metadata': obj.metadata
            })
        
        response = HttpResponse(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="user_events_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    export_as_json.short_description = 'Export selected as JSON'


@admin.register(EventAggregate)
class EventAggregateAdmin(admin.ModelAdmin):
    list_display = ['period_start', 'event_type', 'period', 'total_count', 'unique_users', 'success_rate_display', 'avg_duration_display']
    list_filter = ['period', 'event_type__category', 'period_start']
    search_fields = ['event_type__name']
    date_hierarchy = 'period_start'
    readonly_fields = ['event_type', 'period', 'period_start', 'period_end', 'total_count', 
                      'unique_users', 'success_count', 'failed_count', 'avg_duration_ms']
    ordering = ['-period_start']
    
    def success_rate_display(self, obj):
        rate = obj.success_rate
        color = '#28a745' if rate >= 95 else '#ffc107' if rate >= 80 else '#dc3545'
        return format_html('<span style="color: {}; font-weight: bold;">{:.1f}%</span>', color, rate)
    success_rate_display.short_description = 'Success Rate'
    
    def avg_duration_display(self, obj):
        if obj.avg_duration_ms is None:
            return '-'
        if obj.avg_duration_ms < 1000:
            return f'{obj.avg_duration_ms:.0f}ms'
        return f'{obj.avg_duration_ms/1000:.2f}s'
    avg_duration_display.short_description = 'Avg Duration'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['started_at', 'user_link', 'event_count', 'duration_display', 'device_type', 'ip_address']
    list_filter = ['device_type', 'started_at', 'user']
    search_fields = ['user__username', 'session_id', 'ip_address']
    date_hierarchy = 'started_at'
    readonly_fields = ['user', 'session_id', 'started_at', 'last_activity_at', 'ended_at', 
                      'event_count', 'duration_seconds', 'ip_address', 'user_agent', 'device_type']
    ordering = ['-started_at']
    
    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/users/customuser/{}/change/">{}</a>', 
                             obj.user.id, obj.user.username)
        return format_html('<span style="color: #999;">Anonymous</span>')
    user_link.short_description = 'User'
    
    def duration_display(self, obj):
        return obj.duration_display
    duration_display.short_description = 'Duration'

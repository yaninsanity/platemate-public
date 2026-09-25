"""
Academic-Grade Data Quality Report

Generates comprehensive analytics tracking quality report for HCI research.
Accessible at: /admin/analytics/data-quality-report/
"""

from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate
from datetime import timedelta
from collections import defaultdict

from .models import UserEvent, EventType, UserSession


def data_quality_report_view(request):
    """
    Academic-grade data quality dashboard.
    
    Shows:
    - Event coverage rate (% of critical events tracked)
    - Tracking accuracy (success rate, metadata completeness)
    - Deduplication effectiveness (frontend pollution rate)
    - Data loss rate (missing/failed events)
    """
    # Time window selection
    days = int(request.GET.get('days', 7))
    since = timezone.now() - timedelta(days=days)
    
    # === CRITICAL EVENTS COVERAGE ===
    critical_events = [
        'feed_pet', 'play_with_pet', 'ai_detect_food', 
        'daily_checkin', 'open_reward_box', 'view_recipe_list'
    ]
    
    coverage_data = []
    for event_name in critical_events:
        try:
            event_type = EventType.objects.get(name=event_name)
            count = UserEvent.objects.filter(
                event_type=event_type,
                timestamp__gte=since
            ).count()
            
            unique_users = UserEvent.objects.filter(
                event_type=event_type,
                timestamp__gte=since,
                user__isnull=False
            ).values('user').distinct().count()
            
            coverage_data.append({
                'name': event_name,
                'display_name': event_type.display_name,
                'count': count,
                'unique_users': unique_users,
                'tracked': count > 0
            })
        except EventType.DoesNotExist:
            coverage_data.append({
                'name': event_name,
                'display_name': event_name,
                'count': 0,
                'unique_users': 0,
                'tracked': False,
                'error': 'Event type not defined'
            })
    
    coverage_rate = sum(1 for d in coverage_data if d['tracked']) / len(coverage_data) * 100
    
    # === DATA QUALITY METRICS ===
    total_events = UserEvent.objects.filter(timestamp__gte=since).count()
    
    if total_events > 0:
        success_events = UserEvent.objects.filter(
            timestamp__gte=since, status='success'
        ).count()
        success_rate = (success_events / total_events * 100)
        
        events_with_metadata = UserEvent.objects.filter(
            timestamp__gte=since,
            metadata__isnull=False
        ).exclude(metadata='{}').count()
        metadata_completeness = (events_with_metadata / total_events * 100)
        
        events_with_duration = UserEvent.objects.filter(
            timestamp__gte=since,
            duration_ms__isnull=False,
            duration_ms__gt=0
        ).count()
        duration_tracking_rate = (events_with_duration / total_events * 100)
        
        avg_duration = UserEvent.objects.filter(
            timestamp__gte=since,
            duration_ms__isnull=False
        ).aggregate(avg=Avg('duration_ms'))['avg'] or 0
    else:
        success_rate = 0
        metadata_completeness = 0
        duration_tracking_rate = 0
        avg_duration = 0
    
    # === DEDUPLICATION EFFECTIVENESS ===
    # Check for rapid-fire events (< 500ms apart)
    dedup_analysis = []
    
    for event_name in ['feed_pet', 'play_with_pet', 'use_food_item']:
        try:
            event_type = EventType.objects.get(name=event_name)
            
            events = list(UserEvent.objects.filter(
                event_type=event_type,
                timestamp__gte=since,
                user__isnull=False
            ).order_by('user', 'timestamp').values('user', 'timestamp'))
            
            rapid_count = 0
            total_count = len(events)
            
            for i in range(1, len(events)):
                if events[i]['user'] == events[i-1]['user']:
                    gap = (events[i]['timestamp'] - events[i-1]['timestamp']).total_seconds()
                    if gap < 0.5:
                        rapid_count += 1
            
            pollution_rate = (rapid_count / total_count * 100) if total_count > 0 else 0
            
            dedup_analysis.append({
                'event': event_name,
                'total': total_count,
                'rapid': rapid_count,
                'pollution_rate': pollution_rate,
                'status': 'good' if pollution_rate < 5 else ('warning' if pollution_rate < 15 else 'bad')
            })
        except EventType.DoesNotExist:
            pass
    
    # === HOURLY ACTIVITY PATTERN ===
    hourly_stats = UserEvent.objects.filter(
        timestamp__gte=since
    ).extra(select={'hour': "EXTRACT(hour FROM timestamp)"}).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # === TOP USERS ===
    top_users = UserEvent.objects.filter(
        timestamp__gte=since,
        user__isnull=False
    ).values('user__username').annotate(
        event_count=Count('id')
    ).order_by('-event_count')[:15]
    
    # === EVENT DISTRIBUTION ===
    event_distribution = UserEvent.objects.filter(
        timestamp__gte=since
    ).values(
        'event_type__name',
        'event_type__display_name',
        'event_type__category__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    # === DAILY TREND ===
    daily_trend = UserEvent.objects.filter(
        timestamp__gte=since
    ).annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        count=Count('id'),
        unique_users=Count('user', distinct=True)
    ).order_by('date')
    
    # === OVERALL QUALITY SCORE ===
    quality_score = (
        coverage_rate * 0.3 +
        success_rate * 0.3 +
        metadata_completeness * 0.2 +
        duration_tracking_rate * 0.2
    )
    
    # Determine overall status
    if quality_score >= 90:
        overall_status = 'excellent'
        status_message = '🎉 Excellent - Production-ready for academic research'
    elif quality_score >= 75:
        overall_status = 'good'
        status_message = '✅ Good - Minor improvements recommended'
    elif quality_score >= 60:
        overall_status = 'fair'
        status_message = '⚠️  Fair - Several issues need attention'
    else:
        overall_status = 'poor'
        status_message = '❌ Poor - Not ready for research-grade data collection'
    
    context = {
        'days': days,
        'since': since,
        'total_events': total_events,
        
        # Coverage
        'coverage_data': coverage_data,
        'coverage_rate': coverage_rate,
        
        # Quality metrics
        'success_rate': success_rate,
        'metadata_completeness': metadata_completeness,
        'duration_tracking_rate': duration_tracking_rate,
        'avg_duration': avg_duration,
        
        # Deduplication
        'dedup_analysis': dedup_analysis,
        
        # Activity patterns
        'hourly_stats': list(hourly_stats),
        'daily_trend': list(daily_trend),
        
        # Top data
        'top_users': list(top_users),
        'event_distribution': list(event_distribution),
        
        # Overall
        'quality_score': quality_score,
        'overall_status': overall_status,
        'status_message': status_message,
    }
    
    return render(request, 'admin/analytics/data_quality_report.html', context)


# Register custom admin URL
def get_data_quality_urls():
    """Returns URL patterns for data quality report"""
    return [
        path('data-quality-report/', 
             admin.site.admin_view(data_quality_report_view), 
             name='analytics_data_quality')
    ]

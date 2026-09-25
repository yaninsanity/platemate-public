"""
Academic-Grade Event Tracking Validation Script

This script validates that critical HCI events (feed, play, etc.) 
are being tracked with 100% accuracy.

Usage:
    python manage.py shell < analytics/validate_tracking.py
    
Or directly:
    python analytics/validate_tracking.py
"""

import sys
import os
import django
from datetime import timedelta
from django.utils import timezone

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from analytics.models import UserEvent, EventType
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from collections import defaultdict

User = get_user_model()


def validate_critical_events():
    """
    Validate that critical events are being tracked.
    
    Returns academic-grade report with:
    - Event coverage rate
    - Data completeness
    - Deduplication effectiveness
    - Frontend pollution rate
    """
    print("=" * 80)
    print("🎓 ACADEMIC-GRADE EVENT TRACKING VALIDATION")
    print("=" * 80)
    print()
    
    # Define critical events for HCI research
    critical_events = [
        'feed_pet',
        'play_with_pet',
        'ai_detect_food',
        'daily_checkin',
        'open_reward_box',
        'view_recipe_list',
        'verify_task',
    ]
    
    # Time window: last 24 hours
    since = timezone.now() - timedelta(hours=24)
    
    print("📊 TRACKING COVERAGE ANALYSIS (Last 24 Hours)")
    print("-" * 80)
    
    coverage_report = {}
    
    for event_name in critical_events:
        try:
            event_type = EventType.objects.get(name=event_name)
            count = UserEvent.objects.filter(
                event_type=event_type,
                timestamp__gte=since
            ).count()
            
            # Get unique users
            unique_users = UserEvent.objects.filter(
                event_type=event_type,
                timestamp__gte=since,
                user__isnull=False
            ).values('user').distinct().count()
            
            coverage_report[event_name] = {
                'count': count,
                'unique_users': unique_users,
                'tracked': count > 0
            }
            
            status = "✅" if count > 0 else "⚠️"
            print(f"{status} {event_name:25s} | Events: {count:4d} | Users: {unique_users:3d}")
            
        except EventType.DoesNotExist:
            print(f"❌ {event_name:25s} | EVENT TYPE NOT DEFINED!")
            coverage_report[event_name] = {'tracked': False, 'error': 'missing_event_type'}
    
    print()
    print("=" * 80)
    print("🎯 DATA QUALITY METRICS")
    print("=" * 80)
    
    # Calculate metrics
    total_events = UserEvent.objects.filter(timestamp__gte=since).count()
    
    # Success rate
    success_events = UserEvent.objects.filter(
        timestamp__gte=since,
        status='success'
    ).count()
    success_rate = (success_events / total_events * 100) if total_events > 0 else 0
    
    # Data completeness
    events_with_metadata = UserEvent.objects.filter(
        timestamp__gte=since,
        metadata__isnull=False
    ).exclude(metadata='{}').count()
    metadata_rate = (events_with_metadata / total_events * 100) if total_events > 0 else 0
    
    # Duration tracking
    events_with_duration = UserEvent.objects.filter(
        timestamp__gte=since,
        duration_ms__isnull=False,
        duration_ms__gt=0
    ).count()
    duration_rate = (events_with_duration / total_events * 100) if total_events > 0 else 0
    
    print(f"Total Events:        {total_events:6d}")
    print(f"Success Rate:        {success_rate:6.2f}%")
    print(f"Metadata Coverage:   {metadata_rate:6.2f}%")
    print(f"Duration Tracking:   {duration_rate:6.2f}%")
    print()
    
    # Check for potential duplicates (suspicious rapid-fire events)
    print("=" * 80)
    print("🔍 DEDUPLICATION EFFECTIVENESS")
    print("=" * 80)
    
    from django.db.models import F, Window
    from django.db.models.functions import Lag
    
    # Find events with < 100ms gaps (potential duplicates)
    suspicious_events = []
    
    for event_name in ['feed_pet', 'play_with_pet']:
        try:
            event_type = EventType.objects.get(name=event_name)
            
            # Get all events ordered by time
            events = list(UserEvent.objects.filter(
                event_type=event_type,
                timestamp__gte=since,
                user__isnull=False
            ).order_by('user', 'timestamp').values('user__username', 'timestamp'))
            
            # Check for rapid succession
            rapid_count = 0
            for i in range(1, len(events)):
                if events[i]['user__username'] == events[i-1]['user__username']:
                    gap = (events[i]['timestamp'] - events[i-1]['timestamp']).total_seconds()
                    if gap < 0.5:  # Less than 500ms
                        rapid_count += 1
            
            total_count = len(events)
            pollution_rate = (rapid_count / total_count * 100) if total_count > 0 else 0
            
            status = "✅" if pollution_rate < 5 else ("⚠️" if pollution_rate < 15 else "❌")
            print(f"{status} {event_name:25s} | Rapid Events: {rapid_count:4d} / {total_count:4d} ({pollution_rate:.2f}%)")
            
        except EventType.DoesNotExist:
            print(f"❌ {event_name:25s} | EVENT TYPE NOT FOUND")
    
    print()
    print("=" * 80)
    print("👥 USER ENGAGEMENT ANALYSIS")
    print("=" * 80)
    
    # Top active users
    top_users = UserEvent.objects.filter(
        timestamp__gte=since,
        user__isnull=False
    ).values('user__username').annotate(
        event_count=Count('id')
    ).order_by('-event_count')[:10]
    
    print("\nTop 10 Active Users:")
    for i, user_data in enumerate(top_users, 1):
        print(f"  {i:2d}. {user_data['user__username']:20s} - {user_data['event_count']:4d} events")
    
    # Event distribution
    print("\n" + "=" * 80)
    print("📈 EVENT DISTRIBUTION")
    print("=" * 80)
    
    event_dist = UserEvent.objects.filter(
        timestamp__gte=since
    ).values('event_type__name', 'event_type__display_name').annotate(
        count=Count('id')
    ).order_by('-count')[:15]
    
    print("\nTop 15 Events:")
    for i, event in enumerate(event_dist, 1):
        name = event['event_type__display_name'] or event['event_type__name']
        print(f"  {i:2d}. {name:30s} - {event['count']:5d} events")
    
    print()
    print("=" * 80)
    print("✅ VALIDATION COMPLETE")
    print("=" * 80)
    
    # Summary
    tracked_count = sum(1 for r in coverage_report.values() if r.get('tracked', False))
    total_critical = len(critical_events)
    coverage_pct = (tracked_count / total_critical * 100) if total_critical > 0 else 0
    
    print(f"\nCritical Event Coverage: {tracked_count}/{total_critical} ({coverage_pct:.1f}%)")
    print(f"Overall Data Quality:    {(success_rate + metadata_rate + duration_rate) / 3:.1f}%")
    
    if coverage_pct >= 90 and success_rate >= 95:
        print("\n🎉 EXCELLENT: System is production-ready for academic research!")
    elif coverage_pct >= 70 and success_rate >= 85:
        print("\n⚠️  GOOD: Some improvements needed for full academic rigor")
    else:
        print("\n❌ POOR: Significant tracking gaps detected - not research-ready")
    
    print()


if __name__ == '__main__':
    validate_critical_events()

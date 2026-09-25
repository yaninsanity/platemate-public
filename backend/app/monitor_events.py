#!/usr/bin/env python
"""
Real-time Analytics Event Monitor

Watch for new events as they are created.
Run this while testing the frontend.
"""

import sys
import os
import django
import time
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, '/usr/src/app/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from analytics.models import UserEvent
from django.utils import timezone

print("🔍 Real-time Analytics Event Monitor")
print("=" * 60)
print("Monitoring for new events...")
print("Press Ctrl+C to stop\n")

last_check = timezone.now()

try:
    while True:
        # Check for new events since last check
        new_events = UserEvent.objects.filter(
            timestamp__gte=last_check
        ).order_by('-timestamp')
        
        if new_events.exists():
            for event in new_events:
                user_str = event.user.username if event.user else 'Anonymous'
                timestamp_str = event.timestamp.strftime('%H:%M:%S')
                
                # Color coding
                if event.status == 'success':
                    status_icon = '✅'
                elif event.status == 'failed':
                    status_icon = '❌'
                else:
                    status_icon = '⚠️'
                
                print(f"{timestamp_str} | {status_icon} {event.event_type.name:25s} | User: {user_str:12s} | Status: {event.status}")
            
            # Update last check time
            last_check = timezone.now()
        
        time.sleep(0.5)  # Check every 0.5 seconds

except KeyboardInterrupt:
    print("\n\n✋ Monitoring stopped")
    print("=" * 60)

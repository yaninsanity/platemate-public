"""
Test script to generate sample analytics data for visualization

This will create:
- Sample user events over the past 42 days
- Various event types across all categories
- Different users for per-user analysis
"""

import os
import django
import sys

# Setup Django
sys.path.insert(0, '/usr/src/app/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
import random
from analytics.models import EventType, UserEvent
from users.models import CustomUser

print("Generating sample analytics data...")
print("=" * 60)

# Get or create test users
users = list(CustomUser.objects.all()[:5])
if not users:
    print("No users found. Please create users first.")
    sys.exit(1)

print(f"Found {len(users)} users: {[u.username for u in users]}")

# Get all active event types
event_types = list(EventType.objects.filter(is_active=True))
print(f"Found {len(event_types)} active event types")

# Generate events for past 42 days
now = timezone.now()
events_created = 0

for days_ago in range(42):
    date = now - timedelta(days=days_ago)
    
    # Random number of events per day (10-50)
    num_events = random.randint(10, 50)
    
    for _ in range(num_events):
        user = random.choice(users)
        event_type = random.choice(event_types)
        
        # Random time during the day
        event_time = date.replace(
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
        
        # Create event
        UserEvent.objects.create(
            user=user,
            event_type=event_type,
            timestamp=event_time,
            status=random.choice(['success', 'success', 'success', 'failed']),  # 75% success
            duration_ms=random.randint(50, 5000) if random.random() > 0.5 else None,
            session_id=f'session_{random.randint(1000, 9999)}',
            metadata={'test_data': True}
        )
        events_created += 1
    
    if days_ago % 7 == 0:
        print(f"  Generated events for {42 - days_ago} days...")

print("=" * 60)
print(f"✓ Created {events_created} sample events")
print(f"✓ Covering 42 days of data")
print(f"✓ For {len(users)} users")
print("\nVisit http://localhost:911/admin/analytics/userevent/")
print("to see the 42-day visualization dashboard!")

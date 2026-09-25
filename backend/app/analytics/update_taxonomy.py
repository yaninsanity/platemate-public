"""
Update Analytics Event Taxonomy

Adds new critical events:
- review_round_detail: Battle/Roundly detail view (HCI critical)
- view_battle_list: Battle history list
- view_memory_detail: Couple memory detail view

Run: python manage.py shell < analytics/update_taxonomy.py
"""

import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from analytics.models import EventType, EventCategory
from analytics.event_taxonomy import HCI_EVENT_TAXONOMY

print("=" * 80)
print("🔄 UPDATING EVENT TAXONOMY")
print("=" * 80)
print()

# Get or create categories
for category_key, category_data in HCI_EVENT_TAXONOMY.items():
    category, created = EventCategory.objects.get_or_create(
        name=category_key,
        defaults={
            'display_name': category_data['display_name'],
            'description': category_data['description'],
            'color': category_data['color'],
            'icon': category_data['icon']
        }
    )
    
    if created:
        print(f"✅ Created category: {category.display_name}")
    else:
        # Update existing category
        category.display_name = category_data['display_name']
        category.description = category_data['description']
        category.color = category_data['color']
        category.icon = category_data['icon']
        category.save()
        print(f"🔄 Updated category: {category.display_name}")
    
    # Create/update events in this category
    for event_tuple in category_data['events']:
        event_name, display_name, description = event_tuple
        
        event, created = EventType.objects.get_or_create(
            name=event_name,
            defaults={
                'display_name': display_name,
                'description': description,
                'category': category
            }
        )
        
        if created:
            print(f"  ✅ Created event: {event_name} → {display_name}")
        else:
            # Update existing event
            event.display_name = display_name
            event.description = description
            event.category = category
            event.save()
            print(f"  🔄 Updated event: {event_name} → {display_name}")

print()
print("=" * 80)
print("✅ TAXONOMY UPDATE COMPLETE")
print("=" * 80)
print()

# Show new critical events
print("🎯 NEW CRITICAL EVENTS FOR HCI RESEARCH:")
print("-" * 80)

critical_new_events = [
    'review_round_detail',
    'view_battle_list', 
    'view_memory_detail'
]

for event_name in critical_new_events:
    try:
        event = EventType.objects.get(name=event_name)
        print(f"✅ {event_name:30s} → {event.display_name}")
        print(f"   {event.description}")
        print()
    except EventType.DoesNotExist:
        print(f"❌ {event_name:30s} → NOT FOUND!")
        print()

print("=" * 80)
print("🚀 Ready to track battle review engagement!")
print("=" * 80)

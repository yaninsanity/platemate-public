"""
Test Event Mapping Precision

Validates that:
1. Feed Pet button correctly maps to correct event
2. Battle detail pages are tracked
3. URL prefix matching works correctly
"""

import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.test import RequestFactory
from analytics.middleware import AnalyticsMiddleware
from analytics.models import EventType

print("=" * 80)
print("🧪 TESTING EVENT MAPPING PRECISION")
print("=" * 80)
print()

# Create mock request factory
factory = RequestFactory()
middleware = AnalyticsMiddleware(lambda x: None)

# Test cases
test_cases = [
    # (path, method, expected_event_name, description)
    
    # Pet Care - Order matters!
    ('/api/petcare/food-inventory/couple_comparison/', 'GET', 'compare_couple_food', 
     '✅ Feed button shows couple comparison'),
    
    ('/api/petcare/food-inventory/', 'GET', 'view_food_inventory', 
     '✅ Generic inventory view'),
    
    ('/api/petcare/food-inventory/use/', 'POST', 'use_food_item', 
     '✅ Use specific food'),
    
    ('/api/petcare/pet/feed/', 'POST', 'feed_pet', 
     '✅ Actual feed action'),
    
    # Battle/Roundly - CRITICAL
    ('/api/recipes/brackets/', 'GET', 'view_battle_list', 
     '🎯 Battle history list'),
    
    ('/api/recipes/brackets/17/', 'GET', 'review_round_detail', 
     '🎯 Battle detail view (ID: 17)'),
    
    ('/api/recipes/brackets/123/', 'GET', 'review_round_detail', 
     '🎯 Battle detail view (ID: 123)'),
    
    # Memory
    ('/api/couplememory/memories/', 'GET', 'view_memories', 
     '✅ Memory list'),
    
    ('/api/couplememory/memories/17/', 'GET', 'view_memory_detail', 
     '🎯 Memory detail (ID: 17)'),
]

print("📋 TEST RESULTS:")
print("-" * 80)

passed = 0
failed = 0

for path, method, expected_event, description in test_cases:
    # Create mock request
    request = factory.get(path) if method == 'GET' else factory.post(path)
    request.method = method
    request.path = path
    
    # Get event type
    event_type = middleware._determine_event_type(request)
    
    if event_type:
        actual_event = event_type.name
        if actual_event == expected_event:
            print(f"✅ PASS: {description}")
            print(f"   Path: {path}")
            print(f"   Event: {actual_event}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   Path: {path}")
            print(f"   Expected: {expected_event}")
            print(f"   Got: {actual_event}")
            failed += 1
    else:
        print(f"❌ FAIL: {description}")
        print(f"   Path: {path}")
        print(f"   Expected: {expected_event}")
        print(f"   Got: None (no event type found)")
        failed += 1
    
    print()

print("=" * 80)
print(f"📊 TEST SUMMARY: {passed} passed, {failed} failed")
print("=" * 80)

if failed == 0:
    print("🎉 ALL TESTS PASSED! Event mapping is production-ready.")
else:
    print(f"⚠️  {failed} tests failed. Review event mapping logic.")

print()

# Show all event types for reference
print("=" * 80)
print("📚 ALL REGISTERED EVENT TYPES:")
print("=" * 80)

events_by_category = {}
for event in EventType.objects.all().order_by('category__name', 'name'):
    cat_name = event.category.display_name if event.category else 'Uncategorized'
    if cat_name not in events_by_category:
        events_by_category[cat_name] = []
    events_by_category[cat_name].append(event)

for category, events in events_by_category.items():
    print(f"\n{category}:")
    for event in events:
        print(f"  - {event.name:30s} → {event.display_name}")

print()

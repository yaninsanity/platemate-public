"""
Django Management Command - Initialize Analytics Event Types

🎯 Clean & Precise Event Initialization

运行方法:
cd backend/app
python manage.py init_core_events
"""

from django.core.management.base import BaseCommand
from analytics.models import EventCategory, EventType
from analytics.event_taxonomy import (
    get_all_events, 
    is_important_event, 
    should_track_duration
)


class Command(BaseCommand):
    help = '🎯 Initialize all analytics events (clean & precise edition)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🚀 Starting analytics initialization...'))
        self.stdout.write('')
        
        total_categories = 0
        total_events = 0
        
        # Get all events from clean taxonomy
        all_events = get_all_events()
        
        # Create categories and events
        for category_name, category_data in all_events.items():
            category, created = EventCategory.objects.get_or_create(
                name=category_name,
                defaults={
                    'display_name': category_data['display_name'],
                    'description': category_data['description'],
                    'icon': category_data.get('icon', ''),
                    'color': category_data.get('color', '#6c757d'),
                    'is_active': True,
                }
            )
            
            if created:
                total_categories += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Created category: {category.icon} {category.display_name}')
                )
            
            # Create event types
            for event_name, display_name, description in category_data['events']:
                event_type, created = EventType.objects.get_or_create(
                    name=event_name,
                    defaults={
                        'category': category,
                        'display_name': display_name,
                        'description': description,
                        'is_important': is_important_event(event_name),
                        'is_active': True,
                    }
                )
                
                if created:
                    total_events += 1
                    importance = '⭐' if event_type.is_important else '  '
                    self.stdout.write(
                        self.style.SUCCESS(f'    {importance} {event_name}')
                    )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'✅ Initialization complete!'))
        self.stdout.write(self.style.SUCCESS(f'📊 Categories: {total_categories} created'))
        self.stdout.write(self.style.SUCCESS(f'📈 Events: {total_events} created'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # List key user action events
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('🎯 Key User Action Events:'))
        self.stdout.write('')
        
        key_events = [
            ('Pet Care', [
                ('feed_pet', 'Feed Pet'),
                ('open_feed_panel', 'Open Feed Panel'),
                ('check_game_rewards', 'Check Game Rewards'),
                ('play_game', 'Play Game'),
            ]),
            ('Recipes', [
                ('view_recipe_list', 'View Recipe List'),
                ('view_recipe_detail', 'View Recipe Detail'),
                ('view_recipe_reference', 'View Recipe Reference (Step 3)'),
                ('view_battle_history', 'View Battle History'),
                ('view_battle_detail', 'View Battle Detail'),
            ]),
            ('Memories', [
                ('start_memory_creation', 'Start Memory Creation'),
                ('view_memory_list', 'View Memory List'),
                ('view_memory_detail', 'View Memory Detail'),
            ]),
            ('Social', [
                ('post_comment', 'Post Comment'),
            ]),
            ('Shopping', [
                ('search_stores', 'Search Stores'),
            ]),
            ('Timezone', [
                ('check_time_lag', 'Check Time Lag'),
            ]),
        ]
        
        for category, events in key_events:
            self.stdout.write(f'  {category}:')
            for event_name, description in events:
                exists = EventType.objects.filter(name=event_name).exists()
                status = '✅' if exists else '❌'
                self.stdout.write(f'    {status} {event_name} - {description}')
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('🎉 Ready to track user behavior!'))
        self.stdout.write('')
        self.stdout.write('💡 Next steps:')
        self.stdout.write('   1. Add frontend tracking calls in Vue components')
        self.stdout.write('   2. Test events in Django Admin: /admin/analytics/')
        self.stdout.write('   3. Verify no duplicate tracking')
        self.stdout.write('')
        page_events = [
            'page_diary',
            'page_battles', 
            'page_pet',
            'page_recipes',
            'page_inventory',
            'page_profile',
            'page_settings',
        ]
        for event_name in page_events:
            exists = EventType.objects.filter(name=event_name).exists()
            status = '✅' if exists else '❌'
            self.stdout.write(f'  {status} {event_name}')
        
        # AI events summary
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('🤖 AI Interaction Events:'))
        ai_events = [
            'ai_detect_food',
            'ai_chat_start',
            'ai_chat_message',
            'ai_chat_end',
        ]
        for event_name in ai_events:
            exists = EventType.objects.filter(name=event_name).exists()
            status = '✅' if exists else '❌'
            self.stdout.write(f'  {status} {event_name}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Ready to start tracking user behavior!'))
        self.stdout.write(self.style.SUCCESS('💡 Next steps:'))
        self.stdout.write(self.style.SUCCESS('   1. Test API calls to verify auto-tracking'))
        self.stdout.write(self.style.SUCCESS('   2. Check Django Admin: /admin/analytics/'))
        self.stdout.write(self.style.SUCCESS('   3. Run analysis queries'))

"""
Django management command to initialize Analytics event taxonomy

Usage:
    python manage.py init_analytics
    
This will populate the database with:
- 10 event categories
- 88 predefined event types
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from analytics.models import EventCategory, EventType
from analytics.event_taxonomy import HCI_EVENT_TAXONOMY, is_important_event


class Command(BaseCommand):
    help = 'Initialize Analytics event taxonomy (10 categories, 88 events)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Initializing Analytics Event Taxonomy...'))
        
        total_categories = 0
        total_events = 0
        
        with transaction.atomic():
            for category_name, category_config in HCI_EVENT_TAXONOMY.items():
                # Create or update category
                category, created = EventCategory.objects.update_or_create(
                    name=category_name,
                    defaults={
                        'display_name': category_config['display_name'],
                        'description': category_config['description'],
                        'color': category_config['color'],
                        'is_active': True,
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Created category: {category.display_name}'))
                    total_categories += 1
                else:
                    self.stdout.write(f'  Updated category: {category.display_name}')
                
                # Create or update event types
                for event_name, display_name, description in category_config['events']:
                    event_type, event_created = EventType.objects.update_or_create(
                        name=event_name,
                        defaults={
                            'category': category,
                            'display_name': display_name,
                            'description': description,
                            'is_important': is_important_event(event_name),
                            'is_active': True,
                        }
                    )
                    
                    if event_created:
                        total_events += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nInitialization complete!'))
        self.stdout.write(self.style.SUCCESS(f'  New categories: {total_categories}'))
        self.stdout.write(self.style.SUCCESS(f'  New events: {total_events}'))
        self.stdout.write(self.style.SUCCESS(f'  Total categories: {EventCategory.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Total events: {EventType.objects.count()}'))

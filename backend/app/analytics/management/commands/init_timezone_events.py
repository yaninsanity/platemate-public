"""
seed the timezone-related event types
"""
from django.core.management.base import BaseCommand
from analytics.models import EventType, EventCategory
from analytics.event_taxonomy import HCI_EVENT_TAXONOMY, is_important_event


class Command(BaseCommand):
    help = 'seed the timezone-related event types'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("🌍 初始化 Timezone EventTypes")
        self.stdout.write("=" * 60)
        
        # Get or create timezone category
        timezone_config = HCI_EVENT_TAXONOMY.get('timezone', {})
        category, cat_created = EventCategory.objects.get_or_create(
            name='timezone',
            defaults={
                'display_name': timezone_config.get('display_name', 'Timezone'),
                'description': timezone_config.get('description', '时区查看和转换功能'),
                'icon': timezone_config.get('icon', '🌍'),
                'color': timezone_config.get('color', '#17a2b8'),
                'is_active': True
            }
        )
        
        if cat_created:
            self.stdout.write(self.style.SUCCESS(f"✅ 创建 Category: {category}"))
        else:
            self.stdout.write(f"ℹ️  Category 已存在: {category}")
        
        # Create all timezone event types
        events = timezone_config.get('events', [])
        created_count = 0
        updated_count = 0
        
        for event_tuple in events:
            event_name, display_name, description = event_tuple
            
            event_type, created = EventType.objects.get_or_create(
                name=event_name,
                defaults={
                    'category': category,
                    'display_name': display_name,
                    'description': description,
                    'is_important': is_important_event(event_name),
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                important_mark = "⭐" if event_type.is_important else "  "
                self.stdout.write(self.style.SUCCESS(
                    f"{important_mark} ✅ 创建: {event_name} - {display_name}"
                ))
            else:
                # Update is_important flag if needed
                if event_type.is_important != is_important_event(event_name):
                    event_type.is_important = is_important_event(event_name)
                    event_type.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(
                        f"   🔄 更新: {event_name} - is_important={event_type.is_important}"
                    ))
                else:
                    self.stdout.write(f"   ℹ️  已存在: {event_name}")
        
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(f"📊 总结:")
        self.stdout.write(f"   新创建: {created_count}")
        self.stdout.write(f"   已更新: {updated_count}")
        self.stdout.write(f"   总计: {EventType.objects.filter(category=category).count()}")
        self.stdout.write("=" * 60)

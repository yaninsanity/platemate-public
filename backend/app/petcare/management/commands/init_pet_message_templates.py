"""
管理命令：初始化宠物消息模板数据

Usage:
    python manage.py init_pet_message_templates
    python manage.py init_pet_message_templates --clear  # 先清空现有数据
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from petcare.models import PetMessageTemplate


class Command(BaseCommand):
    help = 'Initialize pet message templates with default data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing templates before loading new ones',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write("Initializing pet message templates...")

        # 获取模板数据
        template_data = self.get_template_data()

        if options['dry_run']:
            self.show_dry_run(template_data)
            return

        try:
            with transaction.atomic():
                if options['clear']:
                    self.clear_existing_templates()

                created_count = self.create_templates(template_data)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created {created_count} pet message templates!'
                    )
                )

        except Exception as e:
            raise CommandError(f'Failed to initialize templates: {e}')

    def get_template_data(self):
        """Return all template data organized by state"""
        return {
            'state1': [
                "We drew {{recipe.name}}! Want to try it together in the next three days?",
                "It's {{recipe.name}} today.",
                "{{recipe.name}} has arrived! It's a three-day joint activity. Take it slow if you like.",
                "This round is {{recipe.name}}. I'll handle reminders; you have fun cooking.",
                "Recipe confirmed: {{recipe.name}}! Start now or save it for later?",
                "Take a quick peek at the ingredient list. Missing anything?",
                "Before starting cooking, don't forget to take a picture for the ingredient verification task!",
                "Finish the Ingredient verification task, and we can start cooking!",
                "I'm so hungry! Let's hunt down everything we need for {{recipe.name}}.",
                "Sniff sniff… I can already smell {{recipe.name}}. Check the list and show me the ingredients!",
            ],
            'state2': [
                "Chefs, gather up! Follow the step card for {{recipe.name}}, and I'll watch the time.",
                "Heat looks good. Let's cook!",
                "Upload your {{recipe.name}} final shot or process photos. Kinny will score them; let's see who's ahead!",
                "Jot down a couple lines about how it felt to cook. Once scores are out, the higher score is this round's champion!",
                "Clearer photos earn extra points; plating counts too. When you're ready, I'll reveal both scores.",
                "Don't be shy, show off your {{recipe.name}} masterpiece! I'll give feedback and announce the winner.",
                "I can smell it already! Drop a final or process photo of {{recipe.name}}, and I'll score it to see who's ahead.",
                "Show me your proudest {{recipe.name}} moment! I'll reply with comments and announce the winner.",
            ],
            'state3': [
                "My tummy's empty! You've got a food reward! feed me a bite?",
                "I smell something yummy! If you have a food reward, share a bit, or just tap me to play.",
                "Beep beep~~~hunger below half. Tap \"Feed,\" or tap me to play together.",
                "…give me a little snack,",
                "I'm so hungry. Feed me with your food reward and my energy will bounce right back!",
                "Want to see my moves? Feed me first, or tap \"Play\" and I'll dance for you.",
            ],
            'state4': [
                "Dice ready! Give it a roll and I'll gently ping your partner.",
                "Ding!!!! You've got a dice to use. Toss it, and I'll call them to prep with you.",
                "Want to speed things up? Use the dice and I'll remind them about ingredients and the activity.",
            ],
            'state5': [
                "A nudge from your partner's dice! Join this round~~~start by checking the ingredient list.",
                "Your partner rolled the dice to summon you",
                "Kinny here: your partner's waiting! Check the list and grab any ingredients you're responsible for.",
            ],
            'state6': [
                "Your partner has finished ingredient verification! It's your turn! Open the list and complete the photo task.",
                "Little nudge: they've passed the check. Snap your ingredient and upload it~~~I'll verify for you.",
                "Nice pace! Your teammate has finished prepping ingredients. Let's get started.",
                "I can smell cooking time! Add your ingredient photo or tick the list so we can move forward.",
            ],
            'state7': [
                "Your partner has finished sharing! Kinny's scoring contest is on. Drop your final photo or a short note.",
                "The contest is live!!! Share your cooking moment now.",
                "The most fun part is here! Upload a photo or a short memory, and let's see who wins the champion.",
                "Your partner is done and a step ahead! Show your result and Kinny will score and comment right away.",
                "The champion isn't decided yet. Your share is the missing piece! Upload it and I'll announce this round's MVP.",
            ],
        }

    def clear_existing_templates(self):
        """Clear existing pet message templates"""
        deleted_count = PetMessageTemplate.objects.all().count()
        PetMessageTemplate.objects.all().delete()

        self.stdout.write(
            self.style.WARNING(f'Cleared {deleted_count} existing templates')
        )

    def create_templates(self, template_data):
        """Create templates from data"""
        created_count = 0

        for state_code, messages in template_data.items():
            self.stdout.write(f"Creating templates for {state_code}...")

            for index, message in enumerate(messages, 1):
                template, created = PetMessageTemplate.objects.get_or_create(
                    state_code=state_code,
                    message_template=message,
                    defaults={
                        'weight': len(messages) - index + 1,  # 前面的消息权重更高
                        'is_active': True,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(f"  ✓ Created: {message[:50]}...")
                else:
                    self.stdout.write(f"  → Exists: {message[:50]}...")

        return created_count

    def show_dry_run(self, template_data):
        """Show what would be created in dry run mode"""
        self.stdout.write(self.style.WARNING("DRY RUN MODE - No data will be created"))

        total_count = 0
        for state_code, messages in template_data.items():
            count = len(messages)
            total_count += count
            self.stdout.write(f"Would create {count} templates for {state_code}:")

            for index, message in enumerate(messages, 1):
                weight = len(messages) - index + 1
                self.stdout.write(f"  [{weight}] {message}")

            self.stdout.write("")  # Empty line for readability

        self.stdout.write(
            self.style.SUCCESS(f"Total: {total_count} templates would be created")
        )

    def validate_template_data(self, template_data):
        """Validate template data structure"""
        required_states = ['state1', 'state2', 'state3', 'state4', 'state5', 'state6', 'state7']

        for state in required_states:
            if state not in template_data:
                raise CommandError(f"Missing required state: {state}")

            if not template_data[state]:
                raise CommandError(f"No messages defined for {state}")

        self.stdout.write("✓ Template data validation passed")


# ────────────────────────────────────────────────────────────
# 额外的管理命令扩展
# ────────────────────────────────────────────────────────────

class TemplateStats:
    """模板统计工具"""

    @staticmethod
    def print_statistics(stdout, style):
        """打印模板统计信息"""
        from django.db.models import Count

        total_count = PetMessageTemplate.objects.count()
        active_count = PetMessageTemplate.objects.filter(is_active=True).count()

        # 按状态统计
        state_stats = (
            PetMessageTemplate.objects
            .values('state_code')
            .annotate(count=Count('id'))
            .order_by('state_code')
        )

        stdout.write("\n" + "=" * 50)
        stdout.write(style.SUCCESS("Pet Message Template Statistics"))
        stdout.write("=" * 50)
        stdout.write(f"Total templates: {total_count}")
        stdout.write(f"Active templates: {active_count}")
        stdout.write(f"Inactive templates: {total_count - active_count}")
        stdout.write("\nBreakdown by state:")

        for stat in state_stats:
            state = stat['state_code']
            count = stat['count']
            active_count = PetMessageTemplate.objects.filter(
                state_code=state, is_active=True
            ).count()
            stdout.write(f"  {state}: {count} total ({active_count} active)")

        stdout.write("=" * 50)
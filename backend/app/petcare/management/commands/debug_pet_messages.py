"""
调试管理命令：测试和调试宠物消息系统 - 更新版

Usage:
    python manage.py debug_pet_messages --user username
    python manage.py debug_pet_messages --couple couple_code
    python manage.py debug_pet_messages --all
    python manage.py debug_pet_messages --sms-preview
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from petcare.utils import debug_user_states, get_user_state_summary, bulk_update_messages
from petcare.pet_message_service import refresh_user_pet_messages, get_random_messages_per_state
from petcare.models import UserPetMessageState, PetMessageTemplate
from petcare.signals import send_daily_sms_messages
from users.models import Couple

User = get_user_model()


class Command(BaseCommand):
    help = 'Debug and test pet message system - updated version'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Debug specific user by username',
        )
        parser.add_argument(
            '--couple',
            type=str,
            help='Debug specific couple by code',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Debug all users with couples',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update messages before debugging',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show system statistics',
        )
        parser.add_argument(
            '--sms-preview',
            action='store_true',
            help='Preview daily SMS content for all users',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write("Pet Message System Debug Tool - Updated")
        self.stdout.write("=" * 60)

        if options['stats']:
            self.show_statistics()
            return

        if options['sms_preview']:
            self.preview_sms_messages()
            return

        if options['user']:
            self.debug_user(options['user'], options.get('update', False))
        elif options['couple']:
            self.debug_couple(options['couple'], options.get('update', False))
        elif options['all']:
            self.debug_all_users(options.get('update', False))
        else:
            self.stdout.write("Please specify --user, --couple, --all, --stats, or --sms-preview")

    def debug_user(self, username: str, update: bool = False):
        """Debug specific user"""
        try:
            user = User.objects.get(username=username)

            if update:
                self.stdout.write(f"Updating messages for {username}...")
                refresh_user_pet_messages(user, "debug_command")

            # 显示调试信息
            debug_info = debug_user_states(user)
            self.stdout.write(debug_info)

            # 显示当前消息
            self.show_user_messages(user)

            # 显示短信预览
            self.show_sms_preview(user)

        except User.DoesNotExist:
            raise CommandError(f'User "{username}" not found')
        except Exception as e:
            raise CommandError(f'Error debugging user: {e}')

    def debug_couple(self, couple_code: str, update: bool = False):
        """Debug specific couple"""
        try:
            couple = Couple.objects.get(code=couple_code)

            self.stdout.write(f"Debugging couple: {couple_code}")
            self.stdout.write(f"Members: {[u.username for u in couple.members.all()]}")
            self.stdout.write("")

            for user in couple.members.all():
                if update:
                    self.stdout.write(f"Updating messages for {user.username}...")
                    refresh_user_pet_messages(user, "debug_command")

                debug_info = debug_user_states(user)
                self.stdout.write(debug_info)
                self.stdout.write("")

        except Couple.DoesNotExist:
            raise CommandError(f'Couple "{couple_code}" not found')
        except Exception as e:
            raise CommandError(f'Error debugging couple: {e}')

    def debug_all_users(self, update: bool = False):
        """Debug all users with couples"""
        users = User.objects.filter(couple__isnull=False)

        if not users.exists():
            self.stdout.write("No users with couples found")
            return

        self.stdout.write(f"Debugging {users.count()} users...")

        if update:
            result = bulk_update_messages(list(users), "debug_command")
            self.stdout.write(f"Update results: {result}")
            self.stdout.write("")

        for user in users:
            summary = get_user_state_summary(user)
            self.stdout.write(f"User: {user.username}")
            self.stdout.write(f"  Couple: {summary.get('couple')}")
            self.stdout.write(f"  Current Recipe: {summary.get('current_recipe')}")

            try:
                state = UserPetMessageState.objects.filter(user=user).first()
                if state:
                    self.stdout.write(f"  Active States: {state.current_states}")
                    self.stdout.write(f"  Messages: {len(state.available_messages)}")
                else:
                    self.stdout.write("  No message state found")
            except Exception as e:
                self.stdout.write(f"  Error: {e}")

            self.stdout.write("")

    def show_user_messages(self, user: User):
        """Display user's current messages"""
        try:
            state = UserPetMessageState.objects.filter(user=user).first()
            if not state:
                self.stdout.write("No message state found")
                return

            self.stdout.write("Current Available Messages:")
            self.stdout.write("-" * 30)

            if not state.available_messages:
                self.stdout.write("No messages available")
            else:
                for i, message in enumerate(state.available_messages, 1):
                    self.stdout.write(f"{i}. {message}")

            self.stdout.write("")

        except Exception as e:
            self.stdout.write(f"Error showing messages: {e}")

    def show_sms_preview(self, user: User):
        """Show SMS preview for user"""
        try:
            self.stdout.write("SMS Preview (Random per state):")
            self.stdout.write("-" * 30)

            messages = get_random_messages_per_state(user)
            if messages:
                sms_content = " | ".join(messages)
                self.stdout.write(f"SMS Content: {sms_content}")
                self.stdout.write(f"Message Count: {len(messages)}")
            else:
                self.stdout.write("No SMS messages available")

            self.stdout.write("")

        except Exception as e:
            self.stdout.write(f"Error showing SMS preview: {e}")

    def preview_sms_messages(self):
        """Preview daily SMS messages for all users"""
        try:
            from petcare.utils import get_all_users_for_sms, generate_daily_sms_content

            users = get_all_users_for_sms()

            self.stdout.write(f"SMS Preview for {users.count()} users:")
            self.stdout.write("=" * 50)

            for user in users:
                try:
                    sms_content = generate_daily_sms_content(user)
                    self.stdout.write(f"User: {user.username}")
                    self.stdout.write(f"Phone: {user.phone}")
                    self.stdout.write(f"SMS: {sms_content}")
                    self.stdout.write("-" * 40)
                except Exception as e:
                    self.stdout.write(f"Error for {user.username}: {e}")

        except Exception as e:
            raise CommandError(f'Error previewing SMS messages: {e}')

    def show_statistics(self):
        """Show system statistics"""
        try:
            # Template statistics
            total_templates = PetMessageTemplate.objects.count()
            active_templates = PetMessageTemplate.objects.filter(is_active=True).count()

            self.stdout.write("System Statistics")
            self.stdout.write("=" * 30)
            self.stdout.write(f"Total Templates: {total_templates}")
            self.stdout.write(f"Active Templates: {active_templates}")

            # By state breakdown
            self.stdout.write("\nTemplates by State:")
            # 更新状态列表，移除state5
            states = ['state1', 'state2', 'state3', 'state6', 'state7']
            for state in states:
                count = PetMessageTemplate.objects.filter(state_code=state).count()
                active_count = PetMessageTemplate.objects.filter(
                    state_code=state, is_active=True
                ).count()
                self.stdout.write(f"  {state}: {count} total ({active_count} active)")

            # User state statistics
            total_user_states = UserPetMessageState.objects.count()
            users_with_messages = UserPetMessageState.objects.exclude(
                available_messages=[]
            ).count()

            self.stdout.write(f"\nUser States: {total_user_states}")
            self.stdout.write(f"Users with Messages: {users_with_messages}")

            # Recent activity
            from django.utils import timezone
            from datetime import timedelta

            recent = timezone.localtime(timezone.now()) - timedelta(hours=24)
            recent_updates = UserPetMessageState.objects.filter(
                last_updated__gte=recent
            ).count()

            self.stdout.write(f"Updated in last 24h: {recent_updates}")

            # SMS statistics
            sms_users = User.objects.filter(
                couple__isnull=False,
                sms_opt_in=True,
                phone__isnull=False
            ).exclude(phone='').count()

            self.stdout.write(f"SMS-enabled users: {sms_users}")

        except Exception as e:
            raise CommandError(f'Error showing statistics: {e}')


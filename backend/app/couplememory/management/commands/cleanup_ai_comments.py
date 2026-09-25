"""
Django management command: Clean up AI comments mixed with user comments

Usage:
python manage.py cleanup_ai_comments
"""

from django.core.management.base import BaseCommand
from couplememory.models import MemoryComment


class Command(BaseCommand):
    help = 'Clean up incorrectly created AI comments, ensure AI analysis is stored only in AIJudgment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show data to be deleted without actually executing',
        )

    def handle(self, *args, **options):
        # Find all comments starting with robot emoji (these should be incorrectly created AI comments)
        ai_comments = MemoryComment.objects.filter(content__startswith='🤖')
        
        self.stdout.write(f'Found {ai_comments.count()} incorrectly created AI comments')
        
        if ai_comments.exists():
            self.stdout.write('\nAI comments to be cleaned:')
            for comment in ai_comments:
                self.stdout.write(f'  Entry #{comment.entry.id}: {comment.content[:60]}...')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\nDry run mode: No data actually deleted'))
        else:
            deleted_count = ai_comments.count()
            ai_comments.delete()
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully cleaned {deleted_count} incorrectly created AI comments')
            )
            self.stdout.write('AI analysis data remains preserved in AIJudgment records for each Entry')

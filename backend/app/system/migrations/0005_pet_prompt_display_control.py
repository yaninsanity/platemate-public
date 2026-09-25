# Generated migration for pet prompt display control

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0004_analytics_dashboard_toggle'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemconfig',
            name='pet_prompt_display_seconds',
            field=models.PositiveIntegerField(
                default=60,
                help_text='Pet message display duration in seconds. Default: 60s (1 minute).'
            ),
        ),
    ]

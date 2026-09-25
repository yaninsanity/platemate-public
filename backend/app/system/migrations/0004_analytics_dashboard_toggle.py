# Generated migration for adding analytics tracking toggle

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0003_reward_cooldown_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemconfig',
            name='enable_analytics_tracking',
            field=models.BooleanField(
                default=True,
                help_text='Enable analytics event tracking. When disabled, no events will be collected.'
            ),
        ),
    ]

# Generated migration for adding reward cooldown configuration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0002_systemconfig_nice_guy_card_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemconfig',
            name='enable_reward_cooldown',
            field=models.BooleanField(
                default=False,
                help_text='Enable the reward cooldown. Off means rewards can be claimed without limit, which suits development and testing.'
            ),
        ),
        migrations.AddField(
            model_name='systemconfig',
            name='reward_cooldown_hours',
            field=models.PositiveIntegerField(
                default=2,
                help_text='Reward cooldown in hours. Applies only when enable_reward_cooldown=True时生效。'
            ),
        ),
    ]

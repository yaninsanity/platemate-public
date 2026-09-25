# Generated migration for adding nice_guy_card_mode field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemconfig',
            name='nice_guy_card_mode',
            field=models.BooleanField(
                default=False,
                help_text='启用"好人卡"mode: rescale AI scores into an encouraging 80-100 band. Off means the raw 0-100 score.'
            ),
        ),
    ]

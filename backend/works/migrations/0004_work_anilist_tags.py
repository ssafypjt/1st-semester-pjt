# Generated manually — adds AniList tags cache field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('works', '0003_alter_work_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='work',
            name='anilist_tags',
            field=models.JSONField(
                'AniList 태그 캐시',
                default=None,
                null=True,
                blank=True,
            ),
        ),
    ]

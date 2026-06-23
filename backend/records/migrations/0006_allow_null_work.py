"""Record.work를 nullable로 변경 — AniList에서 선택하지 않은 기록도 허용."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0005_record_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='work',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='records',
                to='works.work',
            ),
        ),
    ]

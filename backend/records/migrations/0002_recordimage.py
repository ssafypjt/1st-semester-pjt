"""RecordImage 모델 추가.

수동으로 작성한 마이그레이션. 실제로 적용하려면:
    python manage.py migrate records
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import records.models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RecordImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('file', models.ImageField(max_length=500,
                                           upload_to=records.models.record_image_upload_to,
                                           verbose_name='파일')),
                ('original_name', models.CharField(blank=True, max_length=255,
                                                   verbose_name='원본 파일명')),
                ('size', models.PositiveIntegerField(default=0,
                                                      verbose_name='파일 크기(바이트)')),
                ('created_at', models.DateTimeField(auto_now_add=True,
                                                    verbose_name='업로드 시각')),
                ('record', models.ForeignKey(blank=True, null=True,
                                              on_delete=django.db.models.deletion.SET_NULL,
                                              related_name='images',
                                              to='records.record',
                                              verbose_name='연결된 기록')),
                ('uploader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                related_name='uploaded_images',
                                                to=settings.AUTH_USER_MODEL,
                                                verbose_name='업로더')),
            ],
            options={
                'db_table': 'record_image',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['uploader', '-created_at'],
                                 name='ri_uploader_created_idx'),
                ],
            },
        ),
    ]

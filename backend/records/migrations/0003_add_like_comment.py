"""Like / Comment 모델 추가.

수동으로 작성한 마이그레이션. 실제로 적용하려면:
    python manage.py migrate records
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0002_recordimage'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True,
                                                     verbose_name='좋아요 일시')),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='likes',
                                              to='records.record')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                            related_name='record_likes',
                                            to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'record_like',
            },
        ),
        migrations.AddIndex(
            model_name='like',
            index=models.Index(fields=['record', '-created_at'], name='like_record_idx'),
        ),
        migrations.AddIndex(
            model_name='like',
            index=models.Index(fields=['user', '-created_at'], name='like_user_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='like',
            unique_together={('record', 'user')},
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='내용')),
                ('created_at', models.DateTimeField(auto_now_add=True,
                                                     verbose_name='작성일')),
                ('updated_at', models.DateTimeField(auto_now=True,
                                                     verbose_name='수정일')),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='comments',
                                              to='records.record')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                            related_name='record_comments',
                                            to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'record_comment',
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['record', 'created_at'], name='comment_record_idx'),
        ),
    ]

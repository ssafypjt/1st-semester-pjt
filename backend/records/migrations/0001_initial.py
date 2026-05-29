import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('works', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, verbose_name='평점')),
                ('watched_date', models.DateField(blank=True, null=True, verbose_name='감상일')),
                ('content', models.TextField(blank=True, verbose_name='감상문')),
                ('canvas_data', models.JSONField(blank=True, default=dict, verbose_name='캔버스 설정')),
                ('status', models.CharField(choices=[('draft', '임시저장'), ('published', '게시됨'), ('archived', '보관')], default='published', max_length=20, verbose_name='상태')),
                ('visibility', models.CharField(choices=[('public', '전체 공개'), ('friends', '친구 공개'), ('private', '비공개')], default='public', max_length=20, verbose_name='공개 범위')),
                ('like_count', models.IntegerField(default=0, verbose_name='좋아요 수')),
                ('comment_count', models.IntegerField(default=0, verbose_name='댓글 수')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
                ('work', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='records', to='works.work')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'record',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FavoriteScene',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_url', models.URLField(max_length=500)),
                ('order_index', models.IntegerField(default=0)),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite_scenes', to='records.record')),
            ],
            options={
                'db_table': 'favorite_scene',
                'ordering': ['order_index'],
            },
        ),
        migrations.CreateModel(
            name='Decoration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('sticker', '스티커'), ('text', '텍스트'), ('image', '이미지'), ('gif', 'GIF'), ('frame', '프레임'), ('tape', '테이프')], max_length=20)),
                ('content', models.TextField(blank=True)),
                ('position_x', models.FloatField(default=0)),
                ('position_y', models.FloatField(default=0)),
                ('width', models.FloatField(default=100)),
                ('height', models.FloatField(default=100)),
                ('rotation', models.FloatField(default=0)),
                ('z_index', models.IntegerField(default=0)),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='decorations', to='records.record')),
            ],
            options={
                'db_table': 'decoration',
                'ordering': ['z_index'],
            },
        ),
    ]

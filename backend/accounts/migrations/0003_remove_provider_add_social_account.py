"""
User 모델에서 provider/provider_id 컬럼 제거,
SocialAccount 테이블 신규 생성 (1계정 N소셜 연동 지원).
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_profile_image'),
    ]

    operations = [
        # 1. User 테이블에서 provider, provider_id 제거
        migrations.RemoveField(
            model_name='user',
            name='provider',
        ),
        migrations.RemoveField(
            model_name='user',
            name='provider_id',
        ),

        # 2. SocialAccount 테이블 생성
        migrations.CreateModel(
            name='SocialAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(
                    choices=[('google', 'Google'), ('kakao', 'Kakao'), ('apple', 'Apple')],
                    max_length=20,
                    verbose_name='소셜 제공자',
                )),
                ('provider_id', models.CharField(max_length=255, verbose_name='소셜 고유 ID')),
                ('access_token', models.TextField(blank=True, null=True, verbose_name='액세스 토큰')),
                ('refresh_token', models.TextField(blank=True, null=True, verbose_name='리프레시 토큰')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='연동일')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='social_accounts',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='사용자',
                )),
            ],
            options={
                'db_table': 'social_account',
                'unique_together': {('provider', 'provider_id')},
            },
        ),
    ]

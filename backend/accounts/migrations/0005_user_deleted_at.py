"""User.deleted_at 추가 (회원 탈퇴 soft delete).

수동으로 작성한 마이그레이션. 실제로 적용하려면:
    python manage.py migrate accounts
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_follow_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='탈퇴일'),
        ),
    ]

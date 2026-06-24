"""profile_image: URLField → ImageField (로컬 업로드 지원)."""
import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=accounts.models.profile_image_upload_to,
                verbose_name='프로필 이미지',
            ),
        ),
    ]

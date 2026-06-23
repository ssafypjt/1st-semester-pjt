from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0004_stickerasset_usersticker'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='title',
            field=models.CharField('기록 제목', max_length=200, blank=True, default=''),
        ),
    ]

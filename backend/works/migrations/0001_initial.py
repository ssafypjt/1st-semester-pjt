from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('work_type', models.CharField(
                    choices=[('anime', '애니메이션'), ('movie', '영화'), ('book', '도서'),
                             ('game', '게임'), ('drama', '드라마'), ('other', '기타')],
                    default='anime', max_length=20, verbose_name='작품 유형',
                )),
                ('external_id', models.CharField(blank=True, max_length=100, verbose_name='외부 API 작품 ID')),
                ('source', models.CharField(blank=True, help_text='AniList / TMDB / Google Books 등', max_length=30, verbose_name='출처')),
                ('title', models.CharField(max_length=255, verbose_name='제목')),
                ('title_ko', models.CharField(blank=True, max_length=255, verbose_name='한국어 제목')),
                ('title_en', models.CharField(blank=True, max_length=255, verbose_name='영어 제목')),
                ('release_date', models.DateField(blank=True, null=True, verbose_name='공개일')),
                ('genre', models.CharField(blank=True, max_length=100, verbose_name='장르')),
                ('poster_image', models.URLField(blank=True, max_length=500, verbose_name='포스터 URL')),
                ('description', models.TextField(blank=True, verbose_name='작품 설명')),
            ],
            options={
                'db_table': 'work',
                'ordering': ['-release_date', 'title'],
            },
        ),
    ]

"""Work 모델 — 작품 메타데이터.

애니메이션뿐 아니라 영화·도서·게임 등 다양한 콘텐츠 유형을 포괄한다.
work_type 필드로 유형을 구분하며, 외부 API(AniList / TMDB / Google Books 등)
연동은 2단계에서 source + external_id 기반으로 처리한다.
"""
from django.db import models


class Work(models.Model):
    TYPE_CHOICES = [
        ('anime', '애니메이션'),
        ('movie', '영화'),
        ('book', '도서'),
        ('game', '게임'),
        ('drama', '드라마'),
        ('other', '기타'),
    ]

    work_type = models.CharField('작품 유형', max_length=20,
                                 choices=TYPE_CHOICES, default='anime')
    external_id = models.CharField('외부 API 작품 ID', max_length=100, blank=True)
    source = models.CharField('출처', max_length=30, blank=True,
                              help_text='AniList / TMDB / Google Books 등')
    title = models.CharField('제목', max_length=255)
    title_ko = models.CharField('한국어 제목', max_length=255, blank=True)
    title_en = models.CharField('영어 제목', max_length=255, blank=True)
    release_date = models.DateField('공개일', null=True, blank=True)
    genre = models.CharField('장르', max_length=100, blank=True)
    poster_image = models.URLField('포스터 URL', max_length=500, blank=True)
    description = models.TextField('작품 설명', blank=True)

    class Meta:
        db_table = 'work'
        ordering = ['-release_date', 'title']

    def __str__(self):
        return self.title_ko or self.title

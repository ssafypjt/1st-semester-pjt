"""Anime 모델 (ERD) - 작품 메타데이터."""
from django.db import models


class Anime(models.Model):
    external_id = models.CharField('외부 API 작품 ID', max_length=100, blank=True)
    source = models.CharField('출처', max_length=30, blank=True,
                              help_text='AniList / MAL 등')
    title = models.CharField('제목', max_length=255)
    title_ko = models.CharField('한국어 제목', max_length=255, blank=True)
    title_en = models.CharField('영어 제목', max_length=255, blank=True)
    release_date = models.DateField('공개일', null=True, blank=True)
    genre = models.CharField('장르', max_length=100, blank=True)
    poster_image = models.URLField('포스터 URL', max_length=500, blank=True)
    description = models.TextField('작품 설명', blank=True)

    class Meta:
        db_table = 'anime'
        ordering = ['-release_date', 'title']

    def __str__(self):
        return self.title_ko or self.title

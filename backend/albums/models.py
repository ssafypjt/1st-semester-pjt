"""Album, Album_Record (M:N) 모델 - ERD."""
from django.conf import settings
from django.db import models

from works.validators import validate_poster_url as validate_cover_url


class Album(models.Model):
    VISIBILITY_CHOICES = [
        ('public', '전체 공개'),
        ('friends', '친구 공개'),
        ('private', '비공개'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='albums',
        verbose_name='생성자',
    )
    name = models.CharField('앨범명', max_length=100)
    description = models.TextField('앨범 설명', blank=True)
    cover_image = models.URLField('커버 이미지 URL', max_length=500, blank=True,
                                  validators=[validate_cover_url])
    visibility = models.CharField('공개 범위', max_length=20,
                                  choices=VISIBILITY_CHOICES, default='private')
    created_at = models.DateTimeField('생성일', auto_now_add=True)

    # M:N: records와의 연결은 AlbumRecord through 사용
    records = models.ManyToManyField(
        'records.Record',
        through='AlbumRecord',
        related_name='albums',
    )

    class Meta:
        db_table = 'album'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.user.nickname})'


class AlbumRecord(models.Model):
    """ERD: Album_Record - M:N 중간 테이블."""
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    record = models.ForeignKey('records.Record', on_delete=models.CASCADE)
    added_at = models.DateTimeField('추가된 시각', auto_now_add=True)

    class Meta:
        db_table = 'album_record'
        unique_together = [('album', 'record')]
        ordering = ['-added_at']

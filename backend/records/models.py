"""
Record 모델 (ERD - 중심 콘텐츠).

- canvas_data: JSON (배경/필터/테마/BGM)
- 좋아요·댓글 카운트는 캐싱 컬럼 (비정규화)
- 2단계 (Decoration, Favorite_Scene) 도 함께 정의해두지만
  MVP에서는 사용 안 해도 됩니다.
- RecordImage: 사용자가 다꾸용으로 업로드한 이미지. 업로더 본인만 접근 가능
  (배포 정책). 이미지 자체의 URL 노출은 protected view 가 담당한다.
"""
import os
import uuid

from django.conf import settings
from django.db import models


def record_image_upload_to(instance, filename):
    """업로드된 파일을 uploads/<uploader_id>/<uuid>.<ext> 로 정리."""
    ext = os.path.splitext(filename)[1].lower()
    return f'uploads/{instance.uploader_id}/{uuid.uuid4().hex}{ext}'


class Record(models.Model):
    STATUS_CHOICES = [
        ('draft', '임시저장'),
        ('published', '게시됨'),
        ('archived', '보관'),
    ]
    VISIBILITY_CHOICES = [
        ('public', '전체 공개'),
        ('friends', '친구 공개'),
        ('private', '비공개'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='records',
    )
    anime = models.ForeignKey(
        'animes.Anime',
        on_delete=models.PROTECT,
        related_name='records',
    )
    rating = models.DecimalField('평점', max_digits=3, decimal_places=1,
                                 null=True, blank=True)
    watched_date = models.DateField('감상일', null=True, blank=True)
    content = models.TextField('감상문', blank=True)
    canvas_data = models.JSONField('캔버스 설정', default=dict, blank=True)
    status = models.CharField('상태', max_length=20,
                              choices=STATUS_CHOICES, default='published')
    visibility = models.CharField('공개 범위', max_length=20,
                                  choices=VISIBILITY_CHOICES, default='public')
    like_count = models.IntegerField('좋아요 수', default=0)
    comment_count = models.IntegerField('댓글 수', default=0)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        db_table = 'record'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.anime} - {self.user.nickname}'


class RecordImage(models.Model):
    """다꾸 캔버스용으로 업로드된 이미지.

    - 한 유저가 작성 중 여러 장 업로드해도 모두 행으로 추적된다.
    - record 는 처음 업로드 시점에는 null. 기록이 저장될 때 연결한다.
    - 권한 정책: uploader == request.user 인 경우에만 파일 응답.
    """
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_images',
        verbose_name='업로더',
    )
    record = models.ForeignKey(
        'records.Record',
        on_delete=models.SET_NULL,
        related_name='images',
        null=True, blank=True,
        verbose_name='연결된 기록',
    )
    file = models.ImageField('파일', upload_to=record_image_upload_to,
                             max_length=500)
    original_name = models.CharField('원본 파일명', max_length=255, blank=True)
    size = models.PositiveIntegerField('파일 크기(바이트)', default=0)
    created_at = models.DateTimeField('업로드 시각', auto_now_add=True)

    class Meta:
        db_table = 'record_image'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uploader', '-created_at'],
                         name='ri_uploader_created_idx'),
        ]

    def __str__(self):
        return f'RecordImage<{self.id} by {self.uploader_id}>'


class Decoration(models.Model):
    """다꾸 캔버스 위의 개별 요소 (2단계)."""
    TYPE_CHOICES = [
        ('sticker', '스티커'),
        ('text', '텍스트'),
        ('image', '이미지'),
        ('gif', 'GIF'),
        ('frame', '프레임'),
        ('tape', '테이프'),
    ]

    record = models.ForeignKey(Record, on_delete=models.CASCADE,
                               related_name='decorations')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    content = models.TextField(blank=True)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    width = models.FloatField(default=100)
    height = models.FloatField(default=100)
    rotation = models.FloatField(default=0)
    z_index = models.IntegerField(default=0)

    class Meta:
        db_table = 'decoration'
        ordering = ['z_index']


class FavoriteScene(models.Model):
    """명장면 (2단계)."""
    record = models.ForeignKey(Record, on_delete=models.CASCADE,
                               related_name='favorite_scenes')
    image_url = models.URLField(max_length=500)
    order_index = models.IntegerField(default=0)

    class Meta:
        db_table = 'favorite_scene'
        ordering = ['order_index']

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
    work = models.ForeignKey(
        'works.Work',
        on_delete=models.PROTECT,
        related_name='records',
        null=True, blank=True,
    )
    title = models.CharField('기록 제목', max_length=200, blank=True, default='')
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
        return f'{self.work} - {self.user.nickname}'


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


def sticker_upload_to(instance, filename):
    """스티커 이미지를 stickers/<uuid>.<ext> 로 저장."""
    ext = os.path.splitext(filename)[1].lower()
    return f'stickers/{uuid.uuid4().hex}{ext}'


class StickerAsset(models.Model):
    """어드민이 등록하는 스티커 원본 에셋."""
    CATEGORY_CHOICES = [
        ('sticker', '스티커'),
        ('frame', '프레임'),
        ('bubble', '말풍선'),
    ]

    name = models.CharField('스티커명', max_length=100)
    category = models.CharField('카테고리', max_length=20,
                                choices=CATEGORY_CHOICES, default='sticker')
    image = models.ImageField('이미지', upload_to=sticker_upload_to)
    emoji_fallback = models.CharField('이모지 대체', max_length=10, blank=True,
                                      help_text='이미지 없이 이모지로 표시할 경우')
    tone = models.CharField('CSS 톤 클래스', max_length=50, blank=True)
    is_default = models.BooleanField('기본 제공', default=False,
                                     help_text='True면 신규 가입 유저에게 자동 부여')
    is_active = models.BooleanField('활성화', default=True)
    order = models.IntegerField('정렬 순서', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sticker_asset'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.name} ({self.get_category_display()})'


class UserSticker(models.Model):
    """유저별 보유 스티커."""
    ACQUIRE_CHOICES = [
        ('default', '기본 제공'),
        ('reward', '보상'),
        ('purchase', '구매'),
        ('event', '이벤트'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stickers',
    )
    sticker = models.ForeignKey(
        StickerAsset,
        on_delete=models.CASCADE,
        related_name='owners',
    )
    acquired_type = models.CharField('획득 방법', max_length=20,
                                     choices=ACQUIRE_CHOICES, default='default')
    acquired_at = models.DateTimeField('획득일', auto_now_add=True)

    class Meta:
        db_table = 'user_sticker'
        unique_together = [('user', 'sticker')]
        ordering = ['sticker__order', 'sticker__id']

    def __str__(self):
        return f'{self.user_id} owns {self.sticker.name}'


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


class Like(models.Model):
    """기록에 대한 좋아요.

    - (record, user) 유니크: 토글 방식 (있으면 취소, 없으면 생성).
    - Record.like_count 는 캐시 컬럼이므로 토글 시 view 에서 갱신한다.
    """
    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='record_likes',
    )
    created_at = models.DateTimeField('좋아요 일시', auto_now_add=True)

    class Meta:
        db_table = 'record_like'
        unique_together = [('record', 'user')]
        indexes = [
            models.Index(fields=['record', '-created_at'], name='like_record_idx'),
            models.Index(fields=['user', '-created_at'], name='like_user_idx'),
        ]

    def __str__(self):
        return f'{self.user_id} likes record {self.record_id}'


class Comment(models.Model):
    """기록에 대한 댓글 (1차 구현).

    - 1차: 단일 depth (대댓글 없음), 수정/삭제 권한·페이지네이션 등은
      후속 작업으로 PROJECT_CONTEXT.md 에 기록.
    """
    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='record_comments',
    )
    content = models.TextField('내용')
    created_at = models.DateTimeField('작성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        db_table = 'record_comment'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['record', 'created_at'], name='comment_record_idx'),
        ]

    def __str__(self):
        return f'Comment<{self.id} on record {self.record_id}>'

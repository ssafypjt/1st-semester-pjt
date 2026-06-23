"""
공유 카드 모델.

- CardTemplate: 미리 준비된 카드 배경/프레임 템플릿
- ShareCard: Record 기반으로 AI가 생성한 공유 카드 이미지
"""
import os
import uuid

from django.conf import settings
from django.db import models


def share_card_upload_to(instance, filename):
    """공유 카드 이미지를 uploads/shares/<user_id>/<uuid>.png 로 저장."""
    ext = os.path.splitext(filename)[1].lower() or '.png'
    return f'uploads/shares/{instance.record.user_id}/{uuid.uuid4().hex}{ext}'


class CardTemplate(models.Model):
    """미리 준비된 카드 디자인 템플릿.

    AI가 record 내용을 분석해서 적절한 템플릿을 선택하고,
    그 위에 텍스트/이미지를 배치한다.
    """
    CATEGORY_CHOICES = [
        ('minimal', '미니멀'),
        ('emotional', '감성'),
        ('retro', '레트로'),
        ('cute', '큐트'),
        ('dark', '다크'),
    ]

    name = models.CharField('템플릿명', max_length=100)
    category = models.CharField('카테고리', max_length=20, choices=CATEGORY_CHOICES)
    thumbnail = models.URLField('썸네일 URL', max_length=500, blank=True)
    background_image = models.URLField('배경 이미지 URL', max_length=500, blank=True)
    # 템플릿의 레이아웃 정보 (슬롯 위치, 텍스트 영역 등)
    layout_schema = models.JSONField(
        '레이아웃 스키마', default=dict,
        help_text='텍스트/이미지 슬롯의 위치·크기 정의 JSON',
    )
    # AI 프롬프트에서 이 템플릿을 설명할 때 쓰는 문장
    description_for_ai = models.TextField(
        'AI 설명문', blank=True,
        help_text='AI가 템플릿 선택 시 참고할 설명',
    )
    is_active = models.BooleanField('활성화', default=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)

    class Meta:
        db_table = 'card_template'
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} [{self.category}]'


class ShareCard(models.Model):
    """AI가 생성한 공유 카드.

    - record: 원본 감상 기록 (1 Record → N ShareCard, 재생성 가능)
    - template: 사용된 카드 템플릿
    - layout_data: AI가 결정한 최종 배치 정보 (JSON)
    - image: 렌더링된 최종 이미지 파일
    """
    record = models.ForeignKey(
        'records.Record',
        on_delete=models.CASCADE,
        related_name='share_cards',
        verbose_name='원본 기록',
    )
    template = models.ForeignKey(
        CardTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='share_cards',
        verbose_name='사용된 템플릿',
    )
    # AI가 결정한 레이아웃 (텍스트 위치, 폰트, 색상, 이미지 배치 등)
    layout_data = models.JSONField(
        'AI 배치 데이터', default=dict,
        help_text='AI가 반환한 레이아웃 JSON',
    )
    # 최종 렌더링된 이미지
    image = models.ImageField(
        '공유 카드 이미지',
        upload_to=share_card_upload_to,
        blank=True,
    )
    # AI 요청/응답 메타데이터 (디버깅 용)
    ai_model = models.CharField('사용된 AI 모델', max_length=50, blank=True)
    ai_prompt_tokens = models.IntegerField('프롬프트 토큰 수', default=0)
    ai_response_tokens = models.IntegerField('응답 토큰 수', default=0)

    created_at = models.DateTimeField('생성일', auto_now_add=True)

    class Meta:
        db_table = 'share_card'
        ordering = ['-created_at']

    def __str__(self):
        return f'ShareCard<{self.id}> for Record<{self.record_id}>'

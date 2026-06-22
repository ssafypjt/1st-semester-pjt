"""공유 카드 생성 / 조회 / 이미지 서빙 views."""
import logging

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from records.models import Record
from .models import CardTemplate, ShareCard
from .prompts import build_card_prompt
from .renderer import render_card
from .serializers import (CardTemplateSerializer, ShareCardCreateSerializer,
                          ShareCardSerializer)
from .services import GMSClient, GMSError

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_share_card(request, record_id):
    """공유 카드 생성.

    POST /api/shares/<record_id>/generate/

    1. Record 조회 (본인 기록만)
    2. 활성 템플릿 목록 조회
    3. AI에게 프롬프트 전송 → 레이아웃 JSON 수신
    4. Pillow로 이미지 렌더링
    5. ShareCard 저장 후 반환
    """
    # 1) 본인 기록 조회
    record = get_object_or_404(
        Record.objects.select_related('work', 'user'),
        pk=record_id,
        user=request.user,
    )

    # 요청 데이터 검증
    serializer = ShareCardCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    template_id = serializer.validated_data.get('template_id')

    # 2) 사용 가능한 템플릿 목록
    templates = CardTemplate.objects.filter(is_active=True)
    if template_id:
        templates = templates.filter(pk=template_id)

    if not templates.exists():
        return Response(
            {'detail': '사용 가능한 카드 템플릿이 없습니다.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 2-b) 사용자 다이어리 스티커 (canvas_data.placedItems)
    canvas_data = record.canvas_data or {}
    placed_items = canvas_data.get('placedItems', []) if isinstance(canvas_data, dict) else []

    # 3) AI 프롬프트 조립 & 호출
    prompt = build_card_prompt(record, templates, placed_items=placed_items)

    try:
        client = GMSClient()
        layout_data = client.generate_card_layout(prompt)
    except GMSError as e:
        logger.error('공유 카드 AI 생성 실패 (record=%s): %s', record_id, e)
        return Response(
            {'detail': f'AI 카드 생성 실패: {e}'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # 메타데이터 분리
    meta = layout_data.pop('_meta', {})

    # 선택된 템플릿 찾기
    selected_template_id = layout_data.get('template_id')
    template = None
    if selected_template_id:
        template = CardTemplate.objects.filter(
            pk=selected_template_id, is_active=True
        ).first()

    # 4) 이미지 렌더링
    try:
        background_url = template.background_image if template else ''
        poster_url = record.work.poster_image or ''

        # 스티커 중 이미지 URL이 있는 것만 필터
        sticker_items = [
            item for item in placed_items
            if item.get('type') == 'sticker' and item.get('src')
        ]

        image_buf = render_card(
            layout_data,
            poster_url=poster_url,
            background_url=background_url,
            stickers=sticker_items,
        )
    except Exception as e:
        logger.error('공유 카드 렌더링 실패 (record=%s): %s', record_id, e)
        return Response(
            {'detail': f'카드 이미지 렌더링 실패: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 5) ShareCard 저장
    share_card = ShareCard.objects.create(
        record=record,
        template=template,
        layout_data=layout_data,
        ai_model=meta.get('model', ''),
        ai_prompt_tokens=meta.get('prompt_tokens', 0),
        ai_response_tokens=meta.get('completion_tokens', 0),
    )

    # 이미지 파일 저장
    filename = f'share_card_{share_card.id}.png'
    share_card.image.save(filename, ContentFile(image_buf.read()), save=True)

    return Response(
        ShareCardSerializer(share_card, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_share_cards(request, record_id):
    """특정 기록의 공유 카드 목록.

    GET /api/shares/<record_id>/
    """
    record = get_object_or_404(Record, pk=record_id, user=request.user)
    cards = ShareCard.objects.filter(record=record).select_related('template')
    serializer = ShareCardSerializer(cards, many=True,
                                     context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def share_card_detail(request, card_id):
    """공유 카드 단건 조회 (공유 링크용 — 비로그인도 접근 가능).

    GET /api/shares/card/<card_id>/
    """
    card = get_object_or_404(
        ShareCard.objects.select_related('template', 'record__work', 'record__user'),
        pk=card_id,
    )
    return Response(ShareCardSerializer(card, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_templates(request):
    """활성 카드 템플릿 목록.

    GET /api/shares/templates/
    """
    templates = CardTemplate.objects.filter(is_active=True)
    serializer = CardTemplateSerializer(templates, many=True)
    return Response(serializer.data)

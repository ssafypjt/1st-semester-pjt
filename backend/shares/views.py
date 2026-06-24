"""공유 카드 생성 / 조회 / 이미지 서빙 views."""
import logging
import os
import re

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from django.conf import settings
from records.models import Record, RecordImage
from .models import CardTemplate, ShareCard
from .prompts import build_content_prompt, build_card_prompt
from .renderer import render_card
from .serializers import (CardTemplateSerializer, ShareCardCreateSerializer,
                          ShareCardSerializer)
from .services import GMSClient, GMSError

logger = logging.getLogger(__name__)

# 프론트엔드 기본 스티커 이미지 경로 매핑
_FRONTEND_ASSET_DIR = os.path.join(
    settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'images'
)


def _resolve_image_path(url: str) -> str | None:
    """상대 URL을 로컬 파일 경로로 변환한다.

    - /api/records/uploads/<id>/ → RecordImage.file.path
    - /static/src/assets/images/... → frontend 소스 경로
    """

    # 1) /api/records/uploads/<id>/
    m = re.match(r'/api/records/uploads/(\d+)/', url)
    if m:
        try:
            ri = RecordImage.objects.get(pk=int(m.group(1)))
            return ri.file.path
        except (RecordImage.DoesNotExist, ValueError):
            return None

    # 2) /static/src/assets/images/...
    if '/assets/images/' in url:
        filename = url.split('/assets/images/')[-1]
        candidate = os.path.join(_FRONTEND_ASSET_DIR, filename)
        if os.path.isfile(candidate):
            return candidate

    return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_share_card(request, record_id):
    """공유 카드 생성 — 2단계 AI 파이프라인.

    POST /api/shares/<record_id>/generate/

    1. Record 조회 (본인 기록만)
    2. 다이어리 데이터 추출 (메모 + 말풍선 + 감상평)
    3. Stage 1: 콘텐츠 생성 AI (텍스트 요약/생성)
    4. Stage 2: 배치 AI (mood·tags·제목 결정)
    5. Pillow로 이미지 렌더링
    6. ShareCard 저장 후 반환
    """
    # 1) 본인 기록 조회
    record = get_object_or_404(
        Record.objects.select_related('work', 'user'),
        pk=record_id,
        user=request.user,
    )

    # 2) 사용자 다이어리 데이터 추출
    canvas_data = record.canvas_data or {}
    placed_items = (
        canvas_data.get('placed_items')
        or canvas_data.get('placedItems')
        or []
    ) if isinstance(canvas_data, dict) else []

    try:
        client = GMSClient()

        # 3) Stage 1 — 콘텐츠 생성 (메모·말풍선·감상평 종합)
        content_prompt = build_content_prompt(record, placed_items=placed_items)
        stage1_result = client.generate_content(content_prompt)
        stage1_meta = stage1_result.pop('_meta', {})

        # 4) Stage 2 — 배치 (작품 정보 + Stage 1 결과 → 최종 카드 데이터)
        card_prompt = build_card_prompt(record, stage1_result,
                                        placed_items=placed_items)
        layout_data = client.generate_card_layout(card_prompt)

    except GMSError as e:
        logger.error('공유 카드 AI 생성 실패 (record=%s): %s', record_id, e)
        return Response(
            {'detail': f'AI 카드 생성 실패: {e}'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # 메타데이터 분리 (Stage 2 기준, Stage 1 토큰도 합산)
    meta = layout_data.pop('_meta', {})
    meta['prompt_tokens'] = (meta.get('prompt_tokens', 0)
                             + stage1_meta.get('prompt_tokens', 0))
    meta['completion_tokens'] = (meta.get('completion_tokens', 0)
                                 + stage1_meta.get('completion_tokens', 0))

    # 날짜 보강
    if record.watched_date and not layout_data.get('date'):
        layout_data['date'] = str(record.watched_date).replace('-', '.')

    # 레이팅 보강
    if record.rating and not layout_data.get('rating'):
        layout_data['rating'] = f'{record.rating} / 10'

    # 4) 이미지 렌더링
    try:
        poster_url = (record.work.poster_image if record.work else '') or ''

        # sticker_items: 메인 이미지용 / deco_stickers: 장식 스티커용
        sticker_items = []
        deco_stickers = []
        for item in placed_items:
            if item.get('type', 'sticker') in ('text',):
                continue
            item = dict(item)
            img_src = item.get('imageSrc') or ''
            if img_src:
                local = _resolve_image_path(img_src)
                if local:
                    item['_local_path'] = local
            # 사용자 업로드 이미지는 메인용, 나머지는 데코용
            if '/api/records/uploads/' in img_src:
                sticker_items.append(item)
            elif img_src:
                deco_stickers.append(item)

        if poster_url and poster_url.startswith('/'):
            local_poster = _resolve_image_path(poster_url)
            if local_poster:
                poster_url = local_poster

        image_buf = render_card(
            layout_data,
            poster_url=poster_url,
            stickers=sticker_items,
            deco_stickers=deco_stickers,
        )
    except Exception as e:
        logger.error('공유 카드 렌더링 실패 (record=%s): %s', record_id, e)
        return Response(
            {'detail': f'카드 이미지 렌더링 실패: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 5) ShareCard 저장
    template = None
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

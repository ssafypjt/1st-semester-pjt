"""
공유 카드 생성을 위한 프롬프트 조립 모듈 v2.

Record 데이터 + CardTemplate 목록 → AI 프롬프트를 조립한다.
AI는 4존 구조(헤더/콜라주/메모/정보) 범위 안에서 자유롭게 배치를 결정한다.
"""
import json


def build_card_prompt(record, templates, placed_items=None) -> str:
    """Record + 템플릿 목록으로 AI 프롬프트를 생성한다.

    Args:
        record: Record 인스턴스 (select_related('work', 'user') 필수)
        templates: CardTemplate QuerySet (is_active=True)
        placed_items: 사용자 다이어리의 placedItems 리스트 (스티커 정보)

    Returns:
        AI에게 보낼 유저 프롬프트 문자열
    """
    work = record.work
    placed_items = placed_items or []

    # 1) 감상 기록 데이터
    if work:
        work_info = {
            'title': work.title_ko or work.title,
            'title_en': work.title_en,
            'genre': work.genre,
            'poster_url': work.poster_image,
        }
    else:
        work_info = {
            'title': record.title or '제목 없음',
            'title_en': '',
            'genre': '',
            'poster_url': '',
        }
    record_data = {
        'record_id': record.id,
        'work': work_info,
        'rating': str(record.rating) if record.rating else None,
        'watched_date': str(record.watched_date) if record.watched_date else None,
        'content': record.content[:500] if record.content else '',
        'tags': _extract_tags(record),
        'sticker_count': len([i for i in placed_items if i.get('type', 'sticker') not in ('text',)]),
        'stickers': _summarize_stickers(placed_items),
    }

    # 2) 감상문 처리 안내
    content_text = record.content.strip() if record.content else ''
    if len(content_text) <= 20:
        memo_instruction = f'감상문이 짧으므로 원문 그대로 사용: "{content_text}"'
    elif content_text:
        memo_instruction = f'감상문이 길므로 핵심 1~2문장으로 발췌 요약해줘. 원문: "{content_text[:300]}"'
    else:
        memo_instruction = '감상문이 없으므로 memo.text를 빈 문자열로 설정해줘.'

    # 3) 템플릿 목록
    template_list = [
        {
            'id': t.id,
            'name': t.name,
            'category': t.category,
            'description': t.description_for_ai,
            'layout_schema': t.layout_schema,
        }
        for t in templates
    ]

    # 4) 프롬프트 조립
    prompt = f"""아래 감상 기록을 분석해서 공유 카드 레이아웃 JSON을 생성해줘.

## 핵심 디자인 철학
사용자가 업로드한 이미지(is_main_image: true)가 카드의 **주인공**.
포스터(작품 커버)는 작은 폴라로이드로 곁들이는 보조 요소.
스티커·말풍선은 이미지를 꾸며주는 역할.

## 감상 기록
{json.dumps(record_data, ensure_ascii=False, indent=2)}

## 사용 가능한 템플릿
{json.dumps(template_list, ensure_ascii=False, indent=2)}

## 감상문 처리
{memo_instruction}

## 배치 규칙
카드는 1080×1920px, 4개 존으로 나뉜다.

### Zone 1 — 헤더 (y: 0~140)
- 날짜를 좌측에 배치. 우측 x=800 이후는 로고 자동 삽입.

### Zone 2 — 메인 이미지 + 포스터 (y: 140~1200)
이 영역의 **주인공은 사용자 이미지**(is_main_image: true).

#### ★ 메인 이미지 (is_main_image: true) — 주인공
- Zone 2 전체를 **최대한 크게** 차지 (최소 width 600, height 500).
- 여러 장이면 Zone 2를 나눠서 각각 크게. 겹치면 안 됨.
- 다이어리 상대 위치 반영 (왼쪽→카드 왼쪽, 오른쪽→카드 오른쪽).

#### 포스터 (collage.poster) — 보조 요소
- width 160~320px으로 **작게**. 메인 이미지를 가리지 않는 빈 구석에 배치.
- frame은 "polaroid" 고정.

### 스티커 재배치 (중요!)
- stickers 배열의 각 스티커를 index(0부터) 기준으로 x, y, width, height, rotation 지정.
- **y ≥ 140** (헤더 침범 금지).
- 다이어리 원본 x_pct, y_pct 상대 위치를 카드 크기에 맞게 스케일.

#### 일반 스티커 / 이미지 스티커 — 꾸미기 요소
- 아이콘: 60~100px, 이미지 스티커: 100~200px.
- 메인 이미지 중심 70% 보호 영역 배치 금지. 가장자리 30%만 가능.
- rotation: -15~15도. 메모지 테두리와 10~20% 겹쳐도 됨.

#### 말풍선 (type: "bubble")
- 텍스트 잘림 방지: 한글 1글자 ≈ 28×34px. 최소 160×80px.
- font_size 필드 반드시 포함 (16~28).

### Zone 3 — 메모 (y: 1200~1560)
- 감상문을 메모지 느낌으로. font_size: 24~34px.

### Zone 4 — 정보 (y: 1560~1920)
- 작품 제목 (굵게, 중앙), 별점, 해시태그.

## 배경 스타일
장르·분위기에 맞게 배경색 결정.
- 힐링/감성 → 베이지·파스텔 | 액션/다크 → 어두운 톤
- 판타지/몽환 → 보라·파랑 | 일상/코미디 → 노란·분홍

JSON만 응답해. 다른 텍스트 없이.
"""
    return prompt


def _summarize_stickers(placed_items: list) -> list[dict]:
    """placedItems에서 스티커 요약 정보를 추출한다."""
    stickers = []
    for item in placed_items:
        item_type = item.get('type', 'sticker')
        if item_type == 'text':
            continue
        summary = {
            'type': item_type,
            'icon': item.get('icon', ''),
            'x_pct': item.get('x', 0),
            'y_pct': item.get('y', 0),
            'scale': item.get('scale', 1.0),
            'width': item.get('width', 0),
            'height': item.get('height', 0),
            'zIndex': item.get('zIndex', 0),
        }
        if item_type == 'bubble':
            summary['text'] = item.get('text', '')
            summary['bubbleType'] = item.get('bubbleType', 'normal')
        if item.get('imageSrc'):
            summary['has_image'] = True
            summary['is_main_image'] = _is_main_image(item)
        stickers.append(summary)
    return stickers


def _is_main_image(item: dict) -> bool:
    """업로드된 사용자 이미지(장면 캡처 등)인지 판단한다.

    /api/records/uploads/ 경로면 사용자가 직접 올린 이미지 → 메인 이미지.
    기본 스티커(/static/ 등)는 메인이 아님.
    """
    src = item.get('imageSrc') or ''
    return '/api/records/uploads/' in src


def _extract_tags(record) -> list[str]:
    """Record에서 태그 목록을 추출한다."""
    canvas = record.canvas_data or {}
    # canvas_data에 tags가 있으면 사용
    if isinstance(canvas, dict) and canvas.get('tags'):
        return canvas['tags']
    # record 모델에 직접 tags 필드가 있으면 사용
    if hasattr(record, 'tags') and record.tags:
        if isinstance(record.tags, list):
            return record.tags
    return []

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
    record_data = {
        'record_id': record.id,
        'work': {
            'title': work.title_ko or work.title,
            'title_en': work.title_en,
            'genre': work.genre,
            'poster_url': work.poster_image,
        },
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

## 감상 기록
{json.dumps(record_data, ensure_ascii=False, indent=2)}

## 사용 가능한 템플릿
{json.dumps(template_list, ensure_ascii=False, indent=2)}

## 감상문 처리
{memo_instruction}

## 배치 규칙
카드는 1080×1920px이며 4개 존으로 나뉜다. 각 존 범위 안에서 자유롭게 배치해.

### Zone 1 — 헤더 (y: 0~140)
- 날짜를 좌측에 배치 (감상일 또는 오늘 날짜)
- 우측에는 덕꾸 로고가 자동 삽입되므로 x=800 이후 비워둬

### Zone 2 — 콜라주 (y: 140~1100)
- 포스터 이미지 배치 (x, y, width, height 결정)
- frame 스타일 선택: "none" | "polaroid" | "rounded" | "shadow"
- 포스터 아래 캐릭터/작품명 라벨 (선택사항)
- 사용자 스티커 {record_data['sticker_count']}개를 포스터 주변에 배치해야 함 (stickers 배열로 각각 좌표 지정)

### 스티커 재배치 (중요!)
- 입력 데이터의 stickers 배열에 있는 각 스티커를 카드에 재배치해.
- 각 스티커의 index(0부터)에 대응하는 x, y, width, height, rotation을 응답 stickers 배열에 포함해.
- **모든 스티커의 y좌표는 반드시 140 이상이어야 한다 (Zone 1 헤더 영역 침범 금지).**
- **다이어리 원본 배치를 참고해서 재배치해.** 각 스티커의 x_pct, y_pct는 다이어리에서의 상대 위치(%)이다. 이 상대 관계를 최대한 유지하되 카드 크기(1080×1920)에 맞게 스케일해. 예: 다이어리에서 왼쪽 위에 있던 스티커는 카드에서도 왼쪽 위, 오른쪽 아래에 있던 스티커는 카드에서도 오른쪽 아래.

#### 메인 이미지 (is_main_image: true)
- 사용자가 업로드한 장면 캡처/이미지이므로 **가장 중요한 요소**다.
- Zone 2(y: 140~1100) 내에서 **공백을 최대한 채우도록 크게** 배치해.
- 여러 메인 이미지가 있으면 Zone 2 공간을 나눠서 각각 크게 배치. 서로 겹치면 안 됨.
- 다이어리에서의 상대 위치를 반영: 왼쪽에 있던 이미지는 카드 왼쪽, 오른쪽에 있던 이미지는 카드 오른쪽.
- 포스터, 다른 메인 이미지, 메모 영역과 겹치지 않게.
- width, height를 최소 300px 이상으로 설정.

#### 일반 스티커 (has_image: true, is_main_image 없음 / 아이콘 스티커)
- 아이콘 스티커(icon 텍스트): 60~100px 크기로 자유롭게 배치.
- 이미지 스티커(기본 스티커): 100~200px 크기로 자유롭게 배치.
- 다이어리 원본 배치의 상대 위치를 참고해서 비슷한 위치에 배치.
- **단, 메인 이미지의 중심 70% 영역에는 스티커를 배치하지 마.** 예: 메인 이미지가 (x=100, y=200, w=400, h=400)이면 중심 70% 보호 영역은 (x=160, y=260, w=280, h=280). 이 영역 안에 스티커가 들어가면 안 됨. 메인 이미지 가장자리 30%에는 살짝 걸칠 수 있음.
- 스티커끼리도 겹치지 않게.

#### 말풍선 (type: "bubble")
- 말풍선 안의 텍스트가 **절대 잘리지 않도록** 충분한 크기를 확보해.
- 한글 1글자당 약 width 28px, height 34px로 계산. 예: 4글자 한 줄이면 최소 width 140px.
- 텍스트가 길면 여러 줄로 나뉘는 걸 고려해서 height를 충분히 잡아.
- 최소 width 160px, height 80px.
- font_size 필드를 추가해서 말풍선 크기에 맞는 글꼴 크기를 지정 (16~28 범위).

### Zone 3 — 메모 (y: 1100~1500)
- 감상문 텍스트를 메모지 느낌으로 배치
- 메모 배경색, 테두리색, 텍스트색 결정
- font_size 범위: 24~34px

### Zone 4 — 정보 (y: 1500~1920)
- 작품 제목 (굵게, 중앙 정렬)
- 별점 (강조색으로 크게)
- 태그 목록 (작게, 해시태그 형식)

## 배경 스타일
작품의 장르와 태그 분위기에 맞게 배경색을 결정해.
- 힐링/감성 → 따뜻한 베이지·파스텔 계열
- 액션/다크 → 어두운 톤
- 판타지/몽환 → 보라·파랑 그라데이션 느낌
- 일상/코미디 → 밝은 노란·분홍 계열

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
    src = item.get('imageSrc', '')
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

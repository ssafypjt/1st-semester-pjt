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
        'sticker_count': len([i for i in placed_items if i.get('type') == 'sticker']),
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
- 사용자 스티커 {record_data['sticker_count']}개가 자동 배치되므로 공간 고려

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

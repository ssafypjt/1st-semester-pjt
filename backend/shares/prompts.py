"""
공유 카드 생성을 위한 프롬프트 조립 모듈 v5 — 고정 템플릿 기반.

AI는 좌표 배치를 하지 않고 **테마·감상 요약·태그 추출**만 담당한다.
레이아웃은 renderer.py의 고정 템플릿이 처리한다.
"""
import json


def build_card_prompt(record, templates=None, placed_items=None) -> str:
    """Record 데이터로 AI 프롬프트를 생성한다.

    AI에게 요청하는 것:
      1. mood — 작품 분위기 키워드 (테마 결정용)
      2. quote — 감상평에서 한 줄 인용 (또는 직접 생성)
      3. tags — 작품 장르/태그 (API 데이터 기반)
    """
    work = record.work
    placed_items = placed_items or []

    # 작품 정보
    if work:
        work_info = {
            'title_ko': work.title_ko or work.title,
            'title_en': work.title_en or work.title,
            'genre': work.genre,
        }
        # AniList 태그 캐시가 있으면 활용
        if work.anilist_tags and isinstance(work.anilist_tags, dict):
            work_info['genres'] = work.anilist_tags.get('genres', [])
            tags_raw = work.anilist_tags.get('tags', [])
            work_info['top_tags'] = [
                t['name'] for t in sorted(tags_raw, key=lambda t: t.get('rank', 0), reverse=True)[:10]
            ] if tags_raw else []
    else:
        work_info = {
            'title_ko': record.title or '제목 없음',
            'title_en': '',
            'genre': '',
        }

    # 감상문
    content_text = (record.content or '').strip()

    # 메모 (텍스트 박스 내용)
    memo_texts = _extract_text_boxes(placed_items)

    # 레이팅
    rating = str(record.rating) if record.rating else ''

    # 날짜
    date_str = str(record.watched_date) if record.watched_date else ''
    if date_str:
        date_str = date_str.replace('-', '.')

    record_data = {
        'work': work_info,
        'content': content_text[:500],
        'memo_from_textboxes': memo_texts,
        'rating': rating,
        'date': date_str,
    }

    prompt = f"""아래 감상 기록을 분석해서 공유 카드 데이터 JSON을 생성해줘.

## 감상 기록
{json.dumps(record_data, ensure_ascii=False, indent=2)}

## 요청사항
다음 필드를 포함한 JSON만 응답해:

1. **mood**: 작품의 전체 분위기를 한 단어로. 예: "다크", "귀여운", "차가운", "따뜻한", "몽환적", "열정적"
2. **quote**: 감상평(content)에서 카드에 넣을 한 줄 인용문 (30자 내). 감상평이 없으면 작품에 어울리는 한 줄 코멘트 생성.
3. **memo_text**: 텍스트 박스 내용(memo_from_textboxes)을 합쳐서 메모 영역에 넣을 텍스트. 없으면 감상평을 3문장 이내로 요약.
4. **tags**: 작품 장르·태그를 한글로 5개 이내. 예: ["액션", "성장", "가족"]
5. **title_ko**: 한국어 제목
6. **title_en**: 영어/로마자 제목 (대문자)

JSON만 응답해. 다른 텍스트 없이.
"""
    return prompt


def _extract_text_boxes(placed_items: list) -> list[str]:
    """placedItems에서 text 타입 아이템의 내용을 추출한다."""
    texts = []
    for item in placed_items:
        if item.get('type') == 'text':
            text = (item.get('text') or '').strip()
            if text:
                texts.append(text)
    return texts


def _extract_tags(record) -> list[str]:
    """Record에서 태그 목록을 추출한다."""
    canvas = record.canvas_data or {}
    if isinstance(canvas, dict) and canvas.get('tags'):
        return canvas['tags']
    if hasattr(record, 'tags') and record.tags:
        if isinstance(record.tags, list):
            return record.tags
    return []

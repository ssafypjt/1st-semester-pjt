"""
공유 카드 생성을 위한 프롬프트 조립 모듈 — 2단계 파이프라인.

Stage 1: 다이어리 텍스트(메모 + 말풍선 + 감상평) → quote + memo_text 생성
Stage 2: Stage 1 결과 + 작품 정보 → 최종 카드 데이터 JSON
"""
import json


# ═════════════════════════════════════════════════════════
#  Stage 1 — 콘텐츠 생성 프롬프트
# ═════════════════════════════════════════════════════════

def build_content_prompt(record, placed_items=None) -> str:
    """Stage 1: 메모·말풍선·감상평을 수집하여 콘텐츠 생성 프롬프트를 만든다."""
    placed_items = placed_items or []
    work = record.work

    # 작품명 (컨텍스트용)
    title = ''
    if work:
        title = work.title_ko or work.title
    else:
        title = record.title or ''

    # 감상평 (content)
    content_text = (record.content or '').strip()

    # 메모 (텍스트 박스)
    memo_texts = _extract_text_boxes(placed_items)

    # 말풍선 텍스트
    bubble_texts = _extract_bubble_texts(placed_items)

    data = {
        'title': title,
        'content': content_text[:500] if content_text else '',
        'memo_texts': memo_texts,
        'bubble_texts': bubble_texts,
    }

    prompt = f"""아래 다이어리 데이터를 종합해서 공유 카드에 넣을 텍스트를 생성해줘.

## 다이어리 데이터
{json.dumps(data, ensure_ascii=False, indent=2)}

## 설명
- content: 사용자가 작성한 감상평
- memo_texts: 다이어리에 배치된 텍스트 박스 내용
- bubble_texts: 다이어리에 배치된 말풍선 텍스트

이 모든 텍스트를 종합해서:
1. **quote**: 감상의 핵심을 담은 한 줄 (30자 내)
2. **memo_text**: 카드 메모 영역에 넣을 텍스트 (3문장 내, 자연스럽게 정리)

텍스트가 부족하면 작품 "{title}"에 어울리는 내용을 생성해.
JSON만 응답해.
"""
    return prompt


# ═════════════════════════════════════════════════════════
#  Stage 2 — 카드 배치 프롬프트
# ═════════════════════════════════════════════════════════

def build_card_prompt(record, stage1_result: dict,
                      placed_items=None) -> str:
    """Stage 2: Stage 1 결과 + 작품 정보로 최종 카드 데이터 프롬프트를 만든다."""
    placed_items = placed_items or []
    work = record.work

    # 작품 정보
    if work:
        work_info = {
            'title_ko': work.title_ko or work.title,
            'title_en': work.title_en or work.title,
            'genre': work.genre,
        }
        if work.anilist_tags and isinstance(work.anilist_tags, dict):
            work_info['genres'] = work.anilist_tags.get('genres', [])
            tags_raw = work.anilist_tags.get('tags', [])
            work_info['top_tags'] = [
                t['name'] for t in sorted(
                    tags_raw, key=lambda t: t.get('rank', 0), reverse=True
                )[:10]
            ] if tags_raw else []
    else:
        work_info = {
            'title_ko': record.title or '제목 없음',
            'title_en': '',
            'genre': '',
        }

    # 레이팅·날짜
    rating = str(record.rating) if record.rating else ''
    date_str = str(record.watched_date) if record.watched_date else ''
    if date_str:
        date_str = date_str.replace('-', '.')

    data = {
        'work': work_info,
        'rating': rating,
        'date': date_str,
        'stage1_result': {
            'quote': stage1_result.get('quote', ''),
            'memo_text': stage1_result.get('memo_text', ''),
        },
    }

    prompt = f"""아래 작품 정보와 생성된 텍스트로 최종 카드 데이터 JSON을 만들어줘.

## 데이터
{json.dumps(data, ensure_ascii=False, indent=2)}

## 요청사항
1. **mood**: 작품 장르·분위기에 맞는 한 단어 (다크/귀여운/차가운/따뜻한/몽환적/열정적)
2. **quote**: Stage 1 결과를 그대로 사용하거나 다듬어서
3. **memo_text**: Stage 1 결과를 그대로 사용하거나 다듬어서
4. **tags**: 작품 장르·태그를 한글로 5개 이내 (Action → 액션)
5. **title_ko**: 한국어 제목
6. **title_en**: 영어/로마자 제목 (대문자)

JSON만 응답해.
"""
    return prompt


# ═════════════════════════════════════════════════════════
#  텍스트 추출 유틸리티
# ═════════════════════════════════════════════════════════

def _extract_text_boxes(placed_items: list) -> list[str]:
    """placedItems에서 text 타입 아이템의 내용을 추출한다."""
    texts = []
    for item in placed_items:
        if item.get('type') == 'text':
            text = (item.get('text') or '').strip()
            if text:
                texts.append(text)
    return texts


def _extract_bubble_texts(placed_items: list) -> list[str]:
    """placedItems에서 bubble 타입 아이템의 텍스트를 추출한다."""
    texts = []
    for item in placed_items:
        if item.get('type') == 'bubble':
            text = (item.get('text') or '').strip()
            if text:
                texts.append(text)
    return texts

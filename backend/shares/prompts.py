"""
공유 카드 생성을 위한 프롬프트 조립 모듈.

Record 데이터 + 사용 가능한 CardTemplate 목록 → AI에게 보낼 유저 프롬프트를 조립한다.
"""
import json


def build_card_prompt(record, templates) -> str:
    """Record 인스턴스와 CardTemplate 목록으로 AI 유저 프롬프트를 생성한다.

    Args:
        record: Record 인스턴스 (select_related('work', 'user') 필수)
        templates: CardTemplate QuerySet (is_active=True)

    Returns:
        AI에게 보낼 유저 프롬프트 문자열
    """
    work = record.work

    # 1) 감상 기록 데이터
    record_data = {
        'record_id': record.id,
        'work': {
            'title': work.title_ko or work.title,
            'title_en': work.title_en,
            'type': work.get_work_type_display() if hasattr(work, 'get_work_type_display') else work.work_type,
            'genre': work.genre,
            'poster_url': work.poster_image,
        },
        'rating': str(record.rating) if record.rating else None,
        'watched_date': str(record.watched_date) if record.watched_date else None,
        'content': record.content[:500] if record.content else '',  # 500자 제한
        'canvas_data': _extract_canvas_summary(record.canvas_data),
        'user_nickname': record.user.nickname,
    }

    # 2) 사용 가능한 템플릿 목록
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

    # 3) 프롬프트 조립
    prompt = f"""아래 감상 기록 데이터를 분석해서, 가장 어울리는 카드 템플릿을 선택하고
공유 카드 레이아웃 JSON을 생성해줘.

## 감상 기록
{json.dumps(record_data, ensure_ascii=False, indent=2)}

## 사용 가능한 템플릿 목록
{json.dumps(template_list, ensure_ascii=False, indent=2)}

## 배치 요구사항
- 작품 포스터 이미지를 카드 상단 또는 배경에 배치
- 작품 제목을 눈에 띄게 배치
- 평점이 있으면 별점 또는 숫자로 표시
- 감상문은 핵심 부분만 발췌하여 읽기 좋은 크기로 배치
- 감상일과 닉네임은 하단에 작게 배치
- 작품의 장르와 감상문의 분위기에 맞는 템플릿을 선택
- canvas_data에 사용자가 설정한 테마/배경이 있으면 그 분위기를 반영

레이아웃 JSON만 응답해줘.
"""
    return prompt


def _extract_canvas_summary(canvas_data: dict) -> dict:
    """canvas_data에서 AI 프롬프트에 필요한 핵심 정보만 추출.

    canvas_data 구조는 프론트엔드 캔버스 에디터가 정의하며,
    일반적으로 다음을 포함할 수 있다:
    - title: 사용자 지정 제목
    - theme: 테마 이름
    - background: 배경색/이미지
    - filter: 필터 설정
    - bgm: BGM 정보
    """
    if not canvas_data:
        return {}

    return {
        'title': canvas_data.get('title', ''),
        'theme': canvas_data.get('theme', ''),
        'background': canvas_data.get('background', ''),
        'filter': canvas_data.get('filter', ''),
    }

"""외부 API 연동 공통 유틸."""

REQUEST_TIMEOUT = 5  # seconds


class ExternalAPIError(Exception):
    """외부 API 호출/응답 실패 시 공통 예외.

    호출부에서 사용자 흐름을 막지 않으려면 잡아서 무시하거나
    안내 메시지로 변환해 사용한다.
    """


def normalized_work(*, source, external_id, title, title_ko='', title_en='',
                     work_type='anime', release_date=None, genre='',
                     poster_image='', description=''):
    """Work 모델 필드에 대응하는 정규화된 dict.

    release_date 는 'YYYY-MM-DD' 형식 문자열 또는 None.
    일부 API(Google Books 등)는 'YYYY' / 'YYYY-MM'처럼 부분 날짜를 줄 수 있어,
    DateField에 그대로 저장하기 전에 정규화/검증이 필요하다 (후속 작업).
    """
    return {
        'source': source,
        'external_id': str(external_id),
        'title': title,
        'title_ko': title_ko,
        'title_en': title_en,
        'work_type': work_type,
        'release_date': release_date,
        'genre': genre,
        'poster_image': poster_image,
        'description': description,
    }

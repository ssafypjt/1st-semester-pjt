"""TMDB API 연동 (영화 / 드라마 메타데이터).

https://developer.themoviedb.org/
설정: settings.TMDB_API_KEY (.env, 필수), settings.TMDB_API_BASE_URL
"""
import requests
from django.conf import settings

from .base import REQUEST_TIMEOUT, ExternalAPIError, normalized_work

_POSTER_BASE_URL = 'https://image.tmdb.org/t/p/w500'


def search(query, work_type='movie'):
    """제목으로 영화/드라마 검색. 정규화된 dict 리스트 반환.

    Args:
        work_type: 'movie' 또는 'drama' (TMDB의 'tv'에 매핑).

    Raises:
        ExternalAPIError: TMDB_API_KEY 미설정, 네트워크 오류, 비정상 응답.
    """
    if not settings.TMDB_API_KEY:
        raise ExternalAPIError('TMDB_API_KEY가 설정되지 않았습니다 (.env 확인).')

    tmdb_type = 'tv' if work_type == 'drama' else 'movie'
    try:
        resp = requests.get(
            f'{settings.TMDB_API_BASE_URL}/search/{tmdb_type}',
            params={
                'api_key': settings.TMDB_API_KEY,
                'query': query,
                'language': 'ko-KR',
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ExternalAPIError(f'TMDB API 호출 실패: {e}') from e

    results = []
    for item in resp.json().get('results', [])[:10]:
        title_ko = item.get('title') or item.get('name') or ''
        title_en = item.get('original_title') or item.get('original_name') or ''
        release_date = item.get('release_date') or item.get('first_air_date') or None
        poster_path = item.get('poster_path')
        results.append(normalized_work(
            source='tmdb',
            external_id=item['id'],
            title=title_en or title_ko,
            title_ko=title_ko,
            title_en=title_en,
            work_type='drama' if tmdb_type == 'tv' else 'movie',
            release_date=release_date or None,
            # genre_ids → 이름 매핑은 /genre/movie/list, /genre/tv/list 추가
            # 호출이 필요 (후속 작업, 결과 캐싱 고려).
            genre='',
            poster_image=f'{_POSTER_BASE_URL}{poster_path}' if poster_path else '',
            description=item.get('overview') or '',
        ))
    return results

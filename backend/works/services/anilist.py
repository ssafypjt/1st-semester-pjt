"""AniList GraphQL API 연동 (애니메이션 메타데이터).

공개 API — API 키 불필요. https://anilist.co/graphiql
설정: settings.ANILIST_API_URL (기본 https://graphql.anilist.co)
"""
import requests
from django.conf import settings

from .base import REQUEST_TIMEOUT, ExternalAPIError, normalized_work

_SEARCH_QUERY = """
query ($search: String) {
  Page(page: 1, perPage: 10) {
    media(search: $search, type: ANIME) {
      id
      title { romaji english native }
      startDate { year month day }
      genres
      description(asHtml: false)
      coverImage { large }
    }
  }
}
"""


def search(query):
    """제목으로 애니메이션 검색. 정규화된 dict 리스트 반환.

    Raises:
        ExternalAPIError: 네트워크 오류 또는 비정상 응답.
    """
    try:
        resp = requests.post(
            settings.ANILIST_API_URL,
            json={'query': _SEARCH_QUERY, 'variables': {'search': query}},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ExternalAPIError(f'AniList API 호출 실패: {e}') from e

    media_list = resp.json().get('data', {}).get('Page', {}).get('media', [])
    results = []
    for media in media_list:
        title = media.get('title') or {}
        start = media.get('startDate') or {}
        release_date = None
        if start.get('year'):
            release_date = '{:04d}-{:02d}-{:02d}'.format(
                start['year'], start.get('month') or 1, start.get('day') or 1,
            )
        results.append(normalized_work(
            source='anilist',
            external_id=media['id'],
            title=title.get('romaji') or title.get('english') or title.get('native') or '',
            title_ko='',  # AniList는 한국어 제목 미제공 — 후속에서 별도 매핑 고려
            title_en=title.get('english') or '',
            work_type='anime',
            release_date=release_date,
            genre=', '.join(media.get('genres') or []),
            poster_image=(media.get('coverImage') or {}).get('large', ''),
            description=media.get('description') or '',
        ))
    return results

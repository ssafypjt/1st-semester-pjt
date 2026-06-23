"""AniList GraphQL API 연동 (애니메이션 메타데이터).

공개 API — API 키 불필요. https://anilist.co/graphiql
설정: settings.ANILIST_API_URL (기본 https://graphql.anilist.co)
"""
import logging
import re

import requests
from django.conf import settings

from .base import REQUEST_TIMEOUT, ExternalAPIError, normalized_work

logger = logging.getLogger(__name__)

_SEARCH_QUERY = """
query ($search: String) {
  Page(page: 1, perPage: 10) {
    media(search: $search, type: ANIME) {
      id
      title { romaji english native }
      synonyms
      startDate { year month day }
      genres
      description(asHtml: false)
      coverImage { large }
    }
  }
}
"""

_KO_RE = re.compile(r'[가-힣]')


def _pick_korean_title(synonyms):
    """synonyms에서 한글 포함 항목 반환."""
    for s in (synonyms or []):
        if _KO_RE.search(s):
            return s
    return ''

_TAGS_QUERY = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    title { romaji english native }
    genres
    tags {
      id
      name
      category
      rank
      isGeneralSpoiler
      isMediaSpoiler
    }
  }
}
"""


def _anilist_post(query, variables):
    """AniList GraphQL API 공통 호출."""
    try:
        resp = requests.post(
            settings.ANILIST_API_URL,
            json={'query': query, 'variables': variables},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise ExternalAPIError(f'AniList API 호출 실패: {e}') from e


def search(query):
    """제목으로 애니메이션 검색. 정규화된 dict 리스트 반환.

    Raises:
        ExternalAPIError: 네트워크 오류 또는 비정상 응답.
    """
    data = _anilist_post(_SEARCH_QUERY, {'search': query})

    media_list = data.get('data', {}).get('Page', {}).get('media', [])
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
            title_ko=_pick_korean_title(media.get('synonyms')),
            title_en=title.get('english') or '',
            work_type='anime',
            release_date=release_date,
            genre=', '.join(media.get('genres') or []),
            poster_image=(media.get('coverImage') or {}).get('large', ''),
            description=media.get('description') or '',
        ))
    return results


def fetch_tags(anilist_id, max_tags=8):
    """AniList 작품의 태그를 가져온다.

    스포일러 태그를 제거하고 rank 순으로 상위 max_tags개를 반환한다.

    Args:
        anilist_id: AniList 작품 ID (int 또는 str)
        max_tags: 반환할 최대 태그 수 (기본 8)

    Returns:
        {
            'anilist_id': int,
            'genres': ['Action', 'Fantasy', ...],
            'tags': [
                {'name': 'Shounen', 'category': 'Theme-Other', 'rank': 92},
                ...
            ],
        }

    Raises:
        ExternalAPIError: API 호출 실패 시
    """
    anilist_id = int(anilist_id)
    data = _anilist_post(_TAGS_QUERY, {'id': anilist_id})

    media = data.get('data', {}).get('Media')
    if not media:
        raise ExternalAPIError(f'AniList에서 작품을 찾을 수 없음: id={anilist_id}')

    genres = media.get('genres') or []
    raw_tags = media.get('tags') or []

    # 스포일러 태그 제거 → rank 내림차순 정렬 → 상위 N개
    safe_tags = [
        t for t in raw_tags
        if not t.get('isGeneralSpoiler') and not t.get('isMediaSpoiler')
    ]
    safe_tags.sort(key=lambda t: t.get('rank', 0), reverse=True)
    top_tags = [
        {'name': t['name'], 'category': t.get('category', ''), 'rank': t.get('rank', 0)}
        for t in safe_tags[:max_tags]
    ]

    return {
        'anilist_id': anilist_id,
        'genres': genres,
        'tags': top_tags,
    }
    
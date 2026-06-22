"""Google Books API 연동 (도서 메타데이터).

https://developers.google.com/books
설정: settings.GOOGLE_BOOKS_API_KEY (.env, 선택), settings.GOOGLE_BOOKS_API_BASE_URL
  - API 키 없이도 동작하지만, 키가 있으면 할당량이 늘어남.
"""
import requests
from django.conf import settings

from .base import REQUEST_TIMEOUT, ExternalAPIError, normalized_work


def search(query):
    """제목으로 도서 검색. 정규화된 dict 리스트 반환.

    Raises:
        ExternalAPIError: 네트워크 오류 또는 비정상 응답.

    주의: publishedDate 가 'YYYY' 또는 'YYYY-MM' 형태로만 오는 경우가 많아
    release_date 는 그대로 전달한다. Work.release_date(DateField)에 저장하려면
    'YYYY-MM-DD'로 정규화하는 로직이 후속 작업으로 필요하다.
    """
    params = {'q': query, 'maxResults': 10}
    if settings.GOOGLE_BOOKS_API_KEY:
        params['key'] = settings.GOOGLE_BOOKS_API_KEY

    try:
        resp = requests.get(
            f'{settings.GOOGLE_BOOKS_API_BASE_URL}/volumes',
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ExternalAPIError(f'Google Books API 호출 실패: {e}') from e

    results = []
    for item in resp.json().get('items', []):
        info = item.get('volumeInfo', {})
        image_links = info.get('imageLinks', {})
        results.append(normalized_work(
            source='google_books',
            external_id=item['id'],
            title=info.get('title', ''),
            title_ko=info.get('title', ''),
            title_en='',
            work_type='book',
            release_date=info.get('publishedDate') or None,
            genre=', '.join(info.get('categories') or []),
            poster_image=(image_links.get('thumbnail')
                          or image_links.get('smallThumbnail') or ''),
            description=info.get('description', ''),
        ))
    return results

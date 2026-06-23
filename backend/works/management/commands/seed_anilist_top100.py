"""
AniList 인기 상위 100개 애니메이션을 Work 테이블에 시드.

사용: python manage.py seed_anilist_top100
옵션: --with-tags  태그도 함께 캐싱 (API 호출 많아짐, 시간 소요)
"""
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from works.models import Work
from works.services.anilist import fetch_tags
from works.services.base import ExternalAPIError

# AniList는 페이지당 최대 50개, 2페이지로 100개
_TOP_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { total currentPage lastPage hasNextPage }
    media(type: ANIME, sort: POPULARITY_DESC) {
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


import re

_KO_RE = re.compile(r'[가-힣]')  # 한글 감지


def _pick_korean_title(synonyms):
    """synonyms 목록에서 한글이 포함된 첫 번째 항목을 반환."""
    if not synonyms:
        return ''
    for s in synonyms:
        if _KO_RE.search(s):
            return s
    return ''


class Command(BaseCommand):
    help = 'AniList 인기 상위 100개 애니메이션을 Work 테이블에 저장'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-tags', action='store_true',
            help='태그도 함께 가져와서 anilist_tags에 캐싱 (시간 소요)',
        )

    def _api_post(self, api_url, payload, max_retries=3):
        """Rate limit(429) 시 60초 대기 후 재시도."""
        for attempt in range(max_retries):
            try:
                resp = requests.post(api_url, json=payload, timeout=15)
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get('Retry-After', 60))
                    self.stdout.write(self.style.WARNING(
                        f'  Rate limit 도달! {retry_after}초 대기 중... ({attempt + 1}/{max_retries})'
                    ))
                    time.sleep(retry_after)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    self.stdout.write(self.style.WARNING(
                        f'  요청 실패, 60초 후 재시도... ({attempt + 1}/{max_retries}): {e}'
                    ))
                    time.sleep(60)
                else:
                    raise

    def handle(self, *args, **options):
        with_tags = options['with_tags']
        api_url = getattr(settings, 'ANILIST_API_URL', 'https://graphql.anilist.co')

        all_media = []

        # 2페이지 × 50개 = 100개
        for page in (1, 2):
            self.stdout.write(f'AniList API 호출 중... (page {page}/2)')
            try:
                data = self._api_post(api_url, {
                    'query': _TOP_QUERY,
                    'variables': {'page': page, 'perPage': 50},
                })
            except requests.RequestException as e:
                self.stderr.write(self.style.ERROR(f'API 호출 실패: {e}'))
                return

            media_list = data.get('data', {}).get('Page', {}).get('media', [])
            all_media.extend(media_list)
            self.stdout.write(f'  {len(media_list)}개 수신')
            time.sleep(2)  # rate limit 배려

        created_count = 0
        skipped_count = 0

        for media in all_media:
            anilist_id = str(media['id'])
            title_data = media.get('title') or {}
            start = media.get('startDate') or {}

            release_date = None
            if start.get('year'):
                release_date = '{:04d}-{:02d}-{:02d}'.format(
                    start['year'], start.get('month') or 1, start.get('day') or 1,
                )

            title = (
                title_data.get('romaji')
                or title_data.get('english')
                or title_data.get('native')
                or ''
            )
            ko_title = _pick_korean_title(media.get('synonyms'))

            # 이미 존재하면 한글 제목만 업데이트
            existing = Work.objects.filter(source='anilist', external_id=anilist_id).first()
            if existing:
                if ko_title and not existing.title_ko:
                    existing.title_ko = ko_title
                    existing.save(update_fields=['title_ko'])
                    self.stdout.write(f'  한글 제목 업데이트: {title} → {ko_title}')
                skipped_count += 1
                continue

            work = Work.objects.create(
                source='anilist',
                external_id=anilist_id,
                work_type='anime',
                title=title,
                title_ko=ko_title,
                title_en=title_data.get('english') or '',
                release_date=release_date,
                genre=', '.join(media.get('genres') or []),
                poster_image=(media.get('coverImage') or {}).get('large', ''),
                description=(media.get('description') or '')[:500],
            )
            created_count += 1
            self.stdout.write(f'  저장: {title}')

            # 태그 캐싱 (옵션)
            if with_tags:
                try:
                    tags_data = fetch_tags(anilist_id)
                    work.anilist_tags = tags_data
                    work.save(update_fields=['anilist_tags'])
                    self.stdout.write(f'    태그 {len(tags_data.get("tags", []))}개 캐싱')
                    time.sleep(2)  # 분당 30개 제한 대비
                except ExternalAPIError as e:
                    if '429' in str(e) or 'Too Many' in str(e):
                        self.stdout.write(self.style.WARNING('    Rate limit! 60초 대기...'))
                        time.sleep(60)
                        # 한 번 더 시도
                        try:
                            tags_data = fetch_tags(anilist_id)
                            work.anilist_tags = tags_data
                            work.save(update_fields=['anilist_tags'])
                            self.stdout.write(f'    태그 {len(tags_data.get("tags", []))}개 캐싱 (재시도 성공)')
                        except ExternalAPIError:
                            self.stdout.write(self.style.WARNING(f'    태그 재시도 실패, 스킵'))
                    else:
                        self.stdout.write(self.style.WARNING(f'    태그 실패: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'\n완료! 신규 {created_count}개 저장, {skipped_count}개 이미 존재 (총 {len(all_media)}개 조회)'
        ))

"""외부 작품 메타데이터 API 연동 (2단계 스캐폴딩).

각 모듈은 `search(query)` 함수로 외부 API를 조회하고, Work 모델 필드에
대응하는 정규화된 dict 리스트를 반환한다 (`base.normalized_work` 참고).

⚠️ 현재 범위: "정보를 받아서 사용할 수 있도록" 하는 최소 골격만 제공한다.
   - View/엔드포인트에는 아직 연결되지 않음 (검색 API 없음)
   - Work.get_or_create 로 실제 저장하는 로직 없음
   - genre 정규화, release_date 부분 날짜(예: "2020-05") 처리 등은 후속 작업
   이 모듈들을 사용해 실제 동기화/검색 기능을 만드는 것은 다음 라운드에서 진행.
"""
from . import anilist, google_books, tmdb  # noqa: F401
from .base import ExternalAPIError  # noqa: F401

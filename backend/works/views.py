import logging

from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import Work
from .serializers import WorkAdminSerializer, WorkSerializer
from .services.anilist import search as anilist_search, fetch_tags as anilist_fetch_tags
from .services.base import ExternalAPIError

logger = logging.getLogger(__name__)


class WorkViewSet(viewsets.ModelViewSet):
    """작품 CRUD.

    - list/retrieve: 비로그인 포함 누구나 읽기 가능 (AllowAny).
    - create/update/destroy: 관리자(is_staff=True)만.

    시리얼라이저 분기:
    - 읽기  -> WorkSerializer      (source·external_id 미노출)
    - 쓰기  -> WorkAdminSerializer (source·external_id 포함)
    """
    queryset = Work.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "title_ko", "title_en", "genre", "work_type"]

    def get_permissions(self):
        if self.action in ("list", "retrieve", "autocomplete", "select_work", "tags"):
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return WorkAdminSerializer
        return WorkSerializer

    @action(detail=False, methods=["get"], url_path="autocomplete")
    def autocomplete(self, request):
        """통합 자동완성: 로컬 DB + AniList 동시 검색.

        GET /api/works/autocomplete/?q=주술
        결과에 source='local' / source='anilist' 표시.
        """
        q = request.query_params.get("q", "").strip()
        if len(q) < 2:
            return Response([])

        results = []

        # 1) 로컬 DB 검색 (한글·영문·로마자 모두)
        local_qs = Work.objects.filter(
            Q(title_ko__icontains=q) |
            Q(title__icontains=q) |
            Q(title_en__icontains=q)
        )[:10]
        local_ext_ids = set()
        for w in local_qs:
            local_ext_ids.add(f"{w.source}:{w.external_id}")
            results.append({
                "id": w.id,
                "source": "local",
                "external_id": w.external_id,
                "title": w.title,
                "title_ko": w.title_ko,
                "title_en": w.title_en,
                "poster_image": w.poster_image,
                "genre": w.genre,
                "work_type": w.work_type,
                "release_date": str(w.release_date) if w.release_date else None,
                "description": w.description,
            })

        # 2) AniList 검색 (로컬에 결과가 없을 때만)
        if not results:
            try:
                anilist_results = anilist_search(q)
                for item in anilist_results:
                    key = f"anilist:{item['external_id']}"
                    if key in local_ext_ids:
                        continue
                    results.append({
                        "id": None,
                        "source": "anilist",
                        "external_id": item["external_id"],
                        "title": item["title"],
                        "title_ko": item["title_ko"],
                        "title_en": item["title_en"],
                        "poster_image": item["poster_image"],
                        "genre": item["genre"],
                        "work_type": item["work_type"],
                        "release_date": item["release_date"],
                        "description": item["description"],
                    })
            except ExternalAPIError as e:
                logger.warning("AniList 검색 실패: %s", e)

        return Response(results[:15])

    @action(detail=False, methods=["post"], url_path="select")
    def select_work(self, request):
        """자동완성에서 작품 선택 시 Work 레코드 생성/반환.

        이미 로컬에 있으면 기존 레코드 반환.
        AniList 결과면 새 Work 생성. title_ko 매핑 저장.
        """
        data = request.data
        external_id = str(data.get("external_id", ""))
        source = data.get("source", "anilist")
        title_ko = data.get("title_ko", "").strip()

        # 이미 로컬에 존재? (id로)
        if data.get("id"):
            try:
                work = Work.objects.get(id=data["id"])
                if title_ko and title_ko != work.title_ko:
                    work.title_ko = title_ko
                    work.save(update_fields=["title_ko"])
                return Response(WorkSerializer(work).data)
            except Work.DoesNotExist:
                pass

        # external_id로 검색
        if external_id and source:
            work = Work.objects.filter(source=source, external_id=external_id).first()
            if work:
                if title_ko and title_ko != work.title_ko:
                    work.title_ko = title_ko
                    work.save(update_fields=["title_ko"])
                return Response(WorkSerializer(work).data)

        # 새로 생성
        work = Work.objects.create(
            source=source,
            external_id=external_id,
            title=data.get("title", ""),
            title_ko=title_ko,
            title_en=data.get("title_en", ""),
            work_type=data.get("work_type", "anime"),
            release_date=data.get("release_date") or None,
            genre=data.get("genre", ""),
            poster_image=data.get("poster_image", ""),
            description=data.get("description", ""),
        )
        return Response(WorkSerializer(work).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="tags")
    def tags(self, request, pk=None):
        """작품의 AniList 태그 조회.

        GET /api/works/<id>/tags/

        1) DB에 캐싱된 태그가 있으면 바로 반환 (빠름)
        2) 없으면 AniList API 호출 → DB에 저장 → 반환
        """
        work = self.get_object()

        # 1) DB 캐시 확인
        if work.anilist_tags:
            return Response(work.anilist_tags)

        # 2) AniList 연동 작품이 아니면 에러
        if work.source != 'anilist' or not work.external_id:
            return Response(
                {'detail': 'AniList 연동 작품이 아닙니다.', 'genres': [], 'tags': []},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3) AniList API 호출 → DB 캐싱
        try:
            result = anilist_fetch_tags(work.external_id)
            work.anilist_tags = result
            work.save(update_fields=['anilist_tags'])
            return Response(result)
        except ExternalAPIError as e:
            logger.warning("AniList 태그 조회 실패 (work=%s): %s", pk, e)
            return Response(
                {'detail': str(e), 'genres': [], 'tags': []},
                status=status.HTTP_502_BAD_GATEWAY,
            )

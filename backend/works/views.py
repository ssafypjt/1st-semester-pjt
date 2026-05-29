from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny, IsAdminUser
from .models import Work
from .serializers import WorkAdminSerializer, WorkSerializer


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
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return WorkAdminSerializer
        return WorkSerializer

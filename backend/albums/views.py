from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from accounts.models import Follow
from records.models import Record
from .models import Album, AlbumRecord
from .serializers import AlbumSerializer, AlbumRecordSerializer


class AlbumViewSet(viewsets.ModelViewSet):
    """앨범 CRUD.

    - list/retrieve: 비로그인 포함 누구나 공개 앨범 열람 가능.
    - create/update/destroy: 로그인 필수. 수정·삭제는 소유자만 (IsOwnerOrReadOnly 역할은
      perform_update/destroy에서 object-level로 처리).
    """
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """본인 앨범 전체 + 팔로우 중인 유저의 friends 앨범 + 모든 유저의 public 앨범.

        - 팔로우 구현 후 friends 공개 범위 활성화.
        - annotate로 record_count를 미리 집계해 N+1 쿼리를 방지한다.
        """
        qs = Album.objects.annotate(record_count=Count('records'))
        user = self.request.user
        if user.is_authenticated:
            # 내가 팔로우하는 유저 ID 목록
            following_ids = Follow.objects.filter(
                follower=user
            ).values_list('following_id', flat=True)
            return qs.filter(
                Q(user=user) |
                Q(visibility='public') |
                Q(visibility='friends', user_id__in=following_ids)
            )
        return qs.filter(visibility='public')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def _assert_owner(self, album, user):
        """앨범 소유자가 아니면 즉시 403을 raise. perform_update 같은 반환값 없는 메서드에서 안전하게 쓴다."""
        if album.user != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('권한이 없습니다.')

    def update(self, request, *args, **kwargs):
        album = self.get_object()
        self._assert_owner(album, request.user)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        album = self.get_object()
        self._assert_owner(album, request.user)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='add-record')
    def add_record(self, request, pk=None):
        """앨범에 기록 추가.

        접근 가능한 Record 범위:
          - 본인 소유 Record: 공개 여부 무관하게 추가 가능.
          - 타인 Record: visibility='public' AND status='published' 인 경우만 허용.
          (2단계 소셜 기능 확장 시 이 조건을 완화할 수 있다.)
        """
        album = self.get_object()
        self._assert_owner(album, request.user)

        record_id = request.data.get('record_id')
        if not record_id:
            return Response({'detail': 'record_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 접근 가능한 Record만 조회 — 없으면 404 (존재 자체를 숨김)
        record = get_object_or_404(
            Record,
            Q(pk=record_id) & (
                Q(user=request.user) |
                Q(visibility='public', status='published')
            )
        )

        ar, created = AlbumRecord.objects.get_or_create(album=album, record=record)
        return Response(
            AlbumRecordSerializer(ar).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['delete'], url_path='remove-record/(?P<record_id>[^/.]+)')
    def remove_record(self, request, pk=None, record_id=None):
        """앨범에서 기록 제거."""
        album = self.get_object()
        self._assert_owner(album, request.user)
        AlbumRecord.objects.filter(album=album, record_id=record_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

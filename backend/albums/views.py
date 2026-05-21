from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Album, AlbumRecord
from .serializers import AlbumSerializer, AlbumRecordSerializer


class AlbumViewSet(viewsets.ModelViewSet):
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 본인 앨범 + 공개 앨범
        user = self.request.user
        if user.is_authenticated:
            return Album.objects.filter(user=user) | Album.objects.filter(visibility='public')
        return Album.objects.filter(visibility='public')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-record')
    def add_record(self, request, pk=None):
        """앨범에 기록 추가."""
        album = self.get_object()
        if album.user != request.user:
            return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        record_id = request.data.get('record_id')
        if not record_id:
            return Response({'detail': 'record_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        ar, created = AlbumRecord.objects.get_or_create(album=album, record_id=record_id)
        return Response(AlbumRecordSerializer(ar).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='remove-record/(?P<record_id>[^/.]+)')
    def remove_record(self, request, pk=None, record_id=None):
        """앨범에서 기록 제거."""
        album = self.get_object()
        if album.user != request.user:
            return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        AlbumRecord.objects.filter(album=album, record_id=record_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

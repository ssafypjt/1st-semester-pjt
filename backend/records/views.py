"""Record / 이미지 업로드 / 보호된 미디어 서빙 views.

권한 정책 (배포 기준 — 엄격)
─────────────────────────────────────────────────────
- 이미지 업로드: 로그인된 유저만 가능. RecordImage.uploader = request.user.
- 업로드된 이미지 접근: uploader == request.user 인 경우에만 200.
  타인은 404 (존재 자체를 숨김). 인증 안 되면 401(세션 기반).
- /media/ 의 직접 정적 서빙은 DEBUG=True 일 때만 (config/urls.py 참조).
  운영에서는 protected_media view 만이 파일을 노출한다.
"""
import os

from django.conf import settings
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import (api_view, parser_classes,
                                       permission_classes)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Record, RecordImage
from .permissions import IsOwnerOrReadOnly
from .serializers import (RecordDetailSerializer, RecordImageSerializer,
                          RecordListSerializer)


class RecordViewSet(viewsets.ModelViewSet):
    """기록 CRUD.

    - list/retrieve: 본인 기록 + visibility=public 기록만.
    - create: 로그인된 유저 (자동으로 user=request.user).
    - update/partial_update/destroy: 본인 기록만.
    """
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['anime__title', 'anime__title_ko', 'content']
    ordering_fields = ['created_at', 'rating', 'like_count']

    def get_queryset(self):
        user = self.request.user
        qs = Record.objects.select_related('user', 'anime')
        if user.is_authenticated:
            return qs.filter(Q(user=user) | Q(visibility='public'))
        return qs.filter(visibility='public')

    def get_serializer_class(self):
        if self.action == 'list':
            return RecordListSerializer
        return RecordDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ── 이미지 업로드 ────────────────────────────────────
ALLOWED_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    """캔버스 다꾸용 이미지 업로드.

    Request: multipart/form-data, 필드 'file' (선택적으로 'record_id').
    Response: { id, url, filename, size, created_at }
      - url 은 protected URL (/api/records/uploads/<id>/) 로,
        타인이 알아도 접근 불가.
    """
    f = request.FILES.get('file')
    if not f:
        return Response({'detail': "'file' 필드가 필요합니다."},
                        status=status.HTTP_400_BAD_REQUEST)

    ext = os.path.splitext(f.name)[1].lower()
    if ext not in ALLOWED_EXT:
        return Response({'detail': f'허용되지 않은 확장자: {ext}'},
                        status=status.HTTP_400_BAD_REQUEST)

    max_bytes = getattr(settings, 'MEDIA_MAX_UPLOAD_BYTES', 8 * 1024 * 1024)
    if f.size > max_bytes:
        return Response(
            {'detail': f'파일 크기는 {max_bytes // (1024 * 1024)}MB 이하만 가능합니다.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 옵션: record_id 가 들어오면 작성자 본인 여부 확인 후 연결
    record = None
    record_id = request.data.get('record_id')
    if record_id:
        record = get_object_or_404(Record, pk=record_id)
        if record.user_id != request.user.id:
            return Response({'detail': '본인의 기록에만 업로드할 수 있습니다.'},
                            status=status.HTTP_403_FORBIDDEN)

    img = RecordImage.objects.create(
        uploader=request.user,
        record=record,
        file=f,
        original_name=f.name,
        size=f.size,
    )
    return Response(
        RecordImageSerializer(img, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_media(request, pk):
    """업로더 본인만 접근 가능한 이미지 응답.

    /api/records/uploads/<pk>/ 로 매핑.
    향후 nginx 의 X-Accel-Redirect / Apache 의 X-Sendfile 헤더로
    바꿔도 호환되도록 권한 체크 후 FileResponse 만 돌려준다.
    """
    img = get_object_or_404(RecordImage, pk=pk)
    if img.uploader_id != request.user.id:
        # 정책: 작성자 본인만. (Record 가 public 이라도 본인이 아니면 비공개)
        raise Http404

    if not img.file or not img.file.path or not os.path.exists(img.file.path):
        raise Http404

    return FileResponse(
        open(img.file.path, 'rb'),
        as_attachment=False,
        filename=img.original_name or os.path.basename(img.file.name),
    )

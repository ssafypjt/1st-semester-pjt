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
from django.db import IntegrityError
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import (action, api_view, parser_classes,
                                       permission_classes)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from accounts.models import Follow
from .models import Comment, Like, Record, RecordImage, StickerAsset, UserSticker
from .permissions import IsOwnerOrReadOnly
from .serializers import (CommentSerializer, RecordDetailSerializer,
                          RecordImageSerializer, RecordListSerializer,
                          StickerAssetSerializer, UserStickerSerializer)


class RecordViewSet(viewsets.ModelViewSet):
    """기록 CRUD.

    - list/retrieve: 로그인한 본인 기록만.
    - create: 로그인된 유저 (자동으로 user=request.user).
    - update/partial_update/destroy: 본인 기록만.
    """
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['work__title', 'work__title_ko', 'content']
    ordering_fields = ['created_at', 'rating', 'like_count']

    def get_queryset(self):
        user = self.request.user
        # 탈퇴(soft delete) 처리된 유저의 기록은 보관 기간(30일) 동안 비공개.
        # is_active=True 인 유저만 노출 — 재로그인으로 계정이 복구되면
        # is_active=True 로 돌아가 자동으로 다시 노출된다.
        qs = Record.objects.select_related('user', 'work').filter(user__is_active=True)

        # ?mine=1 → 본인 기록만 (내 앨범용)
        if user.is_authenticated and self.request.query_params.get('mine'):
            return qs.filter(user=user)

        if user.is_authenticated:
            # 내가 팔로우하는 유저 ID 목록 (friends 공개 범위용)
            following_ids = Follow.objects.filter(
                follower=user
            ).values_list('following_id', flat=True)
            # 본인 기록은 draft 포함 전체
            # 타인 기록은 public+게시 완료 또는 (friends+게시 완료 AND 팔로우 중)
            qs = qs.filter(
                Q(user=user) |
                Q(visibility='public', status='published') |
                Q(visibility='friends', status='published', user_id__in=following_ids)
            )
        else:
            # 비로그인: 공개+게시 완료만
            qs = qs.filter(visibility='public', status='published')

        # ?q= → 제목·태그 통합 검색 (SearchFilter의 ?search= 와 별도)
        q = self.request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(content__icontains=q) |
                Q(work__title__icontains=q) |
                Q(work__title_ko__icontains=q) |
                Q(work__anilist_tags__icontains=q)
            )

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return RecordListSerializer
        return RecordDetailSerializer

    def get_permissions(self):
        # 좋아요/댓글 액션은 본인 소유 여부와 무관 — IsOwnerOrReadOnly 대신
        # 별도 권한 사용. (조회 가능한 기록인지는 get_object()의
        # get_queryset 필터링이 이미 보장한다.)
        if self.action == 'like_toggle':
            return [IsAuthenticated()]
        if self.action == 'comments':
            return [IsAuthenticatedOrReadOnly()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # ── 좋아요 ────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='like')
    def like_toggle(self, request, pk=None):
        """좋아요 토글. POST /api/records/<pk>/like/"""
        record = self.get_object()
        like_qs = Like.objects.filter(record=record, user=request.user)
        if like_qs.exists():
            like_qs.delete()
            liked = False
        else:
            try:
                Like.objects.create(record=record, user=request.user)
            except IntegrityError:
                # 동시 요청으로 이미 생성된 경우 — 좋아요 상태로 간주
                pass
            liked = True
        like_count = record.likes.count()
        Record.objects.filter(pk=record.pk).update(like_count=like_count)
        return Response({'liked': liked, 'like_count': like_count})

    # ── 댓글 (1차 구현) ──────────────────────────────────
    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, pk=None):
        """댓글 목록 조회 / 작성.

        GET  /api/records/<pk>/comments/  — 조회 가능한 기록의 댓글 전체.
        POST /api/records/<pk>/comments/  — 로그인 필요, content 필수.

        1차 구현: 페이지네이션·수정/삭제는 후속 작업 (PROJECT_CONTEXT.md 참고).
        """
        record = self.get_object()
        if request.method == 'POST':
            serializer = CommentSerializer(data=request.data,
                                           context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save(record=record, user=request.user)
            Record.objects.filter(pk=record.pk).update(
                comment_count=record.comments.count())
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # 탈퇴(soft delete) 처리된 유저의 댓글은 보관 기간 동안 비공개.
        qs = record.comments.select_related('user').filter(user__is_active=True)
        serializer = CommentSerializer(qs, many=True,
                                       context={'request': request})
        return Response(serializer.data)

    # ── 댓글 삭제 ────────────────────────────────────────
    @action(detail=True, methods=['delete'],
            url_path='comments/(?P<comment_id>[0-9]+)')
    def comment_delete(self, request, pk=None, comment_id=None):
        """본인 댓글 삭제. DELETE /api/records/<pk>/comments/<comment_id>/"""
        record = self.get_object()
        comment = get_object_or_404(Comment, pk=comment_id, record=record)
        if comment.user_id != request.user.id:
            return Response({'detail': '본인의 댓글만 삭제할 수 있습니다.'},
                            status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        Record.objects.filter(pk=record.pk).update(
            comment_count=record.comments.count())
        return Response(status=status.HTTP_204_NO_CONTENT)


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


# ── 스티커 ──────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_stickers(request):
    """유저가 보유한 스티커 목록.

    GET /api/records/stickers/
    쿼리 파라미터: ?category=sticker (선택)
    """
    qs = UserSticker.objects.select_related('sticker').filter(
        user=request.user, sticker__is_active=True,
    )
    category = request.query_params.get('category')
    if category:
        qs = qs.filter(sticker__category=category)
    serializer = UserStickerSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def all_stickers(request):
    """전체 활성 스티커 목록 (카탈로그).

    GET /api/records/stickers/all/
    """
    qs = StickerAsset.objects.filter(is_active=True)
    category = request.query_params.get('category')
    if category:
        qs = qs.filter(category=category)
    serializer = StickerAssetSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def grant_default_stickers(request):
    """기본 스티커를 유저에게 부여. 회원가입 후 1회 호출.

    POST /api/records/stickers/init/
    """
    defaults = StickerAsset.objects.filter(is_default=True, is_active=True)
    created = 0
    for sticker in defaults:
        _, was_created = UserSticker.objects.get_or_create(
            user=request.user, sticker=sticker,
            defaults={'acquired_type': 'default'},
        )
        if was_created:
            created += 1
    return Response({'granted': created})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_sticker(request):
    """유저가 커스텀 스티커를 업로드.

    POST /api/records/stickers/upload/
    - image: 이미지 파일 (필수)
    - category: sticker/frame/bubble (기본 sticker)
    - name: 스티커명 (선택, 기본 파일명)
    """
    image = request.FILES.get('image')
    if not image:
        return Response({'detail': '이미지를 첨부해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    category = request.data.get('category', 'sticker')
    if category not in ('sticker', 'frame', 'bubble'):
        category = 'sticker'

    name = request.data.get('name', '') or image.name
    name = name[:100]

    asset = StickerAsset.objects.create(
        name=name,
        category=category,
        image=image,
        is_default=False,
        is_active=True,
    )
    UserSticker.objects.create(
        user=request.user,
        sticker=asset,
        acquired_type='purchase',
    )
    serializer = StickerAssetSerializer(asset, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)

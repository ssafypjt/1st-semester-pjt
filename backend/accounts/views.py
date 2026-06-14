"""인증 + 팔로우 API — 세션 기반."""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Count
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import (api_view, parser_classes, permission_classes,
                                       throttle_classes)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import Follow, User
from .serializers import (FollowUserSerializer, LoginSerializer, PasswordChangeSerializer,
                          PasswordResetConfirmSerializer, PasswordResetRequestSerializer,
                          ProfileUpdateSerializer, SignupSerializer, UserSerializer)

# 탈퇴 후 재로그인으로 계정을 복구할 수 있는 보관 기간 (purge_deleted_users 와 동일하게 유지).
ACCOUNT_RESTORE_DAYS = 30


class PasswordResetRequestThrottle(AnonRateThrottle):
    """비밀번호 재설정 메일 발송 — 메일 폭탄/계정 열거 방지용 IP 기준 제한."""
    scope = 'password_reset_request'


class PasswordResetConfirmThrottle(AnonRateThrottle):
    """비밀번호 재설정 확인 — 토큰 추측 시도 방지용 IP 기준 제한."""
    scope = 'password_reset_confirm'


@api_view(['GET'])
@permission_classes([AllowAny])
def csrf(request):
    return Response({'csrfToken': get_token(request)})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    login(request, user)
    return Response(
        UserSerializer(user, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email'].lower().strip()
    password = serializer.validated_data['password']
    user = authenticate(request, username=email, password=password)

    if user is None:
        # is_active=False 인 계정은 ModelBackend가 인증을 거부한다.
        # 탈퇴(soft delete) 후 보관 기간(30일) 이내이고 비밀번호가 일치하면
        # 계정을 복구(is_active=True, deleted_at=None)하고 로그인 처리한다.
        restored_user = _try_restore_account(email, password)
        if restored_user is not None:
            login(request, restored_user)
            data = UserSerializer(restored_user, context={'request': request}).data
            data['account_restored'] = True
            return Response(data)

        return Response(
            {'detail': '이메일 또는 비밀번호가 올바르지 않습니다.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    login(request, user)
    return Response(UserSerializer(user, context={'request': request}).data)


def _try_restore_account(email, password):
    """탈퇴 후 30일 이내인 계정이면 비밀번호 확인 후 복구해 반환, 아니면 None.

    복구 시 is_active=True 로 돌아가므로 RecordViewSet/comments 등의
    `user__is_active=True` 필터에 의해 비공개 처리됐던 기록/댓글이 자동으로
    다시 노출된다 (별도의 visibility 복원 로직 불필요).
    """
    candidate = User.objects.filter(
        email__iexact=email, is_active=False, deleted_at__isnull=False,
    ).first()
    if candidate is None or not candidate.check_password(password):
        return None

    cutoff = timezone.now() - timedelta(days=ACCOUNT_RESTORE_DAYS)
    if candidate.deleted_at < cutoff:
        return None

    candidate.is_active = True
    candidate.deleted_at = None
    candidate.save(update_fields=['is_active', 'deleted_at'])
    return candidate


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'detail': '로그아웃 되었습니다.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def password_change(request):
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save(update_fields=['password'])
    update_session_auth_hash(request, request.user)
    return Response({'detail': '비밀번호가 변경되었습니다.'})


# ── 비밀번호 재설정 (이메일 인증) ──────────────────────
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRequestThrottle])
def password_reset_request(request):
    """비밀번호 재설정 메일 발송 요청.

    - 계정 존재 여부와 무관하게 항상 동일한 응답을 반환한다 (이메일 등록 여부 노출 방지).
    - 메일에는 프론트엔드 재설정 페이지 링크(uid, token 포함)를 담는다.
      프론트는 해당 페이지에서 uid/token/new_password를 confirm 엔드포인트로 전송.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email'].lower().strip()

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is not None:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f'{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}'
        send_mail(
            subject='[덕꾸] 비밀번호 재설정 안내',
            message=(
                f'{user.nickname}님, 아래 링크에서 비밀번호를 재설정해주세요.\n'
                f'{reset_url}\n\n'
                '본인이 요청하지 않았다면 이 메일을 무시해주세요.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    return Response({'detail': '이메일이 등록되어 있다면 비밀번호 재설정 링크를 발송했습니다.'})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetConfirmThrottle])
def password_reset_confirm(request):
    """비밀번호 재설정 확인. uid/token + new_password."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        user_id = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
        user = User.objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'detail': '유효하지 않은 요청입니다.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, serializer.validated_data['token']):
        return Response({'detail': '재설정 링크가 유효하지 않거나 만료되었습니다.'},
                        status=status.HTTP_400_BAD_REQUEST)

    new_password = serializer.validated_data['new_password']
    try:
        # user 컨텍스트를 포함해 검증 — UserAttributeSimilarityValidator 등이
        # 이메일/닉네임과 유사한 비밀번호를 차단할 수 있도록 한다
        # (PasswordChangeSerializer와 동일한 수준의 검증).
        validate_password(new_password, user=user)
    except DjangoValidationError as e:
        return Response({'new_password': list(e.messages)},
                        status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save(update_fields=['password'])
    return Response({'detail': '비밀번호가 재설정되었습니다. 새 비밀번호로 로그인해주세요.'})


# ── 회원 탈퇴 (soft delete) ────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def account_delete(request):
    """회원 탈퇴 (soft delete).

    - is_active=False, deleted_at=now() 설정 후 세션 로그아웃.
    - 즉시 비공개: 팔로워/팔로잉/프로필 조회 및 RecordViewSet, 댓글 목록 등이
      모두 user__is_active=True 를 필터링하므로, 탈퇴 직후부터 기록/댓글이
      다른 사용자에게 노출되지 않는다 (visibility 값 자체는 변경하지 않음).
    - 30일 이내 같은 이메일/비밀번호로 로그인하면 is_active=True, deleted_at=None
      으로 자동 복구되어 위 콘텐츠가 다시 공개된다 (login_view._try_restore_account).
    - 복구 없이 30일이 지나면 `python manage.py purge_deleted_users` 로 영구 삭제.
    """
    user = request.user
    user.is_active = False
    user.deleted_at = timezone.now()
    user.save(update_fields=['is_active', 'deleted_at'])
    logout(request)
    return Response({'detail': '탈퇴 처리되었습니다. 30일간 데이터가 보관된 후 영구 삭제됩니다.'})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def profile_update(request):
    serializer = ProfileUpdateSerializer(
        request.user,
        data=request.data,
        partial=True,
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserSerializer(user, context={'request': request}).data)


# ── 유저 프로필 공개 조회 ─────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def user_profile(request, pk):
    """타인 프로필 공개 조회.

    follower_count / following_count 를 annotate로 한 번에 집계해 N+1 방지.
    """
    user = get_object_or_404(
        User.objects.annotate(
            follower_count=Count('follower_set', distinct=True),
            following_count=Count('following_set', distinct=True),
        ),
        pk=pk,
        is_active=True,
    )
    return Response(UserSerializer(user, context={'request': request}).data)


# ── 팔로우 토글 ──────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_toggle(request, pk):
    """팔로우 / 언팔로우 토글.

    - 자기 자신은 팔로우 불가 (400 반환).
    - 이미 팔로우 중이면 삭제(언팔로우), 아니면 생성(팔로우).
    - 응답: { following: bool, follower_count: int }
    """
    if request.user.pk == pk:
        return Response({'detail': '자기 자신을 팔로우할 수 없습니다.'},
                        status=status.HTTP_400_BAD_REQUEST)

    target = get_object_or_404(User, pk=pk, is_active=True)
    follow_qs = Follow.objects.filter(follower=request.user, following=target)

    if follow_qs.exists():
        follow_qs.delete()
        is_following = False
    else:
        try:
            Follow.objects.create(follower=request.user, following=target)
        except IntegrityError:
            # 동시 요청으로 이미 생성된 경우 — 팔로우 상태로 간주
            pass
        is_following = True

    follower_count = target.follower_set.count()
    return Response({'following': is_following, 'follower_count': follower_count})


# ── 팔로워 / 팔로잉 목록 ─────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def follower_list(request, pk):
    """pk 유저의 팔로워 목록."""
    get_object_or_404(User, pk=pk, is_active=True)
    users = User.objects.filter(following_set__following_id=pk, is_active=True)
    serializer = FollowUserSerializer(users, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def following_list(request, pk):
    """pk 유저의 팔로잉 목록."""
    get_object_or_404(User, pk=pk, is_active=True)
    users = User.objects.filter(follower_set__follower_id=pk, is_active=True)
    serializer = FollowUserSerializer(users, many=True, context={'request': request})
    return Response(serializer.data)

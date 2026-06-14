"""인증 + 팔로우 API — 세션 기반."""
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db.models import Count
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Follow, User
from .serializers import (FollowUserSerializer, LoginSerializer, PasswordChangeSerializer,
                          ProfileUpdateSerializer, SignupSerializer, UserSerializer)


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
    user = authenticate(
        request,
        username=email,
        password=serializer.validated_data['password'],
    )
    if user is None:
        return Response(
            {'detail': '이메일 또는 비밀번호가 올바르지 않습니다.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    login(request, user)
    return Response(UserSerializer(user, context={'request': request}).data)


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
        Follow.objects.create(follower=request.user, following=target)
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

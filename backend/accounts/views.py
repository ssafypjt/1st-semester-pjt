"""인증 API — 세션 기반.

배포에서도 세션 인증을 그대로 쓴다 (HttpOnly 쿠키 + CSRF 토큰).
JWT 로의 전환은 모바일 앱이 생기는 시점에 검토.

프로필 이미지:
- 회원가입(POST /api/auth/signup/) 시 multipart/form-data 로 선택적 업로드 가능.
- 가입 후 수정은 PATCH /api/auth/me/update/ 로 처리.
"""
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import LoginSerializer, ProfileUpdateSerializer, SignupSerializer, UserSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def csrf(request):
    """CSRF 토큰 발급. 프론트는 이후 요청의 X-CSRFToken 헤더에 부착."""
    return Response({'csrfToken': get_token(request)})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def signup(request):
    """회원가입 + 즉시 로그인.

    Content-Type:
      - multipart/form-data  → 프로필 이미지 포함 가능
      - application/json     → 이미지 없이 가입 (기존 방식 호환)

    이메일/닉네임/패스워드 정책 검증은 SignupSerializer 가 담당한다.
    """
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


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'detail': '로그아웃 되었습니다.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user, context={'request': request}).data)


@csrf_exempt
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def profile_update(request):
    """닉네임 · 프로필 이미지 수정.

    PATCH /api/auth/me/update/
    Content-Type: multipart/form-data
      - nickname      (선택)
      - profile_image (선택, 이미지 파일)
    """
    serializer = ProfileUpdateSerializer(
        request.user,
        data=request.data,
        partial=True,
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserSerializer(user, context={'request': request}).data)

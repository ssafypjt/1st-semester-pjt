"""계정 시리얼라이저.

회원가입은 다음 단계를 모두 통과해야 한다:
1) 이메일 형식 + 중복 체크 (DB unique 제약 위반을 사전에 사용자 친화 메시지로 변환)
2) 닉네임 길이 (2~20)
3) 비밀번호 정책 (Django AUTH_PASSWORD_VALIDATORS — 길이 8자 이상,
   너무 흔한 단어 금지, 사용자 정보와 유사 금지, 숫자만 안 됨)
4) 프로필 이미지 — 선택 사항. 회원가입 또는 프로필 수정 시 업로드 가능.
"""
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import SocialAccount, User

# 프로필 이미지 허용 확장자 (RecordImage와 동일 기준)
PROFILE_ALLOWED_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}


def validate_profile_image(image):
    """확장자 + 파일 크기 공통 검증. Serializer의 validate_profile_image에서 호출."""
    import os
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in PROFILE_ALLOWED_EXT:
        raise serializers.ValidationError(
            f'허용되지 않는 확장자입니다. ({", ".join(sorted(PROFILE_ALLOWED_EXT))})'
        )
    max_bytes = getattr(settings, 'MEDIA_MAX_UPLOAD_BYTES', 8 * 1024 * 1024)
    if image.size > max_bytes:
        raise serializers.ValidationError(
            f'파일 크기는 {max_bytes // (1024 * 1024)}MB 이하여야 합니다.'
        )
    return image


class UserSerializer(serializers.ModelSerializer):
    """현재 로그인한 사용자 정보 응답용."""
    # 필드명은 profile_image 유지 (프론트 호환) — 값은 절대 URL로 반환
    profile_image = serializers.SerializerMethodField()
    # 연결된 소셜 제공자 목록 (예: ["google", "kakao"])
    social_providers = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'nickname', 'profile_image',
                  'social_providers', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_profile_image(self, obj):
        """업로드된 이미지는 절대 URL, 없으면 None."""
        if not obj.profile_image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.profile_image.url)
        return obj.profile_image.url

    def get_social_providers(self, obj):
        """연결된 소셜 제공자 이름 목록. 로컬 전용 계정은 빈 리스트."""
        return list(obj.social_accounts.values_list('provider', flat=True))


class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    nickname = serializers.CharField(min_length=2, max_length=20)
    password = serializers.CharField(
        write_only=True, min_length=8,
        style={'input_type': 'password'},
    )
    # 회원가입 시 프로필 이미지 선택적 업로드
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'nickname', 'profile_image']

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('이미 가입된 이메일입니다.')
        return value

    def validate_nickname(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('닉네임을 입력해주세요.')
        return value

    def validate_profile_image(self, value):
        if value:
            validate_profile_image(value)
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        tmp_user = User(email=attrs.get('email'), nickname=attrs.get('nickname'))
        try:
            validate_password(password, user=tmp_user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        # profile_image는 user.pk 확정 후 저장해야 upload_to가 올바른 경로를 쓸 수 있음
        profile_image = validated_data.pop('profile_image', None)
        user = User.objects.create_user(**validated_data)
        if profile_image:
            user.profile_image = profile_image
            user.save(update_fields=['profile_image'])
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """닉네임 · 프로필 이미지 수정용 (PATCH /api/auth/me/update/).

    profile_image 처리 규칙:
      - 필드 자체를 보내지 않음   → 이미지 변경 없음
      - 이미지 파일을 보냄        → 새 이미지로 교체 (기존 파일 삭제)
      - remove_profile_image=true → 이미지 삭제 (빈 문자열/null 대신 명시적 플래그)
    """
    profile_image = serializers.ImageField(required=False, allow_null=True)
    # 이미지 삭제 전용 플래그 (폼 데이터로 "true" 문자열로 올 수 있음)
    remove_profile_image = serializers.BooleanField(
        required=False, default=False, write_only=True,
    )

    class Meta:
        model = User
        fields = ['nickname', 'profile_image', 'remove_profile_image']

    def validate_nickname(self, value):
        return value.strip()

    def validate_profile_image(self, value):
        if value:
            validate_profile_image(value)
        return value

    def update(self, instance, validated_data):
        instance.nickname = validated_data.get('nickname', instance.nickname)

        remove = validated_data.pop('remove_profile_image', False)
        new_image = validated_data.get('profile_image')

        if remove:
            # 명시적 삭제 요청 — 파일 제거 후 필드 비움
            if instance.profile_image:
                instance.profile_image.delete(save=False)
            instance.profile_image = None
        elif new_image is not None:
            # 새 이미지 교체 — 기존 파일 먼저 삭제
            if instance.profile_image:
                instance.profile_image.delete(save=False)
            instance.profile_image = new_image

        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True,
                                     style={'input_type': 'password'})


class PasswordChangeSerializer(serializers.Serializer):
    """비밀번호 변경 — 기존 비밀번호 검증 후 새 비밀번호로 교체."""
    old_password = serializers.CharField(
        write_only=True, style={'input_type': 'password'},
    )
    new_password = serializers.CharField(
        write_only=True, min_length=8, style={'input_type': 'password'},
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('기존 비밀번호가 일치하지 않습니다.')
        return value

    def validate_new_password(self, value):
        user = self.context['request'].user
        try:
            validate_password(value, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {'new_password': '새 비밀번호는 기존 비밀번호와 달라야 합니다.'}
            )
        return attrs

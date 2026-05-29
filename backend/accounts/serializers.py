"""계정 시리얼라이저.

회원가입은 다음 단계를 모두 통과해야 한다:
1) 이메일 형식 + 중복 체크 (DB unique 제약 위반을 사전에 사용자 친화 메시지로 변환)
2) 닉네임 길이 (2~20)
3) 비밀번호 정책 (Django AUTH_PASSWORD_VALIDATORS — 길이 8자 이상,
   너무 흔한 단어 금지, 사용자 정보와 유사 금지, 숫자만 안 됨)
4) 프로필 이미지 — 선택 사항. 회원가입 또는 프로필 수정 시 업로드 가능.
"""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """현재 로그인한 사용자 정보 응답용."""
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'nickname', 'profile_image_url',
                  'provider', 'created_at']
        read_only_fields = ['id', 'provider', 'created_at']

    def get_profile_image_url(self, obj):
        """업로드된 이미지는 /media/ URL로, 없으면 None."""
        if not obj.profile_image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.profile_image.url)
        return obj.profile_image.url


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
    """닉네임 · 프로필 이미지 수정용 (PATCH /api/auth/me/)."""
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['nickname', 'profile_image']

    def validate_nickname(self, value):
        return value.strip()

    def update(self, instance, validated_data):
        instance.nickname = validated_data.get('nickname', instance.nickname)
        new_image = validated_data.get('profile_image')
        if new_image is not None:
            # 기존 파일 삭제 (선택 사항 — 스토리지 정리)
            if instance.profile_image:
                instance.profile_image.delete(save=False)
            instance.profile_image = new_image
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True,
                                     style={'input_type': 'password'})

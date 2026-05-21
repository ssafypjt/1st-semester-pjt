"""계정 시리얼라이저.

회원가입은 다음 단계를 모두 통과해야 한다:
1) 이메일 형식 + 중복 체크 (DB unique 제약 위반을 사전에 사용자 친화 메시지로 변환)
2) 닉네임 길이 (2~20)
3) 비밀번호 정책 (Django AUTH_PASSWORD_VALIDATORS — settings 에서 길이 8자 이상,
   너무 흔한 단어 금지, 사용자 정보와 유사 금지, 숫자만 안 됨)
"""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """현재 로그인한 사용자 정보 응답용."""

    class Meta:
        model = User
        fields = ['id', 'email', 'nickname', 'profile_image',
                  'provider', 'created_at']
        read_only_fields = ['id', 'provider', 'created_at']


class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    nickname = serializers.CharField(min_length=2, max_length=20)
    password = serializers.CharField(write_only=True, min_length=8,
                                     style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'password', 'nickname']

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
        tmp_user = User(email=attrs.get('email'),
                        nickname=attrs.get('nickname'))
        try:
            validate_password(password, user=tmp_user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True,
                                     style={'input_type': 'password'})

"""계정 시리얼라이저."""
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Follow, SocialAccount, User

PROFILE_ALLOWED_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}


def validate_profile_image(image):
    import os
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in PROFILE_ALLOWED_EXT:
        raise serializers.ValidationError(
            f"허용되지 않는 확장자입니다. ({', '.join(sorted(PROFILE_ALLOWED_EXT))})"
        )
    max_bytes = getattr(settings, 'MEDIA_MAX_UPLOAD_BYTES', 8 * 1024 * 1024)
    if image.size > max_bytes:
        raise serializers.ValidationError(
            f'파일 크기는 {max_bytes // (1024 * 1024)}MB 이하여야 합니다.'
        )
    return image


class UserSerializer(serializers.ModelSerializer):
    """로그인 유저 본인 정보 응답용.

    follower_count / following_count: annotate 또는 역참조 집계.
    is_following: 요청자가 이 유저를 팔로우 중인지 여부 (본인 조회 시 False).
    """
    profile_image = serializers.SerializerMethodField()
    social_providers = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'nickname', 'profile_image', 'social_providers',
            'follower_count', 'following_count', 'is_following',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_profile_image(self, obj):
        if not obj.profile_image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.profile_image.url)
        return obj.profile_image.url

    def get_social_providers(self, obj):
        return list(obj.social_accounts.values_list('provider', flat=True))

    def get_follower_count(self, obj):
        # annotate('follower_count')가 있으면 그 값을, 없으면 역참조 집계
        if hasattr(obj, 'follower_count'):
            return obj.follower_count
        return obj.follower_set.count()

    def get_following_count(self, obj):
        if hasattr(obj, 'following_count'):
            return obj.following_count
        return obj.following_set.count()

    def get_is_following(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if request.user.pk == obj.pk:
            return False
        return Follow.objects.filter(follower=request.user, following=obj).exists()


class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    nickname = serializers.CharField(min_length=2, max_length=20)
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
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
        profile_image = validated_data.pop('profile_image', None)
        user = User.objects.create_user(**validated_data)
        if profile_image:
            user.profile_image = profile_image
            user.save(update_fields=['profile_image'])
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    remove_profile_image = serializers.BooleanField(required=False, default=False, write_only=True)

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
            if instance.profile_image:
                instance.profile_image.delete(save=False)
            instance.profile_image = None
        elif new_image is not None:
            if instance.profile_image:
                instance.profile_image.delete(save=False)
            instance.profile_image = new_image
        instance.save()
        return instance


class FollowUserSerializer(serializers.ModelSerializer):
    """팔로워/팔로잉 목록의 유저 카드용 (경량)."""
    profile_image = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'nickname', 'profile_image', 'is_following']

    def get_profile_image(self, obj):
        if not obj.profile_image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.profile_image.url)
        return obj.profile_image.url

    def get_is_following(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if request.user.pk == obj.pk:
            return False
        return Follow.objects.filter(follower=request.user, following=obj).exists()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

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

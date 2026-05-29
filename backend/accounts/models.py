"""
User 모델 (ERD).
- 이메일 로그인
- 소셜 로그인은 SocialAccount 테이블로 분리 (1계정 N소셜 연동 지원)
- 로컬 회원가입 시 프로필 이미지 직접 업로드 지원 (ImageField)
"""
import os
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


def profile_image_upload_to(instance, filename):
    """프로필 이미지를 uploads/profiles/<user_id>/<uuid>.<ext> 경로에 저장."""
    ext = os.path.splitext(filename)[1].lower()
    user_id = instance.pk or 'tmp'
    return f'uploads/profiles/{user_id}/{uuid.uuid4().hex}{ext}'


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, nickname='', **extra):
        if not email:
            raise ValueError('이메일은 필수입니다.')
        email = self.normalize_email(email)
        user = self.model(email=email, nickname=nickname or email.split('@')[0], **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """ERD: User — 이메일 기반 단일 계정. 소셜 로그인은 SocialAccount 참조."""

    email = models.EmailField('이메일', max_length=255, unique=True)
    nickname = models.CharField('닉네임', max_length=50)
    profile_image = models.ImageField(
        '프로필 이미지',
        upload_to=profile_image_upload_to,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField('가입일', auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname']

    class Meta:
        db_table = 'user'

    def __str__(self):
        return f'{self.nickname} ({self.email})'


class SocialAccount(models.Model):
    """소셜 로그인 연동 정보. User 1개에 여러 소셜 계정 연결 가능."""

    PROVIDER_CHOICES = [
        ('google', 'Google'),
        ('kakao', 'Kakao'),
        ('apple', 'Apple'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='social_accounts',
        verbose_name='사용자',
    )
    provider = models.CharField('소셜 제공자', max_length=20, choices=PROVIDER_CHOICES)
    provider_id = models.CharField('소셜 고유 ID', max_length=255)
    access_token = models.TextField('액세스 토큰', blank=True, null=True)
    refresh_token = models.TextField('리프레시 토큰', blank=True, null=True)
    created_at = models.DateTimeField('연동일', auto_now_add=True)

    class Meta:
        db_table = 'social_account'
        unique_together = [('provider', 'provider_id')]  # 동일 소셜 계정 중복 연결 방지

    def __str__(self):
        return f'{self.user.nickname} — {self.provider}'

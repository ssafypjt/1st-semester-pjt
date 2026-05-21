"""
User 모델 (ERD).
- 이메일 로그인
- 소셜 로그인 확장 대비 (provider/provider_id NULL 허용)
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


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
    """ERD: User"""
    PROVIDER_CHOICES = [
        ('local', 'Local'),
        ('google', 'Google'),
        ('kakao', 'Kakao'),
        ('apple', 'Apple'),
    ]

    email = models.EmailField('이메일', max_length=255, unique=True)
    nickname = models.CharField('닉네임', max_length=50)
    profile_image = models.URLField('프로필 이미지', max_length=500, blank=True)
    provider = models.CharField('소셜 제공자', max_length=20, choices=PROVIDER_CHOICES, default='local')
    provider_id = models.CharField('소셜 ID', max_length=255, blank=True, null=True)
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

"""
덕꾸 (Deokkku) Django settings.

배포 표준 구성:
- 모든 환경변수는 backend/.env 파일에서 읽는다 (django-environ).
- .env 가 없으면 개발용 합리적 기본값으로 동작한다.
- DEBUG=False 일 때 보안 옵션(SSL 리다이렉트, secure 쿠키 등)이 켜진다.
- DATABASE_URL 이 있으면 그걸 사용하고, 없으면 SQLite.
- 미디어는 기본 로컬 디스크. 운영에서는 보호된 view 를 통해서만 접근하도록
  /media/ 의 직접 서빙은 DEBUG=True 인 경우에만 활성화한다.
"""
from pathlib import Path
import mimetypes
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / 'frontend'

mimetypes.add_type('application/javascript', '.js', True)
mimetypes.add_type('text/css', '.css', True)

# ── env ─────────────────────────────────────────────
env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    SECURE_SSL_REDIRECT=(bool, False),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
    MEDIA_MAX_UPLOAD_MB=(int, 8),
    EMAIL_PORT=(int, 25),
    EMAIL_USE_TLS=(bool, True),
)
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env(
    'DJANGO_SECRET_KEY',
    default='django-insecure-deokkku-dev-only-change-me',
)
DEBUG = env('DJANGO_DEBUG')
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ── apps / middleware ──────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'accounts',
    'works',
    'albums',
    'records',
    'shares',
    # DB 레코드 삭제 시 ImageField/FileField 물리 파일 동반 삭제
    'django_cleanup.apps.CleanupConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            FRONTEND_DIR / 'templates',
            BASE_DIR / 'templates',
            FRONTEND_DIR / 'dist',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── 데이터베이스 ───────────────────────────────────
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
    ),
}

AUTH_USER_MODEL = 'accounts.User'

# ── 패스워드 검증 (배포 기준 — 강화) ───────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# ── 정적 / 미디어 ──────────────────────────────────
STATIC_URL = '/static/'
_vite_dist = FRONTEND_DIR / 'dist'
STATICFILES_DIRS = [
    FRONTEND_DIR / 'static',
]
if _vite_dist.exists():
    STATICFILES_DIRS.append(_vite_dist)
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_MAX_UPLOAD_BYTES = env('MEDIA_MAX_UPLOAD_MB') * 1024 * 1024

# ── 이메일 (비밀번호 재설정 등) ─────────────────────
# 개발 기본값: 콘솔에 출력 (runserver 로그에서 메일 내용 확인 가능).
# 운영에서는 .env 에 SMTP 정보를 채워 EMAIL_BACKEND 를 smtp 로 전환.
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='no-reply@deokkku.local')

# 비밀번호 재설정 링크 생성 시 사용할 프론트엔드 베이스 URL.
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:5173')

# ── 외부 작품 메타데이터 API (2단계 스캐폴딩) ────────
# 현재는 키/엔드포인트 설정과 works/services/ 의 클라이언트 모듈만 준비됨.
# 검색 API, Work.get_or_create 동기화 등은 후속 작업 (PROJECT_CONTEXT.md 참고).
ANILIST_API_URL = env('ANILIST_API_URL', default='https://graphql.anilist.co')
TMDB_API_KEY = env('TMDB_API_KEY', default='')
TMDB_API_BASE_URL = env('TMDB_API_BASE_URL', default='https://api.themoviedb.org/3')
GOOGLE_BOOKS_API_KEY = env('GOOGLE_BOOKS_API_KEY', default='')
GOOGLE_BOOKS_API_BASE_URL = env(
    'GOOGLE_BOOKS_API_BASE_URL', default='https://www.googleapis.com/books/v1')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── GMS (AI 게이트웨이) ───────────────────────────────
GMS_API_URL = env('GMS_API_URL', default='https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions')
GMS_API_KEY = env('GMS_KEY', default='')
GMS_TIMEOUT = env.int('GMS_TIMEOUT', default=30)

# ── DRF ────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # 비밀번호 재설정 — 메일 폭탄 / 토큰 추측 시도 방지 (IP 기준).
    'DEFAULT_THROTTLE_RATES': {
        'password_reset_request': '5/hour',
        'password_reset_confirm': '10/hour',
    },
}

# ── CORS / CSRF ────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=[
        'http://localhost:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
    ],
)
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[
        'http://localhost:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
    ],
)

# ── 배포 보안 (DEBUG=False 일 때만 의미) ───────────
if not DEBUG:
    SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT')
    SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE')
    CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'

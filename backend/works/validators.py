"""works 앱 커스텀 validators."""
from urllib.parse import urlparse

from django.conf import settings
from rest_framework.exceptions import ValidationError


def validate_poster_url(value: str) -> None:
    """poster_image URLField 검증.

    1. HTTPS 스킴 필수 (Mixed Content 방지).
    2. POSTER_ALLOWED_DOMAINS 설정이 있으면 도메인 화이트리스트 검사.
    """
    if not value:
        return

    parsed = urlparse(value)

    if parsed.scheme != "https":
        raise ValidationError(
            f"포스터 URL은 HTTPS여야 합니다. (현재 스킴: {parsed.scheme or '없음'})"
        )

    allowed_domains = getattr(settings, "POSTER_ALLOWED_DOMAINS", [])
    if not allowed_domains:
        return

    host = parsed.hostname or ""
    if not any(host == d or host.endswith(f".{d}") for d in allowed_domains):
        raise ValidationError(f"허용되지 않은 포스터 URL 도메인입니다: {host}")

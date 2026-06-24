"""records 앱 권한 클래스.

IsOwnerOrReadOnly
─────────────────
- SAFE_METHODS (GET / HEAD / OPTIONS) 는 인증 여부와 무관하게 통과.
  단, queryset 단계에서 visibility 필터링이 이미 걸려 있으므로 노출 범위는
  자연스럽게 좁아진다.
- 그 외(POST/PATCH/DELETE) 는 로그인 필수, 그리고 본인 소유물이어야 함.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == request.user.id

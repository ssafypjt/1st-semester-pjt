from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'nickname', 'provider', 'created_at', 'is_staff')
    list_filter = ('provider', 'is_staff')
    search_fields = ('email', 'nickname')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('프로필', {'fields': ('nickname', 'profile_image')}),
        ('소셜 로그인', {'fields': ('provider', 'provider_id')}),
        ('권한', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password1', 'password2'),
        }),
    )

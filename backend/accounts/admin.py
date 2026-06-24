from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import SocialAccount, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'nickname', 'created_at', 'is_staff')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'nickname')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('프로필', {'fields': ('nickname', 'profile_image')}),
        ('권한', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password1', 'password2'),
        }),
    )


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'provider_id', 'created_at')
    list_filter = ('provider',)
    search_fields = ('user__email', 'user__nickname', 'provider_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

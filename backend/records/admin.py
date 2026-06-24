from django.contrib import admin

from .models import (
    Comment, Decoration, FavoriteScene, Like, Record, RecordImage,
    StickerAsset, UserSticker,
)


class DecorationInline(admin.TabularInline):
    model = Decoration
    extra = 0


class FavoriteSceneInline(admin.TabularInline):
    model = FavoriteScene
    extra = 0


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'work', 'user', 'rating', 'visibility',
                    'status', 'created_at')
    list_filter = ('status', 'visibility')
    search_fields = ('work__title', 'user__nickname', 'content')
    inlines = [DecorationInline, FavoriteSceneInline]


@admin.register(Decoration)
class DecorationAdmin(admin.ModelAdmin):
    list_display = ('id', 'record', 'type', 'position_x', 'position_y')
    list_filter = ('type',)


@admin.register(FavoriteScene)
class FavoriteSceneAdmin(admin.ModelAdmin):
    list_display = ('id', 'record', 'order_index')


@admin.register(RecordImage)
class RecordImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploader', 'record', 'size', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('uploader__email', 'uploader__nickname', 'original_name')
    readonly_fields = ('size', 'original_name', 'created_at')


@admin.register(StickerAsset)
class StickerAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'is_default', 'is_active', 'order')
    list_filter = ('category', 'is_default', 'is_active')
    list_editable = ('order', 'is_active', 'is_default')
    search_fields = ('name',)


@admin.register(UserSticker)
class UserStickerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'sticker', 'acquired_type', 'acquired_at')
    list_filter = ('acquired_type',)
    search_fields = ('user__nickname', 'sticker__name')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'record', 'user', 'created_at')
    search_fields = ('user__nickname', 'user__email')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'record', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__nickname', 'content')

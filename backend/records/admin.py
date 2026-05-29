from django.contrib import admin

from .models import Decoration, FavoriteScene, Record, RecordImage


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

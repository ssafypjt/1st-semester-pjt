from django.contrib import admin
from .models import Album, AlbumRecord


class AlbumRecordInline(admin.TabularInline):
    model = AlbumRecord
    extra = 0


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'visibility', 'created_at')
    list_filter = ('visibility',)
    search_fields = ('name', 'user__nickname')
    inlines = [AlbumRecordInline]


@admin.register(AlbumRecord)
class AlbumRecordAdmin(admin.ModelAdmin):
    list_display = ('album', 'record', 'added_at')

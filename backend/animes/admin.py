from django.contrib import admin
from .models import Anime


@admin.register(Anime)
class AnimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'title_ko', 'genre', 'release_date', 'source')
    list_filter = ('genre', 'source')
    search_fields = ('title', 'title_ko', 'title_en')

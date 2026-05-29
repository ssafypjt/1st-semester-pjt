from django.contrib import admin
from .models import Work


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'title_ko', 'work_type', 'genre', 'release_date', 'source')
    list_filter = ('work_type', 'genre', 'source')
    search_fields = ('title', 'title_ko', 'title_en')

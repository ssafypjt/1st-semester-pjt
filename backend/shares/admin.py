from django.contrib import admin
from .models import CardTemplate, ShareCard


@admin.register(CardTemplate)
class CardTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']


@admin.register(ShareCard)
class ShareCardAdmin(admin.ModelAdmin):
    list_display = ['id', 'record', 'template', 'ai_model', 'created_at']
    list_filter = ['ai_model']
    raw_id_fields = ['record', 'template']

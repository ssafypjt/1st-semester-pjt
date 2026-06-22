from rest_framework import serializers
from .models import CardTemplate, ShareCard


class CardTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardTemplate
        fields = ['id', 'name', 'category', 'thumbnail', 'layout_schema']


class ShareCardSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    template_name = serializers.CharField(
        source='template.name', read_only=True, default='')

    class Meta:
        model = ShareCard
        fields = ['id', 'record', 'template', 'template_name',
                  'layout_data', 'image_url', 'ai_model',
                  'created_at']
        read_only_fields = fields

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ShareCardCreateSerializer(serializers.Serializer):
    """공유 카드 생성 요청 시리얼라이저.

    선택적으로 template_id를 지정하면 AI가 해당 템플릿으로 고정.
    미지정 시 AI가 자동 선택.
    """
    template_id = serializers.IntegerField(required=False, allow_null=True)

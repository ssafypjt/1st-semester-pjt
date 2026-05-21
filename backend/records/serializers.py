"""records 시리얼라이저.

- 이미지 응답의 url 은 **항상 protected URL** (/api/records/uploads/<id>/) 로 돌려준다.
  배포에서 /media/ 직접 노출이 차단돼도 동작이 깨지지 않는다.
- 작품은 드롭다운 선택이 아니라 작품명 텍스트(anime_title)로 받아 get_or_create.
"""
from rest_framework import serializers

from animes.models import Anime
from animes.serializers import AnimeSerializer

from .models import Decoration, FavoriteScene, Record, RecordImage


# ── RecordImage ──────────────────────────────────────
class RecordImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    filename = serializers.CharField(source='original_name', read_only=True)

    class Meta:
        model = RecordImage
        fields = ['id', 'url', 'filename', 'size', 'created_at']
        read_only_fields = fields

    def get_url(self, obj):
        return f'/api/records/uploads/{obj.pk}/'


# ── Decoration / FavoriteScene ───────────────────────
class DecorationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Decoration
        fields = ['id', 'type', 'content', 'position_x', 'position_y',
                  'width', 'height', 'rotation', 'z_index']


class FavoriteSceneSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteScene
        fields = ['id', 'image_url', 'order_index']


# ── Record ───────────────────────────────────────────
class _OwnershipMixin:
    """is_mine 필드용 헬퍼. request.user 와 obj.user_id 비교."""
    def get_is_mine(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.user_id == request.user.id


class RecordListSerializer(_OwnershipMixin, serializers.ModelSerializer):
    """목록용 (anime 정보 일부 포함)."""
    anime_title = serializers.CharField(source='anime.title_ko', read_only=True)
    anime_poster = serializers.CharField(source='anime.poster_image', read_only=True)
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    is_mine = serializers.SerializerMethodField()
    # 카드 대표 제목 — 사용자가 직접 지은 제목(canvas_data.title) 우선, 없으면 작품명.
    title = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ['id', 'user_nickname', 'anime', 'anime_title', 'anime_poster',
                  'title', 'rating', 'watched_date', 'visibility', 'like_count',
                  'comment_count', 'created_at', 'is_mine']

    def get_title(self, obj):
        cd = obj.canvas_data or {}
        return (cd.get('title') or '').strip() \
            or obj.anime.title_ko or obj.anime.title


class RecordDetailSerializer(_OwnershipMixin, serializers.ModelSerializer):
    """상세용 (anime 전체, decoration, favorite_scene 포함).

    작품은 작품명 텍스트(anime_title)로 받는다. 같은 제목이면 Anime 재사용,
    없으면 새로 만든다. 하위호환을 위해 anime_id 도 받지만 anime_title 우선.
    """
    anime = AnimeSerializer(read_only=True)
    anime_id = serializers.PrimaryKeyRelatedField(
        queryset=Anime.objects.all(),
        source='anime', write_only=True, required=False,
    )
    anime_title = serializers.CharField(write_only=True, required=False,
                                        allow_blank=True)
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    decorations = DecorationSerializer(many=True, read_only=True)
    favorite_scenes = FavoriteSceneSerializer(many=True, read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ['id', 'user_nickname', 'anime', 'anime_id', 'anime_title',
                  'rating', 'watched_date', 'content', 'canvas_data', 'status',
                  'visibility', 'like_count', 'comment_count',
                  'decorations', 'favorite_scenes', 'is_mine',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'like_count', 'comment_count',
                            'created_at', 'updated_at', 'is_mine']

    def _resolve_anime(self, validated_data):
        title = (validated_data.pop('anime_title', '') or '').strip()
        if title:
            anime, _ = Anime.objects.get_or_create(
                title_ko=title,
                defaults={'title': title},
            )
            validated_data['anime'] = anime

    def validate(self, attrs):
        if self.instance is None:
            has_title = bool((attrs.get('anime_title') or '').strip())
            has_anime = attrs.get('anime') is not None
            if not has_title and not has_anime:
                raise serializers.ValidationError(
                    {'anime_title': '작품명을 입력해주세요.'})
        return attrs

    def create(self, validated_data):
        self._resolve_anime(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._resolve_anime(validated_data)
        return super().update(instance, validated_data)

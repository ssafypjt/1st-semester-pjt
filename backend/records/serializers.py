"""records 시리얼라이저.

- 이미지 응답의 url 은 **항상 protected URL** (/api/records/uploads/<id>/) 로 돌려준다.
  배포에서 /media/ 직접 노출이 차단돼도 동작이 깨지지 않는다.
- 작품은 드롭다운 선택이 아니라 작품명 텍스트(work_title)로 받아 get_or_create.
"""
from rest_framework import serializers

from works.models import Work
from works.serializers import WorkSerializer

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
    """목록용 (work 정보 일부 포함)."""
    work_title = serializers.CharField(source='work.title_ko', read_only=True)
    work_poster = serializers.CharField(source='work.poster_image', read_only=True)
    work_type = serializers.CharField(source='work.work_type', read_only=True)
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    is_mine = serializers.SerializerMethodField()
    # 카드 대표 제목 — 사용자가 직접 지은 제목(canvas_data.title) 우선, 없으면 작품명.
    title = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ['id', 'user_nickname', 'work', 'work_title', 'work_poster',
                  'work_type', 'title', 'rating', 'watched_date', 'visibility',
                  'like_count', 'comment_count', 'created_at', 'is_mine']

    def get_title(self, obj):
        cd = obj.canvas_data or {}
        return (cd.get('title') or '').strip() \
            or obj.work.title_ko or obj.work.title


class RecordDetailSerializer(_OwnershipMixin, serializers.ModelSerializer):
    """상세용 (work 전체, decoration, favorite_scene 포함).

    작품은 작품명 텍스트(work_title)로 받는다. 같은 제목이면 Work 재사용,
    없으면 새로 만든다. 하위호환을 위해 work_id 도 받지만 work_title 우선.

    work_type_hint:
        동명이작 구분을 위한 선택적 필드.
        "강철의 연금술사"(애니) vs "강철의 연금술사"(도서)처럼
        title_ko 가 같아도 work_type 이 다르면 별개의 Work 로 처리한다.
        미전송 시 기본값 'anime'.
    """
    work = WorkSerializer(read_only=True)
    work_id = serializers.PrimaryKeyRelatedField(
        queryset=Work.objects.all(),
        source='work', write_only=True, required=False,
    )
    work_title = serializers.CharField(write_only=True, required=False,
                                       allow_blank=True)
    work_type_hint = serializers.ChoiceField(
        choices=Work.TYPE_CHOICES,
        write_only=True, required=False, default='anime',
        help_text='동명이작 구분용. work_title 과 함께 사용. 기본값: anime',
    )
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    decorations = DecorationSerializer(many=True, read_only=True)
    favorite_scenes = FavoriteSceneSerializer(many=True, read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ['id', 'user_nickname', 'work', 'work_id', 'work_title',
                  'work_type_hint',
                  'rating', 'watched_date', 'content', 'canvas_data', 'status',
                  'visibility', 'like_count', 'comment_count',
                  'decorations', 'favorite_scenes', 'is_mine',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'like_count', 'comment_count',
                            'created_at', 'updated_at', 'is_mine']

    def _resolve_work(self, validated_data):
        title = (validated_data.pop('work_title', '') or '').strip()
        work_type = validated_data.pop('work_type_hint', 'anime')
        if title:
            # title_ko + work_type 복합 키로 동명이작 구분.
            # 2단계에서 외부 API 연동 시 source + external_id 기반으로 교체 예정.
            work, _ = Work.objects.get_or_create(
                title_ko=title,
                work_type=work_type,
                defaults={'title': title},
            )
            validated_data['work'] = work
        else:
            validated_data.pop('work_type_hint', None)  # work_id 경로면 제거

    def validate(self, attrs):
        if self.instance is None:
            has_title = bool((attrs.get('work_title') or '').strip())
            has_work = attrs.get('work') is not None
            if not has_title and not has_work:
                raise serializers.ValidationError(
                    {'work_title': '작품명을 입력해주세요.'})
        return attrs

    def create(self, validated_data):
        self._resolve_work(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._resolve_work(validated_data)
        return super().update(instance, validated_data)

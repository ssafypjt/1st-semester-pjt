from rest_framework import serializers
from .models import Album, AlbumRecord


class AlbumSerializer(serializers.ModelSerializer):
    record_count = serializers.IntegerField(read_only=True)
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = Album
        fields = ['id', 'user', 'user_nickname', 'name', 'description',
                  'cover_image', 'visibility', 'record_count', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class AlbumRecordSerializer(serializers.ModelSerializer):
    """add_record 응답용.

    record의 핵심 정보(id, 작품명, 평점)를 함께 반환해 프론트가 추가 요청 없이 UI를 그릴 수 있도록 한다.
    """
    record_id = serializers.IntegerField(source='record.id', read_only=True)
    work_title = serializers.CharField(source='record.work.title_ko', read_only=True)
    rating = serializers.DecimalField(source='record.rating', max_digits=3,
                                      decimal_places=1, read_only=True)

    class Meta:
        model = AlbumRecord
        fields = ['album', 'record_id', 'work_title', 'rating', 'added_at']
        read_only_fields = fields

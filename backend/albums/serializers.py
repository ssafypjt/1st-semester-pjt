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
    class Meta:
        model = AlbumRecord
        fields = ['album', 'record', 'added_at']
        read_only_fields = ['added_at']

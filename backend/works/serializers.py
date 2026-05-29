from rest_framework import serializers
from .models import Work


class WorkSerializer(serializers.ModelSerializer):
    """작품 읽기용 시리얼라이저 (일반 유저 응답).

    internal 필드(external_id, source)는 외부에 노출하지 않는다.
    """
    class Meta:
        model = Work
        fields = [
            "id", "work_type", "title", "title_ko", "title_en",
            "release_date", "genre", "poster_image", "description",
        ]


class WorkAdminSerializer(serializers.ModelSerializer):
    """관리자 전용 읽기/쓰기 시리얼라이저.

    WorkSerializer와 달리 source, external_id 포함.
    create/update/destroy 액션에서 사용한다.
    """
    class Meta:
        model = Work
        fields = [
            "id", "work_type", "source", "external_id",
            "title", "title_ko", "title_en",
            "release_date", "genre", "poster_image", "description",
        ]

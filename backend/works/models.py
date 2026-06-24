"""Work 모델 — 작품 메타데이터."""
from django.db import models
from django.db.models import F

from .validators import validate_poster_url


class Work(models.Model):
    TYPE_CHOICES = [
        ("anime", "애니메이션"),
        ("movie", "영화"),
        ("book", "도서"),
        ("game", "게임"),
        ("drama", "드라마"),
        ("other", "기타"),
    ]

    work_type = models.CharField("작품 유형", max_length=20, choices=TYPE_CHOICES, default="anime")
    external_id = models.CharField("외부 API 작품 ID", max_length=100, blank=True)
    source = models.CharField("출처", max_length=30, blank=True,
                              help_text="AniList / TMDB / Google Books 등")
    title = models.CharField("제목", max_length=255)
    title_ko = models.CharField("한국어 제목", max_length=255, blank=True)
    title_en = models.CharField("영어 제목", max_length=255, blank=True)
    release_date = models.DateField("공개일", null=True, blank=True)
    genre = models.CharField("장르", max_length=100, blank=True)
    poster_image = models.URLField("포스터 URL", max_length=500, blank=True,
                                   validators=[validate_poster_url])
    description = models.TextField("작품 설명", blank=True)

    # AniList 태그 캐시 — 첫 조회 시 API에서 가져와 저장, 이후 DB에서 반환
    # 형식: {"genres": ["Action", ...], "tags": [{"name": "...", "category": "...", "rank": 90}, ...]}
    anilist_tags = models.JSONField("AniList 태그 캐시", default=None, null=True, blank=True)

    class Meta:
        db_table = "work"
        # release_date NULL 작품을 맨 뒤로 — SQLite, PostgreSQL 모두 동일 동작 보장
        ordering = [F("release_date").desc(nulls_last=True), "title"]
        indexes = [
            models.Index(fields=["-release_date", "title"], name="work_release_title_idx"),
            models.Index(fields=["work_type"], name="work_type_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                condition=~models.Q(source="") & ~models.Q(external_id=""),
                name="work_source_external_id_uniq",
            )
        ]

    def save(self, *args, **kwargs):
        if self.genre:
            self.genre = self.genre.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title_ko or self.title

<template>
  <div class="diary-preview-overlay" @click.self="$emit('close')">
    <section class="diary-preview-modal diary-preview-with-comments" role="dialog" aria-modal="true" aria-label="다이어리 원본 보기">
      <header class="diary-preview-header">
        <div>
          <small>DIARY PREVIEW</small>
          <h3>{{ previewRecord.title || '제목 없는 기록' }}</h3>
          <p v-if="previewRecord.author">{{ previewRecord.author }}님의 기록</p>
        </div>
        <button class="diary-preview-close" type="button" @click="$emit('close')">&#10005;</button>
      </header>

      <div v-if="previewError" class="diary-preview-state error">{{ previewError }}</div>

      <div class="diary-preview-body">
        <div class="diary-preview-content">
          <article class="scrapbook blank-scrapbook diary-preview-book" :class="{ loading: previewLoading }" :style="{ '--canvas-scale': canvasScale }">
            <div class="page left-page">
              <div class="record-title-edit diary-preview-title">
                <small>{{ previewRecord.date }}</small>
                <strong>{{ previewRecord.title || '제목 없는 기록' }}</strong>
                <span class="stars">{{ previewStars }}</span>
              </div>
              <div v-if="isPreviewDiaryEmpty" class="blank-guide">
                <strong>{{ previewRecord.title || '다이어리 기록' }}</strong>
                <span>{{ previewRecord.memo || '저장된 꾸미기 요소가 없어 기본 기록 정보로 표시합니다.' }}</span>
              </div>
            </div>
            <div class="binder" aria-hidden="true"><span v-for="ring in 7" :key="'preview-ring-' + ring"></span></div>
            <div class="page right-page">
              <div v-if="isPreviewDiaryEmpty" class="blank-guide right">
                <strong>감상 메모</strong>
                <span>{{ previewRecord.memo || '작성된 감상평이 없습니다.' }}</span>
              </div>
            </div>

            <div class="decoration-layer diary-preview-layer">
              <div
                v-for="item in previewPlacedItems"
                :key="item.id"
                class="placed-decoration diary-preview-decoration"
                :style="placementStyle(item)"
              >
                <div class="placed-sticker" :class="item.tone" :style="stickerStyle(item)">
                  <div v-if="item.type === 'bubble'" class="bubble-editor diary-preview-note" :class="item.bubbleType"
                    :style="bubbleEditorStyle(item)">
                    <p :style="previewTextStyle(item)">{{ item.text }}</p>
                  </div>
                  <div v-else-if="item.type === 'text'" class="memo-editor diary-preview-note">
                    <p :style="previewTextStyle(item)">{{ item.text }}</p>
                  </div>
                  <img v-else-if="item.imageSrc" :src="item.imageSrc" alt="다이어리 이미지" />
                  <span v-else>{{ item.icon }}</span>
                </div>
              </div>
            </div>
          </article>
          <div v-if="previewLoading" class="diary-preview-loading">다이어리를 불러오는 중...</div>
        </div>

        <!-- 댓글 패널 -->
        <aside class="diary-comment-panel">
          <h4>댓글 <span class="comment-count">{{ comments.length }}</span></h4>
          <div class="comment-list" ref="commentList">
            <div v-if="comments.length === 0" class="comment-empty">
              아직 댓글이 없습니다. 첫 댓글을 남겨보세요!
            </div>
            <div v-for="c in comments" :key="c.id" class="comment-item">
              <div class="comment-meta">
                <b>{{ c.user_nickname }}</b>
                <span>{{ formatCommentTime(c.created_at) }}</span>
              </div>
              <p class="comment-body">{{ c.content }}</p>
              <button v-if="c.is_mine" class="comment-delete" type="button" title="삭제"
                @click="deleteComment(c.id)">삭제</button>
            </div>
          </div>
          <div class="comment-input-wrap" v-if="currentUser">
            <textarea v-model="commentText" placeholder="댓글을 입력하세요..." rows="2"
              @keydown.enter.exact.prevent="submitComment"></textarea>
            <button type="button" class="comment-submit"
              :disabled="!commentText.trim() || commentLoading"
              @click="submitComment">{{ commentLoading ? '...' : '등록' }}</button>
          </div>
        </aside>
      </div>
    </section>
  </div>
</template>

<script>
import {
  formatCommentTime,
  cloneForSave,
  normalizeImageUrl,
  formatDisplayDate,
  recordDisplayTitle,
  stars,
} from "../../utils/helpers";

export default {
  name: "DiaryPreviewModal",
  props: {
    record: { type: Object, required: true },
    currentUser: { type: Object, default: null },
    canvasScale: { type: Number, default: 1 },
    apiFetch: { type: Function, required: true },
  },
  emits: ["close", "open-edit"],
  data() {
    return {
      previewLoading: false,
      previewError: "",
      previewRecord: {},
      previewPlacedItems: [],
      previewMainImageSrc: "",
      comments: [],
      commentText: "",
      commentLoading: false,
    };
  },
  computed: {
    previewStars() {
      return stars(this.previewRecord.rating || 0);
    },
    isPreviewDiaryEmpty() {
      return this.previewPlacedItems.length === 0 && !this.previewMainImageSrc;
    },
  },
  watch: {
    record: {
      immediate: true,
      handler(rec) {
        if (rec) this.initPreview(rec);
      },
    },
  },
  methods: {
    formatCommentTime,

    placementStyle(item) {
      return {
        left: `${item.x}%`,
        top: `${item.y}%`,
        width: item.width ? `${item.width}px` : null,
        height: item.height ? `${item.height}px` : null,
        zIndex: item.zIndex || 1,
        transform: `scale(${this.canvasScale || 1})`,
        transformOrigin: "top left",
        "--item-scale":
          item.type === "text" || item.type === "image" || item.type === "bubble"
            ? 1
            : item.scale || 1,
      };
    },

    stickerStyle(item) {
      var scale =
        item.type === "text" || item.type === "image" || item.type === "bubble"
          ? 1
          : item.scale || 1;
      return { transform: `rotate(${item.rotate || 0}deg) scale(${scale})` };
    },

    previewTextStyle(item) {
      return {
        fontSize: `${item.fontSize || 15}px`,
        color: item.textColor || "#342a3f",
      };
    },

    bubbleEditorStyle(item) {
      var style = {};
      if (item.bgColor) style.background = item.bgColor;
      if (item.borderColor) {
        style.borderColor = item.borderColor;
        style["--bubble-border"] = item.borderColor;
      }
      return style;
    },

    async initPreview(record) {
      this.previewError = "";
      this.previewLoading = false;
      this.comments = [];
      this.commentText = "";

      try {
        this.setFromRecord(record);
      } catch (e) {
        this.previewRecord = {
          title: recordDisplayTitle(record),
          author: record?.user_nickname || "",
          date: formatDisplayDate(record?.watched_date || ""),
          rating: record?.rating ?? 0,
          memo: record?.content || "",
        };
        this.previewPlacedItems = this.fallbackItems(this.previewRecord, "");
        this.previewMainImageSrc = "";
      }

      this.loadComments(record.id);

      try {
        var detail = await this.apiFetch(`/api/records/${record.id}/`);
        this.setFromRecord(this.mergeRecord(record, detail));
      } catch (e) {
        this.previewLoading = false;
      }
    },

    setFromRecord(record) {
      var cd = record?.canvas_data || {};
      var watchedDate = record?.watched_date
        ? formatDisplayDate(record.watched_date)
        : "";
      var previewImage = normalizeImageUrl(
        cd.main_image_src ||
          cd.mainImageSrc ||
          cd.imageSrc ||
          record?.work_poster ||
          record?.work?.poster_image ||
          record?.work?.cover_image ||
          record?.poster ||
          record?.image ||
          record?.imageSrc
      );
      var rawItems = Array.isArray(cd.placed_items)
        ? cd.placed_items
        : cd.placedItems;
      var baseItems = Array.isArray(rawItems) ? cloneForSave(rawItems) : [];

      this.previewRecord = {
        title: recordDisplayTitle(record),
        author: record?.user_nickname || "",
        date: watchedDate,
        rating: record?.rating ?? 0,
        memo:
          record?.content ||
          cd.memo ||
          cd.record?.memo ||
          cd.analysis?.phrase ||
          "",
      };
      this.previewMainImageSrc = previewImage;
      this.previewPlacedItems =
        baseItems.length > 0
          ? baseItems
          : this.fallbackItems(this.previewRecord, previewImage);
    },

    mergeRecord(listRecord, detailRecord) {
      var listCanvas = listRecord?.canvas_data || {};
      var detailCanvas = detailRecord?.canvas_data || {};
      return {
        ...listRecord,
        ...detailRecord,
        work_title: detailRecord?.work_title || listRecord?.work_title,
        work_poster: detailRecord?.work_poster || listRecord?.work_poster,
        display_title:
          detailRecord?.display_title || listRecord?.display_title,
        title: detailRecord?.title || listRecord?.title,
        content: detailRecord?.content || listRecord?.content,
        user_nickname:
          detailRecord?.user_nickname || listRecord?.user_nickname,
        watched_date:
          detailRecord?.watched_date || listRecord?.watched_date,
        rating: detailRecord?.rating ?? listRecord?.rating,
        canvas_data: {
          ...listCanvas,
          ...detailCanvas,
          title: detailCanvas.title || listCanvas.title,
          anime_title:
            detailCanvas.anime_title ||
            detailCanvas.animeTitle ||
            listCanvas.anime_title ||
            listCanvas.animeTitle,
          animeTitle:
            detailCanvas.animeTitle ||
            detailCanvas.anime_title ||
            listCanvas.animeTitle ||
            listCanvas.anime_title,
          main_image_src:
            detailCanvas.main_image_src ||
            detailCanvas.mainImageSrc ||
            listCanvas.main_image_src ||
            listCanvas.mainImageSrc,
          mainImageSrc:
            detailCanvas.mainImageSrc ||
            detailCanvas.main_image_src ||
            listCanvas.mainImageSrc ||
            listCanvas.main_image_src,
          placed_items:
            detailCanvas.placed_items ||
            detailCanvas.placedItems ||
            listCanvas.placed_items ||
            listCanvas.placedItems,
          placedItems:
            detailCanvas.placedItems ||
            detailCanvas.placed_items ||
            listCanvas.placedItems ||
            listCanvas.placed_items,
        },
      };
    },

    fallbackItems(record, imageSrc) {
      var items = [];
      if (imageSrc) {
        items.push({
          id: "preview-main-image",
          type: "image",
          imageSrc: imageSrc,
          tone: "custom-image",
          x: 24,
          y: 24,
          width: 220,
          rotate: -3,
          scale: 1,
          zIndex: 1,
        });
      }
      var memoText =
        record.memo ||
        (
          (record.title || "기록") +
          "\n" +
          (record.rating ? record.rating + " / 10" : "")
        ).trim();
      items.push({
        id: "preview-memo",
        type: "text",
        text:
          memoText.length > 140 ? memoText.slice(0, 140) + "…" : memoText,
        tone: "memo-text",
        x: imageSrc ? 56 : 32,
        y: imageSrc ? 32 : 34,
        width: 220,
        height: 150,
        rotate: 2,
        fontSize: 15,
        scale: 1,
        zIndex: 2,
      });
      return items;
    },

    async loadComments(recordId) {
      if (!recordId) return;
      try {
        var data = await this.apiFetch(
          `/api/records/${recordId}/comments/`
        );
        this.comments = Array.isArray(data) ? data : [];
      } catch (e) {
        console.error("댓글 불러오기 실패:", e);
      }
    },

    async submitComment() {
      var text = this.commentText.trim();
      if (!text || !this.record?.id || this.commentLoading) return;
      this.commentLoading = true;
      try {
        await this.apiFetch(
          `/api/records/${this.record.id}/comments/`,
          { method: "POST", body: JSON.stringify({ content: text }) }
        );
        this.commentText = "";
        await this.loadComments(this.record.id);
      } catch (e) {
        console.error("댓글 작성 실패:", e);
      } finally {
        this.commentLoading = false;
      }
    },

    async deleteComment(commentId) {
      if (!this.record?.id) return;
      try {
        await this.apiFetch(
          `/api/records/${this.record.id}/comments/${commentId}/`,
          { method: "DELETE" }
        );
        await this.loadComments(this.record.id);
      } catch (e) {
        console.error("댓글 삭제 실패:", e);
      }
    },
  },
};
</script>

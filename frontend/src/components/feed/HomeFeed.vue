<template>
  <div class="home-feed">
    <p v-if="isFeedLoading" class="feed-empty">불러오는 중...</p>
    <p v-else-if="feedRecords.length === 0" class="feed-empty">아직 공유된 기록이 없습니다.</p>
    <article
      v-for="rec in feedRecords"
      :key="rec.id"
      class="feed-card"
      role="button"
      tabindex="0"
      @click="$emit('open-preview', rec)"
      @keydown.enter.prevent="$emit('open-preview', rec)"
      @keydown.space.prevent="$emit('open-preview', rec)"
    >
      <header class="feed-card-header">
        <div class="feed-user">
          <b>{{ rec.user_nickname || '익명' }}님의 기록</b>
        </div>
        <time>{{ formatFeedDate(rec.created_at) }}</time>
      </header>
      <div class="record-preview" :class="recordPreviewClass(rec)">
        <img
          v-if="currentRecordPreviewImage(rec)"
          class="record-preview-image"
          :src="currentRecordPreviewImage(rec)"
          :alt="recordDisplayTitle(rec)"
          @error="handleRecordPreviewImageError(rec)"
        />
        <div v-else class="record-preview-empty-copy">
          <small>다이어리 기록</small>
          <b>{{ recordDisplayTitle(rec) }}</b>
        </div>
        <span class="record-preview-sticker sticker-a">✦</span>
        <span class="record-preview-sticker sticker-b">♡</span>
        <span class="record-preview-sticker sticker-c">✧</span>
        <div class="preview-memo-note">
          <b>{{ rec.rating ? `${rec.rating} / 10` : '감상 기록' }}</b>
          <p>{{ recordPreviewText(rec) }}</p>
        </div>
      </div>
      <div class="feed-card-body">
        <div class="feed-info">
          <h3>{{ recordDisplayTitle(rec) }}</h3>
          <p v-if="rec.work_title" class="feed-work">{{ rec.work_title }}</p>
          <span v-if="rec.rating" class="feed-rating">{{ stars(rec.rating) }} {{ rec.rating }}</span>
          <p v-if="rec.content" class="feed-content">{{ rec.content.length > 120 ? rec.content.slice(0, 120) + '…' : rec.content }}</p>
        </div>
        <footer class="feed-card-footer">
          <button type="button" class="feed-action" :class="{ liked: rec.is_liked }" @click.stop="$emit('toggle-like', rec)" @keydown.enter.stop @keydown.space.stop>{{ rec.is_liked ? '♥' : '♡' }} {{ rec.like_count || 0 }}</button>
          <button type="button" class="feed-action" @click.stop @keydown.enter.stop @keydown.space.stop>💬 {{ rec.comment_count || 0 }}</button>
          <button v-if="rec.is_mine" type="button" class="feed-action feed-edit" @click.stop="$emit('open-edit', rec)" @keydown.enter.stop @keydown.space.stop>✎ 편집</button>
        </footer>
      </div>
    </article>
  </div>
</template>

<script>
import {
  stars,
  formatFeedDate,
  normalizeImageUrl,
  recordDisplayTitle,
  recordPreviewText,
} from "../../utils/helpers";

export default {
  name: "HomeFeed",

  props: {
    feedRecords: {
      type: Array,
      required: true,
    },
    isFeedLoading: {
      type: Boolean,
      default: false,
    },
    currentUser: {
      type: Object,
      default: null,
    },
  },

  emits: ["open-preview", "open-edit", "toggle-like"],

  data() {
    return {
      recordPreviewCandidateIndexes: {},
      brokenRecordPreviewImages: {},
    };
  },

  watch: {
    feedRecords() {
      this.recordPreviewCandidateIndexes = {};
      this.brokenRecordPreviewImages = {};
    },
  },

  methods: {
    stars,
    formatFeedDate,
    recordDisplayTitle,
    recordPreviewText,

    recordPreviewShareImage(record) {
      return normalizeImageUrl(
        record?.share_card_image ||
          record?.share_image_url ||
          record?.share_card_url ||
          record?.latest_share_card?.image_url ||
          record?.share_card?.image_url
      );
    },

    recordPreviewCandidates(record) {
      const canvasData = record?.canvas_data || {};
      return [
        this.recordPreviewShareImage(record),
        canvasData.main_image_src,
        record?.work_poster,
        record?.work?.poster_image,
        record?.work?.cover_image,
        record?.poster,
        record?.image,
      ]
        .map((v) => normalizeImageUrl(v))
        .filter(Boolean)
        .filter((v, i, l) => l.indexOf(v) === i);
    },

    currentRecordPreviewImage(record) {
      if (this.brokenRecordPreviewImages[record.id]) return "";
      const candidates = this.recordPreviewCandidates(record);
      const index = this.recordPreviewCandidateIndexes[record.id] || 0;
      return candidates[index] || "";
    },

    handleRecordPreviewImageError(record) {
      const candidates = this.recordPreviewCandidates(record);
      const currentIndex =
        this.recordPreviewCandidateIndexes[record.id] || 0;
      const nextIndex = currentIndex + 1;
      if (nextIndex < candidates.length) {
        this.recordPreviewCandidateIndexes = {
          ...this.recordPreviewCandidateIndexes,
          [record.id]: nextIndex,
        };
        return;
      }
      this.brokenRecordPreviewImages = {
        ...this.brokenRecordPreviewImages,
        [record.id]: true,
      };
    },

    recordPreviewClass(record) {
      if (this.recordPreviewShareImage(record))
        return "record-preview--share";
      const canvasData = record?.canvas_data || {};
      if (
        (Array.isArray(canvasData.placed_items) &&
          canvasData.placed_items.length > 0) ||
        canvasData.main_image_src
      )
        return "record-preview--diary";
      if (this.recordPreviewCandidates(record).length > 0)
        return "record-preview--poster";
      return "record-preview--empty";
    },
  },
};
</script>

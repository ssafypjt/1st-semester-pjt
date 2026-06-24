<template>
  <div class="saved-album-grid">
    <article
      v-for="card in savedCards"
      :key="card.id"
      class="saved-card"
      role="button"
      tabindex="0"
      title="저장된 기록 열기"
      @click="$emit('open-card', card)"
      @keydown.enter.prevent="$emit('open-card', card)"
      @keydown.space.prevent="$emit('open-card', card)"
    >
      <button class="saved-card-delete" type="button" title="삭제" aria-label="삭제" @click.stop="$emit('delete-card', card.id)">
        ×
      </button>
      <img
        v-if="currentImageSrc(card)"
        class="saved-card-poster"
        :src="currentImageSrc(card)"
        alt="작품 이미지"
        @error="handleImageError(card)"
      />
      <div v-else class="saved-card-poster saved-card-poster-placeholder">
        이미지 없음
      </div>
      <small>{{ card.date }}</small>
      <h3>{{ card.title }}</h3>
      <p>{{ card.rating }} / 10 {{ stars(card.rating) }}</p>
      <span>스티커 {{ card.stickerCount || 0 }}개 · 메모 {{ card.memoCount || 0 }}개 저장됨</span>
    </article>
    <article v-if="savedCards.length === 0" class="saved-empty">
      <b>아직 저장한 카드가 없어요</b>
      <p>기록 작성에서 다이어리를 꾸민 뒤 저장을 누르면 여기에 보관됩니다.</p>
    </article>
  </div>
</template>

<script>
export default {
  name: "SavedAlbumGrid",
  props: {
    savedCards: {
      type: Array,
      required: true,
    },
    stars: {
      type: Function,
      required: true,
    },
  },
  emits: ["open-card", "delete-card"],
  data() {
    return {
      imageCandidateIndexes: {},
      brokenImages: {},
    };
  },
  methods: {
    imageCandidates(card) {
      if (Array.isArray(card.imageCandidates) && card.imageCandidates.length > 0) {
        return card.imageCandidates;
      }
      return card.imageSrc ? [card.imageSrc] : [];
    },
    currentImageSrc(card) {
      if (this.brokenImages[card.id]) return "";
      const candidates = this.imageCandidates(card);
      const index = this.imageCandidateIndexes[card.id] || 0;
      return candidates[index] || "";
    },
    handleImageError(card) {
      const candidates = this.imageCandidates(card);
      const currentIndex = this.imageCandidateIndexes[card.id] || 0;
      const nextIndex = currentIndex + 1;
      if (nextIndex < candidates.length) {
        this.imageCandidateIndexes = {
          ...this.imageCandidateIndexes,
          [card.id]: nextIndex,
        };
        return;
      }
      this.brokenImages = {
        ...this.brokenImages,
        [card.id]: true,
      };
    },
  },
};
</script>

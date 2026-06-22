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
};
</script>

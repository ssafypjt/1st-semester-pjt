<template>
  <section class="panel-card">
    <header>
      <h3>스티커샵</h3>
      <span>클릭해서 붙이기</span>
    </header>
    <div class="subtabs">
      <button
        v-for="category in stickerCategories"
        :key="category"
        :class="{ active: activeStickerCategory === category }"
        type="button"
        @click="$emit('change-category', category)"
      >
        {{ category }}
      </button>
    </div>
    <div class="sticker-grid">
      <button
        v-for="sticker in visibleDecorations"
        :key="sticker.id || `${sticker.icon}-${sticker.tone}`"
        :class="sticker.tone"
        type="button"
        @click="$emit('add-decoration', sticker)"
      >
        <img v-if="sticker.imageSrc" :src="sticker.imageSrc" :alt="sticker.label || '스티커'" />
        <span v-else>{{ sticker.icon }}</span>
      </button>
    </div>
    <p class="shop-help">스티커, 프레임, 말풍선을 붙인 뒤 드래그로 이동할 수 있어요.</p>
  </section>
</template>

<script>
export default {
  name: "StickerPanel",
  props: {
    stickerCategories: {
      type: Array,
      required: true,
    },
    activeStickerCategory: {
      type: String,
      required: true,
    },
    visibleDecorations: {
      type: Array,
      required: true,
    },
  },
  emits: ["change-category", "add-decoration"],
};
</script>

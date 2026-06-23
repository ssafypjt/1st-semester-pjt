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
        <span v-else-if="sticker.bubbleType" class="bubble-preview" :class="sticker.bubbleType">{{ sticker.icon }}<small>{{ sticker.label }}</small></span>
        <span v-else>{{ sticker.icon }}</span>
      </button>
      <!-- 추가 버튼: 전체 탭이 아닐 때만 표시 -->
      <button
        v-if="activeStickerCategory !== '전체'"
        class="sticker-add-btn"
        type="button"
        title="새 스티커 추가"
        @click="triggerUpload"
      >
        <span>+</span>
      </button>
    </div>
    <input
      ref="fileInput"
      type="file"
      accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
      style="display:none"
      @change="onFileSelected"
    />
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
  emits: ["change-category", "add-decoration", "upload-sticker"],
  methods: {
    triggerUpload() {
      this.$refs.fileInput.click();
    },
    onFileSelected(event) {
      var file = event.target.files && event.target.files[0];
      if (!file) return;
      event.target.value = "";
      // 카테고리 매핑: UI명 → DB값
      var categoryMap = { '스티커': 'sticker', '프레임': 'frame', '말풍선': 'bubble' };
      this.$emit("upload-sticker", {
        file: file,
        category: categoryMap[this.activeStickerCategory] || 'sticker',
      });
    },
  },
};
</script>

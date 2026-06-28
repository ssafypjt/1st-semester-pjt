<template>
  <div class="cardbox-page">
    <div v-if="!cardBoxItems || cardBoxItems.length === 0" class="cardbox-empty">
      <p>아직 만든 공유 카드가 없습니다.</p>
      <small>기록 작성 화면에서 <b>공유하기</b> 버튼을 눌러 카드를 만들어보세요.</small>
    </div>
    <div v-else class="cardbox-grid">
      <div v-for="card in cardBoxItems" :key="card.id" class="cardbox-item">
        <img :src="card.image_url" :alt="card.template_name || '공유 카드'" @click="openPreview(card)" />
        <div class="cardbox-item-info">
          <small>{{ formatFeedDate(card.created_at) }}</small>
        </div>
        <div class="cardbox-item-actions">
          <button type="button" title="간직하기" @click="downloadImage(card)">⬇</button>
          <button type="button" title="삭제" class="cardbox-delete" @click="deleteItem(card)">✕</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatFeedDate } from "../../utils/helpers";

export default {
  name: "CardBoxPage",
  props: {
    cardBoxItems: {
      type: Array,
      default: () => [],
    },
    apiFetch: {
      type: Function,
      required: true,
    },
  },
  emits: ["toast", "update:cardBoxItems"],
  methods: {
    formatFeedDate,
    openPreview(card) {
      if (card.image_url) window.open(card.image_url, "_blank");
    },
    async downloadImage(card) {
      if (!card.image_url) return;
      try {
        const resp = await fetch(card.image_url);
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `deokkku_card_${card.id}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } catch (err) {
        this.$emit("toast", "다운로드에 실패했습니다.");
      }
    },
    async deleteItem(card) {
      if (!confirm("이 카드를 삭제할까요?")) return;
      try {
        await this.apiFetch(`/api/shares/card/${card.id}/delete/`, {
          method: "DELETE",
        });
        this.$emit(
          "update:cardBoxItems",
          this.cardBoxItems.filter((c) => c.id !== card.id)
        );
        this.$emit("toast", "카드가 삭제되었습니다.");
      } catch (e) {
        this.$emit("toast", "삭제에 실패했습니다.");
      }
    },
  },
};
</script>

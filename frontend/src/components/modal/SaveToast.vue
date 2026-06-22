<template>
  <div class="save-popup-backdrop" @click.self="$emit('close')">
    <section class="save-popup" role="alertdialog" aria-modal="true" aria-label="저장 완료 안내">
      <strong>{{ message }}</strong>
      <p>내 앨범에서 저장한 다이어리 카드를 확인할 수 있어요.</p>
      <div>
        <button type="button" @click="$emit('close')">확인</button>
        <button class="primary" type="button" @click="$emit('view-album')">내 앨범 보기</button>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: "SaveToast",
  props: {
    message: {
      type: String,
      required: true,
    },
  },
  emits: ["close", "view-album"],
};
</script>

<template>
  <div class="save-popup-backdrop" @click.self="$emit('close')">
    <section class="save-popup" role="alertdialog" aria-modal="true" aria-label="저장 완료 안내">
      <strong>{{ message }}</strong>
      <div>
        <button type="button" @click="$emit('close')">확인</button>
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

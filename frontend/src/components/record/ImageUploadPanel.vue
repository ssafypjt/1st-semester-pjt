<template>
  <section class="panel-card">
    <header>
      <h3>이미지 첨부</h3>
      <span>내 이미지 붙이기</span>
    </header>
    <label class="upload-drop">
      <input type="file" accept="image/*" @change="$emit('image-upload', $event)" />
      <span>＋</span>
      <b>이미지 선택</b>
      <small>선택한 이미지를 다이어리 위에 붙이고 드래그로 이동할 수 있어요.</small>
    </label>
  </section>
</template>

<script>
export default {
  name: "ImageUploadPanel",
  emits: ["image-upload"],
};
</script>

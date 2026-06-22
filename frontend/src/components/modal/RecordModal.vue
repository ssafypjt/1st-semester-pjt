<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <section class="record-modal" role="dialog" aria-modal="true" aria-label="기록 정보 수정">
      <header>
        <h3>{{ mode === 'edit' ? '기록 정보 수정' : '새 기록 만들기' }}</h3>
        <button type="button" @click="$emit('close')">×</button>
      </header>
      <label>
        <span>작품명</span>
        <input :value="recordForm.title" placeholder="애니메이션 제목을 입력하세요" @input="updateField('title', $event.target.value)" />
      </label>
      <label>
        <span>감상 날짜</span>
        <input type="date" :value="recordForm.date" @input="updateField('date', $event.target.value)" />
      </label>
      <label>
        <span>별점</span>
        <input type="range" min="0" max="10" step="0.5" :value="recordForm.rating" @input="updateField('rating', Number($event.target.value))" />
        <b>{{ recordForm.rating }} / 10 {{ stars(recordForm.rating) }}</b>
      </label>
      <div class="modal-actions">
        <button type="button" @click="$emit('close')">취소</button>
        <button class="primary" type="button" @click="$emit('submit')">
          {{ mode === 'edit' ? '수정하기' : '시작하기' }}
        </button>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: "RecordModal",
  props: {
    recordForm: {
      type: Object,
      required: true,
    },
    mode: {
      type: String,
      required: true,
    },
    stars: {
      type: Function,
      required: true,
    },
  },
  emits: ["update:recordForm", "close", "submit"],
  methods: {
    updateField(field, value) {
      this.$emit("update:recordForm", {
        ...this.recordForm,
        [field]: value,
      });
    },
  },
};
</script>

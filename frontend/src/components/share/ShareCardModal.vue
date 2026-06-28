<template>
  <div class="share-modal-overlay" @click.self="$emit('close')">
    <div class="share-modal">
      <div class="share-modal-header">
        <div>
          <small>SHARE PREVIEW</small>
          <h3>공유 카드 만들기</h3>
        </div>
        <button class="share-modal-close" type="button" @click="$emit('close')">&#10005;</button>
      </div>

      <div class="share-modal-body">
        <div class="share-preview-card">
          <div v-if="latestShareCard" class="share-preview-image">
            <img :src="latestShareCard.image_url" alt="공유 카드" />
          </div>
          <div v-else-if="isGeneratingCard" class="share-preview-placeholder">
            <div class="spinner"></div>
            <p>AI가 배치 중...</p>
          </div>
          <div v-else class="share-preview-placeholder">
            <p>아래 버튼을 눌러 공유 카드를 생성하세요.</p>
          </div>

          <div class="share-preview-info">
            <b>{{ currentRecord.title }}</b>
            <span v-if="currentRecord.rating" class="share-preview-rating">{{ currentRecord.rating }} / 10</span>
            <div v-if="currentRecord.tags && currentRecord.tags.length" class="share-preview-tags">
              <span v-for="tag in currentRecord.tags" :key="tag">#{{ tag }}</span>
            </div>
          </div>
        </div>

        <div class="share-actions">
          <p v-if="shareCardError" class="share-error">{{ shareCardError }}</p>
          <p v-if="latestShareCard" class="share-result-desc">{{ latestShareCard.template_name || '이미지 폴라로이드' }}</p>
          <p v-if="latestShareCard" class="share-result-sub">AI가 자동으로 배치한 공유 카드입니다.</p>

          <div class="share-btn-group">
            <button class="share-btn outline" type="button" :disabled="isGeneratingCard" @click="generateShareCard">
              {{ latestShareCard ? '다시 만들기' : (isGeneratingCard ? 'AI 생성 중...' : 'AI 카드 생성') }}
            </button>
            <button v-if="latestShareCard" class="share-btn primary" type="button" @click="downloadShareImage">간직하기</button>
            <button v-if="latestShareCard" class="share-btn primary" type="button" @click="saveToCardBox">카드함으로 보내기</button>
            <button class="share-btn" type="button" @click="$emit('close')">닫기</button>
          </div>
          <div v-if="showCardBoxConfirm" class="cardbox-confirm-overlay">
            <div class="cardbox-confirm-box">
              <p>카드함으로 보냈습니다!</p>
              <div class="cardbox-confirm-btns">
                <button class="share-btn primary" type="button" @click="$emit('go-cardbox')">이동</button>
                <button class="share-btn outline" type="button" @click="showCardBoxConfirm = false">닫기</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ShareCardModal',
  props: {
    currentRecord: {
      type: Object,
      required: true,
    },
    currentRecordId: {
      type: Number,
      required: true,
    },
    apiFetch: {
      type: Function,
      required: true,
    },
  },
  emits: ['close', 'go-cardbox', 'toast'],
  data() {
    return {
      shareCards: [],
      isGeneratingCard: false,
      shareCardError: '',
      showCardBoxConfirm: false,
    };
  },
  computed: {
    latestShareCard() {
      return this.shareCards.length > 0 ? this.shareCards[0] : null;
    },
  },
  watch: {
    currentRecordId: {
      immediate: true,
      handler(id) {
        if (id) this.loadShareCards(id);
      },
    },
  },
  methods: {
    async generateShareCard() {
      if (!this.currentRecordId) {
        this.shareCardError = '기록을 먼저 저장해주세요.';
        return;
      }
      this.isGeneratingCard = true;
      this.shareCardError = '';
      try {
        const data = await this.apiFetch(
          `/api/shares/${this.currentRecordId}/generate/`,
          { method: 'POST', body: JSON.stringify({}) }
        );
        this.shareCards.unshift(data);
      } catch (e) {
        this.shareCardError = '카드 생성에 실패했습니다. 다시 시도해주세요.';
      } finally {
        this.isGeneratingCard = false;
      }
    },
    async loadShareCards(recordId) {
      try {
        const data = await this.apiFetch(`/api/shares/${recordId}/`);
        this.shareCards = Array.isArray(data) ? data : (data.results || []);
      } catch (e) {
        this.shareCards = [];
      }
    },
    async downloadShareImage() {
      if (!this.latestShareCard?.image_url) return;
      try {
        const resp = await fetch(this.latestShareCard.image_url);
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const title = (this.currentRecord.title || 'deokkku')
          .replace(/[\\/:*?"<>|]/g, '')
          .replace(/\s+/g, '_');
        link.href = url;
        link.download = `${title}_sharecard.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } catch (err) {
        alert('이미지 다운로드에 실패했습니다.');
      }
    },
    saveToCardBox() {
      if (!this.latestShareCard) {
        this.$emit('toast', '저장할 공유 카드가 없습니다.');
        return;
      }
      this.showCardBoxConfirm = true;
    },
  },
};
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <section class="record-modal" role="dialog" aria-modal="true" aria-label="기록 정보 수정">
      <header>
        <h3>{{ mode === 'edit' ? '기록 정보 수정' : '새 기록 만들기' }}</h3>
        <button type="button" @click="$emit('close')">×</button>
      </header>

      <!-- 작품명 검색 -->
      <div class="autocomplete-wrap">
        <span class="field-label">작품명</span>
        <div v-if="!selectedWork" class="search-bar">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input
            ref="titleInput"
            :value="recordForm.title"
            placeholder="제목을 검색하세요 (한글/영어)"
            autocomplete="off"
            @input="onTitleInput($event.target.value)"
            @focus="showDropdown = suggestions.length > 0"
            @keydown.down.prevent="moveHighlight(1)"
            @keydown.up.prevent="moveHighlight(-1)"
            @keydown.enter.prevent="selectHighlighted"
            @keydown.escape="showDropdown = false"
          />
        </div>
        <!-- 선택된 작품 뱃지 -->
        <div v-if="selectedWork" class="selected-work-badge">
          <img v-if="selectedWork.poster_image" :src="selectedWork.poster_image" class="badge-poster" />
          <span class="badge-title">{{ selectedWork.title_ko || selectedWork.title }}</span>
          <button type="button" class="badge-clear" @click="clearSelection">&times;</button>
        </div>
        <!-- 한글 제목: 없으면 입력, 있으면 수정 버튼 -->
        <div v-if="selectedWork && (!selectedWork.title_ko || isEditingKo)" class="ko-title-input">
          <input
            v-model="koTitleInput"
            :placeholder="selectedWork.title_ko ? '한글 제목 수정' : '한글 제목 입력 (예: 주술회전)'"
            class="ko-title-field"
          />
          <span class="ko-hint">다음 검색부터 한글로 찾을 수 있어요</span>
        </div>
        <div v-if="selectedWork && selectedWork.title_ko && !isEditingKo" class="ko-title-display">
          <span>한글: {{ selectedWork.title_ko }}</span>
          <button type="button" class="ko-edit-btn" @click="startEditKo">수정</button>
        </div>
        <!-- 드롭다운 -->
        <ul v-if="showDropdown && suggestions.length" class="autocomplete-dropdown">
          <li
            v-for="(item, idx) in suggestions"
            :key="(item.source || '') + ':' + (item.external_id || item.id)"
            :class="{ highlighted: idx === highlightIdx }"
            @mousedown.prevent="selectSuggestion(item)"
            @mouseenter="highlightIdx = idx"
          >
            <img v-if="item.poster_image" :src="item.poster_image" class="ac-poster" />
            <div class="ac-info">
              <strong>{{ item.title_ko || item.title }}</strong>
              <span v-if="item.title_ko && item.title !== item.title_ko" class="ac-sub">{{ item.title }}</span>
              <span v-if="!item.title_ko && item.title_en" class="ac-sub">{{ item.title_en }}</span>
              <span class="ac-meta">
                <em v-if="item.source === 'local'" class="ac-tag local">DB</em>
                <em v-else class="ac-tag anilist">AniList</em>
                {{ item.genre ? item.genre.split(',')[0].trim() : '' }}
                {{ item.release_date ? item.release_date.slice(0,4) : '' }}
              </span>
            </div>
          </li>
        </ul>
        <div v-if="showDropdown && isSearching" class="ac-loading">검색 중...</div>
        <div v-if="showDropdown && !isSearching && !suggestions.length && recordForm.title.trim().length >= 2" class="ac-empty">
          검색 결과가 없습니다.<br/>
          <span class="ac-empty-hint">영어로 검색해보세요 (ex: naruto)</span>
        </div>
      </div>

      <label>
        <span>감상 날짜</span>
        <input type="date" :value="recordForm.date" @input="updateField('date', $event.target.value)" />
      </label>
      <label>
        <span>별점</span>
        <input type="range" min="0" max="10" step="0.5" :value="recordForm.rating" @input="updateField('rating', Number($event.target.value))" />
        <b>{{ recordForm.rating }} / 10 {{ stars(recordForm.rating) }}</b>
      </label>
      <p v-if="submitError" class="submit-error">{{ submitError }}</p>
      <div class="modal-actions">
        <button type="button" @click="$emit('close')">취소</button>
        <button class="primary" type="button" @click="handleSubmit">
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
    apiFetch: {
      type: Function,
      required: true,
    },
  },
  emits: ["update:recordForm", "close", "submit"],
  data() {
    return {
      suggestions: [],
      showDropdown: false,
      highlightIdx: -1,
      isSearching: false,
      selectedWork: null,
      koTitleInput: "",
      searchTimer: null,
      submitError: "",
      isEditingKo: false,
    };
  },
  methods: {
    updateField(field, value) {
      this.$emit("update:recordForm", {
        ...this.recordForm,
        [field]: value,
      });
    },
    onTitleInput(value) {
      this.updateField("title", value);
      this.selectedWork = null;
      clearTimeout(this.searchTimer);
      if (value.trim().length < 2) {
        this.suggestions = [];
        this.showDropdown = false;
        return;
      }
      this.searchTimer = setTimeout(() => this.searchWorks(value.trim()), 300);
    },
    async searchWorks(query) {
      this.isSearching = true;
      this.showDropdown = true;
      try {
        const encoded = encodeURIComponent(query);
        const res = await this.apiFetch("/api/works/autocomplete/?q=" + encoded);
        this.suggestions = res;
        this.highlightIdx = -1;
      } catch (e) {
        console.error("자동완성 검색 실패:", e);
        this.suggestions = [];
      } finally {
        this.isSearching = false;
      }
    },
    async selectSuggestion(item) {
      this.showDropdown = false;
      this.suggestions = [];
      try {
        const work = await this.apiFetch("/api/works/select/", {
          method: "POST",
          body: JSON.stringify(item),
        });
        this.selectedWork = Object.assign({}, item, work, { source: item.source });
        var displayTitle = work.title_ko || work.title || item.title;
        this.updateField("title", displayTitle);
        this.updateField("workId", work.id);
        this.koTitleInput = "";
      } catch (e) {
        console.error("작품 선택 실패:", e);
        this.updateField("title", item.title_ko || item.title);
      }
    },
    startEditKo() {
      this.koTitleInput = this.selectedWork.title_ko;
      this.isEditingKo = true;
    },
    clearSelection() {
      this.selectedWork = null;
      this.koTitleInput = "";
      this.isEditingKo = false;
      this.updateField("title", "");
      this.updateField("workId", null);
      var self = this;
      this.$nextTick(function() {
        if (self.$refs.titleInput) self.$refs.titleInput.focus();
      });
    },
    moveHighlight(delta) {
      if (!this.suggestions.length) return;
      this.highlightIdx = (this.highlightIdx + delta + this.suggestions.length) % this.suggestions.length;
    },
    selectHighlighted() {
      if (this.highlightIdx >= 0 && this.highlightIdx < this.suggestions.length) {
        this.selectSuggestion(this.suggestions[this.highlightIdx]);
      }
    },
    handleSubmit() {
      if (!this.selectedWork) {
        this.submitError = '작품을 검색해서 선택해주세요.';
        return;
      }
      this.submitError = '';
      if (this.koTitleInput && this.koTitleInput !== this.selectedWork.title_ko) {
        this.apiFetch("/api/works/select/", {
          method: "POST",
          body: JSON.stringify({
            id: this.selectedWork.id,
            title_ko: this.koTitleInput,
          }),
        }).catch(function() {});
        this.updateField("title", this.koTitleInput);
      } else {
        // 선택된 작품의 제목으로 확정 (검색어가 아닌 실제 작품명)
        var correctTitle = this.selectedWork.title_ko || this.selectedWork.title;
        if (correctTitle && this.recordForm.title !== correctTitle) {
          this.updateField("title", correctTitle);
        }
      }
      this.$emit("submit");
    },
  },
  beforeUnmount() {
    clearTimeout(this.searchTimer);
  },
};
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <section class="record-modal" role="dialog" aria-modal="true" aria-label="기록 정보 수정">
      <header>
        <h3>{{ mode === 'edit' ? '기록 정보 수정' : '새 기록 만들기' }}</h3>
        <button type="button" @click="$emit('close')">×</button>
      </header>

      <!-- 작품명 자동완성 -->
      <label class="autocomplete-wrap">
        <span>작품명</span>
        <input
          v-if="!selectedWork"
          ref="titleInput"
          :value="recordForm.title"
          placeholder="애니메이션 제목 검색 (한글/영어)"
          autocomplete="off"
          @input="onTitleInput($event.target.value)"
          @focus="showDropdown = suggestions.length > 0"
          @keydown.down.prevent="moveHighlight(1)"
          @keydown.up.prevent="moveHighlight(-1)"
          @keydown.enter.prevent="selectHighlighted"
          @keydown.escape="showDropdown = false"
        />
        <!-- 선택된 작품 뱃지 -->
        <div v-if="selectedWork" class="selected-work-badge">
          <img
            v-if="workPosterSrc(selectedWork)"
            :src="workPosterSrc(selectedWork)"
            class="badge-poster"
            alt=""
            @error="handlePosterError(selectedWork)"
          />
          <span v-else class="badge-poster badge-poster-placeholder">이미지 없음</span>
          <span class="badge-title">{{ selectedWork.title_ko || selectedWork.title }}</span>
          <button type="button" class="badge-clear" @click="clearSelection">&times;</button>
        </div>
        <!-- 한글 제목 입력 (AniList에서 선택 + 한글 제목 없을 때) -->
        <div v-if="selectedWork && !selectedWork.title_ko && selectedWork.source !== 'local'" class="ko-title-input">
          <input
            v-model="koTitleInput"
            placeholder="한글 제목 입력 (예: 주술회전)"
            class="ko-title-field"
          />
          <span class="ko-hint">다음 검색부터 한글로 찾을 수 있어요</span>
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
            <img
              v-if="workPosterSrc(item)"
              :src="workPosterSrc(item)"
              class="ac-poster"
              alt=""
              @error="handlePosterError(item)"
            />
            <span v-else class="ac-poster ac-poster-placeholder">이미지 없음</span>
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
      brokenPosterKeys: {},
    };
  },
  methods: {
    posterKey(item) {
      return `${item?.source || "local"}:${item?.external_id || item?.id || item?.title || ""}`;
    },
    normalizeImageUrl(value) {
      const rawValue = String(value || "").trim();
      if (!rawValue) return "";
      if (rawValue.startsWith("/") || rawValue.startsWith("data:image/")) return rawValue;

      const markdownMatch = rawValue.match(/\[[^\]]*\]\((https?:\/\/[^)]+)\)/);
      if (markdownMatch) return markdownMatch[1];

      const urlMatch = rawValue.match(/https?:\/\/[^\s)]+/);
      return urlMatch ? urlMatch[0] : "";
    },
    workPosterSrc(item) {
      if (!item || this.brokenPosterKeys[this.posterKey(item)]) return "";
      return this.normalizeImageUrl(item.poster_image || item.work_poster || item.image || item.poster);
    },
    handlePosterError(item) {
      this.brokenPosterKeys = {
        ...this.brokenPosterKeys,
        [this.posterKey(item)]: true,
      };
    },
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
        this.$emit("update:recordForm", {
          ...this.recordForm,
          title: displayTitle,
          workId: work.id,
        });
        this.koTitleInput = "";
      } catch (e) {
        console.error("작품 선택 실패:", e);
        this.updateField("title", item.title_ko || item.title);
      }
    },
    clearSelection() {
      this.selectedWork = null;
      this.koTitleInput = "";
      this.$emit("update:recordForm", {
        ...this.recordForm,
        title: "",
        workId: null,
      });
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
      if (!this.selectedWork && !this.recordForm.workId) {
        this.submitError = '작품을 검색해서 선택해주세요.';
        return;
      }
      this.submitError = '';
      if (this.selectedWork && this.koTitleInput && !this.selectedWork.title_ko) {
        this.apiFetch("/api/works/select/", {
          method: "POST",
          body: JSON.stringify({
            id: this.selectedWork.id,
            title_ko: this.koTitleInput,
          }),
        }).catch(function() {});
        this.updateField("title", this.koTitleInput);
      }
      this.$emit("submit");
    },
  },
  mounted() {
    if (this.recordForm.workId && this.recordForm.title) {
      this.selectedWork = {
        id: this.recordForm.workId,
        title: this.recordForm.title,
        title_ko: this.recordForm.title,
        source: "local",
      };
    }
  },
  beforeUnmount() {
    clearTimeout(this.searchTimer);
  },
};
</script>

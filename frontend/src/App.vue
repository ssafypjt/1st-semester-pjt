<template>
  <div v-cloak>
    <div class="shell-bg">
      <span class="tape tape-a"></span>
      <span class="tape tape-b"></span>
      <span class="spark s1">*</span>
      <span class="spark s2">*</span>
      <span class="spark s3">*</span>
      <span class="polaroid polaroid-left"></span>
      <span class="memo memo-right">Today's log<br />감상<br />명장면<br />공유</span>
    </div>

    <!-- 로그인 / 회원가입 (미인증 시) -->
    <login-page
      v-if="!isCheckingAuth && !currentUser"
      :main-logo-url="mainLogoUrl"
      :mode="$route.name === 'signup' ? 'signup' : 'login'"
      @login="onAuthSuccess"
      @signup="onAuthSuccess"
    />

    <section v-if="!isCheckingAuth && currentUser" class="workspace">
      <sidebar
        :simple-logo-url="simpleLogoUrl"
        :nav="nav"
        :active-page="activePage"
        :recent-tags="recentTags"
        :nav-icon="navIcon"
        :my-page-icon-url="myPageIconUrl"
        :review-icon-url="reviewIconUrl"
        :add-record-icon-url="addRecordIconUrl"
        :album-icon-url="albumIconUrl"
        :home-icon-url="homeIconUrl"
        :has-record-in-progress="hasRecordInProgress"
        @navigate="navigatePage"
      />

      <main class="main">
        <topbar
          ref="profileMenu"
          v-model:query="query"
          :current-user="currentUser"
          :show-profile-menu="showProfileMenu"
          :profile-initial="profileInitial"
          :activity-stats="activityStats"
          @open-record="openRecordModal"
          @toggle-profile="toggleProfileMenu"
          @view-profile="openProfilePageFromDropdown"
          @logout="logout"
        />

        <!-- 기록 작성 에디터 -->
        <record-editor
          v-if="activePage === '기록 작성'"
          ref="recordEditor"
          :current-record="currentRecord"
          :record-title="recordTitle"
          :record-visibility="recordVisibility"
          :selected-view="selectedView"
          :selected-view-stars="selectedViewStars"
          :canvas-scale="canvasScale"
          :sticker-categories="stickerCategories"
          :canvas-tools="canvasTools"
          :ai="ai"
          :api-fetch="apiFetch"
          @update:current-record="currentRecord = $event"
          @update:record-title="recordTitle = $event"
          @update:record-visibility="recordVisibility = $event"
          @save="saveCard"
          @close="confirmCloseRecord"
          @open-record-modal="openRecordModal"
          @open-share-modal="openShareModal"
          @sticker-upload="handleStickerUpload"
          @image-upload="handleImageUpload"
          @toast="toastMessage = $event"
        />

        <!-- 페이지별 상세 -->
        <section v-else class="detail-page">
          <header>
            <img v-if="activePage === nav[4]" class="detail-page-icon-image" :src="myPageIconUrl" alt="" />
            <img v-else-if="activePage === nav[3]" class="detail-page-icon-image" :src="reviewIconUrl" alt="" />
            <img v-else-if="activePage === nav[1]" class="detail-page-icon-image" :src="albumIconUrl" alt="" />
            <img v-else-if="activePage === nav[0]" class="detail-page-icon-image" :src="homeIconUrl" alt="" />
            <span v-else>{{ navIcon(activePage) }}</span>
            <div>
              <h2>{{ activePage }}</h2>
              <p>{{ pageDescriptionText }}</p>
            </div>
          </header>

          <!-- 마이페이지 대시보드 -->
          <my-page-dashboard
            v-if="activePage === nav[4]"
            :current-user="currentUser"
            :profile-preview-url="profilePreviewUrl"
            :profile-initial="profileInitial"
            :joined-date="currentUser?.created_at ? formatProfileDate(currentUser.created_at) : ''"
            :profile-stats="profileStats"
            :featured-badges="featuredBadges"
            @edit-profile="openProfileModal"
            @open-badges="openBadgeModal"
          />

          <!-- 상세 카드 그리드 -->
          <div v-if="activePage !== nav[0] && activePage !== nav[1] && activePage !== nav[4]" class="detail-grid">
            <article
              v-for="card in detailCards"
              :key="card.title"
              class="detail-card"
              :class="{ clickable: card.action }"
              :role="card.action ? 'button' : null"
              :tabindex="card.action ? 0 : null"
              @click="card.action && navigatePage(card.action)"
              @keydown.enter.prevent="card.action && navigatePage(card.action)"
              @keydown.space.prevent="card.action && navigatePage(card.action)"
            >
              <span v-if="card.icon" class="detail-card-icon">{{ card.icon }}</span>
              <b>{{ card.title }}</b>
              <p>{{ card.body }}</p>
            </article>
          </div>

          <!-- 홈 피드 -->
          <home-feed
            v-if="activePage === '홈'"
            :feed-records="feedRecords"
            :is-feed-loading="isFeedLoading"
            :current-user="currentUser"
            @open-preview="openFeedDiaryPreview"
            @open-edit="openFeedRecord"
            @toggle-like="toggleFeedLike"
          />

          <!-- 내 앨범 -->
          <saved-album-grid
            v-if="activePage === '내 앨범'"
            :saved-cards="savedCards"
            :stars="stars"
            @open-card="openSavedCard"
            @delete-card="deleteSavedCard"
          />

          <!-- 카드함 -->
          <card-box-page
            v-if="activePage === '카드함'"
            :card-box-items="cardBoxItems"
            :api-fetch="apiFetch"
            @update:card-box-items="cardBoxItems = $event"
            @toast="toastMessage = $event"
          />
        </section>

        <!-- 모달 레이어 -->
        <record-modal
          v-if="isRecordModalOpen"
          v-model:record-form="recordForm"
          :mode="recordModalMode"
          :stars="stars"
          :api-fetch="apiFetch"
          @close="closeRecordModal"
          @submit="createBlankRecord"
        />

        <save-toast
          v-if="toastMessage"
          :message="toastMessage"
          @close="toastMessage = ''"
          @view-album="openAlbumFromToast"
        />

        <profile-modal
          v-if="isProfileModalOpen"
          v-model:profile-form="profileForm"
          :profile-preview-url="profilePreviewUrl"
          :profile-initial="profileInitial"
          :profile-status="profileStatus"
          :current-user="currentUser"
          :is-profile-saving="isProfileSaving"
          @close="closeProfileModal"
          @submit="updateProfile"
          @image-change="handleProfileImageChange"
        />

        <badge-modal
          v-if="isBadgeModalOpen"
          :available-badges="availableBadges"
          :selected-badge-ids="selectedBadgeIds"
          @close="closeBadgeModal"
          @toggle-badge="toggleRepresentativeBadge"
        />

        <diary-preview-modal
          v-if="isDiaryPreviewOpen"
          :record="previewTargetRecord"
          :current-user="currentUser"
          :canvas-scale="canvasScale"
          :api-fetch="apiFetch"
          @close="closeFeedDiaryPreview"
          @open-edit="openFeedRecord"
        />

        <share-card-modal
          v-if="isShareModalOpen"
          :current-record="currentRecord"
          :current-record-id="currentRecordId"
          :api-fetch="apiFetch"
          @close="closeShareModal"
          @go-cardbox="goToCardBox"
          @toast="toastMessage = $event"
        />
      </main>
    </section>
  </div>
</template>

<script>
import simpleLogoUrl from "./assets/images/simple_logo.png";
import mainLogoUrl from "./assets/images/main-logo.png";
import basicProfileUrl from "./assets/images/basic_profile.png";
import myPageIconUrl from "./assets/images/my_page_icon.png";
import reviewIconUrl from "./assets/images/card_icon.png";
import addRecordIconUrl from "./assets/images/add_record_icon.png";
import albumIconUrl from "./assets/images/album_icon.png";
import homeIconUrl from "./assets/images/home_icon.png";

import {
  stars, formatDisplayDate, formatInputDate, formatProfileDate,
  normalizeImageUrl, cloneForSave, navIcon, pageDescription,
  recordDisplayTitle,
} from "./utils/helpers";

import { canvasTools, nav, recentTags } from "./constants/navigation";
import { stickerCategories } from "./constants/stickers";
import { defaultAnalysis } from "./constants/defaultAnalysis";

import LoginPage from "./components/auth/LoginPage.vue";
import Sidebar from "./components/layout/Sidebar.vue";
import Topbar from "./components/layout/Topbar.vue";
import RecordEditor from "./components/record/RecordEditor.vue";
import HomeFeed from "./components/feed/HomeFeed.vue";
import SavedAlbumGrid from "./components/album/SavedAlbumGrid.vue";
import CardBoxPage from "./components/share/CardBoxPage.vue";
import MyPageDashboard from "./components/profile/MyPageDashboard.vue";
import RecordModal from "./components/modal/RecordModal.vue";
import SaveToast from "./components/modal/SaveToast.vue";
import ProfileModal from "./components/modal/ProfileModal.vue";
import BadgeModal from "./components/modal/BadgeModal.vue";
import DiaryPreviewModal from "./components/modal/DiaryPreviewModal.vue";
import ShareCardModal from "./components/share/ShareCardModal.vue";

const PAGE_TO_ROUTE = {
  "홈": "home",
  "내 앨범": "diaries",
  "기록 작성": "record-new",
  "카드함": "cardbox",
  "마이페이지": "mypage",
  "공유 페이지": "share",
};
const ROUTE_TO_PAGE = {};
Object.keys(PAGE_TO_ROUTE).forEach(k => { ROUTE_TO_PAGE[PAGE_TO_ROUTE[k]] = k; });
ROUTE_TO_PAGE["diary-detail"] = "기록 작성";

export default {
  name: "App",
  components: {
    LoginPage, Sidebar, Topbar, RecordEditor, HomeFeed, SavedAlbumGrid,
    CardBoxPage, MyPageDashboard, RecordModal, SaveToast, ProfileModal,
    BadgeModal, DiaryPreviewModal, ShareCardModal,
  },

  data() {
    return {
      simpleLogoUrl, mainLogoUrl, basicProfileUrl,
      myPageIconUrl, reviewIconUrl, addRecordIconUrl, albumIconUrl, homeIconUrl,
      nav, recentTags, canvasTools, stickerCategories,
      query: "",
      currentRecord: {
        title: "새 감상 기록", date: "2026.05.18", rating: 0,
        memo: "좋아하는 장면과 감정을 자유롭게 남겨보세요.", tags: [],
      },
      recordForm: {
        title: "", date: new Date().toISOString().slice(0, 10), rating: 0, workId: null,
      },
      recordModalMode: "create",
      isRecordModalOpen: false,
      currentRecordId: null,
      recordVisibility: "public",
      recordTitle: "",
      isSaving: false,
      lastSaveAt: 0,
      _dirty: false,
      savedCards: [],
      feedRecords: [],
      isFeedLoading: false,
      isDiaryPreviewOpen: false,
      previewTargetRecord: null,
      isShareModalOpen: false,
      cardBoxItems: [],
      isCheckingAuth: true,
      currentUser: null,
      isLoggingOut: false,
      csrfToken: "",
      showProfileMenu: false,
      isProfileModalOpen: false,
      isProfileSaving: false,
      profileForm: { nickname: "", profileImage: null, removeProfileImage: false },
      profilePreviewLocalUrl: "",
      profileStatus: { type: "", message: "" },
      isBadgeModalOpen: false,
      selectedBadgeIds: [],
      toastMessage: "",
      canvasScale: 1,
      ai: defaultAnalysis,
    };
  },

  computed: {
    activePage() {
      const meta = this.$route?.meta;
      if (meta?.navPage) return meta.navPage;
      const name = this.$route?.name;
      return ROUTE_TO_PAGE[name] || "홈";
    },
    selectedView() { return this.currentRecord; },
    selectedViewStars() { return stars(this.selectedView.rating); },
    hasRecordInProgress() {
      const editor = this.$refs.recordEditor;
      if (editor) return editor.hasContent || !!this.currentRecordId;
      return !!this.currentRecordId;
    },
    pageDescriptionText() { return pageDescription(this.activePage); },
    profilePreviewUrl() {
      return this.profilePreviewLocalUrl || this.currentUser?.profile_image || this.basicProfileUrl;
    },
    profileInitial() {
      const source = this.currentUser?.nickname || this.currentUser?.email || "?";
      return source.trim().slice(0, 1).toUpperCase();
    },
    activityStats() { return this.getActivityStats(); },
    profileStats() {
      const stats = this.activityStats;
      const unlockedBadges = this.availableBadges.filter(b => b.unlocked).length;
      return [
        { icon: "🏅", label: "수집한 뱃지", value: unlockedBadges, action: "badges" },
        { icon: "▣", label: "내 앨범", value: stats.albums },
        { icon: "↗", label: "공유 카드", value: stats.shares },
        { icon: "⭐", label: "대표 뱃지", value: this.featuredBadges.length },
      ];
    },
    availableBadges() { return this.getUserBadges(); },
    featuredBadges() {
      const unlocked = this.availableBadges.filter(b => b.unlocked);
      return this.selectedBadgeIds.map(id => unlocked.find(b => b.id === id)).filter(Boolean).slice(0, 3);
    },
    detailCards() {
      if (this.activePage === this.nav[4]) {
        return [
          { icon: "✏", title: "기록 작성", body: "새 감상 다이어리를 작성합니다.", action: this.nav[2] },
          { icon: "▣", title: "내 앨범", body: "작성한 기록을 확인합니다.", action: this.nav[1] },
          { icon: "↗", title: "공유 페이지", body: "공유 이미지를 생성하고 저장합니다.", action: "공유 페이지" },
        ];
      }
      return [
        { title: "기록 작성", body: "이미지, 스티커, 메모를 붙여 새 감상 다이어리를 만듭니다.", action: "기록 작성" },
        { title: "내 앨범", body: "저장한 다이어리 카드를 다시 열고 편집할 수 있습니다.", action: "내 앨범" },
        { title: "공유 페이지", body: "완성한 기록을 이미지로 생성하고 저장합니다.", action: "공유 페이지" },
      ];
    },
  },

  watch: {
    activePage() { this.$nextTick(() => this._observeScrapbook()); },
    isDiaryPreviewOpen() { this.$nextTick(() => this._observeScrapbook()); },
    "$route"(to) {
      if (to.name === "cardbox") this.loadCardBox();
      if (to.name === "diary-detail" && to.params.id) this.openDiaryById(to.params.id);
    },
  },

  mounted() {
    document.addEventListener("click", this.handleProfileOutsideClick);
    document.addEventListener("keydown", this.handleGlobalKeydown);
    this._beforeUnloadHandler = (e) => {
      if (this._isEditing()) { this._autosaveDraft(); e.preventDefault(); e.returnValue = ""; }
    };
    window.addEventListener("beforeunload", this._beforeUnloadHandler);
    window.addEventListener("pagehide", () => { if (this._isEditing()) this._autosaveDraft(); });
    this._scrapbookRO = new ResizeObserver((entries) => {
      for (const entry of entries) this.canvasScale = Math.min(entry.contentRect.width / 1800, 1);
    });
    this.$nextTick(() => this._observeScrapbook());
    this.loadRepresentativeBadges();
    this.checkAuth();
    this.loadFeedRecords();
    this.loadSavedCards().then(() => {
      this._checkAutosaveRestore();
      this.$nextTick(() => { this._dirty = false; });
    });
  },

  beforeUnmount() {
    document.removeEventListener("click", this.handleProfileOutsideClick);
    document.removeEventListener("keydown", this.handleGlobalKeydown);
    window.removeEventListener("beforeunload", this._beforeUnloadHandler);
    if (this._scrapbookRO) this._scrapbookRO.disconnect();
  },

  methods: {
    stars,
    navIcon,
    formatProfileDate,

    async checkAuth() {
      try {
        this.currentUser = await this.apiFetch("/api/auth/me/");
        this.resetProfileForm();
        this.loadRepresentativeBadges();
        this.loadUserStickers();
        if (this.$route.meta?.guest) {
          this.$router.replace({ name: "home" });
        }
        if (this.$route.name === "diary-detail" && this.$route.params.id) {
          this.$nextTick(() => this.openDiaryById(this.$route.params.id));
        }
      } catch (e) {
        this.currentUser = null;
        if (this.$route.meta?.auth) {
          this.$router.replace({ name: "login" });
        }
      } finally {
        this.isCheckingAuth = false;
      }
    },
    onAuthSuccess(user) {
      this.currentUser = user;
      this.resetProfileForm();
      this.loadRepresentativeBadges();
      this.loadUserStickers();
      this.loadSavedCards();
      this.loadFeedRecords();
      this.$router.push({ name: "home" });
    },
    async logout() {
      if (this.isLoggingOut) return;
      this.isLoggingOut = true;
      try {
        this.csrfToken = "";
        await this.apiFetch("/api/auth/logout/", { method: "POST", body: JSON.stringify({}) });
      } catch (e) { /* ignore */ }
      this.currentUser = null;
      this.csrfToken = "";
      this.isLoggingOut = false;
      this.$router.push({ name: "login" });
    },

    async getCsrfToken(forceRefresh = false) {
      if (this.csrfToken && !forceRefresh) return this.csrfToken;
      const response = await fetch("/api/auth/csrf/", {
        credentials: "include", cache: "no-store",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) throw new Error("CSRF token request failed: " + response.status);
      const data = await response.json();
      this.csrfToken = data.csrfToken || "";
      return this.csrfToken;
    },
    async apiFetch(url, options = {}, _retried = false) {
      const method = (options.method || "GET").toUpperCase();
      const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
      const needsCsrf = !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method);
      if (needsCsrf) headers["X-CSRFToken"] = await this.getCsrfToken();
      const response = await fetch(url, { credentials: "include", ...options, headers });
      if (!response.ok) {
        const responseBody = await response.text();
        if (response.status === 403 && needsCsrf && !_retried && responseBody.includes("CSRF")) {
          this.csrfToken = "";
          return this.apiFetch(url, options, true);
        }
        let detail = responseBody;
        try { const ed = JSON.parse(responseBody); detail = ed.detail || JSON.stringify(ed); } catch (e) {}
        throw new Error("API request failed: " + response.status + " " + detail);
      }
      if (response.status === 204) return null;
      return response.json();
    },

    navigatePage(page) {
      if (page === "기록 작성" && !this.hasRecordInProgress) {
        this.openRecordModal("create");
        return;
      }
      const routeName = PAGE_TO_ROUTE[page];
      if (routeName) {
        this.$router.push({ name: routeName });
      }
      if (page === "카드함") this.loadCardBox();
    },
    openProfilePageFromDropdown() { this.navigatePage(this.nav[4]); this.closeProfileMenu(); },
    openAlbumFromToast() { this.navigatePage("내 앨범"); this.toastMessage = ""; },

    toggleProfileMenu() { this.showProfileMenu = !this.showProfileMenu; },
    closeProfileMenu() { this.showProfileMenu = false; },
    handleProfileOutsideClick(event) {
      if (!this.showProfileMenu) return;
      const menu = this.$refs.profileMenu;
      if (menu && !menu.contains(event.target)) this.closeProfileMenu();
    },
    handleGlobalKeydown(event) {
      if (event.key !== "Escape") return;
      this.closeProfileMenu();
      if (this.isProfileModalOpen) this.closeProfileModal();
      if (this.isBadgeModalOpen) this.closeBadgeModal();
      if (this.isDiaryPreviewOpen) this.closeFeedDiaryPreview();
    },

    openProfileModal() { this.resetProfileForm(); this.isProfileModalOpen = true; },
    closeProfileModal() { this.isProfileModalOpen = false; this.resetProfileForm(); },
    resetProfileForm() {
      if (this.profilePreviewLocalUrl) URL.revokeObjectURL(this.profilePreviewLocalUrl);
      this.profilePreviewLocalUrl = "";
      this.profileForm = { nickname: this.currentUser?.nickname || "", profileImage: null, removeProfileImage: false };
      this.profileStatus = { type: "", message: "" };
    },
    handleProfileImageChange(event) {
      const file = event.target.files?.[0] || null;
      if (this.profilePreviewLocalUrl) URL.revokeObjectURL(this.profilePreviewLocalUrl);
      this.profilePreviewLocalUrl = file ? URL.createObjectURL(file) : "";
      this.profileForm.profileImage = file;
      if (file) this.profileForm.removeProfileImage = false;
      this.profileStatus = { type: "", message: "" };
    },
    async updateProfile() {
      const nickname = this.profileForm.nickname.trim();
      if (!nickname) { this.profileStatus = { type: "error", message: "닉네임을 입력해주세요." }; return; }
      this.isProfileSaving = true;
      this.profileStatus = { type: "", message: "" };
      try {
        const csrfToken = await this.getCsrfToken();
        const formData = new FormData();
        formData.append("nickname", nickname);
        formData.append("remove_profile_image", this.profileForm.removeProfileImage ? "true" : "false");
        if (this.profileForm.profileImage && !this.profileForm.removeProfileImage) {
          formData.append("profile_image", this.profileForm.profileImage);
        }
        const response = await fetch("/api/auth/me/update/", {
          method: "PATCH", credentials: "include",
          headers: { "X-CSRFToken": csrfToken }, body: formData,
        });
        if (!response.ok) {
          const rb = await response.text();
          let detail = rb;
          try { const ed = JSON.parse(rb); detail = ed.detail || JSON.stringify(ed); } catch (e) {}
          throw new Error("프로필 저장에 실패했습니다. (" + response.status + ") " + detail);
        }
        this.currentUser = await response.json();
        this.resetProfileForm();
        this.profileStatus = { type: "success", message: "프로필이 저장되었습니다." };
      } catch (e) {
        this.profileStatus = { type: "error", message: e.message || "프로필 저장에 실패했습니다." };
      } finally {
        this.isProfileSaving = false;
      }
    },

    openBadgeModal() { this.isBadgeModalOpen = true; },
    closeBadgeModal() { this.isBadgeModalOpen = false; },
    badgeStorageKey() { return "deokkkuRepresentativeBadges:" + (this.currentUser?.email || "guest"); },
    loadRepresentativeBadges() {
      try {
        const stored = JSON.parse(localStorage.getItem(this.badgeStorageKey()) || "[]");
        this.selectedBadgeIds = Array.isArray(stored) ? stored.slice(0, 3) : [];
      } catch (e) { this.selectedBadgeIds = []; }
    },
    persistRepresentativeBadges() {
      try { localStorage.setItem(this.badgeStorageKey(), JSON.stringify(this.selectedBadgeIds.slice(0, 3))); } catch (e) {}
    },
    toggleRepresentativeBadge(badge) {
      if (!badge.unlocked) return;
      if (this.selectedBadgeIds.includes(badge.id)) {
        this.selectedBadgeIds = this.selectedBadgeIds.filter(id => id !== badge.id);
      } else {
        this.selectedBadgeIds = [...this.selectedBadgeIds, badge.id].slice(-3);
      }
      this.persistRepresentativeBadges();
    },
    getActivityStats() {
      const albums = Array.isArray(this.savedCards) ? this.savedCards.length : 0;
      return { records: albums, albums, shares: 0, recent: Math.min(albums, 9) };
    },
    getUserBadges() {
      const stats = this.getActivityStats();
      const ratedCount = (this.savedCards || []).filter(c => Number(c.rating || 0) > 0).length;
      return [
        { id: "first-record", icon: "🏆", label: "첫 기록 작성", description: "기록 1개 이상", unlocked: stats.records + stats.albums >= 1 },
        { id: "archive-collector", icon: "📚", label: "기록 수집가", description: "기록 5개 이상", unlocked: stats.records + stats.albums >= 5 },
        { id: "rating-master", icon: "⭐", label: "별점 마스터", description: "별점 기록 3개 이상", unlocked: ratedCount >= 3 },
        { id: "decoration-starter", icon: "🎨", label: "다꾸 입문자", description: "저장한 다이어리 1개 이상", unlocked: stats.albums >= 1 },
        { id: "steady-logger", icon: "📝", label: "꾸준한 기록러", description: "기록 10개 이상", unlocked: stats.records + stats.albums >= 10 },
      ];
    },

    openRecordModal(mode = "create") {
      this.recordModalMode = mode;
      this.recordForm = {
        title: mode === "edit" ? this.currentRecord.title : "",
        date: mode === "edit" ? formatInputDate(this.currentRecord.date) : new Date().toISOString().slice(0, 10),
        rating: mode === "edit" ? this.currentRecord.rating : 0,
        workId: mode === "edit" ? (this.currentRecord.workId || null) : null,
      };
      this.isRecordModalOpen = true;
    },
    closeRecordModal() { this.isRecordModalOpen = false; },
    createBlankRecord() {
      this.currentRecord = {
        title: this.recordForm.title || "제목 없는 기록",
        date: formatDisplayDate(this.recordForm.date),
        rating: this.recordForm.rating,
        memo: "새롭게 작성한 감상 기록입니다.", tags: [],
      };
      if (this.recordModalMode !== "edit") {
        this.currentRecordId = null;
        this.recordVisibility = "public";
        this.recordTitle = "";
        this.$nextTick(() => {
          if (this.$refs.recordEditor) this.$refs.recordEditor.setCanvasState({ placedItems: [], mainImageSrc: "" });
        });
      }
      this.$router.push({ name: "record-new" });
      this.isRecordModalOpen = false;
    },

    async confirmCloseRecord() {
      const editor = this.$refs.recordEditor;
      const isEmpty = editor ? !editor.hasContent : true;
      if (isEmpty && !this.currentRecordId) { this.closeRecord(); return; }
      if (confirm("저장하시겠습니까?\n\n확인: 저장 후 내 앨범으로 이동\n취소: 저장하지 않고 내 앨범으로 이동")) {
        await this.saveCard();
      }
      this.closeRecord();
    },
    closeRecord() {
      this.currentRecordId = null;
      this.recordTitle = "";
      this._dirty = false;
      this.currentRecord = {
        title: "새 감상 기록", date: "2026.05.18", rating: 0,
        memo: "좋아하는 장면과 감정을 자유롭게 남겨보세요.", tags: [],
      };
      this.$router.push({ name: "diaries" });
    },

    async saveCard() {
      const now = Date.now();
      if (now - this.lastSaveAt < 350 || this.isSaving) return;
      this.lastSaveAt = now;
      this.isSaving = true;
      try {
        const editor = this.$refs.recordEditor;
        const canvasState = editor ? editor.getCanvasState() : { placedItems: [], mainImageSrc: "" };
        const animeTitle = (this.currentRecord.title || this.recordForm.title || "").trim() || "제목 없는 기록";
        const payload = {
          ...(this.recordForm.workId ? { work_id: this.recordForm.workId } : {}),
          title: this.recordTitle.trim() || animeTitle,
          work_title: animeTitle,
          anime_title: animeTitle,
          rating: this.currentRecord.rating ?? null,
          watched_date: formatInputDate(this.currentRecord.date) || null,
          content: this.currentRecord.memo || "",
          canvas_data: {
            title: this.recordTitle,
            anime_title: animeTitle,
            placed_items: canvasState.placedItems,
            main_image_src: canvasState.mainImageSrc,
            analysis: cloneForSave(this.ai),
          },
          status: "published",
          visibility: this.recordVisibility,
        };
        let record;
        if (this.currentRecordId) {
          record = await this.apiFetch("/api/records/" + this.currentRecordId + "/", { method: "PATCH", body: JSON.stringify(payload) });
          const updated = this.apiRecordToSavedCard(record);
          const idx = this.savedCards.findIndex(c => c.id === this.currentRecordId);
          if (idx !== -1) this.savedCards.splice(idx, 1, updated);
          else this.savedCards.unshift(updated);
        } else {
          record = await this.apiFetch("/api/records/", { method: "POST", body: JSON.stringify(payload) });
          this.currentRecordId = record.id;
          this.savedCards.unshift(this.apiRecordToSavedCard(record));
        }
        if (this.currentRecordId && this.$route.name !== "diary-detail") {
          this.$router.replace({ name: "diary-detail", params: { id: this.currentRecordId } });
        }
        this.toastMessage = "저장되었습니다";
        this._dirty = false;
        this._clearAutosave();
        this.loadFeedRecords();
      } catch (e) {
        console.error("저장 실패:", e);
        this.toastMessage = "저장에 실패했습니다. 다시 시도해주세요.";
      } finally {
        this.isSaving = false;
      }
    },

    apiRecordToSavedCard(record) {
      const cd = record.canvas_data || {};
      const placedItems = Array.isArray(cd.placed_items) ? cd.placed_items : (Array.isArray(cd.placedItems) ? cd.placedItems : []);
      const recordTitle = (cd.title || "").trim();
      const workTitle = record.work?.title_ko || record.work?.title || record.work_title || "";
      const title = (cd.anime_title || cd.animeTitle || "").trim() || workTitle || recordDisplayTitle(record);
      const watchedDate = record.watched_date ? record.watched_date.replaceAll("-", ".") : "";
      const imageCandidates = [record.work_poster, record.work?.poster_image, record.work?.cover_image]
        .map(v => normalizeImageUrl(v)).filter(Boolean).filter((v, i, l) => l.indexOf(v) === i);
      return {
        id: record.id, title, recordTitle, date: watchedDate, rating: record.rating ?? 0,
        imageSrc: imageCandidates[0] || "", imageCandidates,
        workId: record.work?.id || record.work || null,
        visibility: record.visibility || "private",
        memoCount: placedItems.filter(i => i.type === "text").length,
        stickerCount: placedItems.filter(i => i.type !== "text").length,
        savedAt: record.created_at,
        snapshot: {
          record: { title, date: watchedDate, rating: record.rating ?? 0, memo: record.content || cd.memo || cd.record?.memo || "", tags: [], workId: record.work?.id || record.work || null },
          placedItems,
          mainImageSrc: normalizeImageUrl(cd.main_image_src || cd.mainImageSrc),
          analysis: cd.analysis || null,
        },
      };
    },

    async loadSavedCards() {
      try {
        const data = await this.apiFetch("/api/records/?mine=1");
        const results = Array.isArray(data) ? data : (data.results || []);
        this.savedCards = results.map(r => this.apiRecordToSavedCard(r));
      } catch (e) { this.savedCards = []; }
    },
    async loadFeedRecords() {
      this.isFeedLoading = true;
      try {
        const data = await this.apiFetch("/api/records/");
        this.feedRecords = Array.isArray(data) ? data : (data.results || []);
      } catch (e) { this.feedRecords = []; }
      finally { this.isFeedLoading = false; }
    },
    async toggleFeedLike(record) {
      if (!this.currentUser) return;
      try {
        const data = await this.apiFetch("/api/records/" + record.id + "/like/", { method: "POST" });
        record.is_liked = data.liked;
        record.like_count = data.like_count;
      } catch (e) { console.error("좋아요 실패:", e); }
    },

    openSavedCard(card) {
      this.currentRecord = cloneForSave(
        card.snapshot?.record || { title: card.title, date: card.date, rating: card.rating, memo: "", tags: [] }
      );
      this.currentRecordId = card.id;
      this.recordVisibility = card.visibility || "private";
      this.recordTitle = card.recordTitle || card.title || "";
      this.toastMessage = "";
      if (card.snapshot?.analysis) this.ai = cloneForSave(card.snapshot.analysis);
      this.$router.push({ name: "diary-detail", params: { id: card.id } });
      this.$nextTick(() => {
        if (this.$refs.recordEditor) {
          this.$refs.recordEditor.setCanvasState({
            placedItems: card.snapshot?.placedItems || [],
            mainImageSrc: card.snapshot?.mainImageSrc || "",
          });
        }
        this._dirty = false;
      });
    },
    async openDiaryById(id) {
      const numId = Number(id);
      if (this.currentRecordId === numId) return;
      let card = this.savedCards.find(c => c.id === numId);
      if (card) { this.openSavedCard(card); return; }
      try {
        const record = await this.apiFetch("/api/records/" + numId + "/");
        card = this.apiRecordToSavedCard(record);
        this.openSavedCard(card);
      } catch (e) {
        console.error("기록 로드 실패:", e);
        this.$router.replace({ name: "diaries" });
      }
    },
    async deleteSavedCard(cardId) {
      try {
        await this.apiFetch("/api/records/" + cardId + "/", { method: "DELETE" });
      } catch (e) {
        if (!e.message?.includes("404")) { alert("삭제에 실패했습니다. 다시 시도해주세요."); return; }
      }
      this.savedCards = this.savedCards.filter(c => c.id !== cardId);
      if (this.currentRecordId === cardId) this.currentRecordId = null;
    },

    openFeedDiaryPreview(record) {
      this.previewTargetRecord = record;
      this.isDiaryPreviewOpen = true;
    },
    closeFeedDiaryPreview() {
      this.isDiaryPreviewOpen = false;
      this.previewTargetRecord = null;
    },
    async openFeedRecord(record) {
      if (!record?.id) return;
      this.closeFeedDiaryPreview();
      try {
        const detail = await this.apiFetch("/api/records/" + record.id + "/");
        const merged = { ...record, ...detail };
        this.openSavedCard(this.apiRecordToSavedCard(merged));
      } catch (e) {
        this.openSavedCard(this.apiRecordToSavedCard(record));
      }
    },

    openShareModal() {
      if (!this.currentRecordId) { this.toastMessage = "먼저 기록을 저장한 뒤 공유할 수 있습니다."; return; }
      this.isShareModalOpen = true;
    },
    closeShareModal() { this.isShareModalOpen = false; },
    goToCardBox() { this.isShareModalOpen = false; this.$router.push({ name: "cardbox" }); },
    async loadCardBox() {
      try {
        const data = await this.apiFetch("/api/shares/my/");
        this.cardBoxItems = Array.isArray(data) ? data : (data.results || []);
      } catch (e) { this.cardBoxItems = []; }
    },

    async loadUserStickers() {
      try {
        const data = await this.apiFetch("/api/records/stickers/");
        const categoryMap = { sticker: "스티커", frame: "프레임", bubble: "말풍선" };
        const stickers = data.map(item => {
          let tone = item.sticker.tone || "";
          if (item.sticker.image_url && tone.indexOf("sticker-image") === -1) tone = ("sticker-image " + tone).trim();
          return {
            id: item.sticker.id, icon: item.sticker.emoji_fallback || "⬡",
            label: item.sticker.name, tone,
            category: categoryMap[item.sticker.category] || "스티커",
            imageSrc: item.sticker.image_url || null,
          };
        });
        this.$nextTick(() => {
          if (this.$refs.recordEditor) this.$refs.recordEditor.setUserStickers(stickers);
        });
      } catch (e) { console.error("스티커 로드 실패:", e); }
    },
    async handleStickerUpload({ file, category }) {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("category", category);
      formData.append("name", file.name.replace(/\.[^.]+$/, ""));
      try {
        const csrfToken = await this.getCsrfToken();
        const resp = await fetch("/api/records/stickers/upload/", {
          method: "POST", headers: { "X-CSRFToken": csrfToken },
          credentials: "include", body: formData,
        });
        if (!resp.ok) throw new Error("업로드 실패");
        await this.loadUserStickers();
        this.toastMessage = "스티커가 추가되었습니다!";
      } catch (e) { this.toastMessage = "스티커 업로드에 실패했습니다."; }
    },
    async handleImageUpload(event) {
      const file = event.target.files?.[0];
      if (!file) return;
      event.target.value = "";
      try {
        const csrfToken = await this.getCsrfToken();
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch("/api/records/upload/", {
          method: "POST", credentials: "include",
          headers: { "X-CSRFToken": csrfToken }, body: formData,
        });
        if (!response.ok) throw new Error("이미지 업로드 실패");
        const data = await response.json();
        if (this.$refs.recordEditor) this.$refs.recordEditor.addImageItem(data.url);
      } catch (e) {
        console.error(e);
        alert("이미지 업로드에 실패했습니다. 다시 시도해주세요.");
      }
    },

    _observeScrapbook() {
      if (!this._scrapbookRO) return;
      this._scrapbookRO.disconnect();
      const scrapbooks = this.$el.querySelectorAll(".scrapbook");
      scrapbooks.forEach(el => this._scrapbookRO.observe(el));
    },

    _isEditing() {
      const editor = this.$refs.recordEditor;
      return this.activePage === "기록 작성" && this._dirty && editor?.hasContent;
    },
    _autosaveKey() { return "deokkkuAutosave:" + (this.currentUser?.email || "guest"); },
    _autosaveDraft() {
      try {
        const editor = this.$refs.recordEditor;
        const canvasState = editor ? editor.getCanvasState() : { placedItems: [], mainImageSrc: "" };
        const data = {
          currentRecord: JSON.parse(JSON.stringify(this.currentRecord)),
          placedItems: canvasState.placedItems,
          mainImageSrc: canvasState.mainImageSrc,
          currentRecordId: this.currentRecordId,
          routeName: this.$route.name,
          savedAt: new Date().toISOString(),
        };
        localStorage.setItem(this._autosaveKey(), JSON.stringify(data));
      } catch (e) { console.warn("임시저장 실패:", e); }
    },
    _clearAutosave() { try { localStorage.removeItem(this._autosaveKey()); } catch (e) {} },
    _checkAutosaveRestore() {
      try {
        const raw = localStorage.getItem(this._autosaveKey());
        if (!raw) return;
        const saved = JSON.parse(raw);
        if (!saved?.currentRecord) { this._clearAutosave(); return; }
        const wasEditing = saved.routeName === "record-new" || saved.routeName === "diary-detail" || saved.activePage === "기록 작성";
        if (!wasEditing) { this._clearAutosave(); return; }
        const hasWork = (saved.placedItems?.length > 0) || saved.mainImageSrc;
        if (!hasWork) { this._clearAutosave(); return; }
        const title = saved.currentRecord.title || "제목 없음";
        const when = saved.savedAt ? new Date(saved.savedAt).toLocaleString("ko-KR") : "";
        if (confirm("작성 중이던 기록이 있습니다.\n\n\"" + title + "\" (" + when + ")\n\n복원하시겠습니까?\n[확인] 복원  /  [취소] 삭제")) {
          this.currentRecord = saved.currentRecord;
          this.currentRecordId = saved.currentRecordId || null;
          const targetRoute = this.currentRecordId
            ? { name: "diary-detail", params: { id: this.currentRecordId } }
            : { name: "record-new" };
          this.$router.push(targetRoute);
          this.$nextTick(() => {
            if (this.$refs.recordEditor) {
              this.$refs.recordEditor.setCanvasState({
                placedItems: Array.isArray(saved.placedItems) ? saved.placedItems : [],
                mainImageSrc: saved.mainImageSrc || "",
              });
            }
            this._dirty = true;
          });
        }
        this._clearAutosave();
      } catch (e) { console.warn("임시저장 복원 실패:", e); this._clearAutosave(); }
    },
  },
};
</script>

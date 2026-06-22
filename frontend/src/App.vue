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

    <section v-if="!isCheckingAuth && currentUser" class="workspace">
      <sidebar
        :simple-logo-url="simpleLogoUrl"
        :nav="nav"
        :active-page="activePage"
        :recent-tags="recentTags"
        :nav-icon="navIcon"
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

        <div v-if="activePage === '기록 작성'" class="content-grid">
          <section class="editor-zone">
            <div class="section-head">
              <div>
                <h2>새 기록</h2>
              </div>
              <div class="toolset">
                <button
                  class="tool-action"
                  type="button"
                  :disabled="!canUndo"
                  title="이전 작업으로 되돌리기"
                  @click="undoLastCanvasChange"
                >
                  <span>↶</span><b>실행 취소</b>
                </button>
                <button class="tool-action memo-action" type="button" title="메모 추가" @click="addTextMemo">
                  <span>T</span><b>메모 추가</b>
                </button>
                <button class="primary small tool-action save-action" type="button" title="저장" @click="saveCard">
                  <span class="save-icon"></span><b>저장</b>
                </button>
              </div>
            </div>

            <article class="scrapbook blank-scrapbook" @click.self="clearDecorationSelection">
              <div class="page left-page" @click="clearDecorationSelection">
                <button class="record-title-edit" type="button" title="기록 정보 수정" @click.stop="openRecordModal('edit')">
                  <small>{{ selectedView.date }}</small>
                  <strong>{{ selectedView.title }}</strong>
                  <span class="stars">{{ selectedViewStars }}</span>
                </button>
                <div v-if="isCanvasEmpty" class="blank-guide">
                  <strong>빈 다이어리</strong>
                  <span>오른쪽 도구에서 이미지, 메모, 스티커를 붙여 자유롭게 꾸며보세요.</span>
                </div>
              </div>
              <div class="binder" aria-hidden="true"><span v-for="ring in 7" :key="ring"></span></div>
              <div class="page right-page" @click="clearDecorationSelection">
                <div v-if="isCanvasEmpty" class="blank-guide right">
                  <strong>꾸미기 영역</strong>
                  <span>텍스트 메모는 입력, 이동, 삭제, 크기 조절이 가능합니다.</span>
                </div>
              </div>

              <div class="decoration-layer" ref="canvasLayer" @click.self="clearDecorationSelection">
                <div
                  v-for="item in placedItems"
                  :key="item.id"
                  class="placed-decoration"
                  :class="{ selected: selectedDecorationId === item.id }"
                  :style="placementStyle(item)"
                  role="button"
                  tabindex="0"
                  title="드래그로 이동"
                  @click.stop="selectDecoration(item.id)"
                  @pointerdown="startDrag($event, item)"
                >
                  <div class="placed-sticker" :class="item.tone" :style="stickerStyle(item)">
                    <div v-if="item.type === 'text'" class="memo-editor">
                      <textarea
                        v-model="item.text"
                        :style="{ fontSize: `${item.fontSize || 15}px` }"
                        placeholder="메모를 입력하세요"
                        @click.stop="selectDecoration(item.id)"
                      ></textarea>
                      <label v-if="selectedDecorationId === item.id" class="memo-font-control" @pointerdown.stop @click.stop>
                        <span>글자</span>
                        <input type="range" min="11" max="34" step="1" v-model.number="item.fontSize" title="글자 크기 조절" />
                      </label>
                    </div>
                    <img v-else-if="item.imageSrc" :src="item.imageSrc" alt="첨부 이미지" />
                    <span v-else>{{ item.icon }}</span>
                  </div>
                  <button
                    v-if="selectedDecorationId === item.id"
                    class="rotate-decoration"
                    type="button"
                    title="기울기 조절"
                    @pointerdown.stop="startRotate($event, item)"
                    @click.stop
                  >
                    ↻
                  </button>
                  <button
                    v-if="selectedDecorationId === item.id"
                    class="resize-decoration"
                    type="button"
                    title="크기 조절"
                    aria-label="크기 조절"
                    @pointerdown.stop="startResize($event, item)"
                    @click.stop
                  ></button>
                  <button
                    v-if="selectedDecorationId === item.id"
                    class="delete-decoration"
                    type="button"
                    title="삭제"
                    @pointerdown.stop
                    @click.stop="removeSticker(item.id)"
                  >
                    ×
                  </button>
                </div>
              </div>
            </article>

            <div class="canvas-tools">
              <button v-for="tool in canvasTools" :key="tool.label" type="button" @click="runCanvasTool(tool)">
                {{ tool.icon }} {{ tool.label }}
              </button>
              <span></span>
              <button type="button">－</button>
              <b>100%</b>
              <button type="button">＋</button>
            </div>
          </section>

          <aside class="right-rail">
            <sticker-panel
              :sticker-categories="stickerCategories"
              :active-sticker-category="activeStickerCategory"
              :visible-decorations="visibleDecorations"
              @change-category="activeStickerCategory = $event"
              @add-decoration="addDecoration"
            />

            <image-upload-panel @image-upload="handleImageUpload" />

            <section class="panel-card">
              <header>
                <h3>추천 키워드</h3>
                <span>AI 추천</span>
              </header>
              <div class="keyword-list">
                <button v-for="tag in ai.tags" :key="tag" type="button">#{{ tag }}</button>
              </div>
            </section>
          </aside>
        </div>

        <section v-else class="detail-page">
          <header>
            <span>{{ navIcon(activePage) }}</span>
            <div>
              <h2>{{ activePage }}</h2>
              <p>{{ pageDescription }}</p>
            </div>
          </header>
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

          <div v-if="activePage !== nav[4]" class="detail-grid">
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
          <saved-album-grid
            v-if="activePage === '내 앨범'"
            :saved-cards="savedCards"
            :stars="stars"
            @open-card="openSavedCard"
            @delete-card="deleteSavedCard"
          />
        </section>

        <record-modal
          v-if="isRecordModalOpen"
          v-model:record-form="recordForm"
          :mode="recordModalMode"
          :stars="stars"
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
      </main>
    </section>
  </div>
</template>

<script>
import simpleLogoUrl from "./assets/images/simple_logo.png";
import SavedAlbumGrid from "./components/album/SavedAlbumGrid.vue";
import Sidebar from "./components/layout/Sidebar.vue";
import Topbar from "./components/layout/Topbar.vue";
import BadgeModal from "./components/modal/BadgeModal.vue";
import ProfileModal from "./components/modal/ProfileModal.vue";
import RecordModal from "./components/modal/RecordModal.vue";
import SaveToast from "./components/modal/SaveToast.vue";
import MyPageDashboard from "./components/profile/MyPageDashboard.vue";
import ImageUploadPanel from "./components/record/ImageUploadPanel.vue";
import StickerPanel from "./components/record/StickerPanel.vue";
import { canvasTools, nav, recentTags } from "./constants/navigation";
import { decorations, stickerCategories } from "./constants/stickers";
import { defaultAnalysis } from "./constants/defaultAnalysis";

function initialPageFromPath() {
  const path = window.location.pathname;
  if (path === "/deokkku/" || path === "/deokkku/home/") return "홈";
  if (path === "/deokkku/my_album/" || path === "/diaries/") return "내 앨범";
  if (path.startsWith("/diaries/")) return "내 앨범";
  if (path === "/reviews/" || path.startsWith("/reviews/")) return "리뷰";
  if (path === "/mypage/") return "마이페이지";
  return "기록 작성";
}

export default {
  name: "App",
  components: {
    BadgeModal,
    ImageUploadPanel,
    MyPageDashboard,
    ProfileModal,
    RecordModal,
    SavedAlbumGrid,
    SaveToast,
    Sidebar,
    StickerPanel,
    Topbar,
  },
  data() {
    return {
      simpleLogoUrl,
      query: "",
      activePage: initialPageFromPath(),
      activeStickerCategory: "전체",
      isRecordModalOpen: false,
      selectedDecorationId: null,
      mainImageSrc: "",
      currentRecord: {
        title: "새 감상 기록",
        date: "2026.05.18",
        rating: 0,
        memo: "좋아하는 장면과 감정을 자유롭게 남겨보세요.",
        tags: [],
      },
      recordForm: {
        title: "",
        date: new Date().toISOString().slice(0, 10),
        rating: 0,
      },
      recordModalMode: "create",
      savedCards: [],
      undoHistory: [],
      layerZIndex: 0,
      lastSaveAt: 0,
      toastMessage: "",
      isCheckingAuth: true,
      currentUser: null,
      isLoggingOut: false,
      isProfileSaving: false,
      showProfileMenu: false,
      isProfileModalOpen: false,
      isBadgeModalOpen: false,
      csrfToken: "",
      profileForm: {
        nickname: "",
        profileImage: null,
        removeProfileImage: false,
      },
      profilePreviewLocalUrl: "",
      profileStatus: {
        type: "",
        message: "",
      },
      selectedBadgeIds: [],
      dragging: null,
      resizing: null,
      rotating: null,
      nav,
      recentTags,
      canvasTools,
      stickerCategories,
      decorations,
      placedItems: [],
      ai: defaultAnalysis,
      currentRecordId: null,  // 현재 편집 중인 백엔드 Record ID (null이면 신규)
      isSaving: false,         // 저장 중 중복 요청 방지
    };
  },
  computed: {
    selectedView() {
      return this.currentRecord;
    },
    selectedViewStars() {
      return this.stars(this.selectedView.rating);
    },
    isCanvasEmpty() {
      return this.placedItems.length === 0 && !this.mainImageSrc;
    },
    canUndo() {
      return this.undoHistory.length > 0;
    },
    profilePreviewUrl() {
      return this.profilePreviewLocalUrl || this.currentUser?.profile_image || "";
    },
    profileInitial() {
      const source = this.currentUser?.nickname || this.currentUser?.email || "?";
      return source.trim().slice(0, 1).toUpperCase();
    },
    activityStats() {
      return this.getActivityStats();
    },
    profileStats() {
      const stats = this.activityStats;
      const unlockedBadges = this.availableBadges.filter((badge) => badge.unlocked).length;
      return [
        { icon: "🏅", label: "수집한 뱃지", value: unlockedBadges, action: "badges" },
        { icon: "▣", label: "내 앨범", value: stats.albums },
        { icon: "↗", label: "공유 카드", value: stats.shares },
        { icon: "⭐", label: "대표 뱃지", value: this.featuredBadges.length },
      ];
    },
    availableBadges() {
      return this.getUserBadges();
    },
    featuredBadges() {
      const unlocked = this.availableBadges.filter((badge) => badge.unlocked);
      const selected = this.selectedBadgeIds
        .map((id) => unlocked.find((badge) => badge.id === id))
        .filter(Boolean);
      return selected.slice(0, 3);
    },
    recentActivities() {
      return (this.savedCards || []).slice(0, 5).map((card) => ({
        id: `saved-${card.id}`,
        icon: "▣",
        title: card.title || "저장한 다이어리",
        description: "내 앨범에 저장한 감상 카드",
        date: card.date || "최근",
      }));
    },
    visibleDecorations() {
      if (this.activeStickerCategory === "전체") {
        return this.decorations;
      }
      return this.decorations.filter((item) => item.category === this.activeStickerCategory);
    },
    pageDescription() {
      const descriptions = {
        홈: "최근 감상 기록과 다이어리 꾸미기를 한눈에 확인합니다.",
        "내 앨범": "저장한 다이어리 카드를 모아보는 공간입니다.",
        리뷰: "작품별 감상과 별점을 정리합니다.",
        마이페이지: "내 취향과 활동 기록을 확인합니다.",
        "공유 페이지": "다이어리 기록을 공유용 이미지로 생성하고 저장합니다.",
      };
      return descriptions[this.activePage] || "선택한 기록 모음을 다이어리 카드로 미리 봅니다.";
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
  mounted() {
    window.addEventListener("pointermove", this.handlePointerMove);
    window.addEventListener("pointerup", this.stopPointerWork);
    document.addEventListener("click", this.handleProfileOutsideClick);
    document.addEventListener("keydown", this.handleGlobalKeydown);
    this.loadRepresentativeBadges();
    this.checkAuth();
    this.loadSavedCards();
  },
  beforeUnmount() {
    window.removeEventListener("pointermove", this.handlePointerMove);
    window.removeEventListener("pointerup", this.stopPointerWork);
    document.removeEventListener("click", this.handleProfileOutsideClick);
    document.removeEventListener("keydown", this.handleGlobalKeydown);
  },
  methods: {
    async checkAuth() {
      try {
        this.currentUser = await this.apiFetch("/api/auth/me/");
        this.resetProfileForm();
        this.loadRepresentativeBadges();
        this.isCheckingAuth = false;
      } catch (error) {
        console.error(error);
        window.location.href = this.loginRedirectUrl();
      }
    },
    loginRedirectUrl() {
      const { protocol, hostname, port } = window.location;
      const isViteDevServer = ["5173", "5174"].includes(port);
      if (isViteDevServer) {
        return `${protocol}//${hostname}:8000/deokkku/login/`;
      }
      return "/deokkku/login/";
    },
    async getCsrfToken(forceRefresh = false) {
      if (this.csrfToken && !forceRefresh) return this.csrfToken;
      const response = await fetch("/api/auth/csrf/", {
        credentials: "include",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) {
        const errorBody = await response.text();
        console.error("CSRF token request failed:", response.status, errorBody);
        throw new Error(`CSRF token request failed: ${response.status}`);
      }
      const data = await response.json();
      this.csrfToken = data.csrfToken || "";
      return this.csrfToken;
    },
    toggleProfileMenu() {
      this.showProfileMenu = !this.showProfileMenu;
    },
    closeProfileMenu() {
      this.showProfileMenu = false;
    },
    handleProfileOutsideClick(event) {
      if (!this.showProfileMenu) return;
      const menu = this.$refs.profileMenu;
      if (menu && !menu.contains(event.target)) {
        this.closeProfileMenu();
      }
    },
    handleGlobalKeydown(event) {
      if (event.key !== "Escape") return;
      this.closeProfileMenu();
      if (this.isProfileModalOpen) {
        this.closeProfileModal();
      }
      if (this.isBadgeModalOpen) {
        this.closeBadgeModal();
      }
    },
    openProfileModal() {
      this.resetProfileForm();
      this.isProfileModalOpen = true;
    },
    closeProfileModal() {
      this.isProfileModalOpen = false;
      this.resetProfileForm();
    },
    openBadgeModal() {
      this.isBadgeModalOpen = true;
    },
    closeBadgeModal() {
      this.isBadgeModalOpen = false;
    },
    badgeStorageKey() {
      return `deokkkuRepresentativeBadges:${this.currentUser?.email || "guest"}`;
    },
    loadRepresentativeBadges() {
      try {
        const stored = JSON.parse(localStorage.getItem(this.badgeStorageKey()) || "[]");
        this.selectedBadgeIds = Array.isArray(stored) ? stored.slice(0, 3) : [];
      } catch (error) {
        this.selectedBadgeIds = [];
      }
    },
    persistRepresentativeBadges() {
      try {
        localStorage.setItem(this.badgeStorageKey(), JSON.stringify(this.selectedBadgeIds.slice(0, 3)));
      } catch (error) {
        // 대표 뱃지는 화면 표시용이므로 저장 실패 시 현재 세션 상태만 유지합니다.
      }
    },
    toggleRepresentativeBadge(badge) {
      if (!badge.unlocked) return;
      if (this.selectedBadgeIds.includes(badge.id)) {
        this.selectedBadgeIds = this.selectedBadgeIds.filter((id) => id !== badge.id);
      } else {
        this.selectedBadgeIds = [...this.selectedBadgeIds, badge.id].slice(-3);
      }
      this.persistRepresentativeBadges();
    },
    getActivityStats() {
      const albums = Array.isArray(this.savedCards) ? this.savedCards.length : 0;
      const shares = 0;
      return {
        records: albums,
        albums,
        shares,
        recent: Math.min(albums + shares, 9),
      };
    },
    getFavoriteGenres() {
      return [];
    },
    getUserBadges() {
      const stats = this.getActivityStats();
      const ratedCount = (this.savedCards || []).filter((card) => Number(card.rating || 0) > 0).length;
      return [
        {
          id: "first-record",
          icon: "🏆",
          label: "첫 기록 작성",
          description: "기록 1개 이상",
          unlocked: stats.records + stats.albums >= 1,
        },
        {
          id: "archive-collector",
          icon: "📚",
          label: "기록 수집가",
          description: "기록 5개 이상",
          unlocked: stats.records + stats.albums >= 5,
        },
        {
          id: "rating-master",
          icon: "⭐",
          label: "별점 마스터",
          description: "별점 기록 3개 이상",
          unlocked: ratedCount >= 3,
        },
        {
          id: "decoration-starter",
          icon: "🎨",
          label: "다꾸 입문자",
          description: "저장한 다이어리 1개 이상",
          unlocked: stats.albums >= 1,
        },
        {
          id: "steady-logger",
          icon: "📝",
          label: "꾸준한 기록러",
          description: "기록 10개 이상",
          unlocked: stats.records + stats.albums >= 10,
        },
      ];
    },
    resetProfileForm() {
      if (this.profilePreviewLocalUrl) {
        URL.revokeObjectURL(this.profilePreviewLocalUrl);
      }
      this.profilePreviewLocalUrl = "";
      this.profileForm = {
        nickname: this.currentUser?.nickname || "",
        profileImage: null,
        removeProfileImage: false,
      };
      this.profileStatus = { type: "", message: "" };
    },
    handleProfileImageChange(event) {
      const file = event.target.files?.[0] || null;
      if (this.profilePreviewLocalUrl) {
        URL.revokeObjectURL(this.profilePreviewLocalUrl);
      }
      this.profilePreviewLocalUrl = file ? URL.createObjectURL(file) : "";
      this.profileForm.profileImage = file;
      if (file) {
        this.profileForm.removeProfileImage = false;
      }
      this.profileStatus = { type: "", message: "" };
    },
    formatProfileDate(value) {
      if (!value) return "";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "";
      return date.toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    },
    async updateProfile() {
      const nickname = this.profileForm.nickname.trim();
      if (!nickname) {
        this.profileStatus = { type: "error", message: "닉네임을 입력해주세요." };
        return;
      }

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
          method: "PATCH",
          credentials: "include",
          headers: { "X-CSRFToken": csrfToken },
          body: formData,
        });
        if (!response.ok) {
          const responseBody = await response.text();
          let detail = responseBody;
          try {
            const errorData = JSON.parse(responseBody);
            detail = errorData.detail || JSON.stringify(errorData);
          } catch (error) {
            // Keep the raw response body when the server does not return JSON.
          }
          throw new Error(`프로필 저장에 실패했습니다. (${response.status}) ${detail}`);
        }

        this.currentUser = await response.json();
        this.resetProfileForm();
        this.profileStatus = { type: "success", message: "프로필이 저장되었습니다." };
      } catch (error) {
        this.profileStatus = { type: "error", message: error.message || "프로필 저장에 실패했습니다." };
      } finally {
        this.isProfileSaving = false;
      }
    },
    async apiFetch(url, options = {}) {
      const method = (options.method || "GET").toUpperCase();
      const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      };
      const needsCsrf = !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method);
      if (needsCsrf) {
        headers["X-CSRFToken"] = await this.getCsrfToken();
      }

      const response = await fetch(url, {
        credentials: "include",
        ...options,
        headers,
      });
      if (!response.ok) {
        const responseBody = await response.text();
        let detail = responseBody;
        try {
          const errorData = JSON.parse(responseBody);
          detail = errorData.detail || JSON.stringify(errorData);
        } catch (error) {
          // Keep the raw response body when the server does not return JSON.
        }
        console.error("API request failed:", response.status, detail);
        throw new Error(`API request failed: ${response.status} ${detail}`);
      }
      // 204 No Content (DELETE 등) — 본문 없음
      if (response.status === 204) return null;
      return response.json();
    },
    async logout() {
      if (this.isLoggingOut) return;
      this.isLoggingOut = true;
      try {
        await this.apiFetch("/api/auth/logout/", {
          method: "POST",
          body: JSON.stringify({}),
        });
        window.location.href = this.loginRedirectUrl();
      } catch (error) {
        console.error(error);
      } finally {
        this.isLoggingOut = false;
      }
    },
    navigatePage(page) {
      this.activePage = page;
    },
    openProfilePageFromDropdown() {
      this.navigatePage(this.nav[4]);
      this.closeProfileMenu();
    },
    openAlbumFromToast() {
      this.navigatePage("내 앨범");
      this.toastMessage = "";
    },
    navIcon(item) {
      const icons = {
        홈: "⌂",
        "내 앨범": "▣",
        "기록 작성": "✎",
        리뷰: "★",
        마이페이지: "◉",
        "공유 페이지": "↗",
      };
      return icons[item] || "•";
    },
    stars(score) {
      const filled = Math.max(0, Math.min(5, Math.round(score / 2)));
      return "★".repeat(filled) + "☆".repeat(5 - filled);
    },
    placementStyle(item) {
      return {
        left: `${item.x}%`,
        top: `${item.y}%`,
        width: item.width ? `${item.width}px` : null,
        height: item.height ? `${item.height}px` : null,
        zIndex: item.zIndex || 1,
        "--item-scale": item.type === "text" ? 1 : item.scale || 1,
      };
    },
    stickerStyle(item) {
      const scale = item.type === "text" ? 1 : item.scale || 1;
      return {
        transform: `rotate(${item.rotate || 0}deg) scale(${scale})`,
      };
    },
    canvasRect() {
      return this.$refs.canvasLayer.getBoundingClientRect();
    },
    clamp(value, min, max) {
      return Math.max(min, Math.min(max, value));
    },
    cloneForSave(value) {
      return JSON.parse(JSON.stringify(value));
    },
    canvasSnapshot() {
      return {
        placedItems: this.cloneForSave(this.placedItems),
        mainImageSrc: this.mainImageSrc,
        selectedDecorationId: this.selectedDecorationId,
      };
    },
    pushUndoState() {
      this.undoHistory.push(this.canvasSnapshot());
      if (this.undoHistory.length > 50) {
        this.undoHistory.shift();
      }
    },
    undoLastCanvasChange() {
      const previousState = this.undoHistory.pop();
      if (!previousState) return;
      this.placedItems = this.cloneForSave(previousState.placedItems);
      this.mainImageSrc = previousState.mainImageSrc || "";
      this.selectedDecorationId = previousState.selectedDecorationId || null;
      this.syncLayerZIndex();
    },
    currentMaxLayerZIndex() {
      return this.placedItems.reduce((maxZIndex, item) => Math.max(maxZIndex, item.zIndex || 0), 0);
    },
    nextLayerZIndex() {
      this.layerZIndex = Math.max(this.layerZIndex, this.currentMaxLayerZIndex()) + 1;
      return this.layerZIndex;
    },
    syncLayerZIndex() {
      this.layerZIndex = this.currentMaxLayerZIndex();
    },
    bringDecorationToFront(id) {
      const item = this.placedItems.find((decoration) => decoration.id === id);
      if (!item) return;
      item.zIndex = this.nextLayerZIndex();
    },
    selectDecoration(id) {
      this.selectedDecorationId = id;
      this.bringDecorationToFront(id);
    },
    clearDecorationSelection() {
      this.selectedDecorationId = null;
    },
    addDecoration(sticker) {
      this.pushUndoState();
      const nextId = Date.now();
      const nextItem = {
        id: nextId,
        icon: sticker.icon,
        tone: sticker.tone,
        imageSrc: sticker.imageSrc || null,
        x: 24 + (this.placedItems.length * 11) % 52,
        y: 20 + (this.placedItems.length * 17) % 56,
        rotate: -14 + (this.placedItems.length * 9) % 28,
        scale: sticker.imageSrc ? 0.72 : sticker.icon.length > 1 ? 0.86 : 1.08,
        zIndex: this.nextLayerZIndex(),
      };
      this.placedItems.push(nextItem);
      this.selectedDecorationId = nextId;
    },
    addTextMemo() {
      this.pushUndoState();
      const nextId = Date.now();
      this.placedItems.push({
        id: nextId,
        type: "text",
        text: "새 메모",
        tone: "memo-text",
        x: 38 + (this.placedItems.length * 9) % 35,
        y: 34 + (this.placedItems.length * 7) % 36,
        rotate: -4 + (this.placedItems.length * 3) % 9,
        scale: 1,
        fontSize: 15,
        width: 190,
        height: 150,
        zIndex: this.nextLayerZIndex(),
      });
      this.selectedDecorationId = nextId;
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
          method: "POST",
          credentials: "include",
          headers: { "X-CSRFToken": csrfToken },
          body: formData,
        });
        if (!response.ok) {
          const err = await response.text();
          throw new Error(`이미지 업로드 실패: ${response.status} ${err}`);
        }
        const data = await response.json();

        this.pushUndoState();
        const nextId = Date.now();
        const nextItem = {
          id: nextId,
          icon: "",
          imageSrc: data.url,  // 백엔드 protected URL
          tone: "custom-image",
          x: 31 + (this.placedItems.length * 7) % 38,
          y: 24 + (this.placedItems.length * 9) % 44,
          rotate: -6 + (this.placedItems.length * 5) % 14,
          scale: 1,
          zIndex: this.nextLayerZIndex(),
        };
        this.placedItems.push(nextItem);
        this.mainImageSrc = data.url;
        this.selectedDecorationId = nextId;
      } catch (error) {
        console.error(error);
        alert("이미지 업로드에 실패했습니다. 다시 시도해주세요.");
      }
    },
    removeSticker(id) {
      this.pushUndoState();
      this.placedItems = this.placedItems.filter((sticker) => sticker.id !== id);
      if (this.selectedDecorationId === id) {
        this.selectedDecorationId = null;
      }
    },
    runCanvasTool(tool) {
      if (tool.action === "memo") {
        this.addTextMemo();
      }
    },
    startDrag(event, item) {
      if (!event.target.closest("textarea")) {
        event.preventDefault();
      }
      this.selectDecoration(item.id);
      const rect = this.canvasRect();
      this.dragging = {
        item,
        rect,
        offsetX: event.clientX - (rect.left + (item.x / 100) * rect.width),
        offsetY: event.clientY - (rect.top + (item.y / 100) * rect.height),
      };
    },
    startResize(event, item) {
      event.preventDefault();
      this.selectDecoration(item.id);
      this.resizing = item.type === "text"
        ? {
            item,
            mode: "box",
            startX: event.clientX,
            startY: event.clientY,
            startWidth: item.width || 190,
            startHeight: item.height || 150,
          }
        : {
            item,
            mode: "scale",
            startX: event.clientX,
            startY: event.clientY,
            startScale: item.scale || 1,
          };
    },
    startRotate(event, item) {
      event.preventDefault();
      this.selectDecoration(item.id);
      const rect = event.currentTarget.parentElement.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      this.rotating = {
        item,
        centerX,
        centerY,
        startAngle: Math.atan2(event.clientY - centerY, event.clientX - centerX),
        startRotate: item.rotate || 0,
      };
    },
    angleToDegrees(radians) {
      return radians * 180 / Math.PI;
    },
    handlePointerMove(event) {
      if (this.dragging) {
        const { item, rect, offsetX, offsetY } = this.dragging;
        const nextX = ((event.clientX - offsetX - rect.left) / rect.width) * 100;
        const nextY = ((event.clientY - offsetY - rect.top) / rect.height) * 100;
        item.x = this.clamp(nextX, 2, 94);
        item.y = this.clamp(nextY, 3, 90);
      }

      if (this.resizing) {
        const { item, mode, startX, startY } = this.resizing;
        if (mode === "box") {
          item.width = this.clamp(this.resizing.startWidth + event.clientX - startX, 120, 440);
          item.height = this.clamp(this.resizing.startHeight + event.clientY - startY, 100, 380);
        } else {
          const delta = Math.max(event.clientX - startX, event.clientY - startY);
          item.scale = this.clamp(this.resizing.startScale + delta / 140, 0.45, 2.8);
        }
      }

      if (this.rotating) {
        const { item, centerX, centerY, startAngle, startRotate } = this.rotating;
        const currentAngle = Math.atan2(event.clientY - centerY, event.clientX - centerX);
        item.rotate = Math.round(startRotate + this.angleToDegrees(currentAngle - startAngle));
      }
    },
    stopPointerWork() {
      this.dragging = null;
      this.resizing = null;
      this.rotating = null;
    },
    openRecordModal(mode = "create") {
      this.recordModalMode = mode;
      this.recordForm = {
        title: mode === "edit" ? this.currentRecord.title : "",
        date: mode === "edit" ? this.formatInputDate(this.currentRecord.date) : new Date().toISOString().slice(0, 10),
        rating: mode === "edit" ? this.currentRecord.rating : 0,
      };
      this.isRecordModalOpen = true;
    },
    closeRecordModal() {
      this.isRecordModalOpen = false;
    },
    formatDisplayDate(value) {
      if (!value) return "";
      return value.replaceAll("-", ".");
    },
    formatInputDate(value) {
      if (!value) return new Date().toISOString().slice(0, 10);
      return value.replaceAll(".", "-");
    },
    createBlankRecord() {
      this.currentRecord = {
        title: this.recordForm.title || "제목 없는 기록",
        date: this.formatDisplayDate(this.recordForm.date),
        rating: this.recordForm.rating,
        memo: "새롭게 작성한 감상 기록입니다.",
        tags: [],
      };
      if (this.recordModalMode !== "edit") {
        // 신규 기록이면 백엔드 ID 초기화 (저장 시 POST)
        this.currentRecordId = null;
        this.placedItems = [];
        this.mainImageSrc = "";
        this.selectedDecorationId = null;
        this.undoHistory = [];
        this.syncLayerZIndex();
      }
      this.activePage = "기록 작성";
      this.isRecordModalOpen = false;
    },

    // ── 백엔드 Record → 프론트 savedCard 포맷 변환 헬퍼 ──────────────────
    apiRecordToSavedCard(record) {
      const cd = record.canvas_data || {};
      const placedItems = cd.placed_items || [];
      const title = (cd.title || "").trim() || record.work_title || record.title || record.anime_title || "제목 없는 기록";
      const rawDate = record.watched_date || record.created_at || "";
      const watchedDate = rawDate ? rawDate.slice(0, 10).replaceAll("-", ".") : "";
      const imageSrc = cd.main_image_src || record.work_poster || "";
      return {
        id: record.id,
        title,
        date: watchedDate,
        rating: record.rating ?? 0,
        imageSrc,
        memoCount: placedItems.filter((i) => i.type === "text").length,
        stickerCount: placedItems.filter((i) => i.type !== "text").length,
        savedAt: record.created_at,
        snapshot: {
          record: {
            title,
            date: watchedDate,
            rating: record.rating ?? 0,
            memo: record.content || "",
            tags: [],
          },
          placedItems,
          mainImageSrc: imageSrc,
          analysis: cd.analysis || null,
        },
      };
    },

    // ── 기록 목록 불러오기 (GET /api/records/) ────────────────────────────
    async loadSavedCards() {
      try {
        const data = await this.apiFetch("/api/records/");
        const results = Array.isArray(data) ? data : (Array.isArray(data?.results) ? data.results : []);
        this.savedCards = results.map((r) => this.apiRecordToSavedCard(r));
      } catch (error) {
        console.error("기록 목록 불러오기 실패:", error);
        this.savedCards = [];
      }
    },

    // ── 저장 (신규: POST / 수정: PATCH) ──────────────────────────────────
    async saveCard() {
      const now = Date.now();
      if (now - this.lastSaveAt < 350 || this.isSaving) return;
      this.lastSaveAt = now;
      this.isSaving = true;

      try {
        const recordTitle = (this.currentRecord.title || this.recordForm.title || "").trim() || "제목 없는 기록";
        const payload = {
          work_title: recordTitle,
          anime_title: recordTitle,
          rating: this.currentRecord.rating ?? null,
          watched_date: this.formatInputDate(this.currentRecord.date) || null,
          content: this.currentRecord.memo || "",
          canvas_data: {
            title: recordTitle,
            placed_items: this.cloneForSave(this.placedItems),
            main_image_src: this.mainImageSrc,
            analysis: this.cloneForSave(this.ai),
          },
          status: "published",
          visibility: "private",
        };

        let record;
        if (this.currentRecordId) {
          // 기존 기록 수정 (PATCH)
          record = await this.apiFetch(`/api/records/${this.currentRecordId}/`, {
            method: "PATCH",
            body: JSON.stringify(payload),
          });
          const updated = this.apiRecordToSavedCard(record);
          const idx = this.savedCards.findIndex((c) => c.id === this.currentRecordId);
          if (idx !== -1) this.savedCards.splice(idx, 1, updated);
          else this.savedCards.unshift(updated);
        } else {
          // 새 기록 생성 (POST)
          record = await this.apiFetch("/api/records/", {
            method: "POST",
            body: JSON.stringify(payload),
          });
          this.currentRecordId = record.id;
          this.savedCards.unshift(this.apiRecordToSavedCard(record));
        }

        this.toastMessage = "저장되었습니다";
      } catch (error) {
        console.error("저장 실패:", error);
        this.toastMessage = "저장에 실패했습니다. 다시 시도해주세요.";
      } finally {
        this.isSaving = false;
      }
    },

    // ── 저장된 카드 열기 ──────────────────────────────────────────────────
    openSavedCard(card) {
      if (card.id) {
        const baseUrl = ["5173", "5174"].includes(window.location.port)
          ? (import.meta.env.BASE_URL || "/").replace(/\/$/, "")
          : "";
        window.history.pushState({}, "", `${baseUrl}/diaries/${card.id}/`);
      }
      this.currentRecord = this.cloneForSave(
        card.snapshot?.record || {
          title: card.title,
          date: card.date,
          rating: card.rating,
          memo: "",
          tags: [],
        }
      );
      this.placedItems = this.cloneForSave(card.snapshot?.placedItems || []);
      this.mainImageSrc = card.snapshot?.mainImageSrc || "";
      this.selectedDecorationId = null;
      this.currentRecordId = card.id;  // 수정 모드 — 저장 시 PATCH
      this.activePage = "기록 작성";
      this.toastMessage = "";
      this.undoHistory = [];
      this.syncLayerZIndex();
      if (card.snapshot?.analysis) {
        this.ai = this.cloneForSave(card.snapshot.analysis);
      }
    },

    // ── 기록 삭제 (DELETE /api/records/{id}/) ────────────────────────────
    async deleteSavedCard(cardId) {
      try {
        await this.apiFetch(`/api/records/${cardId}/`, { method: "DELETE" });
        this.savedCards = this.savedCards.filter((card) => card.id !== cardId);
        if (this.currentRecordId === cardId) {
          this.currentRecordId = null;
        }
      } catch (error) {
        console.error("삭제 실패:", error);
        alert("삭제에 실패했습니다. 다시 시도해주세요.");
      }
    },
  },
};
</script>

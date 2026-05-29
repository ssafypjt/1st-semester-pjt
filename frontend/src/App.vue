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
      <aside class="sidebar">
        <button class="brand deokkku-mini" type="button" @click="activePage = '홈'" aria-label="Deokkku">
          <img class="simple-logo-img" :src="simpleLogoUrl" alt="Deokkku 로고" />
          <span>덕꾸</span>
          <small>Deokkku</small>
        </button>
        <p>내가 사랑하는 애니메이션을<br />기록하고, 모으고, 공유하는 공간</p>
        <nav>
          <button
            v-for="item in nav"
            :key="item"
            :class="{ active: activePage === item }"
            type="button"
            @click="navigatePage(item)"
          >
            <span>{{ navIcon(item) }}</span>{{ item }}
          </button>
        </nav>
        <div class="today">
          <b>오늘의 한 마디</b>
          <p>좋아하는 작품을 기록하는 시간이 내 취향을 더 선명하게 만듭니다.</p>
        </div>
        <div class="tags">
          <b>최근 태그</b>
          <span v-for="tag in recentTags" :key="tag">#{{ tag }}</span>
        </div>
      </aside>

      <main class="main">
        <header class="topbar">
          <label class="search">
            <input v-model="query" placeholder="애니 제목, 캐릭터, 태그로 검색해보세요" />
            <span>⌕</span>
          </label>
          <div class="top-actions">
            <button class="primary" type="button" @click="openRecordModal">＋ 새 기록</button>
            <button class="icon-btn" type="button" title="알림">!</button>
            <button v-if="!isCheckingAuth && currentUser" class="logout-btn" type="button" :disabled="isLoggingOut" @click="logout">로그아웃</button>
            <button class="avatar" type="button"></button>
          </div>
        </header>

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
            <section class="panel-card">
              <header>
                <h3>스티커샵</h3>
                <span>클릭해서 붙이기</span>
              </header>
              <div class="subtabs">
                <button
                  v-for="category in stickerCategories"
                  :key="category"
                  :class="{ active: activeStickerCategory === category }"
                  type="button"
                  @click="activeStickerCategory = category"
                >
                  {{ category }}
                </button>
              </div>
              <div class="sticker-grid">
                <button
                  v-for="sticker in visibleDecorations"
                  :key="sticker.id || `${sticker.icon}-${sticker.tone}`"
                  :class="sticker.tone"
                  type="button"
                  @click="addDecoration(sticker)"
                >
                  <img v-if="sticker.imageSrc" :src="sticker.imageSrc" :alt="sticker.label || '스티커'" />
                  <span v-else>{{ sticker.icon }}</span>
                </button>
              </div>
              <p class="shop-help">스티커, 프레임, 말풍선을 붙인 뒤 드래그로 이동할 수 있어요.</p>
            </section>

            <section class="panel-card">
              <header>
                <h3>이미지 첨부</h3>
                <span>내 이미지 붙이기</span>
              </header>
              <label class="upload-drop">
                <input type="file" accept="image/*" @change="handleImageUpload" />
                <span>＋</span>
                <b>이미지 선택</b>
                <small>선택한 이미지를 다이어리 위에 붙이고 드래그로 이동할 수 있어요.</small>
              </label>
            </section>

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
          <div class="detail-grid">
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
              <b>{{ card.title }}</b>
              <p>{{ card.body }}</p>
            </article>
          </div>
          <div v-if="activePage === '내 앨범'" class="saved-album-grid">
            <article
              v-for="card in savedCards"
              :key="card.id"
              class="saved-card"
              role="button"
              tabindex="0"
              title="저장된 기록 열기"
              @click="openSavedCard(card)"
              @keydown.enter.prevent="openSavedCard(card)"
              @keydown.space.prevent="openSavedCard(card)"
            >
              <button class="saved-card-delete" type="button" title="삭제" aria-label="삭제" @click.stop="deleteSavedCard(card.id)">
                ×
              </button>
              <small>{{ card.date }}</small>
              <h3>{{ card.title }}</h3>
              <p>{{ card.rating }} / 10 {{ stars(card.rating) }}</p>
              <span>스티커 {{ card.stickerCount || 0 }}개 · 메모 {{ card.memoCount || 0 }}개 저장됨</span>
            </article>
            <article v-if="savedCards.length === 0" class="saved-empty">
              <b>아직 저장한 카드가 없어요</b>
              <p>기록 작성에서 다이어리를 꾸민 뒤 저장을 누르면 여기에 보관됩니다.</p>
            </article>
          </div>
        </section>

        <section v-if="activePage === '기록 작성' || activePage === '공유 페이지'" class="share-showcase">
          <div class="panel-head">
            <div>
              <h3>모바일 공유 스타일</h3>
              <p>앱에서 만든 다이어리 기록을 스토리, 피드, 링크 카드, 이미지 저장용으로 미리 봅니다.</p>
            </div>
            <div class="share-tabs">
              <button v-for="mode in shareModes" :key="mode.id" :class="{ active: shareMode === mode.id }" type="button" @click="shareMode = mode.id">
                {{ mode.label }}
              </button>
            </div>
          </div>
          <div class="share-preview-board">
            <article class="phone-preview" :class="shareMode">
              <div class="phone-top"><span></span><b>ANILOG</b><span></span></div>
              <div class="mobile-card">
                <small>{{ selectedView.date }}</small>
                <h4>{{ selectedView.title }}</h4>
                <div class="mobile-art">
                  <img v-if="mainImageSrc" :src="mainImageSrc" alt="" />
                  <span v-else class="empty-image-slot">
                    <strong>＋</strong>
                    <em>이미지</em>
                  </span>
                  <i v-for="item in placedItems.slice(0, 6)" :key="item.id">
                    <span v-if="item.type === 'text'">T</span>
                    <img v-else-if="item.imageSrc" :src="item.imageSrc" alt="" />
                    <span v-else>{{ item.icon }}</span>
                  </i>
                </div>
                <p>{{ selectedView.memo }}</p>
                <strong>{{ selectedView.rating }} / 10 {{ stars(selectedView.rating) }}</strong>
              </div>
              <div class="phone-actions">
                <button type="button">이미지 저장</button>
                <button type="button">링크 복사</button>
                <button type="button">스토리 저장</button>
              </div>
            </article>
            <article class="share-note">
              <b>공유 형식</b>
              <p>스토리형, 피드형, 링크형 카드 구성을 기존 화면처럼 유지했습니다.</p>
              <div class="share-icons"><span>◎</span><span>K</span><span>↗</span><span>↓</span></div>
            </article>
          </div>
        </section>

        <div v-if="isRecordModalOpen" class="modal-backdrop" @click.self="closeRecordModal">
          <section class="record-modal" role="dialog" aria-modal="true" aria-label="기록 정보 수정">
            <header>
              <h3>{{ recordModalMode === 'edit' ? '기록 정보 수정' : '새 기록 만들기' }}</h3>
              <button type="button" @click="closeRecordModal">×</button>
            </header>
            <label>
              <span>작품명</span>
              <input v-model="recordForm.title" placeholder="애니메이션 제목을 입력하세요" />
            </label>
            <label>
              <span>감상 날짜</span>
              <input type="date" v-model="recordForm.date" />
            </label>
            <label>
              <span>별점</span>
              <input type="range" min="0" max="10" step="0.5" v-model.number="recordForm.rating" />
              <b>{{ recordForm.rating }} / 10 {{ stars(recordForm.rating) }}</b>
            </label>
            <div class="modal-actions">
              <button type="button" @click="closeRecordModal">취소</button>
              <button class="primary" type="button" @click="createBlankRecord">
                {{ recordModalMode === 'edit' ? '수정하기' : '시작하기' }}
              </button>
            </div>
          </section>
        </div>

        <div v-if="toastMessage" class="save-popup-backdrop" @click.self="toastMessage = ''">
          <section class="save-popup" role="alertdialog" aria-modal="true" aria-label="저장 완료 안내">
            <strong>{{ toastMessage }}</strong>
            <p>내 앨범에서 저장한 다이어리 카드를 확인할 수 있어요.</p>
            <div>
              <button type="button" @click="toastMessage = ''">확인</button>
              <button class="primary" type="button" @click="navigatePage('내 앨범'); toastMessage = ''">내 앨범 보기</button>
            </div>
          </section>
        </div>
      </main>
    </section>
  </div>
</template>

<script>
import guineapigUrl from "./assets/images/guineapig.png";
import simpleLogoUrl from "./assets/images/simple_logo.png";

const defaultAnalysis = {
  summary: "좋아하는 장면과 감정을 다이어리 카드로 남겨보세요.",
  phrase: "오래 기억하고 싶은 감상",
  tags: ["감성", "명장면", "OST", "캐릭터", "공유하기"],
  preference: "감정선과 장면 기록을 좋아하는 취향",
};

export default {
  name: "App",
  data() {
    return {
      simpleLogoUrl,
      query: "",
      activePage: "기록 작성",
      activeStickerCategory: "전체",
      shareMode: "story",
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
      csrfToken: "",
      dragging: null,
      resizing: null,
      rotating: null,
      nav: ["홈", "내 앨범", "기록 작성", "리뷰", "마이페이지"],
      recentTags: ["감성애니", "인생작", "명장면", "음악", "OST맛집"],
      canvasTools: [
        { icon: "▦", label: "배경" },
        { icon: "★", label: "스티커" },
        { icon: "T", label: "메모", action: "memo" },
        { icon: "＋", label: "이미지" },
        { icon: "◇", label: "테이프" },
      ],
      stickerCategories: ["전체", "스티커", "프레임", "말풍선", "아이콘", "배경"],
      decorations: [
        { id: "guineapig", icon: "guineapig", label: "기니피그", tone: "sticker-image guineapig-sticker", category: "스티커", imageSrc: guineapigUrl },
        { icon: "♡", tone: "pink", category: "스티커" },
        { icon: "★", tone: "purple", category: "스티커" },
        { icon: "✦", tone: "line", category: "스티커" },
        { icon: "♪", tone: "soft", category: "스티커" },
        { icon: "!", tone: "pink", category: "아이콘" },
        { icon: "#", tone: "purple", category: "아이콘" },
        { icon: "Zzz", tone: "line bubble", category: "말풍선" },
        { icon: "좋아해", tone: "pink bubble", category: "말풍선" },
        { icon: "최애 장면", tone: "purple bubble", category: "말풍선" },
        { icon: "POLA", tone: "ink frame", category: "프레임" },
        { icon: "FILM", tone: "purple frame", category: "프레임" },
        { icon: "grid", tone: "soft bg", category: "배경" },
        { icon: "dot", tone: "pink bg", category: "배경" },
        { icon: "tape", tone: "masking-tape tape-lavender", category: "스티커" },
        { icon: "tape", tone: "masking-tape tape-rose", category: "스티커" },
        { icon: "tape", tone: "masking-tape tape-mint", category: "스티커" },
      ],
      placedItems: [],
      shareModes: [
        { id: "story", label: "스토리 9:16" },
        { id: "feed", label: "피드 1:1" },
        { id: "link", label: "링크 카드" },
        { id: "image", label: "이미지 저장" },
      ],
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
        "공유 페이지": "다이어리 카드를 공유용 이미지와 링크로 미리 봅니다.",
      };
      return descriptions[this.activePage] || "선택한 기록 모음을 다이어리 카드로 미리 봅니다.";
    },
    detailCards() {
      return [
        { title: "기록 작성", body: "이미지, 스티커, 메모를 붙여 새 감상 다이어리를 만듭니다.", action: "기록 작성" },
        { title: "내 앨범", body: "저장한 다이어리 카드를 다시 열고 편집할 수 있습니다.", action: "내 앨범" },
        { title: "공유 페이지", body: "스토리와 피드용 공유 미리보기를 확인합니다.", action: "공유 페이지" },
      ];
    },
  },
  mounted() {
    window.addEventListener("pointermove", this.handlePointerMove);
    window.addEventListener("pointerup", this.stopPointerWork);
    this.checkAuth();
    this.loadSavedCards();
  },
  beforeUnmount() {
    window.removeEventListener("pointermove", this.handlePointerMove);
    window.removeEventListener("pointerup", this.stopPointerWork);
  },
  methods: {
    async checkAuth() {
      try {
        this.currentUser = await this.apiFetch("/api/auth/me/");
        this.isCheckingAuth = false;
      } catch (error) {
        console.error(error);
        window.location.href = this.loginRedirectUrl();
      }
    },
    loginRedirectUrl() {
      const { hostname, port } = window.location;
      if (hostname === "localhost" && ["5173", "5174"].includes(port)) {
        return "http://localhost:8000/deokkku/login/";
      }
      if (hostname === "127.0.0.1" && ["5173", "5174"].includes(port)) {
        return "http://127.0.0.1:8000/deokkku/login/";
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
        window.location.href = "/deokkku/login/";
      } catch (error) {
        console.error(error);
      } finally {
        this.isLoggingOut = false;
      }
    },
    navigatePage(page) {
      this.activePage = page;
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
      const title = (cd.title || "").trim() || record.work_title || "제목 없는 기록";
      const watchedDate = record.watched_date
        ? record.watched_date.replaceAll("-", ".")
        : "";
      return {
        id: record.id,
        title,
        date: watchedDate,
        rating: record.rating ?? 0,
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
          mainImageSrc: cd.main_image_src || "",
          analysis: cd.analysis || null,
        },
      };
    },

    // ── 기록 목록 불러오기 (GET /api/records/) ────────────────────────────
    async loadSavedCards() {
      try {
        const data = await this.apiFetch("/api/records/");
        const results = Array.isArray(data) ? data : (data.results || []);
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
        const payload = {
          work_title: this.currentRecord.title || "제목 없는 기록",
          rating: this.currentRecord.rating ?? null,
          watched_date: this.formatInputDate(this.currentRecord.date) || null,
          content: this.currentRecord.memo || "",
          canvas_data: {
            title: this.currentRecord.title,
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

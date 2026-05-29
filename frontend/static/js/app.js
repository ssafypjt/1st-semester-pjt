window.addEventListener("load", () => {
  const { createApp } = Vue;
  const initialRouteElement = document.getElementById("initial-route");
  const initialRoute = initialRouteElement ? JSON.parse(initialRouteElement.textContent) : { page: "home" };

  const PanelCard = {
    props: ["title"],
    template: `
      <section class="panel-card">
        <header>
          <h3>{{ title }}</h3>
          <span><slot name="action"></slot></span>
        </header>
        <slot></slot>
      </section>
    `,
  };

  const PlacedDecoration = {
    props: ["item", "selected"],
    emits: ["select", "drag-start", "resize-start", "rotate-start", "remove"],
    computed: {
      placementStyle() {
        return {
          left: `${this.item.x}%`,
          top: `${this.item.y}%`,
          width: this.item.width ? `${this.item.width}px` : null,
          height: this.item.height ? `${this.item.height}px` : null,
          zIndex: this.item.zIndex || 1,
          "--item-scale": this.item.type === "text" ? 1 : this.item.scale || 1,
        };
      },
      stickerStyle() {
        const scale = this.item.type === "text" ? 1 : this.item.scale || 1;
        return {
          transform: `rotate(${this.item.rotate}deg) scale(${scale})`,
        };
      },
      textStyle() {
        return {
          fontSize: `${this.item.fontSize || 15}px`,
        };
      },
    },
    template: `
      <div
        class="placed-decoration"
        :class="{ selected }"
        :style="placementStyle"
        role="button"
        tabindex="0"
        @click.stop="$emit('select', item.id)"
        @pointerdown="$emit('drag-start', $event, item)"
        title="드래그로 이동"
      >
        <div class="placed-sticker" :class="item.tone" :style="stickerStyle">
          <div v-if="item.type === 'text'" class="memo-editor">
            <textarea
              v-model="item.text"
              :style="textStyle"
              @click.stop="$emit('select', item.id)"
              placeholder="메모를 입력하세요"
            ></textarea>
            <label v-if="selected" class="memo-font-control" @pointerdown.stop @click.stop>
              <span>글자</span>
              <input type="range" min="11" max="34" step="1" v-model.number="item.fontSize" title="글자 크기 조절" />
            </label>
          </div>
          <img v-else-if="item.imageSrc" :src="item.imageSrc" alt="첨부 이미지" />
          <span v-else>{{ item.icon }}</span>
        </div>
        <button
          v-if="selected"
          class="rotate-decoration"
          type="button"
          @pointerdown.stop="$emit('rotate-start', $event, item)"
          @click.stop
          title="드래그해서 기울기 조절"
        >
          ↻
        </button>
        <button
          v-if="selected"
          class="resize-decoration"
          type="button"
          @pointerdown.stop="$emit('resize-start', $event, item)"
          @click.stop
          title="드래그해서 전체 크기 조절"
          aria-label="크기 조절"
        ></button>
        <button
          v-if="selected"
          class="delete-decoration"
          type="button"
          @pointerdown.stop
          @click.stop="$emit('remove', item.id)"
          title="삭제"
        >
          ×
        </button>
      </div>
    `,
  };

  const DecorationLayer = {
    components: { "placed-decoration": PlacedDecoration },
    props: ["items", "selectedId"],
    emits: ["select", "clear", "remove"],
    data() {
      return {
        dragging: null,
        resizing: null,
        rotating: null,
      };
    },
    mounted() {
      window.addEventListener("pointermove", this.handlePointerMove);
      window.addEventListener("pointerup", this.stopPointerWork);
    },
    beforeUnmount() {
      window.removeEventListener("pointermove", this.handlePointerMove);
      window.removeEventListener("pointerup", this.stopPointerWork);
    },
    methods: {
      canvasRect() {
        return this.$refs.layer.getBoundingClientRect();
      },
      clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
      },
      select(itemId) {
        this.$emit("select", itemId);
      },
      remove(itemId) {
        this.$emit("remove", itemId);
      },
      startDrag(event, item) {
        if (!event.target.closest("textarea")) {
          event.preventDefault();
        }
        this.select(item.id);
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
        this.select(item.id);
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
        this.select(item.id);
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
    },
    template: `
      <div class="decoration-layer" ref="layer" @click.self="$emit('clear')">
        <placed-decoration
          v-for="item in items"
          :key="item.id"
          :item="item"
          :selected="selectedId === item.id"
          @select="select"
          @drag-start="startDrag"
          @resize-start="startResize"
          @rotate-start="startRotate"
          @remove="remove"
        ></placed-decoration>
      </div>
    `,
  };

  const DiaryCanvas = {
    components: { "decoration-layer": DecorationLayer },
    props: ["selectedView", "starLabel", "isEmpty", "placedItems", "selectedDecorationId"],
    emits: ["edit-record", "select-decoration", "clear-decoration", "remove-decoration"],
    template: `
      <article class="scrapbook blank-scrapbook" @click.self="$emit('clear-decoration')">
        <div class="page left-page" @click="$emit('clear-decoration')">
          <button
            class="record-title-edit"
            type="button"
            title="기록 정보 수정"
            @click.stop="$emit('edit-record')"
          >
            <small>{{ selectedView.date }}</small>
            <strong>{{ selectedView.title }}</strong>
            <span class="stars">{{ starLabel }}</span>
          </button>
          <div v-if="isEmpty" class="blank-guide">
            <strong>빈 다이어리</strong>
            <span>오른쪽 도구에서 이미지, 메모, 스티커를 붙여 자유롭게 꾸며보세요.</span>
          </div>
        </div>
        <div class="binder" aria-hidden="true"><span v-for="ring in 7" :key="ring"></span></div>
        <div class="page right-page" @click="$emit('clear-decoration')">
          <div v-if="isEmpty" class="blank-guide right">
            <strong>꾸미기 영역</strong>
            <span>텍스트 메모는 입력, 이동, 삭제, 크기 조절이 가능합니다.</span>
          </div>
        </div>

        <decoration-layer
          :items="placedItems"
          :selected-id="selectedDecorationId"
          @select="$emit('select-decoration', $event)"
          @clear="$emit('clear-decoration')"
          @remove="$emit('remove-decoration', $event)"
        ></decoration-layer>
      </article>
    `,
  };

  const CanvasToolbar = {
    props: ["tools"],
    emits: ["run-tool"],
    template: `
      <div class="canvas-tools">
        <button v-for="tool in tools" :key="tool.label" type="button" @click="$emit('run-tool', tool)">
          {{ tool.icon }} {{ tool.label }}
        </button>
        <span></span>
        <button type="button">−</button>
        <b>100%</b>
        <button type="button">＋</button>
      </div>
    `,
  };

  const StickerShop = {
    props: ["categories", "activeCategory", "decorations"],
    emits: ["change-category", "add-decoration"],
    template: `
      <panel-card title="스티커샵">
        <template #action>클릭해서 붙이기</template>
        <div class="subtabs">
          <button
            v-for="category in categories"
            :key="category"
            :class="{ active: activeCategory === category }"
            type="button"
            @click="$emit('change-category', category)"
          >
            {{ category }}
          </button>
        </div>
        <div class="sticker-grid">
          <button
            v-for="sticker in decorations"
            :key="sticker.id || sticker.icon"
            :class="sticker.tone"
            type="button"
            @click="$emit('add-decoration', sticker)"
          >
            <img v-if="sticker.imageSrc" :src="sticker.imageSrc" :alt="sticker.label || '스티커'" />
            <span v-else>{{ sticker.icon }}</span>
          </button>
        </div>
        <p class="shop-help">스티커, 프레임, 말풍선, 아이콘을 붙인 뒤 드래그로 옮길 수 있어요.</p>
      </panel-card>
    `,
  };

  const ImageUploadPanel = {
    emits: ["image-upload"],
    template: `
      <panel-card title="이미지 첨부">
        <template #action>내 이미지 붙이기</template>
        <label class="upload-drop">
          <input type="file" accept="image/*" @change="$emit('image-upload', $event)" />
          <span>＋</span>
          <b>이미지 선택</b>
          <small>선택한 이미지는 다이어리 위에 붙고 드래그로 옮길 수 있어요.</small>
        </label>
      </panel-card>
    `,
  };

  const KeywordPanel = {
    props: ["tags"],
    template: `
      <panel-card title="추천 키워드">
        <template #action>AI 추천</template>
        <div class="keyword-list">
          <button v-for="tag in tags" :key="tag" type="button">#{{ tag }}</button>
        </div>
      </panel-card>
    `,
  };

  const DiaryEditor = {
    components: {
      "diary-canvas": DiaryCanvas,
      "canvas-toolbar": CanvasToolbar,
      "sticker-shop": StickerShop,
      "image-upload-panel": ImageUploadPanel,
      "keyword-panel": KeywordPanel,
    },
    props: [
      "selectedView",
      "starLabel",
      "isCanvasEmpty",
      "placedItems",
      "selectedDecorationId",
      "canvasTools",
      "stickerCategories",
      "activeStickerCategory",
      "visibleDecorations",
      "aiTags",
      "canUndo",
    ],
    emits: [
      "add-memo",
      "undo",
      "save-card",
      "open-share-modal",
      "select-decoration",
      "clear-decoration",
      "remove-decoration",
      "run-tool",
      "change-sticker-category",
      "add-decoration",
      "image-upload",
      "edit-record",
    ],
    template: `
      <div class="content-grid">
        <section class="editor-zone">
          <div class="section-head">
            <div>
              <h2>내 기록</h2>
            </div>
            <div class="toolset">
              <button
                class="tool-action"
                type="button"
                :disabled="!canUndo"
                @click="$emit('undo')"
                title="이전 작업으로 되돌리기"
              ><span>↶</span><b>실행 취소</b></button>
              <button class="tool-action memo-action" type="button" @click="$emit('add-memo')" title="움직일 수 있는 메모 추가"><span>T</span><b>메모 추가</b></button>
              <button
                class="primary small tool-action save-action"
                type="button"
                @pointerdown.stop.prevent="$emit('save-card')"
                @click.stop.prevent="$emit('save-card')"
                @keydown.enter.prevent="$emit('save-card')"
                @keydown.space.prevent="$emit('save-card')"
                title="현재 다이어리 카드 저장"
              ><span class="save-icon">▣</span><b>저장</b></button>
              <button
                class="share-button editor-share-button"
                type="button"
                @click="$emit('open-share-modal')"
                title="공유 카드 만들기"
              ><span>↗</span><b>공유하기</b></button>
            </div>
          </div>

          <diary-canvas
            :selected-view="selectedView"
            :star-label="starLabel"
            :is-empty="isCanvasEmpty"
            :placed-items="placedItems"
            :selected-decoration-id="selectedDecorationId"
            @select-decoration="$emit('select-decoration', $event)"
            @clear-decoration="$emit('clear-decoration')"
            @remove-decoration="$emit('remove-decoration', $event)"
            @edit-record="$emit('edit-record')"
          ></diary-canvas>

          <canvas-toolbar :tools="canvasTools" @run-tool="$emit('run-tool', $event)"></canvas-toolbar>
        </section>

        <aside class="right-rail">
          <sticker-shop
            :categories="stickerCategories"
            :active-category="activeStickerCategory"
            :decorations="visibleDecorations"
            @change-category="$emit('change-sticker-category', $event)"
            @add-decoration="$emit('add-decoration', $event)"
          ></sticker-shop>
          <image-upload-panel @image-upload="$emit('image-upload', $event)"></image-upload-panel>
          <keyword-panel :tags="aiTags"></keyword-panel>
        </aside>
      </div>
    `,
  };

  const defaultAnalysis = {
    summary: "재난과 판타지, 성장의 요소가 자연스럽게 어우러진 작품. 잔잔한 음악과 장면들이 오래 남아요.",
    phrase: "오래 기억에 남을 감정이에요.",
    tags: ["스즈메의문단속", "너의이름은", "귀멸의칼날", "하이큐", "코노스바", "지브리", "최애장면", "감정선"],
    preference: "감정선과 관계성 서사를 오래 곱씹는 아카이빙 취향",
  };

  createApp({
    delimiters: ["[[", "]]"],
    components: {
      "panel-card": PanelCard,
      "diary-editor": DiaryEditor,
    },
    data() {
      return {
        screen: "login",
        routePage: initialRoute.page || "home",
        routeObjectId: initialRoute.objectId || null,
        query: "",
        activePage: "홈",
        activeTab: "전체",
        activeStickerCategory: "전체",
        isShareModalOpen: false,
        shareCard: {
          template: "memo-collage",
          theme: "#f6dde9",
          accent: "#7f5bb8",
          title: "",
          date: "",
          rating: "",
          tags: [],
          memo: "",
          tapes: [],
          collageItems: [],
        },
        isLoading: false,
        isAuthSubmitting: false,
        isLoggingOut: false,
        csrfToken: "",
        authError: "",
        isRecordModalOpen: false,
        selectedDecorationId: null,
        mainImageSrc: "",
        currentRecord: {
          title: "새 감상 기록",
          date: "2026.05.18",
          rating: 0,
          memo: "",
          tags: [],
        },
        recordForm: {
          title: "",
          date: "2026-05-18",
          rating: 0,
        },
        recordModalMode: "create",
        savedCards: [],
        currentUserEmail: "",
        editingSavedCardId: null,
        undoHistory: [],
        layerZIndex: 0,
        lastSaveAt: 0,
        toastMessage: "",
        login: {
          email: "",
          nickname: "",
          password: "",
          remember: false,
        },
        nav: ["홈", "내 앨범", "기록 작성", "리뷰", "마이페이지"],
        tabs: ["전체", "시청 중", "완료", "보류", "찜 목록"],
        recentTags: ["감성애니", "인생작", "성장물", "힐링", "명작", "OST맛집"],
        canvasTools: [
          { icon: "▦", label: "배경" },
          { icon: "☺", label: "스티커" },
          { icon: "T", label: "메모", action: "memo" },
          { icon: "▧", label: "이미지" },
          { icon: "⌘", label: "테이프" },
          { icon: "✎", label: "손글씨" },
        ],
        stickerCategories: ["전체", "스티커", "프레임", "말풍선", "아이콘", "배경"],
        decorations: [
          { id: "guineapig", icon: "guineapig", label: "기니피그", tone: "sticker-image guineapig-sticker", category: "스티커", imageSrc: "/static/images/guineapig.png?v=1" },
          { icon: "🎬", tone: "ink", category: "스티커" },
          { icon: "📔", tone: "purple", category: "스티커" },
          { icon: "✧", tone: "line", category: "스티커" },
          { icon: "☁", tone: "soft", category: "스티커" },
          { icon: "♡", tone: "pink", category: "스티커" },
          { icon: "✿", tone: "purple", category: "스티커" },
          { icon: "🎀", tone: "pink", category: "스티커" },
          { icon: "🐾", tone: "soft", category: "스티커" },
          { icon: "⭐", tone: "line", category: "스티커" },
          { icon: "💜", tone: "purple", category: "스티커" },
          { icon: "📎", tone: "ink", category: "스티커" },
          { icon: "🐱", tone: "soft", category: "스티커" },
          { icon: "🍰", tone: "pink", category: "스티커" },
          { icon: "🎧", tone: "ink", category: "스티커" },
          { icon: "tape", tone: "masking-tape tape-lavender", category: "스티커" },
          { icon: "tape", tone: "masking-tape tape-rose", category: "스티커" },
          { icon: "tape", tone: "masking-tape tape-mint", category: "스티커" },
          { icon: "tape", tone: "masking-tape tape-grid", category: "스티커" },
          { icon: "▶", tone: "purple", category: "아이콘" },
          { icon: "＋", tone: "line", category: "아이콘" },
          { icon: "↗", tone: "ink", category: "아이콘" },
          { icon: "✓", tone: "soft", category: "아이콘" },
          { icon: "!", tone: "pink", category: "아이콘" },
          { icon: "#", tone: "purple", category: "아이콘" },
          { icon: "Zzz", tone: "line bubble", category: "말풍선" },
          { icon: "좋았다", tone: "pink bubble", category: "말풍선" },
          { icon: "최애 장면", tone: "purple bubble", category: "말풍선" },
          { icon: "여운...", tone: "soft bubble", category: "말풍선" },
          { icon: "다시 볼래", tone: "line bubble", category: "말풍선" },
          { icon: "□", tone: "line frame", category: "프레임" },
          { icon: "▱", tone: "pink frame", category: "프레임" },
          { icon: "◇", tone: "purple frame", category: "프레임" },
          { icon: "POLA", tone: "ink frame", category: "프레임" },
          { icon: "FILM", tone: "purple frame", category: "프레임" },
          { icon: "grid", tone: "soft bg", category: "배경" },
          { icon: "dot", tone: "pink bg", category: "배경" },
          { icon: "tape", tone: "purple bg", category: "배경" },
          { icon: "memo", tone: "line bg", category: "배경" },
        ],
        placedItems: [],
        colors: ["#cdb6ec", "#8d63d0", "#bdd5ed", "#bde5e1", "#dfdfc8", "#ffd9b4", "#dedbe3"],
        ai: defaultAnalysis,
        draft: {
          title: "장송의 프리렌",
          memo: "잔잔한데 여운이 오래 남았다.",
          mood: "여운",
          tags: "여운,관계성서사,힐링",
        },
        records: [],
        selectedIndex: 0,
        tabViews: {
          전체: {
            title: "스즈메의 문단속",
            date: "2024.05.12",
            memo: "매번 상상만 했던 곳을 떠나는 용기를 얻게 된 것 같은 기분이었다.",
            tags: ["여행", "성장", "감동", "OST"],
            description: "모든 감상 기록을 한 권의 다이어리처럼 모아 보는 공간",
          },
          "시청 중": {
            title: "장송의 프리렌",
            date: "2024.05.18",
            memo: "천천히 쌓이는 관계와 여행의 공기가 좋아서 다음 회차가 기다려진다.",
            tags: ["시청중", "여운", "관계성", "힐링"],
            description: "아직 보는 중인 작품의 감정과 다음 회차 메모를 정리",
          },
          완료: {
            title: "스즈메의 문단속",
            date: "2024.05.12",
            memo: "마지막 장면까지 보고 나니 문을 닫는다는 말이 오래 남았다.",
            tags: ["완료", "감동", "명대사", "여운"],
            description: "완주한 작품의 별점, 명장면, 감상문을 보관",
          },
          보류: {
            title: "다시 볼 작품 메모",
            date: "2024.05.03",
            memo: "지금은 잠깐 멈췄지만 분위기가 좋아서 여유 있을 때 다시 보고 싶다.",
            tags: ["보류", "재시청", "메모", "취향"],
            description: "잠시 멈춘 작품을 잊지 않도록 이유와 분위기를 기록",
          },
          "찜 목록": {
            title: "보고 싶은 애니 리스트",
            date: "2024.05.01",
            memo: "추천받은 작품과 포스터가 예뻤던 작품을 먼저 모아둔다.",
            tags: ["찜", "추천", "기대작", "다음작품"],
            description: "나중에 볼 작품을 다꾸 위시리스트처럼 모아두는 공간",
          },
        },
      };
    },
    computed: {
      selected() {
        return this.records[this.selectedIndex] || {
          date: "",
          title: "기록을 불러오는 중",
          memo: "",
          rating: 0,
          tags: [],
          count: 0,
          cover: "#f1eafd",
        };
      },
      filteredRecords() {
        const needle = this.query.trim().toLowerCase();
        if (!needle) return this.records;
        return this.records.filter((record) => {
          const haystack = [record.title, record.memo, ...record.tags].join(" ").toLowerCase();
          return haystack.includes(needle);
        });
      },
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
      shareTemplateLabel() {
        const labels = {
          "image-polaroid": "이미지 폴라로이드",
          "memo-collage": "메모 콜라주",
        };
        return labels[this.shareCard.template] || "공유 카드";
      },
      tabDescription() {
        return this.selectedView.description || "선택한 기록 모음을 다이어리 카드로 미리 봅니다.";
      },
      pageDescription() {
        const descriptions = {
          홈: "최근 기록과 이어서 작성할 다꾸를 빠르게 확인하는 대시보드입니다.",
          "내 앨범": "완성한 다이어리 기록을 앨범 단위로 모아보는 공간입니다.",
          "기록 작성": "새 기록을 만들고 스티커, 이미지, 메모로 자유롭게 꾸밉니다.",
          보관함: "저장했지만 아직 공유하지 않은 카드와 임시 기록을 보관합니다.",
          스티커샵: "다꾸에 사용할 스티커, 프레임, 말풍선 세트를 관리합니다.",
          탐색: "작품명, 캐릭터, 태그로 기록과 애니메이션을 찾아봅니다.",
          설정: "계정, 공개 범위, 공유 이미지 설정을 조정합니다.",
        };
        return descriptions[this.activePage] || "덕꾸 기록을 관리합니다.";
      },
      detailCards() {
        const cards = {
          홈: [
            { title: "최근 기록", body: "방금 저장했거나 최근 편집한 다꾸 기록을 빠르게 다시 엽니다.", action: "기록 작성" },
            { title: "내 앨범 바로가기", body: "완성된 기록을 앨범 단위로 모아보고 이어서 확인합니다.", action: "내 앨범" },
            { title: "기록 작성", body: "새로운 감상 기록을 만들고 꾸미기 화면으로 이동합니다.", action: "기록 작성" },
          ],
          "내 앨범": [
            { title: "완성 카드", body: "저장한 다꾸 카드를 앨범별로 정리합니다." },
            { title: "최근 기록", body: "최근 편집한 기록을 빠르게 다시 열 수 있습니다." },
            { title: "하이라이트", body: "여러 기록을 모아 공유용 하이라이트로 만들 수 있습니다." },
          ],
          "기록 작성": [
            { title: "꾸미기 캔버스", body: "이미지, 메모, 스티커를 배치해 감상 기록을 만듭니다." },
            { title: "실행 취소", body: "스티커와 이미지를 추가하기 전 상태로 한 단계씩 되돌립니다." },
            { title: "저장과 공유", body: "완성한 기록은 내 앨범에 저장하고 공유용 카드로 확인합니다." },
          ],
          보관함: [
            { title: "임시 저장", body: "편집 중인 기록을 안전하게 모아둡니다." },
            { title: "비공개 카드", body: "공개하지 않은 개인 감상 카드를 보관합니다." },
          ],
          스티커샵: [
            { title: "스티커 세트", body: "자주 쓰는 스티커와 프레임을 모아둡니다." },
            { title: "내 이미지", body: "직접 업로드한 이미지 장식을 관리합니다." },
            { title: "추천 장식", body: "감상 분위기에 맞는 장식을 추천받을 수 있습니다." },
          ],
          탐색: [
            { title: "작품 검색", body: "나중에 AniList 자동완성과 연결할 검색 영역입니다." },
            { title: "태그 탐색", body: "여운, 청량, 피폐 같은 감정 태그로 기록을 찾습니다." },
          ],
          설정: [
            { title: "공개 범위", body: "기록별 공개/비공개 기본값을 설정합니다." },
            { title: "공유 이미지", body: "스토리, 피드, 링크 카드 출력 옵션을 조정합니다." },
          ],
        };
        return cards[this.activePage] || [];
      },
      visibleDecorations() {
        if (this.activeStickerCategory === "전체") return this.decorations;
        return this.decorations.filter((item) => item.category === this.activeStickerCategory);
      },
    },
    mounted() {
      this.applyRoute(initialRoute.page || "home", initialRoute.objectId || null, false);
      window.addEventListener("popstate", this.handlePopState);
      this.handleSaveControl = (event) => {
        const target = event.target.closest ? event.target : event.target.parentElement;
        if (target?.closest(".save-action")) {
          event.preventDefault();
          this.saveCard();
        }
      };
      document.addEventListener("click", this.handleSaveControl, true);
      document.addEventListener("pointerdown", this.handleSaveControl, true);
      this.loadSavedCards();
      this.loadRecords();
    },
    beforeUnmount() {
      window.removeEventListener("popstate", this.handlePopState);
      document.removeEventListener("click", this.handleSaveControl, true);
      document.removeEventListener("pointerdown", this.handleSaveControl, true);
    },
    methods: {
      routeForPage(page, objectId = null) {
        const routes = {
          홈: "/deokkku/home/",
          "내 앨범": "/deokkku/my_album/",
          "기록 작성": `/diaries/${objectId || 0}/`,
          리뷰: "/reviews/",
          마이페이지: "/mypage/",
          "공유 페이지": `/share/${objectId || 0}/`,
        };
        return routes[page] || "/";
      },
      routeNameForPage(page) {
        return {
          홈: "home",
          "내 앨범": "diary-list",
          "기록 작성": "diary-detail",
          리뷰: "review-list",
          마이페이지: "mypage",
          "공유 페이지": "share",
        }[page] || "home";
      },
      pageForRoute(routeName) {
        return {
          home: "홈",
          "diary-list": "내 앨범",
          "diary-detail": "기록 작성",
          "review-list": "리뷰",
          "review-detail": "리뷰",
          mypage: "마이페이지",
          share: "공유 페이지",
        }[routeName] || "홈";
      },
      navigateRoute(routeName, objectId = null) {
        this.applyRoute(routeName, objectId, true);
      },
      navigatePage(page) {
        this.applyPage(page, true);
      },
      applyPage(page, push = true, objectId = null) {
        this.screen = "dashboard";
        this.activePage = page;
        const routeName = this.routeNameForPage(page);
        this.routePage = routeName;
        this.routeObjectId = objectId;
        if (push) {
          window.history.pushState({ page: routeName, objectId }, "", this.routeForPage(page, objectId));
        }
      },
      applyRoute(routeName, objectId = null, push = true) {
        this.routePage = routeName;
        this.routeObjectId = objectId;

        if (routeName === "login" || routeName === "signup") {
          this.screen = routeName;
          if (push) {
            const authPath = routeName === "login" ? "/deokkku/login/" : "/deokkku/join/";
            window.history.pushState({ page: routeName, objectId }, "", authPath);
          }
          return;
        }

        const page = this.pageForRoute(routeName);
        this.applyPage(page, push, objectId);
      },
      handlePopState(event) {
        const state = event.state || {};
        this.applyRoute(state.page || this.routeNameFromPath(window.location.pathname), state.objectId || null, false);
      },
      routeNameFromPath(pathname) {
        if (pathname === "/deokkku/login/" || pathname === "/login/") return "login";
        if (pathname === "/deokkku/join/" || pathname === "/signup/") return "signup";
        if (pathname === "/deokkku/my_album/" || pathname === "/diaries/") return "diary-list";
        if (pathname.startsWith("/diaries/")) return "diary-detail";
        if (pathname === "/reviews/") return "review-list";
        if (pathname.startsWith("/reviews/")) return "review-detail";
        if (pathname === "/deokkku/home/" || pathname === "/deokkku/" || pathname === "/deokku/") return "home";
        if (pathname === "/mypage/") return "mypage";
        if (pathname.startsWith("/share/")) return "share";
        return "home";
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
        let response = await fetch(url, {
          credentials: "same-origin",
          headers,
          ...options,
        });
        if (!response.ok && response.status === 403 && needsCsrf) {
          headers["X-CSRFToken"] = await this.getCsrfToken(true);
          response = await fetch(url, {
            credentials: "same-origin",
            headers,
            ...options,
          });
        }
        if (!response.ok) {
          let message = `API 요청 실패: ${response.status}`;
          try {
            const errorData = await response.json();
            message = errorData.detail || Object.values(errorData).flat().join(" ") || message;
          } catch (error) {
            // Keep the status-based message when the server does not return JSON.
          }
          throw new Error(message);
        }
        return response.json();
      },
      async getCsrfToken(forceRefresh = false) {
        if (this.csrfToken && !forceRefresh) return this.csrfToken;
        const response = await fetch("/api/auth/csrf/", {
          credentials: "same-origin",
          cache: "no-store",
          headers: {
            "Content-Type": "application/json",
          },
        });
        if (!response.ok) {
          throw new Error("CSRF 토큰을 가져오지 못했습니다.");
        }
        const data = await response.json();
        this.csrfToken = data.csrfToken || "";
        return this.csrfToken;
      },
      async submitLogin() {
        this.authError = "";
        const email = this.login.email.trim();
        const password = this.login.password;

        if (!email || !password) {
          this.authError = "이메일과 비밀번호를 입력해주세요.";
          return;
        }

        this.isAuthSubmitting = true;
        try {
          const user = await this.apiFetch("/api/auth/login/", {
            method: "POST",
            body: JSON.stringify({ email, password }),
          });
          this.currentUserEmail = user.email || email;
          this.csrfToken = "";
          this.loadSavedCards();
          await this.loadRecords();
          this.navigateRoute("home");
        } catch (error) {
          this.authError = error.message || "로그인에 실패했습니다.";
        } finally {
          this.isAuthSubmitting = false;
        }
      },
      async submitSignup() {
        this.authError = "";
        const email = this.login.email.trim();
        const nickname = this.login.nickname.trim();
        const password = this.login.password;

        if (!email || !nickname || !password) {
          this.authError = "이메일, 닉네임, 비밀번호를 모두 입력해주세요.";
          return;
        }

        this.isAuthSubmitting = true;
        try {
          const user = await this.apiFetch("/api/auth/signup/", {
            method: "POST",
            body: JSON.stringify({ email, nickname, password }),
          });
          this.currentUserEmail = user.email || email;
          this.csrfToken = "";
          this.loadSavedCards();
          await this.loadRecords();
          this.selectedIndex = 0;
          this.navigateRoute("home");
        } catch (error) {
          this.authError = error.message || "회원가입에 실패했습니다.";
        } finally {
          this.isAuthSubmitting = false;
        }
      },
      async logout() {
        if (this.isLoggingOut) return;
        this.isLoggingOut = true;
        try {
          await this.apiFetch("/api/auth/logout/", {
            method: "POST",
            body: JSON.stringify({}),
          });
        } catch (error) {
          // If the session is already gone, return to login anyway.
        } finally {
          this.isLoggingOut = false;
          this.csrfToken = "";
          this.currentUserEmail = "";
          this.records = [];
          this.savedCards = [];
          this.login.password = "";
          this.navigateRoute("login");
        }
      },
      normalizeBackendRecord(record) {
        const rawDate = record.date || record.watched_date || (record.created_at || "").slice(0, 10);
        const displayDate = rawDate ? rawDate.replaceAll("-", ".") : "";
        const title = record.title || record.anime_title || record.anime?.title_ko || record.anime?.title || "새 감상 기록";
        const tags = Array.isArray(record.tags) ? record.tags : [
          record.visibility,
          record.status,
        ].filter(Boolean);

        return {
          id: record.id,
          date: displayDate,
          title,
          memo: record.memo || record.content || "",
          rating: Number(record.rating || 0),
          tags,
          count: record.count || record.like_count || 0,
          cover: record.cover || record.anime_poster || "linear-gradient(160deg, #b99be0, #ffd1e4)",
          raw: record,
        };
      },
      async loadRecords() {
        this.isLoading = true;
        try {
          const data = await this.apiFetch("/api/records/");
          const records = data.records || data.results || (Array.isArray(data) ? data : []);
          this.records = records.map(this.normalizeBackendRecord);
          this.selectedIndex = 0;
          if (this.records.length) {
            try {
              await this.analyzeFromRecord(this.records[0]);
            } catch (error) {
              this.ai = {
                ...defaultAnalysis,
                tags: [...this.records[0].tags, "명장면", "공유하기"],
              };
            }
          }
        } finally {
          this.isLoading = false;
        }
      },
      savedCardsKey() {
        const owner = this.currentUserEmail || "guest";
        return `deokkkuSavedCards:${owner}`;
      },
      loadSavedCards() {
        try {
          const storedCards = JSON.parse(localStorage.getItem(this.savedCardsKey()) || "[]");
          this.savedCards = Array.isArray(storedCards) ? storedCards : [];
        } catch (error) {
          this.savedCards = [];
        }
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
      resetUndoHistory() {
        this.undoHistory = [];
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
      persistSavedCards() {
        try {
          localStorage.setItem(this.savedCardsKey(), JSON.stringify(this.savedCards));
        } catch (error) {
          // 저장소를 사용할 수 없어도 현재 화면의 앨범 목록과 알림은 유지합니다.
        }
      },
      deleteSavedCard(cardId) {
        this.savedCards = this.savedCards.filter((card) => card.id !== cardId);
        if (this.editingSavedCardId === cardId) {
          this.editingSavedCardId = null;
        }
        this.persistSavedCards();
      },
      navIcon(item) {
        const icons = {
          홈: "⌂",
          "내 앨범": "▧",
          "기록 작성": "✎",
          리뷰: "☰",
          보관함: "▣",
          스티커샵: "✿",
          탐색: "⌕",
          마이페이지: "◌",
          설정: "⚙",
          "공유 페이지": "↗",
        };
        return icons[item] || "•";
      },
      stars(score) {
        const filled = Math.max(0, Math.min(5, Math.round(score / 2)));
        return "★".repeat(filled) + "☆".repeat(5 - filled);
      },
      async selectRecord(record) {
        this.selectedIndex = this.records.findIndex((item) => item.title === record.title);
        this.currentRecord = {
          title: record.title,
          date: record.date,
          rating: record.rating,
          memo: "",
          tags: [],
        };
        this.placedItems = [];
        this.mainImageSrc = "";
        this.selectedDecorationId = null;
        this.editingSavedCardId = null;
        this.resetUndoHistory();
        this.syncLayerZIndex();
        await this.analyzeFromRecord(record);
      },
      async openSavedCard(card) {
        const savedRecord = card.snapshot?.record || {
          title: card.title,
          date: card.date,
          rating: card.rating,
          memo: "",
          tags: [],
        };
        const matchingIndex = this.records.findIndex((item) => (
          item.title === savedRecord.title && item.date === savedRecord.date
        ));

        this.currentRecord = this.cloneForSave(savedRecord);
        this.placedItems = this.cloneForSave(card.snapshot?.placedItems || []);
        this.mainImageSrc = card.snapshot?.mainImageSrc || "";
        this.selectedDecorationId = null;
        this.editingSavedCardId = card.id;
        this.selectedIndex = matchingIndex >= 0 ? matchingIndex : this.selectedIndex;
        this.applyPage("기록 작성", true);
        this.toastMessage = "";
        this.resetUndoHistory();
        this.syncLayerZIndex();

        if (card.snapshot?.analysis) {
          this.ai = this.cloneForSave(card.snapshot.analysis);
        } else if (matchingIndex >= 0) {
          await this.analyzeFromRecord(this.records[matchingIndex]);
        }
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
          memo: "",
          tags: [],
        };
        if (this.recordModalMode !== "edit") {
          this.placedItems = [];
          this.mainImageSrc = "";
          this.selectedDecorationId = null;
          this.editingSavedCardId = null;
          this.resetUndoHistory();
          this.syncLayerZIndex();
        }
        this.applyPage("기록 작성", true);
        this.isRecordModalOpen = false;
      },
      openComposer() {
        this.draft = {
          title: "",
          memo: "",
          mood: "여운",
          tags: "",
        };
      },
      async analyze() {
        const data = await this.apiFetch("/api/analyze/", {
          method: "POST",
          body: JSON.stringify(this.draft),
        });
        this.ai = data.analysis;
      },
      async analyzeFromRecord(record) {
        const data = await this.apiFetch("/api/analyze/", {
          method: "POST",
          body: JSON.stringify({
            title: record.title,
            memo: record.memo,
            mood: record.tags[0] || "여운",
          }),
        });
        this.ai = {
          ...data.analysis,
          tags: [...record.tags, "최애장면", "앨범저장", "공유하기"],
        };
      },
      async createRecord() {
        const data = await this.apiFetch("/api/records/create/", {
          method: "POST",
          body: JSON.stringify(this.draft),
        });
        this.records.unshift(data.record);
        this.selectedIndex = 0;
        this.ai = data.analysis;
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
      handleImageUpload(event) {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
          this.pushUndoState();
          const nextId = Date.now();
          const nextItem = {
            id: nextId,
            icon: "",
            imageSrc: reader.result,
            tone: "custom-image",
            x: 31 + (this.placedItems.length * 7) % 38,
            y: 24 + (this.placedItems.length * 9) % 44,
            rotate: -6 + (this.placedItems.length * 5) % 14,
            scale: 1,
            zIndex: this.nextLayerZIndex(),
          };
          this.placedItems.push(nextItem);
          this.selectedDecorationId = nextId;
          event.target.value = "";
        };
        reader.readAsDataURL(file);
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
      handleMainImageUpload(event) {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
          this.pushUndoState();
          this.mainImageSrc = reader.result;
          event.target.value = "";
        };
        reader.readAsDataURL(file);
      },
      removeSticker(id) {
        this.placedItems = this.placedItems.filter((sticker) => sticker.id !== id);
        if (this.selectedDecorationId === id) {
          this.selectedDecorationId = null;
        }
      },
      selectDecoration(id) {
        this.selectedDecorationId = id;
        this.bringDecorationToFront(id);
      },
      clearDecorationSelection() {
        this.selectedDecorationId = null;
      },
      runCanvasTool(tool) {
        if (tool.action === "memo") {
          this.addTextMemo();
        }
      },
      clearStickers() {
        this.placedItems = [];
        this.selectedDecorationId = null;
      },
      pickRandom(items) {
        return items[Math.floor(Math.random() * items.length)];
      },
      clampShareValue(value, min, max) {
        return Math.max(min, Math.min(max, value));
      },
      formatShareDate(date) {
        if (!date) return new Date().toISOString().slice(0, 10).replaceAll("-", ".");
        return String(date).replaceAll("-", ".").replace(/\.$/, "");
      },
      truncateShareText(text, maxLength = 46) {
        const cleanText = String(text || "").replace(/\s+/g, " ").trim();
        if (cleanText.length <= maxLength) return cleanText;
        return `${cleanText.slice(0, maxLength - 1)}…`;
      },
      shareCollageStyle(item) {
        return {
          left: `${item.x}%`,
          top: `${item.y}%`,
          width: item.width ? `${item.width}px` : `${item.size}px`,
          height: item.kind === "memo" ? "auto" : `${item.size}px`,
          transform: `rotate(${item.rotate}deg)`,
          zIndex: item.zIndex,
        };
      },
      shareTapeStyle(tape) {
        return {
          left: `${tape.x}%`,
          top: `${tape.y}%`,
          width: `${tape.width}px`,
          transform: `rotate(${tape.rotate}deg)`,
        };
      },
      buildShareTapes(cardType) {
        const count = cardType === "image-polaroid" ? 2 : 3;
        return Array.from({ length: count }, (_, index) => ({
          id: `tape-${index}`,
          x: this.randomBetween(8, 72),
          y: this.randomBetween(6, 72),
          width: this.randomBetween(54, 86),
          rotate: this.randomBetween(-18, 18),
        }));
      },
      randomBetween(min, max) {
        return min + Math.random() * (max - min);
      },
      isShareDecorativeIcon(icon) {
        const value = String(icon || "").trim();
        if (!value) return false;
        if (["#", "!", "T"].includes(value)) return false;
        if ([...value].length > 2) return false;
        return !/[A-Za-z0-9ㄱ-ㅎ가-힣]/.test(value);
      },
      buildShareCollageItems(cardType, memoText) {
        const collageItems = [];
        const hasMainImage = cardType === "image-polaroid";
        const hasCanvasMemo = Boolean(String(memoText || "").trim());
        const stickerSlots = hasMainImage
          ? [
              { x: 68, y: 18 },
              { x: 12, y: 34 },
              { x: 72, y: 58 },
              { x: 18, y: 70 },
            ]
          : [
              { x: 72, y: 18 },
              { x: 12, y: 28 },
              { x: 76, y: 48 },
              { x: 16, y: 68 },
              { x: 58, y: 74 },
            ];

        if (hasMainImage) {
          collageItems.push({
            id: "main-image",
            kind: "image",
            imageSrc: this.mainImageSrc,
            x: 15,
            y: 12,
            size: 146,
            rotate: this.randomBetween(-7, -2),
            zIndex: 3,
          });
        }

        const stickerItems = this.placedItems
          .filter((item) => item.type !== "text")
          .filter((item) => item.imageSrc || this.isShareDecorativeIcon(item.icon))
          .slice(0, hasMainImage ? 4 : 5);
        const cleanMemo = this.truncateShareText(memoText, hasMainImage ? 28 : 96);

        if (hasMainImage && hasCanvasMemo) {
          collageItems.push({
            id: "share-memo",
            kind: "memo",
            text: cleanMemo,
            x: 52,
            y: 58,
            width: 94,
            size: 94,
            rotate: this.randomBetween(-9, 9),
            zIndex: 8,
          });
        }

        if (!hasMainImage && hasCanvasMemo) {
          collageItems.push({
            id: "share-main-memo",
            kind: "memo",
            text: cleanMemo,
            x: this.randomBetween(10, 14),
            y: this.randomBetween(32, 38),
            width: this.randomBetween(224, 242),
            size: 188,
            rotate: this.randomBetween(-3, 3),
            zIndex: 6,
          });
        }

        stickerItems.forEach((item, index) => {
          const isMemo = item.type === "text";
          const hasImage = Boolean(item.imageSrc);
          const icon = !isMemo && !hasImage ? item.icon : "";
          if (!hasImage && !icon) return;

          const slot = stickerSlots[index % stickerSlots.length];
          collageItems.push({
            id: item.id || `item-${index}`,
            kind: hasImage ? "sticker-image" : "sticker",
            imageSrc: hasImage ? item.imageSrc : "",
            icon,
            x: hasMainImage
              ? this.clampShareValue(16 + (Number(item.x) || 0) * 0.62 + (index % 2) * 6, 8, 76)
              : this.clampShareValue(slot.x + this.randomBetween(-4, 4), 8, 78),
            y: hasMainImage
              ? this.clampShareValue(14 + (Number(item.y) || 0) * 0.5 + (index % 3) * 4, 8, 68)
              : this.clampShareValue(slot.y + this.randomBetween(-5, 5), 8, 74),
            size: hasImage ? this.randomBetween(38, 50) : this.randomBetween(32, 44),
            rotate: this.randomBetween(-18, 18),
            zIndex: 9 + index,
          });
        });

        if (!hasMainImage) {
          const shapeCount = hasCanvasMemo ? 5 + Math.floor(Math.random() * 3) : 8 + Math.floor(Math.random() * 3);
          for (let index = 0; index < shapeCount; index += 1) {
            collageItems.push({
              id: `shape-${index}`,
              kind: "shape",
              icon: "",
              x: this.randomBetween(8, 78),
              y: this.randomBetween(10, 70),
              size: this.randomBetween(22, 42),
              rotate: this.randomBetween(-20, 20),
              zIndex: 2 + index,
            });
          }
        }

        if (!collageItems.length) {
          collageItems.push({
            id: "fallback-shape",
            kind: "shape",
            icon: "",
            x: 42,
            y: 36,
            size: 70,
            rotate: 0,
            zIndex: 4,
          });
        }

        return collageItems.slice(0, hasMainImage ? 9 : 11);
      },
      buildShareCardFromDiary() {
        const themes = [
          { theme: "#f6dde9", accent: "#7f5bb8" },
          { theme: "#dff3ee", accent: "#24796f" },
          { theme: "#ffe7c7", accent: "#b45b2b" },
          { theme: "#e6efff", accent: "#466eb5" },
          { theme: "#f1eadb", accent: "#6f5a45" },
        ];
        const nextTheme = this.pickRandom(themes);
        const memoItems = this.placedItems
          .filter((item) => item.type === "text" && item.text)
          .map((item) => item.text);
        const canvasMemoText = memoItems[0] || "";
        const recordMemoText = canvasMemoText || this.currentRecord.memo || "";
        const tags = this.currentRecord.tags?.length
          ? this.currentRecord.tags.map((tag) => `#${String(tag).replace(/^#/, "")}`).join(" ")
          : "#감상 #다이어리 #덕꾸";
        const tagList = tags.split(/\s+/).filter(Boolean).slice(0, 4);
        const cardType = this.mainImageSrc ? "image-polaroid" : "memo-collage";

        this.shareCard = {
          template: cardType,
          theme: nextTheme.theme,
          accent: nextTheme.accent,
          title: this.currentRecord.title || "제목 없는 기록",
          date: this.formatShareDate(this.currentRecord.date),
          rating: `${this.currentRecord.rating || 0} / 10`,
          tags: tagList,
          memo: this.truncateShareText(recordMemoText, 42),
          tapes: this.buildShareTapes(cardType),
          collageItems: this.buildShareCollageItems(cardType, canvasMemoText),
        };
      },
      randomizeShareCard() {
        this.buildShareCardFromDiary();
      },
      openShareModal() {
        this.buildShareCardFromDiary();
        this.isShareModalOpen = true;
      },
      closeShareModal() {
        this.isShareModalOpen = false;
      },
      async downloadShareCard() {
        const target = this.$refs.shareCard;
        if (!target || !window.html2canvas) {
          console.log("share card image save requested", this.shareCard);
          return;
        }
        try {
          const canvas = await window.html2canvas(target, {
            backgroundColor: null,
            scale: 2,
            useCORS: true,
          });
          const link = document.createElement("a");
          link.download = "deokkku-share-card.png";
          link.href = canvas.toDataURL("image/png");
          link.click();
        } catch (error) {
          console.log("share card image save failed", error);
        }
      },
      saveCard() {
        const now = Date.now();
        if (now - this.lastSaveAt < 350) return;
        this.lastSaveAt = now;
        const existingCardId = this.editingSavedCardId;
        const savedCard = {
          id: existingCardId || now,
          title: this.currentRecord.title || "제목 없는 기록",
          date: this.currentRecord.date,
          rating: this.currentRecord.rating,
          itemCount: this.placedItems.length + (this.mainImageSrc ? 1 : 0),
          memoCount: this.placedItems.filter((item) => item.type === "text").length,
          stickerCount: this.placedItems.filter((item) => item.type !== "text").length,
          savedAt: new Date().toISOString(),
          snapshot: {
            record: this.cloneForSave(this.currentRecord),
            placedItems: this.cloneForSave(this.placedItems),
            mainImageSrc: this.mainImageSrc,
            analysis: this.cloneForSave(this.ai),
          },
        };
        if (existingCardId) {
          const existingIndex = this.savedCards.findIndex((card) => card.id === existingCardId);
          if (existingIndex >= 0) {
            this.savedCards.splice(existingIndex, 1, savedCard);
          } else {
            this.savedCards.unshift(savedCard);
          }
        } else {
          this.savedCards.unshift(savedCard);
          this.editingSavedCardId = savedCard.id;
        }
        this.toastMessage = "저장되었습니다";
        this.persistSavedCards();
      },
    },
  }).mount("#app");
});

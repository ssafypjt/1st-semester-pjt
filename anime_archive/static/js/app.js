window.addEventListener("load", () => {
  const { createApp } = Vue;

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
    emits: ["select-decoration", "clear-decoration", "remove-decoration"],
    template: `
      <article class="scrapbook blank-scrapbook" @click.self="$emit('clear-decoration')">
        <div class="page left-page" @click="$emit('clear-decoration')">
          <small>{{ selectedView.date }}</small>
          <h3>{{ selectedView.title }}</h3>
          <div class="stars">{{ starLabel }}</div>
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
            :key="sticker.icon"
            :class="sticker.tone"
            type="button"
            @click="$emit('add-decoration', sticker)"
          >
            {{ sticker.icon }}
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
    ],
    emits: [
      "add-memo",
      "save-card",
      "select-decoration",
      "clear-decoration",
      "remove-decoration",
      "run-tool",
      "change-sticker-category",
      "add-decoration",
      "image-upload",
    ],
    template: `
      <div class="content-grid">
        <section class="editor-zone">
          <div class="section-head">
            <div>
              <h2>내 기록</h2>
            </div>
            <div class="toolset">
              <button class="tool-action" type="button" title="이전 작업으로 되돌리기"><span>↶</span><b>실행 취소</b></button>
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
        query: "",
        activePage: "홈",
        activeTab: "전체",
        activeStickerCategory: "전체",
        shareMode: "story",
        isLoading: false,
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
        savedCards: [],
        lastSaveAt: 0,
        toastMessage: "",
        login: {
          email: "",
          password: "",
          remember: false,
        },
        nav: ["홈", "내 앨범", "보관함", "스티커샵", "탐색", "설정"],
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
        shareModes: [
          { id: "story", label: "스토리 9:16" },
          { id: "feed", label: "피드 1:1" },
          { id: "link", label: "링크 카드" },
          { id: "image", label: "이미지 저장" },
        ],
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
      tabDescription() {
        return this.selectedView.description || "선택한 기록 모음을 다이어리 카드로 미리 봅니다.";
      },
      pageDescription() {
        const descriptions = {
          "내 앨범": "완성한 다이어리 기록을 앨범 단위로 모아보는 공간입니다.",
          보관함: "저장했지만 아직 공유하지 않은 카드와 임시 기록을 보관합니다.",
          스티커샵: "다꾸에 사용할 스티커, 프레임, 말풍선 세트를 관리합니다.",
          탐색: "작품명, 캐릭터, 태그로 기록과 애니메이션을 찾아봅니다.",
          설정: "계정, 공개 범위, 공유 이미지 설정을 조정합니다.",
        };
        return descriptions[this.activePage] || "덕꾸 기록을 관리합니다.";
      },
      detailCards() {
        const cards = {
          "내 앨범": [
            { title: "완성 카드", body: "저장한 다꾸 카드를 앨범별로 정리합니다." },
            { title: "최근 기록", body: "최근 편집한 기록을 빠르게 다시 열 수 있습니다." },
            { title: "하이라이트", body: "여러 기록을 모아 공유용 하이라이트로 만들 수 있습니다." },
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
      document.removeEventListener("click", this.handleSaveControl, true);
      document.removeEventListener("pointerdown", this.handleSaveControl, true);
    },
    methods: {
      async apiFetch(url, options = {}) {
        const response = await fetch(url, {
          headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
          },
          ...options,
        });
        if (!response.ok) {
          throw new Error(`API 요청 실패: ${response.status}`);
        }
        return response.json();
      },
      async loadRecords() {
        this.isLoading = true;
        try {
          const data = await this.apiFetch("/api/records/");
          this.records = data.records;
          this.selectedIndex = 0;
          if (this.records.length) {
            await this.analyzeFromRecord(this.records[0]);
          }
        } finally {
          this.isLoading = false;
        }
      },
      loadSavedCards() {
        try {
          const storedCards = JSON.parse(localStorage.getItem("deokkkuSavedCards") || "[]");
          this.savedCards = Array.isArray(storedCards) ? storedCards : [];
        } catch (error) {
          this.savedCards = [];
        }
      },
      persistSavedCards() {
        try {
          localStorage.setItem("deokkkuSavedCards", JSON.stringify(this.savedCards));
        } catch (error) {
          // 저장소를 사용할 수 없어도 현재 화면의 앨범 목록과 알림은 유지합니다.
        }
      },
      navIcon(item) {
        return {
          홈: "⌂",
          "내 앨범": "▧",
          보관함: "▣",
          스티커샵: "✿",
          탐색: "⌕",
          설정: "⚙",
        }[item];
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
        await this.analyzeFromRecord(record);
      },
      openRecordModal() {
        this.recordForm = {
          title: "",
          date: new Date().toISOString().slice(0, 10),
          rating: 0,
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
      createBlankRecord() {
        this.currentRecord = {
          title: this.recordForm.title || "제목 없는 기록",
          date: this.formatDisplayDate(this.recordForm.date),
          rating: this.recordForm.rating,
          memo: "",
          tags: [],
        };
        this.placedItems = [];
        this.mainImageSrc = "";
        this.selectedDecorationId = null;
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
        const nextId = Date.now();
        const nextItem = {
          id: nextId,
          icon: sticker.icon,
          tone: sticker.tone,
          x: 24 + (this.placedItems.length * 11) % 52,
          y: 20 + (this.placedItems.length * 17) % 56,
          rotate: -14 + (this.placedItems.length * 9) % 28,
          scale: sticker.icon.length > 1 ? 0.86 : 1.08,
        };
        this.placedItems.push(nextItem);
        this.selectedDecorationId = nextId;
      },
      handleImageUpload(event) {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
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
          };
          this.placedItems.push(nextItem);
          this.selectedDecorationId = nextId;
          event.target.value = "";
        };
        reader.readAsDataURL(file);
      },
      addTextMemo() {
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
        });
        this.selectedDecorationId = nextId;
      },
      handleMainImageUpload(event) {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
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
      saveCard() {
        const now = Date.now();
        if (now - this.lastSaveAt < 350) return;
        this.lastSaveAt = now;
        const savedCard = {
          id: now,
          title: this.currentRecord.title || "제목 없는 기록",
          date: this.currentRecord.date,
          rating: this.currentRecord.rating,
          itemCount: this.placedItems.length + (this.mainImageSrc ? 1 : 0),
          memoCount: this.placedItems.filter((item) => item.type === "text").length,
          stickerCount: this.placedItems.filter((item) => item.type !== "text").length,
          savedAt: new Date().toISOString(),
        };
        this.savedCards.unshift(savedCard);
        this.toastMessage = "저장되었습니다";
        this.persistSavedCards();
      },
    },
  }).mount("#app");
});

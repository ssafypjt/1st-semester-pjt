window.addEventListener("load", () => {
  const { createApp } = Vue;

  const defaultAnalysis = {
    summary: "재난과 판타지, 성장의 요소가 자연스럽게 어우러진 작품. 잔잔한 음악과 장면들이 오래 남아요.",
    phrase: "오래 기억에 남을 감정이에요.",
    tags: ["스즈메의문단속", "너의이름은", "귀멸의칼날", "하이큐", "코노스바", "지브리", "최애장면", "감정선"],
    preference: "감정선과 관계성 서사를 오래 곱씹는 아카이빙 취향",
  };

  createApp({
    delimiters: ["[[", "]]"],
    components: {
      "panel-card": {
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
      },
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
        draggingSticker: null,
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
      this.loadRecords();
      window.addEventListener("pointermove", this.dragSticker);
      window.addEventListener("pointerup", this.stopStickerDrag);
    },
    beforeUnmount() {
      window.removeEventListener("pointermove", this.dragSticker);
      window.removeEventListener("pointerup", this.stopStickerDrag);
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
        this.placedItems.push({
          id: nextId,
          icon: sticker.icon,
          tone: sticker.tone,
          x: 24 + (this.placedItems.length * 11) % 52,
          y: 20 + (this.placedItems.length * 17) % 56,
          rotate: -14 + (this.placedItems.length * 9) % 28,
          scale: sticker.icon.length > 1 ? 0.86 : 1.08,
        });
      },
      handleImageUpload(event) {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
          const nextId = Date.now();
          this.placedItems.push({
            id: nextId,
            icon: "",
            imageSrc: reader.result,
            tone: "custom-image",
            x: 31 + (this.placedItems.length * 7) % 38,
            y: 24 + (this.placedItems.length * 9) % 44,
            rotate: -6 + (this.placedItems.length * 5) % 14,
            scale: 1,
          });
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
          width: 190,
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
      startStickerDrag(event, sticker) {
        event.preventDefault();
        const rect = this.$refs.scrapbook.getBoundingClientRect();
        this.draggingSticker = {
          sticker,
          rect,
          offsetX: event.clientX - (rect.left + (sticker.x / 100) * rect.width),
          offsetY: event.clientY - (rect.top + (sticker.y / 100) * rect.height),
        };
      },
      dragSticker(event) {
        if (!this.draggingSticker) return;
        const { sticker, rect, offsetX, offsetY } = this.draggingSticker;
        const nextX = ((event.clientX - offsetX - rect.left) / rect.width) * 100;
        const nextY = ((event.clientY - offsetY - rect.top) / rect.height) * 100;
        sticker.x = Math.max(2, Math.min(94, nextX));
        sticker.y = Math.max(3, Math.min(90, nextY));
      },
      stopStickerDrag() {
        this.draggingSticker = null;
      },
      removeSticker(id) {
        this.placedItems = this.placedItems.filter((sticker) => sticker.id !== id);
        if (this.selectedDecorationId === id) {
          this.selectedDecorationId = null;
        }
      },
      selectDecoration(id) {
        this.selectedDecorationId = this.selectedDecorationId === id ? null : id;
      },
      clearStickers() {
        this.placedItems = [];
        this.selectedDecorationId = null;
      },
      saveCard() {
        const savedCard = {
          id: Date.now(),
          title: this.currentRecord.title || "제목 없는 기록",
          date: this.currentRecord.date,
          rating: this.currentRecord.rating,
          itemCount: this.placedItems.length + (this.mainImageSrc ? 1 : 0),
        };
        this.savedCards.unshift(savedCard);
        this.toastMessage = "내 앨범에 저장되었습니다.";
        window.setTimeout(() => {
          this.toastMessage = "";
        }, 1800);
      },
    },
  }).mount("#app");
});

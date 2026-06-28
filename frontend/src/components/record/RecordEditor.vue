<template>
  <div class="content-grid">
    <section class="editor-zone">
      <div class="section-head">
        <div>
          <input class="record-title-input" type="text" :value="recordTitle"
            @input="$emit('update:recordTitle', $event.target.value)"
            placeholder="기록 제목을 입력하세요" maxlength="100" />
        </div>
        <div class="toolset">
          <button class="tool-action close-record-action" type="button" title="기록 닫기" @click="$emit('close')">
            <span>✕</span><b>닫기</b>
          </button>
          <button class="tool-action" type="button" :disabled="!canUndo" title="이전 작업으로 되돌리기" @click="undoLastCanvasChange">
            <span>↶</span><b>실행 취소</b>
          </button>
          <button class="tool-action memo-action" type="button" title="메모 추가" @click="addTextMemo">
            <span>T</span><b>메모 추가</b>
          </button>
          <fieldset class="visibility-toggle" aria-label="공개 설정">
            <legend>공개 설정</legend>
            <label :class="{ active: recordVisibility === 'public' }">
              <input type="radio" value="public" :checked="recordVisibility === 'public'" @change="$emit('update:recordVisibility', 'public')" />
              <span><b>공개</b><small>홈 피드에 다른 사용자도 볼 수 있어요</small></span>
            </label>
            <label :class="{ active: recordVisibility === 'private' }">
              <input type="radio" value="private" :checked="recordVisibility === 'private'" @change="$emit('update:recordVisibility', 'private')" />
              <span><b>비공개</b><small>내 앨범에서만 볼 수 있어요</small></span>
            </label>
          </fieldset>
          <button class="primary small tool-action save-action" type="button" title="저장" @click="$emit('save')">
            <span class="save-icon"></span><b>저장</b>
          </button>
          <button class="tool-action share-action" type="button" title="공유하기" @click="$emit('open-share-modal')">
            <span>✂</span><b>공유하기</b>
          </button>
        </div>
      </div>

      <article class="scrapbook blank-scrapbook" :style="{ '--canvas-scale': canvasScale }" @click.self="clearDecorationSelection">
        <div class="page left-page" @click="clearDecorationSelection">
          <button class="record-title-edit" type="button" title="기록 정보 수정" @click.stop="$emit('open-record-modal', 'edit')">
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
          <div v-for="item in placedItems" :key="item.id" class="placed-decoration"
            :class="{ selected: selectedDecorationId === item.id }"
            :style="placementStyle(item)" role="button" tabindex="0" title="드래그로 이동"
            @click.stop="selectDecoration(item.id)" @pointerdown="startDrag($event, item)">
            <div class="placed-sticker" :class="item.tone" :style="stickerStyle(item)">
              <div v-if="item.type === 'bubble'" class="bubble-editor" :class="item.bubbleType" :style="bubbleEditorStyle(item)">
                <textarea v-model="item.text" :style="{ fontSize: `${item.fontSize || 14}px`, color: item.textColor || '#342a3f' }"
                  placeholder="내용을 입력하세요" @click.stop="selectDecoration(item.id)"></textarea>
              </div>
              <div v-else-if="item.type === 'text'" class="memo-editor">
                <textarea v-model="item.text" :style="{ fontSize: `${item.fontSize || 15}px` }"
                  placeholder="메모를 입력하세요" @click.stop="selectDecoration(item.id)"></textarea>
                <label v-if="selectedDecorationId === item.id" class="memo-font-control" @pointerdown.stop @click.stop>
                  <span>글자</span>
                  <input type="range" min="11" max="34" step="1" v-model.number="item.fontSize" title="글자 크기 조절" />
                </label>
              </div>
              <img v-else-if="item.imageSrc" :src="item.imageSrc" alt="첨부 이미지" />
              <span v-else>{{ item.icon }}</span>
            </div>
            <button v-if="selectedDecorationId === item.id" class="rotate-decoration" type="button" title="기울기 조절"
              @pointerdown.stop="startRotate($event, item)" @click.stop>↻</button>
            <button v-if="selectedDecorationId === item.id" class="resize-decoration" type="button" title="크기 조절"
              aria-label="크기 조절" @pointerdown.stop="startResize($event, item)" @click.stop></button>
            <button v-if="selectedDecorationId === item.id" class="delete-decoration" type="button" title="삭제"
              @pointerdown.stop @click.stop="removeSticker(item.id)">×</button>
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

      <!-- 말풍선 편집 툴바 -->
      <div v-if="selectedBubbleItem" class="bubble-toolbar">
        <div class="bt-section">
          <span class="bt-label">글꼴 크기</span>
          <div class="bt-font-size">
            <button type="button" @click="changeBubbleFontSize(-1)">−</button>
            <span>{{ selectedBubbleItem.fontSize || 14 }}px</span>
            <button type="button" @click="changeBubbleFontSize(1)">+</button>
          </div>
        </div>
        <div class="bt-section">
          <span class="bt-label">배경색</span>
          <div class="bt-colors">
            <button v-for="c in bubblePresetColors" :key="'bg-'+c" class="bt-swatch"
              :class="{ active: (selectedBubbleItem.bgColor || '#ffffff') === c }"
              :style="{ background: c }" type="button" @click="selectedBubbleItem.bgColor = c"></button>
            <label class="bt-custom-color">
              <input type="color" :value="selectedBubbleItem.bgColor || '#ffffff'" @input="selectedBubbleItem.bgColor = $event.target.value" />
              <span class="bt-swatch custom" :style="{ background: selectedBubbleItem.bgColor || '#ffffff' }">⋯</span>
            </label>
          </div>
        </div>
        <div class="bt-section">
          <span class="bt-label">테두리색</span>
          <div class="bt-colors">
            <button v-for="c in bubblePresetBorders" :key="'bd-'+c" class="bt-swatch"
              :class="{ active: (selectedBubbleItem.borderColor || '#b49cd8') === c }"
              :style="{ background: c }" type="button" @click="selectedBubbleItem.borderColor = c"></button>
            <label class="bt-custom-color">
              <input type="color" :value="selectedBubbleItem.borderColor || '#b49cd8'" @input="selectedBubbleItem.borderColor = $event.target.value" />
              <span class="bt-swatch custom" :style="{ background: selectedBubbleItem.borderColor || '#b49cd8' }">⋯</span>
            </label>
          </div>
        </div>
      </div>
    </section>

    <aside class="right-rail">
      <sticker-panel
        :sticker-categories="stickerCategories"
        :active-sticker-category="activeStickerCategory"
        :visible-decorations="visibleDecorations"
        @change-category="activeStickerCategory = $event"
        @add-decoration="addDecoration"
        @upload-sticker="$emit('sticker-upload', $event)"
      />
      <image-upload-panel @image-upload="$emit('image-upload', $event)" />
      <section class="panel-card">
        <header><h3>감상평</h3><span>메모</span></header>
        <textarea class="content-textarea" :value="currentRecord.memo"
          @input="$emit('update:currentRecord', { ...currentRecord, memo: $event.target.value })"
          placeholder="작품에 대한 감상평을 자유롭게 작성하세요..." rows="5"></textarea>
      </section>
      <section class="panel-card">
        <header><h3>추천 키워드</h3><span>AI 추천</span></header>
        <div class="keyword-list">
          <button v-for="tag in ai.tags" :key="tag" type="button">#{{ tag }}</button>
        </div>
      </section>
    </aside>
  </div>
</template>

<script>
import { clamp, cloneForSave, angleToDegrees } from "../../utils/helpers";
import { decorations } from "../../constants/stickers";
import StickerPanel from "./StickerPanel.vue";
import ImageUploadPanel from "./ImageUploadPanel.vue";

export default {
  name: "RecordEditor",
  components: { StickerPanel, ImageUploadPanel },
  props: {
    currentRecord: { type: Object, required: true },
    recordTitle: { type: String, default: "" },
    recordVisibility: { type: String, default: "public" },
    selectedView: { type: Object, default: () => ({ title: "", date: "", rating: 0 }) },
    selectedViewStars: { type: String, default: "" },
    canvasScale: { type: Number, default: 1 },
    stickerCategories: { type: Array, default: () => [] },
    canvasTools: { type: Array, default: () => [] },
    ai: { type: Object, default: () => ({ tags: [] }) },
    apiFetch: { type: Function, required: true },
  },
  emits: [
    "update:currentRecord",
    "update:recordTitle",
    "update:recordVisibility",
    "save",
    "close",
    "open-record-modal",
    "open-share-modal",
    "sticker-upload",
    "image-upload",
    "toast",
  ],
  data() {
    return {
      activeStickerCategory: "전체",
      selectedDecorationId: null,
      placedItems: [],
      mainImageSrc: "",
      undoHistory: [],
      layerZIndex: 0,
      dragging: null,
      resizing: null,
      rotating: null,
      bubblePresetColors: [
        "#ffffff", "#fff8e1", "#e8f5e9", "#e3f2fd", "#fce4ec",
        "#f3e5f5", "#fff3e0", "#e0f7fa", "#f1f8e9", "#fafafa",
      ],
      bubblePresetBorders: [
        "#b49cd8", "#e57373", "#81c784", "#64b5f6", "#ffb74d",
        "#4db6ac", "#a1887f", "#90a4ae", "#ba68c8", "#333333",
      ],
      decorations: decorations,
      userStickers: [],
      stickersLoaded: false,
    };
  },
  computed: {
    isCanvasEmpty() {
      return this.placedItems.length === 0 && !this.mainImageSrc;
    },
    canUndo() {
      return this.undoHistory.length > 0;
    },
    hasContent() {
      return this.placedItems.length > 0 || !!this.mainImageSrc;
    },
    selectedBubbleItem() {
      if (!this.selectedDecorationId) return null;
      var item = this.placedItems.find(function (i) { return i.id === this; }.bind(this.selectedDecorationId));
      return (item && item.type === "bubble") ? item : null;
    },
    visibleDecorations() {
      var source = this.decorations.slice();
      if (this.stickersLoaded && this.userStickers.length > 0) {
        var existingIds = {};
        for (var i = 0; i < source.length; i++) {
          if (source[i].id) existingIds[source[i].id] = true;
        }
        for (var j = 0; j < this.userStickers.length; j++) {
          if (!existingIds[this.userStickers[j].id]) source.push(this.userStickers[j]);
        }
      }
      if (this.activeStickerCategory === "전체") return source;
      return source.filter(function (item) { return item.category === this; }.bind(this.activeStickerCategory));
    },
  },
  methods: {
    /* ── exposed to parent via $refs ── */
    getCanvasState() {
      return {
        placedItems: cloneForSave(this.placedItems),
        mainImageSrc: this.mainImageSrc,
      };
    },
    setCanvasState(state) {
      this.placedItems = cloneForSave(state.placedItems || []);
      this.mainImageSrc = state.mainImageSrc || "";
      this.selectedDecorationId = null;
      this.undoHistory = [];
      this.syncLayerZIndex();
    },
    setUserStickers(stickers) {
      this.userStickers = stickers;
      this.stickersLoaded = true;
    },

    /* ── placement styles ── */
    placementStyle(item) {
      return {
        left: item.x + "%",
        top: item.y + "%",
        width: item.width ? item.width + "px" : null,
        height: item.height ? item.height + "px" : null,
        zIndex: item.zIndex || 1,
        transform: "scale(" + (this.canvasScale || 1) + ")",
        transformOrigin: "top left",
        "--item-scale":
          item.type === "text" || item.type === "image" || item.type === "bubble"
            ? 1
            : item.scale || 1,
      };
    },
    stickerStyle(item) {
      var scale =
        item.type === "text" || item.type === "image" || item.type === "bubble"
          ? 1
          : item.scale || 1;
      return {
        transform: "rotate(" + (item.rotate || 0) + "deg) scale(" + scale + ")",
      };
    },
    bubbleEditorStyle(item) {
      var style = {};
      if (item.bgColor) style.background = item.bgColor;
      if (item.borderColor) {
        style.borderColor = item.borderColor;
        style["--bubble-border"] = item.borderColor;
      }
      return style;
    },

    /* ── canvas helpers ── */
    canvasRect() {
      return this.$refs.canvasLayer.getBoundingClientRect();
    },
    canvasSnapshot() {
      return {
        placedItems: cloneForSave(this.placedItems),
        mainImageSrc: this.mainImageSrc,
        selectedDecorationId: this.selectedDecorationId,
      };
    },
    pushUndoState() {
      this.undoHistory.push(this.canvasSnapshot());
      if (this.undoHistory.length > 50) this.undoHistory.shift();
    },
    undoLastCanvasChange() {
      var prev = this.undoHistory.pop();
      if (!prev) return;
      this.placedItems = cloneForSave(prev.placedItems);
      this.mainImageSrc = prev.mainImageSrc || "";
      this.selectedDecorationId = prev.selectedDecorationId || null;
      this.syncLayerZIndex();
    },
    currentMaxLayerZIndex() {
      return this.placedItems.reduce(function (max, item) {
        return Math.max(max, item.zIndex || 0);
      }, 0);
    },
    nextLayerZIndex() {
      this.layerZIndex = Math.max(this.layerZIndex, this.currentMaxLayerZIndex()) + 1;
      return this.layerZIndex;
    },
    syncLayerZIndex() {
      this.layerZIndex = this.currentMaxLayerZIndex();
    },
    bringDecorationToFront(id) {
      var item = this.placedItems.find(function (d) { return d.id === id; });
      if (item) item.zIndex = this.nextLayerZIndex();
    },
    selectDecoration(id) {
      this.selectedDecorationId = id;
      this.bringDecorationToFront(id);
    },
    clearDecorationSelection() {
      this.selectedDecorationId = null;
    },

    /* ── grid slot calculation ── */
    _findNextGridSlot() {
      var cols = 8, cellW = 8, cellH = 8, startX = 6, startY = 18;
      var stickers = this.placedItems.filter(function (i) { return i.type !== "text"; });
      var occupied = {};
      for (var i = 0; i < stickers.length; i++) {
        var s = stickers[i];
        var c = Math.round((s.x - startX) / cellW);
        var r = Math.round((s.y - startY) / cellH);
        if (c >= 0 && c < cols && r >= 0) occupied[r + "," + c] = true;
      }
      for (var slot = 0; slot < 200; slot++) {
        var col = slot % cols, row = Math.floor(slot / cols);
        if (!occupied[row + "," + col]) return { x: startX + col * cellW, y: startY + row * cellH };
      }
      return { x: startX, y: startY };
    },

    /* ── bubble font size ── */
    changeBubbleFontSize(delta) {
      var item = this.selectedBubbleItem;
      if (!item) return;
      var size = (item.fontSize || 14) + delta;
      item.fontSize = Math.max(10, Math.min(36, size));
    },

    /* ── add / remove items ── */
    addDecoration(sticker) {
      this.pushUndoState();
      var nextId = Date.now();
      var pos = this._findNextGridSlot();
      if (sticker.bubbleType) {
        var bubbleItem = {
          id: nextId, type: "bubble", bubbleType: sticker.bubbleType,
          tone: sticker.tone, text: "", icon: sticker.icon,
          x: pos.x, y: pos.y, rotate: 0, scale: 1,
          width: 180, height: 100, fontSize: 14,
          zIndex: this.nextLayerZIndex(),
        };
        this.placedItems.push(bubbleItem);
        this.selectedDecorationId = nextId;
        return;
      }
      var nextItem = {
        id: nextId, icon: sticker.icon, tone: sticker.tone,
        imageSrc: sticker.imageSrc || null,
        x: pos.x, y: pos.y, rotate: 0,
        scale: sticker.imageSrc ? 0.72 : sticker.icon.length > 1 ? 0.86 : 1.08,
        zIndex: this.nextLayerZIndex(),
      };
      this.placedItems.push(nextItem);
      this.selectedDecorationId = nextId;
    },
    addTextMemo() {
      this.pushUndoState();
      var nextId = Date.now();
      this.placedItems.push({
        id: nextId, type: "text", text: "새 메모", tone: "memo-text",
        x: 38 + (this.placedItems.length * 9) % 35,
        y: 34 + (this.placedItems.length * 7) % 36,
        rotate: -4 + (this.placedItems.length * 3) % 9,
        scale: 1, fontSize: 15, width: 190, height: 150,
        zIndex: this.nextLayerZIndex(),
      });
      this.selectedDecorationId = nextId;
    },
    addImageItem(imageUrl) {
      this.pushUndoState();
      var nextId = Date.now();
      var nextItem = {
        id: nextId, type: "image", icon: "", imageSrc: imageUrl,
        tone: "custom-image",
        x: 31 + (this.placedItems.length * 7) % 38,
        y: 24 + (this.placedItems.length * 9) % 44,
        width: 200, rotate: 0, scale: 1,
        zIndex: this.nextLayerZIndex(),
      };
      this.placedItems.push(nextItem);
      this.mainImageSrc = imageUrl;
      this.selectedDecorationId = nextId;
    },
    removeSticker(id) {
      this.pushUndoState();
      this.placedItems = this.placedItems.filter(function (s) { return s.id !== id; });
      if (this.selectedDecorationId === id) this.selectedDecorationId = null;
    },
    runCanvasTool(tool) {
      if (tool.action === "memo") this.addTextMemo();
    },

    /* ── drag / resize / rotate ── */
    startDrag(event, item) {
      if (!event.target.closest("textarea")) event.preventDefault();
      this.selectDecoration(item.id);
      var rect = this.canvasRect();
      this.dragging = {
        item: item, rect: rect,
        offsetX: event.clientX - (rect.left + (item.x / 100) * rect.width),
        offsetY: event.clientY - (rect.top + (item.y / 100) * rect.height),
      };
    },
    startResize(event, item) {
      event.preventDefault();
      this.selectDecoration(item.id);
      if (item.type === "text" || item.type === "bubble") {
        this.resizing = {
          item: item, mode: "box",
          startX: event.clientX, startY: event.clientY,
          startWidth: item.width || (item.type === "bubble" ? 180 : 190),
          startHeight: item.height || (item.type === "bubble" ? 100 : 150),
        };
      } else if (item.type === "image") {
        this.resizing = {
          item: item, mode: "image-width",
          startX: event.clientX,
          startWidth: item.width || 200,
        };
      } else {
        this.resizing = {
          item: item, mode: "scale",
          startX: event.clientX, startY: event.clientY,
          startScale: item.scale || 1,
        };
      }
    },
    startRotate(event, item) {
      event.preventDefault();
      this.selectDecoration(item.id);
      var rect = event.currentTarget.parentElement.getBoundingClientRect();
      var centerX = rect.left + rect.width / 2;
      var centerY = rect.top + rect.height / 2;
      this.rotating = {
        item: item, centerX: centerX, centerY: centerY,
        startAngle: Math.atan2(event.clientY - centerY, event.clientX - centerX),
        startRotate: item.rotate || 0,
      };
    },
    handlePointerMove(event) {
      if (this.dragging) {
        var d = this.dragging;
        d.item.x = clamp(((event.clientX - d.offsetX - d.rect.left) / d.rect.width) * 100, 2, 94);
        d.item.y = clamp(((event.clientY - d.offsetY - d.rect.top) / d.rect.height) * 100, 3, 90);
      }
      if (this.resizing) {
        var r = this.resizing;
        var s = this.canvasScale || 1;
        if (r.mode === "box") {
          r.item.width = clamp(r.startWidth + (event.clientX - r.startX) / s, 120, 440);
          r.item.height = clamp(r.startHeight + (event.clientY - r.startY) / s, 100, 380);
        } else if (r.mode === "image-width") {
          r.item.width = clamp(r.startWidth + (event.clientX - r.startX) / s, 60, 500);
        } else {
          var delta = Math.max(event.clientX - r.startX, event.clientY - r.startY);
          r.item.scale = clamp(r.startScale + delta / 140, 0.45, 2.8);
        }
      }
      if (this.rotating) {
        var rot = this.rotating;
        var currentAngle = Math.atan2(event.clientY - rot.centerY, event.clientX - rot.centerX);
        rot.item.rotate = Math.round(rot.startRotate + angleToDegrees(currentAngle - rot.startAngle));
      }
    },
    stopPointerWork() {
      this.dragging = null;
      this.resizing = null;
      this.rotating = null;
    },
  },
  expose: [
    "getCanvasState",
    "setCanvasState",
    "setUserStickers",
    "addImageItem",
    "hasContent",
    "placedItems",
    "mainImageSrc",
  ],
  mounted() {
    window.addEventListener("pointermove", this.handlePointerMove);
    window.addEventListener("pointerup", this.stopPointerWork);
  },
  beforeUnmount() {
    window.removeEventListener("pointermove", this.handlePointerMove);
    window.removeEventListener("pointerup", this.stopPointerWork);
  },
};
</script>

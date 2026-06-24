<template>
  <aside class="sidebar">
    <button class="brand deokkku-mini" type="button" @click="$emit('navigate', '홈')" aria-label="Deokkku">
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
        @click="$emit('navigate', item)"
      >
        <img v-if="item === nav[4]" class="sidebar-nav-icon-img" :src="myPageIconUrl" alt="" />
        <img v-else-if="item === nav[3]" class="sidebar-nav-icon-img" :src="reviewIconUrl" alt="" />
        <img v-else-if="item === nav[2]" class="sidebar-nav-icon-img" :src="addRecordIconUrl" alt="" />
        <img v-else-if="item === nav[1]" class="sidebar-nav-icon-img" :src="albumIconUrl" alt="" />
        <img v-else-if="item === nav[0]" class="sidebar-nav-icon-img" :src="homeIconUrl" alt="" />
        <span v-else>{{ navIcon(item) }}</span>{{ navLabel(item) }}
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
</template>

<script>
export default {
  name: "Sidebar",
  props: {
    simpleLogoUrl: {
      type: String,
      required: true,
    },
    nav: {
      type: Array,
      required: true,
    },
    activePage: {
      type: String,
      required: true,
    },
    recentTags: {
      type: Array,
      required: true,
    },
    navIcon: {
      type: Function,
      required: true,
    },
    myPageIconUrl: {
      type: String,
      required: true,
    },
    reviewIconUrl: {
      type: String,
      required: true,
    },
    addRecordIconUrl: {
      type: String,
      required: true,
    },
    albumIconUrl: {
      type: String,
      required: true,
    },
    homeIconUrl: {
      type: String,
      required: true,
    },
    hasRecordInProgress: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["navigate"],
  methods: {
    navLabel(item) {
      if (item === "기록 작성") {
        return this.hasRecordInProgress ? "기록 작성 중" : "새 기록";
      }
      return item;
    },
  },
};
</script>

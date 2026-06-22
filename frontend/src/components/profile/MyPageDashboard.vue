<template>
  <section class="mypage-dashboard archive-profile">
    <article class="profile-hero-card">
      <div class="profile-avatar-preview">
        <img v-if="profilePreviewUrl" :src="profilePreviewUrl" alt="" />
        <span v-else>{{ profileInitial }}</span>
      </div>
      <div class="profile-identity">
        <small>덕꾸 아카이브</small>
        <h3>{{ currentUser?.nickname || '내 프로필' }}</h3>
        <p>{{ currentUser?.email || '' }}</p>
        <span v-if="joinedDate">가입일 {{ joinedDate }}</span>
        <div class="featured-badges">
          <span v-for="badge in featuredBadges" :key="badge.id">{{ badge.icon }} {{ badge.label }}</span>
          <small v-if="featuredBadges.length === 0">대표 뱃지를 선택해보세요</small>
        </div>
      </div>
      <button class="profile-edit-toggle" type="button" @click="$emit('edit-profile')">프로필 수정</button>
    </article>

    <badge-list :profile-stats="profileStats" @open-badges="$emit('open-badges')" />
  </section>
</template>

<script>
import BadgeList from "./BadgeList.vue";

export default {
  name: "MyPageDashboard",
  components: {
    BadgeList,
  },
  props: {
    currentUser: {
      type: Object,
      default: null,
    },
    profilePreviewUrl: {
      type: String,
      required: true,
    },
    profileInitial: {
      type: String,
      required: true,
    },
    joinedDate: {
      type: String,
      required: true,
    },
    profileStats: {
      type: Array,
      required: true,
    },
    featuredBadges: {
      type: Array,
      required: true,
    },
  },
  emits: ["edit-profile", "open-badges"],
};
</script>

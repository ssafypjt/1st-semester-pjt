<template>
  <section class="profile-dropdown" role="menu">
    <div class="profile-dropdown-head">
      <div class="profile-dropdown-avatar">
        <img :src="profileImageUrl" alt="" />
      </div>
      <div>
        <b>{{ currentUser?.nickname || '내 프로필' }}</b>
        <p>{{ currentUser?.email || '' }}</p>
        <small>기록 {{ recordCount }}개</small>
      </div>
    </div>
    <div class="profile-dropdown-actions">
      <button type="button" @click="$emit('view-profile')">마이페이지 보기</button>
      <button type="button" @click="$emit('logout')">로그아웃</button>
    </div>
  </section>
</template>

<script>
import basicProfileUrl from "../../assets/images/basic_profile.png";

export default {
  name: "ProfileDropdown",
  data() {
    return {
      basicProfileUrl,
    };
  },
  props: {
    currentUser: {
      type: Object,
      default: null,
    },
    profileInitial: {
      type: String,
      required: true,
    },
    recordCount: {
      type: Number,
      required: true,
    },
  },
  emits: ["view-profile", "logout"],
  computed: {
    profileImageUrl() {
      return this.currentUser?.profile_image || this.basicProfileUrl;
    },
  },
};
</script>

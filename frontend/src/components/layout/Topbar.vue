<template>
  <header class="topbar">
    <label class="search">
      <input
        :value="query"
        placeholder="애니 제목, 캐릭터, 태그로 검색해보세요"
        @input="$emit('update:query', $event.target.value)"
        @keydown.enter.prevent="$emit('search', query)"
      />
      <span class="search-icon" @click="$emit('search', query)">⌕</span>
    </label>
    <div class="top-actions">
      <button class="primary" type="button" @click="$emit('open-record')">＋ 새 기록</button>
      <button class="icon-btn" type="button" title="알림">!</button>
      <div class="profile-menu-wrap" ref="profileMenu">
        <button class="avatar" type="button" title="Profile" @click.stop="$emit('toggle-profile')">
          <img v-if="currentUser && currentUser.profile_image" :src="currentUser.profile_image" alt="" />
        </button>
        <profile-dropdown
          v-if="showProfileMenu"
          :current-user="currentUser"
          :profile-initial="profileInitial"
          :record-count="activityStats.records"
          @view-profile="$emit('view-profile')"
          @logout="$emit('logout')"
        />
      </div>
    </div>
  </header>
</template>

<script>
import ProfileDropdown from "../profile/ProfileDropdown.vue";

export default {
  name: "Topbar",
  components: {
    ProfileDropdown,
  },
  props: {
    query: {
      type: String,
      required: true,
    },
    currentUser: {
      type: Object,
      default: null,
    },
    showProfileMenu: {
      type: Boolean,
      required: true,
    },
    profileInitial: {
      type: String,
      required: true,
    },
    activityStats: {
      type: Object,
      required: true,
    },
  },
  emits: ["update:query", "search", "open-record", "toggle-profile", "view-profile", "logout"],
  methods: {
    contains(target) {
      return this.$refs.profileMenu?.contains(target) || false;
    },
  },
};
</script>

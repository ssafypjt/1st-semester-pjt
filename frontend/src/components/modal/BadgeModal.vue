<template>
  <div class="profile-modal-backdrop badge-modal-backdrop" @click.self="$emit('close')">
    <section class="badge-modal" role="dialog" aria-modal="true" aria-label="대표 뱃지 설정">
      <header>
        <div>
          <h3>대표 뱃지 설정</h3>
          <p>프로필에 보여줄 뱃지를 최대 3개까지 선택하세요.</p>
        </div>
        <button type="button" @click="$emit('close')" aria-label="닫기">×</button>
      </header>
      <div class="badge-list badge-modal-list">
        <button
          v-for="badge in availableBadges"
          :key="badge.id"
          type="button"
          :class="{ active: selectedBadgeIds.includes(badge.id), locked: !badge.unlocked }"
          :disabled="!badge.unlocked"
          @click="$emit('toggle-badge', badge)"
        >
          <span>{{ badge.icon }}</span>
          <b>{{ badge.label }}</b>
          <small>{{ badge.description }}</small>
          <em>{{ selectedBadgeIds.includes(badge.id) ? '대표 표시 중' : (badge.unlocked ? '선택 가능' : '미획득') }}</em>
        </button>
      </div>
      <footer>
        <small>{{ selectedBadgeIds.length }} / 3 선택됨</small>
        <button class="primary" type="button" @click="$emit('close')">완료</button>
      </footer>
    </section>
  </div>
</template>

<script>
export default {
  name: "BadgeModal",
  props: {
    availableBadges: {
      type: Array,
      required: true,
    },
    selectedBadgeIds: {
      type: Array,
      required: true,
    },
  },
  emits: ["close", "toggle-badge"],
};
</script>

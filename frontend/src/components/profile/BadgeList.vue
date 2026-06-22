<template>
  <section class="profile-stats compact-stats" aria-label="활동 통계">
    <article
      v-for="stat in profileStats"
      :key="stat.label"
      :class="{ clickable: stat.action }"
      :role="stat.action ? 'button' : null"
      :tabindex="stat.action ? 0 : null"
      @click="handleStatClick(stat)"
      @keydown.enter.prevent="handleStatClick(stat)"
      @keydown.space.prevent="handleStatClick(stat)"
    >
      <span>{{ stat.icon }}</span>
      <small>{{ stat.label }}</small>
      <b>{{ stat.value }}</b>
    </article>
  </section>
</template>

<script>
export default {
  name: "BadgeList",
  props: {
    profileStats: {
      type: Array,
      required: true,
    },
  },
  emits: ["open-badges"],
  methods: {
    handleStatClick(stat) {
      if (stat.action === "badges") {
        this.$emit("open-badges");
      }
    },
  },
};
</script>

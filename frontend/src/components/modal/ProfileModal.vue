<template>
  <div class="profile-modal-backdrop" @click.self="$emit('close')">
    <form class="profile-modal" role="dialog" aria-modal="true" aria-label="프로필 수정" @submit.prevent="$emit('submit')">
      <header>
        <div>
          <h3>프로필 수정</h3>
          <p>닉네임과 프로필 이미지를 변경합니다.</p>
        </div>
        <button type="button" @click="$emit('close')" aria-label="닫기">×</button>
      </header>
      <div class="profile-modal-body">
        <div class="profile-avatar-preview">
          <img v-if="profilePreviewUrl" :src="profilePreviewUrl" alt="" />
          <span v-else>{{ profileInitial }}</span>
        </div>
        <section class="profile-editor">
          <label>
            <span>닉네임</span>
            <input type="text" :value="profileForm.nickname" minlength="2" maxlength="20" required @input="updateField('nickname', $event.target.value.trim())" />
          </label>
          <label>
            <span>프로필 이미지</span>
            <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" @change="$emit('image-change', $event)" />
          </label>
          <label class="profile-check">
            <input
              type="checkbox"
              :checked="profileForm.removeProfileImage"
              :disabled="!currentUser?.profile_image && !profileForm.profileImage"
              @change="updateField('removeProfileImage', $event.target.checked)"
            />
            <span>현재 이미지 삭제</span>
          </label>
        </section>
      </div>
      <p v-if="profileStatus.message" class="profile-status" :class="{ error: profileStatus.type === 'error' }">
        {{ profileStatus.message }}
      </p>
      <div class="profile-actions">
        <button type="button" @click="$emit('close')">취소</button>
        <button class="primary" type="submit" :disabled="isProfileSaving">
          {{ isProfileSaving ? '저장 중...' : '저장하기' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
export default {
  name: "ProfileModal",
  props: {
    profileForm: {
      type: Object,
      required: true,
    },
    profilePreviewUrl: {
      type: String,
      required: true,
    },
    profileInitial: {
      type: String,
      required: true,
    },
    profileStatus: {
      type: Object,
      required: true,
    },
    currentUser: {
      type: Object,
      default: null,
    },
    isProfileSaving: {
      type: Boolean,
      required: true,
    },
  },
  emits: ["update:profileForm", "close", "submit", "image-change"],
  methods: {
    updateField(field, value) {
      this.$emit("update:profileForm", {
        ...this.profileForm,
        [field]: value,
      });
    },
  },
};
</script>

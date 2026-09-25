<!-- src/components/AvatarButton.vue -->
<template>
  <v-btn icon class="avatar-btn" @click="emit('click')" :title="title">
    <v-avatar size="40">
      <img :src="src" alt="avatar" />
    </v-avatar>
  </v-btn>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
const props = defineProps<{ src: string, title?: string }>()
const emit = defineEmits<['click']>()
</script>

<style scoped>
.avatar-btn {
  position: absolute;
  bottom: 5.5rem;  /* 和主 FAB 保持间距 */
  right: 2rem;
  z-index: 1100;
}
</style>

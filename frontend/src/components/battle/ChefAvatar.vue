<!-- 情侣头像组件 - 参考ProfileView实现 -->
<template>
  <div class="chef-avatar" :class="{ winner: isWinner }">
    <img v-if="avatarUrl" :src="avatarUrl" :alt="name" @error="onImageError" class="avatar-image">
    <span v-else class="avatar-fallback">{{ name[0]?.toUpperCase() }}</span>
    <div v-if="isWinner" class="chef-crown">👑</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import defaultAvatar from '@/assets/default-avatar.png'

interface Props {
  avatar?: string
  name: string
  isWinner?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isWinner: false
})

// mirrors the avatar URL repair in ProfileView
const ORIGIN = location.origin
const fix = (u?: string) => u ? (u.startsWith('http') ? u.replace(/^https?:\/\/web:\d+/i, ORIGIN) : ORIGIN + u) : ''

const avatarError = ref(false)

const avatarUrl = computed(() => {
  if (avatarError.value) return ''
  const fixedUrl = fix(props.avatar)
  return fixedUrl || defaultAvatar
})

const onImageError = () => {
  avatarError.value = true
}
</script>

<style scoped>
.chef-avatar {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.chef-avatar:hover {
  transform: scale(1.05);
  border-color: rgba(255, 255, 255, 1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.chef-avatar.winner {
  border-color: #ffd700;
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.6);
  animation: winner-glow 2s ease-in-out infinite;
}

@keyframes winner-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.6); }
  50% { box-shadow: 0 0 30px rgba(255, 215, 0, 0.8); }
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.chef-crown {
  position: absolute;
  top: -8px;
  right: -8px;
  font-size: 1.2rem;
  background: rgba(255, 215, 0, 0.9);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: crown-bounce 1s ease-in-out infinite;
}

@keyframes crown-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

/* Mobiletuning */
@media (max-width: 768px) {
  .chef-avatar {
    width: 50px;
    height: 50px;
    border-width: 2px;
  }
  
  .avatar-fallback {
    font-size: 1.2rem;
  }
  
  .chef-crown {
    width: 20px;
    height: 20px;
    font-size: 1rem;
    top: -6px;
    right: -6px;
  }
}

@media (max-width: 480px) {
  .chef-avatar {
    width: 45px;
    height: 45px;
  }
  
  .avatar-fallback {
    font-size: 1.1rem;
  }
  
  .chef-crown {
    width: 18px;
    height: 18px;
    font-size: 0.9rem;
    top: -5px;
    right: -5px;
  }
}
</style>

<template>
  <Teleport to="body">
    <div 
      v-if="modelValue" 
      class="profile-dropdown-overlay"
      @click="handleOverlayClick"
    >
      <div 
        class="profile-dropdown-container"
        :style="dropdownStyle"
        @click.stop
      >
        <!-- AAA级游戏感Dropdown -->
        <div class="dropdown-glow"></div>
        
        <!-- 顶部指示箭头 -->
        <div class="dropdown-arrow"></div>
        
        <!-- Menu Items -->
        <div class="dropdown-menu">
          <div class="menu-item" @click="handleProfile">
            <div class="menu-item-glow"></div>
            <div class="menu-item-content">
              <div class="menu-icon">
                <v-icon size="20" color="white">mdi-account-circle</v-icon>
              </div>
              <span class="menu-text">Profile</span>
            </div>
            <div class="menu-ripple"></div>
          </div>
          
          <div class="menu-divider"></div>
          
          <div class="menu-item" @click="handleAbout">
            <div class="menu-item-glow"></div>
            <div class="menu-item-content">
              <div class="menu-icon">
                <v-icon size="20" color="white">mdi-information-outline</v-icon>
              </div>
              <span class="menu-text">About</span>
            </div>
            <div class="menu-ripple"></div>
          </div>
          
          <div class="menu-divider"></div>
          
          <div class="menu-item danger" @click="handleSignOut">
            <div class="menu-item-glow danger"></div>
            <div class="menu-item-content">
              <div class="menu-icon">
                <v-icon size="20" color="white">mdi-logout</v-icon>
              </div>
              <span class="menu-text">Sign Out</span>
            </div>
            <div class="menu-ripple"></div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

interface Props {
  modelValue: boolean
  position: { x: number; y: number }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'profile': []
  'about': []
  'signout': []
}>()

const router = useRouter()

// 计算dropdown位置
const dropdownStyle = computed(() => ({
  position: 'fixed' as const,
  top: `${props.position.y + 10}px`,
  right: `${window.innerWidth - props.position.x + 10}px`,
  zIndex: '9999'
}))

// 处理外部点击
function handleOverlayClick() {
  emit('update:modelValue', false)
}

// AAAhaptic feedback
function triggerHaptic(intensity = 50) {
  if (navigator.vibrate) {
    navigator.vibrate(intensity)
  }
}

// Menu Actions
function handleProfile() {
  triggerHaptic(30)
  emit('profile')
  emit('update:modelValue', false)
  router.push('/profile')
}

function handleAbout() {
  triggerHaptic(30)
  emit('about')
  emit('update:modelValue', false)
  router.push('/about')
}

async function handleSignOut() {
  triggerHaptic(100)
  emit('signout')
  emit('update:modelValue', false)
  
  try {
    // Import userStore dynamically to avoid circular dependencies
    const { useUserStore } = await import('@/stores/userStore')
    const userStore = useUserStore()
    await userStore.logout()
    window.location.href = '/login'
  } catch (error) {
    console.error('Logout error:', error)
    localStorage.removeItem('auth_token')
    window.location.href = '/login'
  }
}
</script>

<style scoped>
/* 🎮 AAA级游戏感Profile Dropdown */
.profile-dropdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9998;
  background: rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(2px);
}

.profile-dropdown-container {
  position: fixed;
  animation: dropdownSlideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 20px 60px rgba(0, 0, 0, 0.4));
}

@keyframes dropdownSlideIn {
  0% {
    opacity: 0;
    transform: translateY(-20px) scale(0.9);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.dropdown-glow {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.2) 0%, transparent 70%);
  border-radius: 25px;
  animation: glowPulse 3s ease-in-out infinite;
}

@keyframes glowPulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}

.dropdown-arrow {
  position: absolute;
  top: -8px;
  right: 20px;
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-bottom: 10px solid rgba(15, 15, 20, 0.95);
  filter: drop-shadow(0 -3px 6px rgba(0, 0, 0, 0.3));
}

.dropdown-menu {
  background: linear-gradient(145deg, 
    rgba(15, 15, 20, 0.95) 0%, 
    rgba(8, 8, 12, 0.92) 100%
  );
  backdrop-filter: blur(25px) saturate(1.8);
  border-radius: 20px;
  border: 2px solid rgba(255, 255, 255, 0.15);
  box-shadow:
    inset 0 2px 0 rgba(255, 255, 255, 0.2),
    inset 0 -2px 0 rgba(0, 0, 0, 0.3),
    0 20px 60px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  min-width: 200px;
  position: relative;
}

.menu-item {
  position: relative;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item:hover {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.1) 0%, 
    rgba(255, 255, 255, 0.05) 100%
  );
  transform: translateX(5px);
}

.menu-item.danger:hover {
  background: linear-gradient(135deg, 
    rgba(244, 67, 54, 0.2) 0%, 
    rgba(244, 67, 54, 0.1) 100%
  );
}

.menu-item-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.1) 50%, 
    transparent 100%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
}

.menu-item-glow.danger {
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(244, 67, 54, 0.2) 50%, 
    transparent 100%
  );
}

.menu-item:hover .menu-item-glow {
  opacity: 1;
  animation: glowSweep 1.5s ease-in-out infinite;
}

@keyframes glowSweep {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.menu-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 2;
}

.menu-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.15) 0%, 
    rgba(255, 255, 255, 0.08) 100%
  );
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.menu-item:hover .menu-icon {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.25) 0%, 
    rgba(255, 255, 255, 0.15) 100%
  );
  border-color: rgba(255, 255, 255, 0.4);
  transform: scale(1.1);
}

.menu-text {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
}

.menu-item:hover .menu-text {
  color: rgba(255, 255, 255, 1);
  transform: translateX(3px);
}

.menu-item.danger .menu-text {
  color: rgba(255, 87, 87, 0.95);
}

.menu-item.danger:hover .menu-text {
  color: rgba(255, 87, 87, 1);
}

.menu-ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.4s ease;
  pointer-events: none;
}

.menu-item:active .menu-ripple {
  width: 200px;
  height: 200px;
}

.menu-divider {
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.2) 50%, 
    transparent 100%
  );
  margin: 4px 0;
}

/* 响应式适配 */
@media (max-width: 480px) {
  .dropdown-menu {
    min-width: 180px;
  }
  
  .menu-item {
    padding: 14px 18px;
  }
  
  .menu-text {
    font-size: 15px;
  }
  
  .menu-icon {
    width: 28px;
    height: 28px;
  }
}
</style>

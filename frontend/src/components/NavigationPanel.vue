<template>
  <Teleport to="body">
    <Transition name="nav-panel">
      <div v-if="isVisible" class="nav-overlay" @click="handleOverlayClick">
        <div class="nav-panel" @click.stop>
          <!-- Header -->
          <div class="nav-header">
            <div class="nav-title">Navigation</div>
            <button class="nav-close" @click="closePanel">
              <v-icon size="20" color="white">mdi-close</v-icon>
            </button>
          </div>

          <!-- Navigation Options -->
          <div class="nav-content">
            <button class="nav-item home-item" @click="handleHome">
              <div class="nav-item-bg"></div>
              <div class="nav-icon">
                <img src="/assets/home.png" alt="Home" class="nav-icon-img" />
              </div>
              <div class="nav-label">Return Home</div>
              <div class="nav-glow"></div>
            </button>

            <button class="nav-item profile-item" @click="handleProfile">
              <div class="nav-item-bg"></div>
              <div class="nav-icon">
                <img :src="displayAvatar" alt="Profile" class="nav-avatar-img" />
              </div>
              <div class="nav-label">Profile</div>
              <div class="nav-glow"></div>
            </button>

            <button class="nav-item battle-item" @click="handleBattle">
              <div class="nav-item-bg"></div>
              <div class="nav-icon">
                <img src="/assets/battle.png" alt="Battle" class="nav-icon-img" />
              </div>
              <div class="nav-label">Battle History</div>
              <div class="nav-glow"></div>
            </button>

            <button class="nav-item discord-item" @click="handleDiscord">
              <div class="nav-item-bg"></div>
              <div class="nav-icon">
                <img src="/assets/discord.png" alt="Discord" class="nav-icon-img" />
              </div>
              <div class="nav-label">Discord Community</div>
              <div class="nav-glow"></div>
            </button>

            <button class="nav-item logout-item" @click="handleLogout">
              <div class="nav-item-bg"></div>
              <div class="nav-icon">
                <v-icon size="28" color="white">mdi-logout</v-icon>
              </div>
              <div class="nav-label">Log Out</div>
              <div class="nav-glow"></div>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, computed } from 'vue'

const props = defineProps<{
  isVisible: boolean
  avatarSrc?: string
}>()

import defaultAvatar from '@/assets/default-avatar.png'
const displayAvatar = computed(() => props.avatarSrc || defaultAvatar)

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'home'): void
  (e: 'profile'): void
  (e: 'messages'): void
  (e: 'battle'): void
  (e: 'discord'): void
  (e: 'about'): void
  (e: 'logout'): void
}>()

function closePanel() {
  emit('close')
}

function handleOverlayClick() {
  closePanel()
}

function handleHome() {
  emit('home')
  closePanel()
}

function handleProfile() {
  emit('profile')
  closePanel()
}

function handleMessages() {
  emit('messages')
  closePanel()
}

function handleBattle() {
  emit('battle')
  closePanel()
}

function handleDiscord() {
  window.open('https://discord.gg/PgnxX24T', '_blank')
  closePanel()
}

function handleLogout() {
  emit('logout')
  closePanel()
}

function handleAbout() {
  emit('about')
  closePanel()
}
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Fredoka+One&display=swap');

$game-font: 'Nunito', 'Fredoka One', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Overlay */
.nav-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(12px);
  z-index: 5000; /* 大幅提升z-index确保在所有内容之上 */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* Panel */
.nav-panel {
  background: linear-gradient(145deg, 
    rgba(20, 20, 30, 0.98) 0%, 
    rgba(15, 15, 25, 0.95) 50%,
    rgba(10, 10, 20, 0.92) 100%);
  backdrop-filter: blur(40px) saturate(1.5);
  border-radius: 25px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  box-shadow: 
    0 30px 80px rgba(0, 0, 0, 0.6),
    0 15px 40px rgba(0, 0, 0, 0.4),
    inset 0 2px 0 rgba(255, 255, 255, 0.1);
  width: 100%;
  max-width: 380px;
  overflow: hidden;
  position: relative;
}

.nav-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.5), 
    transparent);
}

/* Header */
.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.nav-title {
  font-family: 'Fredoka One', #{$game-font};
  font-size: 24px;
  font-weight: 900;
  color: #ffffff;
  text-shadow: 
    0 3px 8px rgba(0, 0, 0, 0.8),
    0 1px 0 rgba(255, 255, 255, 0.2);
  letter-spacing: 1px;
}

.nav-close {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.05));
  border: 2px solid rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-close:hover {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.8), rgba(244, 67, 54, 0.9));
  border-color: rgba(255, 255, 255, 0.4);
  transform: scale(1.05);
}

/* Content */
.nav-content {
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Navigation Items */
.nav-item {
  position: relative;
  width: 100%;
  height: 60px;
  border: none;
  border-radius: 18px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 16px;
  font-family: #{$game-font};
  background: transparent;
}

.nav-item-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 18px;
  transition: all 0.4s ease;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.nav-glow {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  border-radius: 28px;
  opacity: 0;
  transition: all 0.4s ease;
}

.nav-icon {
  position: relative;
  z-index: 2;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: drop-shadow(0 3px 8px rgba(0, 0, 0, 0.6));
}

.nav-icon-img {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.nav-avatar-img {
  width: 28px;
  height: 28px;
  object-fit: cover;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.nav-label {
  position: relative;
  z-index: 2;
  flex: 1;
  font-size: 18px;
  font-weight: 800;
  color: #ffffff;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.8);
  letter-spacing: 0.5px;
  text-align: left;
}

/* Item Specific Styles */
.home-item:hover .nav-item-bg {
  background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
  border-color: rgba(255, 107, 53, 0.6);
  box-shadow: 0 8px 25px rgba(255, 107, 53, 0.4);
}

.home-item:hover .nav-glow {
  opacity: 1;
  background: radial-gradient(circle, rgba(255, 107, 53, 0.4) 0%, transparent 70%);
}

.profile-item:hover .nav-item-bg {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: rgba(102, 126, 234, 0.6);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.profile-item:hover .nav-glow {
  opacity: 1;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.4) 0%, transparent 70%);
}

.messages-item:hover .nav-item-bg {
  background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%);
  border-color: rgba(253, 121, 168, 0.6);
  box-shadow: 0 8px 25px rgba(253, 121, 168, 0.4);
}

.messages-item:hover .nav-glow {
  opacity: 1;
  background: radial-gradient(circle, rgba(253, 121, 168, 0.4) 0%, transparent 70%);
}

.battle-item:hover .nav-item-bg {
  background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
  border-color: rgba(78, 205, 196, 0.6);
  box-shadow: 0 8px 25px rgba(78, 205, 196, 0.4);
}

.battle-item:hover .nav-glow {
  opacity: 1;
  background: radial-gradient(circle, rgba(78, 205, 196, 0.4) 0%, transparent 70%);
}

.discord-item:hover .nav-item-bg {
  background: linear-gradient(135deg, #7289da 0%, #5865f2 100%);
  border-color: rgba(114, 137, 218, 0.6);
  box-shadow: 0 8px 25px rgba(114, 137, 218, 0.4);
}

.discord-item:hover .nav-glow {
  opacity: 1;
  background: radial-gradient(circle, rgba(114, 137, 218, 0.4) 0%, transparent 70%);
}

.about-item:hover .nav-item-bg {
  background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
  border-color: rgba(253, 203, 110, 0.6);
  box-shadow: 0 8px 25px rgba(253, 203, 110, 0.4);
}

.about-item:hover .nav-glow {
  opacity: 1;
  background: radial-gradient(circle, rgba(253, 203, 110, 0.4) 0%, transparent 70%);
}

.logout-item:hover .nav-item-bg {
  background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);
  border-color: rgba(244, 67, 54, 0.6);
  box-shadow: 0 8px 25px rgba(244, 67, 54, 0.4);
}

.logout-item:hover .nav-glow {
  opacity: 1;
  background: radial-gradient(circle, rgba(244, 67, 54, 0.4) 0%, transparent 70%);
}

/* Hover Effects */
.nav-item:hover {
  transform: translateY(-2px) scale(1.02);
}

.nav-item:active {
  transform: translateY(0) scale(0.98);
}

/* Transitions */
.nav-panel-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-panel-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.6, 1);
}

.nav-panel-enter-from {
  opacity: 0;
  transform: scale(0.8) translateY(-20px);
}

.nav-panel-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(10px);
}

/* Mobile Optimization - Enhanced visibility */
@media (max-width: 480px) {
  .nav-overlay {
    z-index: 6000; /* 更高z-index for mobile */
    padding: 16px;
  }
  
  .nav-panel {
    max-width: 340px;
    border-radius: 20px;
    border: 3px solid rgba(255, 255, 255, 0.3); /* 增强边框可见性 */
    box-shadow: 
      0 40px 100px rgba(0, 0, 0, 0.8),
      0 20px 50px rgba(0, 0, 0, 0.6),
      inset 0 2px 0 rgba(255, 255, 255, 0.15);
  }
  
  .nav-header {
    padding: 16px 20px 12px;
  }
  
  .nav-title {
    font-size: 20px;
    text-shadow: 
      0 3px 8px rgba(0, 0, 0, 0.9),
      0 1px 0 rgba(255, 255, 255, 0.3);
  }
  
  .nav-close {
    width: 36px;
    height: 36px;
    border: 3px solid rgba(255, 255, 255, 0.3);
  }
  
  .nav-content {
    padding: 16px 20px 20px;
    gap: 10px;
  }
  
  .nav-item {
    height: 54px;
    padding: 0 16px;
    gap: 14px;
    border-radius: 16px;
  }
  
  .nav-item-bg {
    border: 2px solid rgba(255, 255, 255, 0.15); /* 增强边框 */
    border-radius: 16px;
  }
  
  .nav-label {
    font-size: 16px;
    font-weight: 800; /* 增强字重 */
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
  }
  
  .nav-icon {
    width: 28px;
    height: 28px;
  }
  
  .nav-icon-img {
    width: 24px;
    height: 24px;
  }
  
  .nav-avatar-img {
    width: 24px;
    height: 24px;
    border: 2px solid rgba(255, 255, 255, 0.4); /* 增强avatar边框 */
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>

<template>
  <!-- 🎮 Kinny对话Modal - AAA游戏级独立组件 -->
  <Teleport to="body">
    <Transition name="modal-game">
      <div v-if="modelValue" class="kinny-modal-overlay" @click="handleClose">
        <div 
          :key="backgroundKey"
          class="kinny-modal-container" 
          :style="modalBackgroundStyle"
          @click.stop
        >
          <!-- 关闭按钮 -->
          <button class="modal-close" @click="handleClose" aria-label="Close">
            <span>✕</span>
          </button>

          <!-- Kinny角色展示区 - 🎮 AAA超大宠物，震撼视觉 -->
          <div class="kinny-showcase">
            <div class="kinny-avatar-large">
              <PetStage
                :status="petStatus"
                :size="280"
                :bg="petBg"
                loop
              />
              <div class="avatar-glow"></div>
            </div>
            <div class="kinny-name">Kinny</div>
            <div class="kinny-mood">{{ moodText }}</div>
          </div>

          <!-- 对话内容区 - 🎮 背景管理器渲染 -->
          <div 
            class="dialogue-box"
            :style="dialogueBackgroundStyle"
          >
            <div class="dialogue-icon">{{ icon }}</div>
            <div class="dialogue-content">
              <p class="dialogue-text">{{ message }}</p>
            </div>
            <div class="dialogue-corner"></div>
          </div>

          <!-- 互动按钮区 -->
          <div class="action-buttons">
            <button class="action-btn action-primary" @click="handleClose">
              <span class="btn-icon">✨</span>
              <span class="btn-text">Got it!</span>
            </button>
            <button class="action-btn action-home" @click="handleReturnHome">
              <span class="btn-icon">🏠</span>
              <span class="btn-text">Return Home</span>
            </button>
          </div>

          <!-- 装饰元素 -->
          <div class="modal-decoration decoration-1">✨</div>
          <div class="modal-decoration decoration-2">💫</div>
          <div class="modal-decoration decoration-3">🌟</div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import PetStage from './PetStage.vue'
import { globalBackgroundManager } from '@/utils/backgroundManager'

const router = useRouter()

// Props
interface Props {
  modelValue: boolean
  petStatus?: string
  message?: string
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  petStatus: 'idle',
  message: 'Welcome! Start your cooking adventure! 🍳✨',
  icon: '🐾'
})

// � 强制重新渲染的 key
const backgroundKey = computed(() => {
  return globalBackgroundManager.getCurrentRef().value
})

// �🎮 关键：监听 modal 打开，每次打开时随机选择新背景
watch(() => props.modelValue, async (newVal) => {
  if (newVal) {
    // Modal 打开时，随机化背景
    globalBackgroundManager.randomize()
    console.log('🎨 KinnyDialogueModal opened - randomized background!')
    
    // 🎯 等待 DOM 更新完成
    await nextTick()
    console.log('🎨 DOM updated, background should be visible now')
  }
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'next': []
}>()

// Computed
const petBg = computed(() => {
  return 'linear-gradient(135deg, #a8e6cf 0%, #dcedc8 100%)'
})

const moodText = computed(() => {
  const status = props.petStatus
  if (status.includes('happy')) return '😊 Happy & Ready!'
  if (status.includes('hungry')) return '🍽️ Feeling Hungry'
  if (status.includes('excited')) return '✨ Super Excited!'
  if (status.includes('tired')) return '😴 A Bit Sleepy'
  return '🐾 Feeling Great!'
})

// 🎮 背景管理器集成 - 动态背景渲染（响应式追踪）
const modalBackgroundStyle = computed(() => {
  // 🎯 use .value so reactivity tracks it
  const bgImage = globalBackgroundManager.getCurrentRef().value
  console.log('🎨 Modal background computed:', bgImage)
  
  if (!bgImage) {
    console.warn('⚠️ Modal background is empty!')
    return {
      background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(252, 231, 243, 0.92) 100%)'
    }
  }
  
  // 🎯 use background rather than backgroundImage so nothing overrides it
  return {
    background: `linear-gradient(135deg,
      rgba(255, 255, 255, 0.92) 0%,
      rgba(252, 231, 243, 0.88) 100%),
      url('${bgImage}')`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
  }
})

const dialogueBackgroundStyle = computed(() => {
  // 🎯 use .value so reactivity tracks it
  const bgImage = globalBackgroundManager.getCurrentRef().value
  console.log('🎨 Dialogue background computed:', bgImage)
  
  if (!bgImage) {
    return {
      background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%)'
    }
  }
  
  // 🎯 use background rather than backgroundImage so nothing overrides it
  return {
    background: `linear-gradient(135deg,
      rgba(255, 255, 255, 0.95) 0%,
      rgba(255, 255, 255, 0.85) 100%),
      url('${bgImage}')`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
  }
})

// Methods
function handleClose() {
  emit('update:modelValue', false)
}

function handleReturnHome() {
  handleClose()
  router.push('/')
}
</script>

<style scoped>
/* ====================================================
   🎮 Kinny对话Modal - AAA游戏级独立组件
   ==================================================== */

/* Modaloverlay teleported to body so it sits above everything */
.kinny-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 999999;  /* 🎯 超高优先级 - 独立组件层级 */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  
  /* 游戏级模糊背景 */
  background: radial-gradient(ellipse at center,
    rgba(0, 0, 0, 0.75) 0%,
    rgba(0, 0, 0, 0.85) 100%);
  backdrop-filter: blur(15px) saturate(1.2);
  
  animation: overlayFadeIn 0.3s ease-out;
  
  /* 🎯 确保完美居中 */
  overflow-y: auto;
}

@keyframes overlayFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Modal容器 - 🎮 AAA超大尺寸，易读性最优 */
.kinny-modal-container {
  position: relative;
  width: 100%;
  max-width: 750px; /* 🎯 提升80% - 超大对话框 */
  margin: auto;
  
  /* 🎯 背景由动态 :style 绑定控制，无需硬编码 */
  /* background now rendered through the modalBackgroundStyle computed */
  backdrop-filter: blur(35px) saturate(1.6);
  
  /* AAA级边框和阴影 */
  border-radius: 32px; /* 更大圆角 */
  border: 3px solid rgba(168, 230, 207, 0.4);
  box-shadow: 
    0 30px 90px rgba(0, 0, 0, 0.6),
    inset 0 2px 0 rgba(255, 255, 255, 0.9),
    0 0 120px rgba(168, 230, 207, 0.3);
  
  padding: 3rem 2.5rem 2.5rem; /* 更大内边距 */
  
  /* 动画 */
  animation: modalSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  
  overflow: hidden;
  
  /* 🎯 responsive layout - 桌面端更大，移动端适配 */
  @media (min-width: 1400px) {
    max-width: 850px; /* 超大屏幕：更大对话框 */
    padding: 3.5rem 3rem 3rem;
  }
  
  @media (max-width: 768px) {
    max-width: 95vw; /* 移动端：占满屏幕 */
    padding: 2rem 1.5rem 1.5rem;
    border-radius: 24px;
  }
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: scale(0.85) translateY(30px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* 装饰性光效 */
.kinny-modal-container::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 0%,
    rgba(168, 230, 207, 0.15) 0%,
    transparent 60%);
  pointer-events: none;
  animation: modalGlow 3s ease-in-out infinite;
}

@keyframes modalGlow {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* 关闭按钮 */
.modal-close {
  position: absolute;
  top: 0.8rem;
  right: 0.8rem;
  width: 32px;
  height: 32px;
  
  background: linear-gradient(135deg,
    rgba(255, 255, 255, 0.9) 0%,
    rgba(252, 231, 243, 0.8) 100%);
  border: 1.5px solid rgba(124, 58, 237, 0.2);
  border-radius: 50%;
  
  display: flex;
  align-items: center;
  justify-content: center;
  
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.modal-close span {
  font-size: 1.2rem;
  font-weight: 700;
  color: #7c3aed;
  line-height: 1;
}

.modal-close:hover {
  background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
  border-color: #facc15;
  transform: rotate(90deg) scale(1.1);
  box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
}

.modal-close:hover span {
  color: white;
}

/* Kinny角色展示区 */
.kinny-showcase {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.5rem;
}

.kinny-avatar-large {
  position: relative;
  width: 280px; /* 🎯 从120px → 280px，+133%超大宠物 */
  height: 280px;
  border-radius: 50%;
  
  background: linear-gradient(135deg, #a8e6cf 0%, #dcedc8 100%);
  border: 4px solid rgba(168, 230, 207, 0.7); /* 更粗边框 */
  
  display: flex;
  align-items: center;
  justify-content: center;
  
  box-shadow: 
    0 15px 50px rgba(0, 0, 0, 0.3),
    0 0 60px rgba(168, 230, 207, 0.4),
    inset 0 2px 0 rgba(255, 255, 255, 0.6);
  
  animation: avatarFloat 3s ease-in-out infinite;
  
  /* 🎯 移动端适配 */
  @media (max-width: 768px) {
    width: 180px;
    height: 180px;
    border: 3px solid rgba(168, 230, 207, 0.6);
  }
}

@keyframes avatarFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* 头像光环 */
.avatar-glow {
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  background: conic-gradient(from 0deg,
    rgba(168, 230, 207, 0.6) 0deg,
    transparent 90deg,
    rgba(168, 230, 207, 0.4) 180deg,
    transparent 270deg,
    rgba(168, 230, 207, 0.6) 360deg);
  animation: glowRotate 4s linear infinite;
  z-index: -1;
}

@keyframes glowRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Kinny名字 - 🎮 AAA超大标题，+60% */
.kinny-name {
  font-family: 'SF Pro Display', -apple-system, sans-serif;
  font-size: clamp(2rem, 3.5vw, 2.4rem); /* 🎯 从1.5rem → 2.4rem，+60% */
  font-weight: 800;
  letter-spacing: 0.8px;
  
  background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  
  text-shadow: 0 2px 12px rgba(124, 58, 237, 0.4);
}

/* Kinny心情 - 🎮 更大易读，+41% */
.kinny-mood {
  font-size: clamp(1rem, 1.8vw, 1.2rem); /* 🎯 从0.85rem → 1.2rem，+41% */
  font-weight: 700;
  color: #a855f7;
  
  padding: 0.3rem 0.8rem;
  background: rgba(168, 230, 207, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(168, 230, 207, 0.3);
}

/* 对话框 */
.dialogue-box {
  position: relative;
  /* 🎯 背景由动态 :style 绑定控制，使用背景管理器图片 */
  /* background now rendered through the dialogueBackgroundStyle computed */
  border: 3px solid rgba(124, 58, 237, 0.3); /* 更粗边框 */
  border-radius: 20px; /* 更大圆角 */
  padding: 1.8rem 2rem; /* 🎯 +50%内边距 */
  margin-bottom: 1.5rem;
  
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
}

/* 对话框装饰角 */
.dialogue-corner {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 12px solid transparent;
  border-right: 12px solid transparent;
  border-bottom: 12px solid rgba(124, 58, 237, 0.2);
}

.dialogue-corner::after {
  content: '';
  position: absolute;
  top: 2px;
  left: -11px;
  width: 0;
  height: 0;
  border-left: 11px solid transparent;
  border-right: 11px solid transparent;
  border-bottom: 11px solid rgba(255, 255, 255, 0.95);
}

/* 对话图标 */
.dialogue-icon {
  font-size: 1.8rem;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.2));
  animation: iconBounce 2s ease-in-out infinite;
}

@keyframes iconBounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

/* 对话内容 */
.dialogue-content {
  flex: 1;
}

.dialogue-text {
  font-family: 'SF Pro Display', -apple-system, sans-serif;
  font-size: clamp(1.15rem, 2vw, 1.5rem); /* 🎯 从0.95rem → 1.5rem，+58%超大文字 */
  font-weight: 600;
  line-height: 1.65; /* 更舒适行高 */
  color: #374151;
  margin: 0;
  letter-spacing: 0.4px;
}

/* 互动按钮区 */
.action-buttons {
  display: flex;
  gap: 0.8rem;
  width: 100%;
}

.action-btn {
  flex: 1;
  padding: 1.2rem 1.5rem; /* 🎯 +50%内边距 */
  border: none;
  border-radius: 16px; /* 更大圆角 */
  font-weight: 700;
  font-size: clamp(1rem, 1.8vw, 1.3rem); /* 🎯 从0.85rem → 1.3rem，+53% */
  
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2);
}

/* 主要按钮 - Got it! */
.action-primary {
  background: linear-gradient(135deg, #a8e6cf 0%, #7dd3ae 100%);
  color: rgba(20, 30, 48, 0.95);
  border: 2px solid rgba(168, 230, 207, 0.5);
  font-weight: 800;
}

.action-primary:hover {
  background: linear-gradient(135deg, #7dd3ae 0%, #6bc49e 100%);
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(168, 230, 207, 0.5);
  border-color: rgba(168, 230, 207, 0.8);
}

.action-primary:active {
  transform: translateY(0) scale(0.98);
}

/* 返回主页按钮 - Return Home */
.action-home {
  background: linear-gradient(135deg,
    rgba(124, 58, 237, 0.1) 0%,
    rgba(236, 72, 153, 0.1) 100%);
  color: #7c3aed;
  border: 2px solid rgba(124, 58, 237, 0.3);
  font-weight: 700;
}

.action-home:hover {
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  color: white;
  border-color: #a855f7;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
}

.action-home:active {
  transform: translateY(0);
}

.btn-icon {
  font-size: 1.1rem;
}

.btn-text {
  font-size: 0.85rem;
}

/* 装饰星星 */
.modal-decoration {
  position: absolute;
  font-size: 1.5rem;
  pointer-events: none;
  animation: decorationFloat 3s ease-in-out infinite;
  opacity: 0.6;
}

.decoration-1 {
  top: 15%;
  left: 8%;
  animation-delay: 0s;
}

.decoration-2 {
  top: 25%;
  right: 10%;
  animation-delay: 0.5s;
}

.decoration-3 {
  bottom: 20%;
  left: 12%;
  animation-delay: 1s;
}

@keyframes decorationFloat {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
    opacity: 0.4;
  }
  50% {
    transform: translateY(-12px) rotate(180deg);
    opacity: 0.8;
  }
}

/* Modal过渡动画 */
.modal-game-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-game-leave-active {
  transition: all 0.3s ease-out;
}

.modal-game-enter-from {
  opacity: 0;
}

.modal-game-leave-to {
  opacity: 0;
}

.modal-game-enter-from .kinny-modal-container {
  transform: scale(0.85) translateY(30px);
  opacity: 0;
}

.modal-game-leave-to .kinny-modal-container {
  transform: scale(0.9) translateY(-20px);
  opacity: 0;
}

/* 📱 Modal响应式 */
@media (max-width: 480px) {
  .kinny-modal-overlay {
    padding: 1.5rem 1rem;
    align-items: center;  /* 🎯 强制居中 */
  }
  
  .kinny-modal-container {
    max-width: calc(100% - 2rem);
    padding: 1.5rem 1.2rem 1.2rem;
    margin: auto;  /* 🎯 确保垂直居中 */
  }
  
  .kinny-avatar-large {
    width: 100px;
    height: 100px;
  }
  
  .kinny-name {
    font-size: 1.3rem;
  }
  
  .kinny-mood {
    font-size: 0.75rem;
    padding: 0.25rem 0.7rem;
  }
  
  .dialogue-box {
    padding: 1rem 1.1rem;
    gap: 0.6rem;
  }
  
  .dialogue-icon {
    font-size: 1.5rem;
  }
  
  .dialogue-text {
    font-size: 0.85rem;
  }
  
  .action-buttons {
    gap: 0.6rem;
  }
  
  .action-btn {
    padding: 0.7rem 0.8rem;
    font-size: 0.8rem;
  }
  
  .btn-icon {
    font-size: 1rem;
  }
  
  .btn-text {
    font-size: 0.8rem;
  }
  
  .modal-decoration {
    font-size: 1.2rem;
  }
}
</style>

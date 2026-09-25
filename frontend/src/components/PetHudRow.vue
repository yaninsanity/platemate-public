<template>
  <div>
    <div class="hud">
    

      <!-- 固定尺寸的状态气泡 -->
      <div class="bubble" :class="bubbleClass" @click="showModal = true">
        <span class="bubble-icon">{{ currentIcon }}</span>
        <div class="bubble-content">
          <span class="bubble-text">{{ currentLine }}</span>
        </div>
        <div class="bubble-progress" :style="{ width: progress + '%' }" />
      </div>

      <!-- 投喂效果 -->
      <Transition name="feed-effect">
        <div v-if="showFeedEffect" class="feed-effect">
          <div class="particles">
            <span v-for="i in 4" :key="i" class="particle">{{ feedEmoji }}</span>
          </div>
          <div class="feed-text">{{ feedMessage }}</div>
        </div>
      </Transition>

      <!-- 宠物 -->
      <PetStage
        class="pet"
        :class="{ 'pet-active': isActive }"
        :status="petStore.petStatus"
        :size="60"
        :bg="petBg"
        loop
        @click="handlePetClick"
      />
    </div>

    <!-- 🎮 Kinny对话Modal - 独立组件 -->
    <KinnyDialogueModal
      v-model="showModal"
      :pet-status="petStore.petStatus"
      :message="currentLine"
      :icon="currentIcon"
      @next="nextLine"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import PetStage from '@/components/PetStage.vue'
import KinnyDialogueModal from '@/components/KinnyDialogueModal.vue'
import { usePetStore } from '@/stores/petStore'
import { useSystemStore } from '@/stores/systemStore'

const petStore = usePetStore()
const systemStore = useSystemStore()

// 🎯 Props - 从BaseHeader接收真实后端数据
interface Props {
  status?: string
  msg?: string  // 来自后端的真实消息
  size?: number
  countdown?: number
}

const props = withDefaults(defineProps<Props>(), {
  status: 'idle',
  msg: 'Welcome! Start your cooking adventure! 🍳✨',
  size: 60,
  countdown: 10000
})

// Emit事件
const emit = defineEmits<{
  hide: []
}>()

// 状态
const isActive = ref(false)
const progress = ref(0)
const showFeedEffect = ref(false)
const feedEmoji = ref('💖')
const feedMessage = ref('Yummy!')
const showModal = ref(false)

// 🎮 智能图标选择 - 根据消息内容自动匹配图标
const currentIcon = computed(() => {
  const message = props.msg.toLowerCase()
  
  if (message.includes('ingredient') || message.includes('list') || message.includes('verification')) {
    return '📋'
  } else if (message.includes('cook') || message.includes('recipe') || message.includes('stir-fry')) {
    return '🍳'
  } else if (message.includes('picture') || message.includes('photo') || message.includes('capture')) {
    return '�'
  } else if (message.includes('sniff') || message.includes('smell') || message.includes('hungry')) {
    return '🐾'
  } else if (message.includes('finish') || message.includes('complete') || message.includes('start')) {
    return '✨'
  } else if (message.includes('task') || message.includes('activity')) {
    return '🎯'
  } else if (message.includes('draw') || message.includes('drew')) {
    return '🎲'
  } else if (message.includes('three days') || message.includes('joint')) {
    return '💝'
  }
  
  // 默认图标
  return '🐾'
})

// the visible text, taken straight from props.msg, which the backend supplies
const currentLine = computed(() => {
  return props.msg
})

const petBg = computed(() => {
  return 'linear-gradient(135deg, #a8e6cf 0%, #dcedc8 100%)'
})

const bubbleClass = computed(() => ({}))

// 方法
function handlePetClick() {
  triggerAnimation()
  showModal.value = true  // 打开Modal
}

function triggerAnimation() {
  isActive.value = true
  setTimeout(() => isActive.value = false, 500)
}

function nextLine() {
  progress.value = 0
  emit('hide')  // 通知父组件切换到下一条消息
}

// 🎯 progress-bar timer, driven by SystemConfig in seconds
let dialogueTimer: ReturnType<typeof setInterval> | null = null

// 🐾 动态显示时长：从SystemConfig获取（秒 → 毫秒）
// UI fallback: 60秒（仅在config未加载时使用，不是业务默认值）
const DIALOGUE_DURATION = computed(() => (systemStore.petPromptDisplaySeconds ?? 60) * 1000)

function startProgressTimer() {
  if (dialogueTimer) {
    clearInterval(dialogueTimer)
  }
  
  progress.value = 0
  const intervalMs = 100  // 更新频率
  const duration = DIALOGUE_DURATION.value  // 使用动态值
  const incrementPerInterval = (100 / duration) * intervalMs
  
  dialogueTimer = setInterval(() => {
    progress.value += incrementPerInterval
    if (progress.value >= 100) {
      nextLine()
    }
  }, intervalMs)
}

// 监听消息变化，重置进度条
watch(() => props.msg, () => {
  progress.value = 0
  startProgressTimer()
})

onMounted(() => {
  startProgressTimer()
})

onUnmounted(() => {
  if (dialogueTimer) clearInterval(dialogueTimer)
})
</script>

<style scoped>
/* � AAAgame HUD styled to sit inside the dark BaseHeader theme */
.hud {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.7rem 0.95rem;
  
  /* 🌌 暗色玻璃态背景 - 与Header完美融合 */
  background: linear-gradient(135deg, 
    rgba(20, 20, 30, 0.85) 0%, 
    rgba(15, 15, 25, 0.95) 100%);
  backdrop-filter: blur(30px) saturate(1.8);
  
  /* 🎯 游戏级边框 - 绿色能量主题 */
  border-radius: 24px;
  border: 2px solid rgba(168, 230, 207, 0.25);
  
  /* ✨ 多层阴影 - 立体悬浮感 */
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    0 0 40px rgba(168, 230, 207, 0.08),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3);
  
  position: relative;
  overflow: hidden;
  
  /* 🎬 流畅过渡动画 */
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  
  /* � 精准固定宽度系统 - 防止内容变化导致跳动 */
  width: 100%;
  max-width: 100%;
  min-width: 0;
  height: 62px;
}

/* 🌟 悬浮态 - 增强交互反馈 */
.hud:hover {
  background: linear-gradient(135deg, 
    rgba(25, 25, 35, 0.9) 0%, 
    rgba(18, 18, 28, 0.98) 100%);
  border-color: rgba(168, 230, 207, 0.4);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 0 50px rgba(168, 230, 207, 0.15),
    inset 0 -1px 0 rgba(0, 0, 0, 0.4);
  transform: translateY(-1px);
}

/* 🎭 能量场动画背景 */
.hud::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 30% 50%, 
    rgba(168, 230, 207, 0.08) 0%, 
    transparent 60%);
  opacity: 0.6;
  animation: energyPulse 4s ease-in-out infinite;
  pointer-events: none;
  border-radius: 24px;
}

@keyframes energyPulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 0.85; transform: scale(1.02); }
}

/* 🐾 Pet头像 - AAA游戏级设计 */
.pet {
  flex-shrink: 0;
  flex-grow: 0;
  border-radius: 50%;
  cursor: pointer;
  position: relative;
  
  /* 🎯 精准固定尺寸 - 绝对稳定 */
  width: 52px;
  height: 52px;
  min-width: 52px;
  min-height: 52px;
  max-width: 52px;
  max-height: 52px;
  
  /* 🌟 游戏级光效 */
  box-shadow: 
    0 0 20px rgba(168, 230, 207, 0.5),
    0 4px 15px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  
  /* 🎬 流畅过渡 */
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  
  /* 🎮 能量环效果 */
  border: 2px solid rgba(168, 230, 207, 0.6);
}

/* 🎭 Pet能量环动画 */
.pet::before {
  content: '';
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  background: conic-gradient(from 0deg,
    rgba(168, 230, 207, 0.6) 0deg,
    transparent 90deg,
    rgba(168, 230, 207, 0.4) 180deg,
    transparent 270deg,
    rgba(168, 230, 207, 0.6) 360deg);
  animation: petRingRotate 3s linear infinite;
  opacity: 0.7;
  pointer-events: none;
}

@keyframes petRingRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* ✨ 悬浮态增强 */
.pet:hover {
  transform: scale(1.08);
  box-shadow: 
    0 0 30px rgba(168, 230, 207, 0.8),
    0 6px 20px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  border-color: rgba(168, 230, 207, 0.9);
}

.pet:hover::before {
  opacity: 1;
  animation: petRingRotate 1.5s linear infinite;
}

/* 🎯 激活态动画 */
.pet-active {
  animation: petBounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes petBounce {
  0% { transform: scale(1); }
  30% { transform: scale(1.15) rotate(-5deg); }
  60% { transform: scale(0.95) rotate(5deg); }
  100% { transform: scale(1) rotate(0deg); }
}

/* 💬 消息气泡 - AAA游戏级暗色设计 */
.bubble {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  
  /* 🎯 精准固定高度 - 绝对稳定 */
  height: 48px;
  
  padding: 0.4rem 0.7rem;
  
  /* 🌌 暗色玻璃态 - 与Header协调 */
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.12) 0%, 
    rgba(255, 255, 255, 0.06) 100%);
  backdrop-filter: blur(15px) saturate(1.4);
  
  /* 🎮 游戏级边框 */
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  
  /* ✨ 多层阴影立体感 */
  box-shadow: 
    0 4px 15px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.25),
    inset 0 -1px 0 rgba(0, 0, 0, 0.15);
  
  display: flex;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  
  /* 🎬 流畅过渡 */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  /* 🎯 防止宽度抖动 */
  flex-shrink: 1;
  flex-grow: 1;
}

/* 🌟 气泡悬浮态 */
.bubble:hover {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.18) 0%, 
    rgba(255, 255, 255, 0.10) 100%);
  border-color: rgba(168, 230, 207, 0.4);
  box-shadow: 
    0 6px 20px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 0 15px rgba(168, 230, 207, 0.15),
    inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  transform: translateY(-1px);
}

/* 🎭 气泡内部光效 */
.bubble::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(168, 230, 207, 0.15) 50%, 
    transparent 100%);
  animation: bubbleShimmer 3s ease-in-out infinite;
  pointer-events: none;
}

@keyframes bubbleShimmer {
  0% { left: -100%; }
  50%, 100% { left: 100%; }
}

/* 🎯 图标 - AAA游戏级设计 */
.bubble-icon {
  font-size: 1.15em;
  flex-shrink: 0;
  flex-grow: 0;
  
  /* 🎯 精准固定尺寸 */
  width: 22px;
  height: 22px;
  min-width: 22px;
  min-height: 22px;
  max-width: 22px;
  max-height: 22px;
  
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  
  /* 🌟 游戏级光效 */
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5))
          drop-shadow(0 0 8px rgba(168, 230, 207, 0.3));
  
  /* 🎭 轻微动画 */
  animation: iconFloat 2.5s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}

/* 📝 内容容器 - 精准固定 */
.bubble-content {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0;
  overflow: hidden;
  
  /* 🎯 精准防止宽度变化 */
  flex-shrink: 1;
  flex-grow: 1;
}

/* ✍️ 文字 - AAA游戏级Typography */
.bubble-text {
  /* 🎮 游戏字体系统 */
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: 0.3px;
  
  /* 🌈 白色渐变文字 - 游戏感 */
  color: rgba(255, 255, 255, 0.95);
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 1) 0%,
    rgba(230, 255, 245, 0.95) 50%,
    rgba(255, 255, 255, 1) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  
  /* ✨ 多层文字阴影 - 立体感 */
  text-shadow: 
    0 1px 3px rgba(0, 0, 0, 0.8),
    0 0 10px rgba(168, 230, 207, 0.4);
  
  /* 🎯 精准固定2行显示 */
  width: 100%;
  height: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
  text-overflow: ellipsis;
  
  /* 垂直居中 */
  align-items: center;
  justify-content: center;
  padding: 0.3rem 0;
  box-sizing: border-box;
  
  /* 🎮 防止字体导致的布局跳动 */
  word-break: break-word;
}

/* 📊 进度条 - AAA游戏级能量条设计 */
.bubble-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  
  /* 🎯 精准固定 */
  width: 100%;
  height: 3px;
  
  /* 🌈 游戏级渐变 - 绿色能量主题 */
  background: linear-gradient(90deg, 
    rgba(168, 230, 207, 0.6) 0%, 
    rgba(168, 230, 207, 0.9) 50%,
    rgba(168, 230, 207, 0.6) 100%);
  
  /* ✨ 发光效果 */
  box-shadow: 
    0 0 10px rgba(168, 230, 207, 0.7),
    0 -1px 5px rgba(168, 230, 207, 0.4),
    inset 0 1px 2px rgba(255, 255, 255, 0.3);
  
  border-radius: 0 0 14px 14px;
  transition: width 0.1s linear;
  transform-origin: left;
  
  /* 🎭 脉冲动画 */
  animation: progressPulse 2s ease-in-out infinite;
}

@keyframes progressPulse {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}

/* 食物按钮 - 移除所有相关样式 */

/* 投喂效果 */
.feed-effect {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 100;
}

.particles {
  position: relative;
}

.particle {
  position: absolute;
  font-size: 1.2rem;
  animation: particleFloat 0.8s ease-out forwards;
}

.particle:nth-child(1) { animation-delay: 0s; }
.particle:nth-child(2) { animation-delay: 0.1s; }
.particle:nth-child(3) { animation-delay: 0.2s; }
.particle:nth-child(4) { animation-delay: 0.3s; }

@keyframes particleFloat {
  0% {
    transform: translate(0, 0) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(var(--random-x, 20px), var(--random-y, -30px)) scale(0.3);
    opacity: 0;
  }
}

.feed-text {
  position: absolute;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.8rem;
  font-weight: 600;
  color: #4CAF50;
  animation: textFade 0.8s ease-out forwards;
}

@keyframes textFade {
  0% { opacity: 1; transform: translateX(-50%) translateY(0); }
  100% { opacity: 0; transform: translateX(-50%) translateY(-20px); }
}

/* 过渡 */
.feed-effect-enter-active,
.feed-effect-leave-active {
  transition: all 0.5s ease;
}

.feed-effect-enter-from,
.feed-effect-leave-to {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.8);
}

/* 📱 响应式 - AAA游戏级移动体验 */
@media (max-width: 768px) {
  .hud {
    gap: 0.7rem;
    padding: 0.65rem 0.8rem;
    height: 56px;
    border-radius: 20px;
  }
  
  .pet {
    width: 48px;
    height: 48px;
    min-width: 48px;
    min-height: 48px;
    max-width: 48px;
    max-height: 48px;
  }
  
  .pet::before {
    inset: -5px;
  }
  
  .bubble {
    padding: 0.35rem 0.6rem;
    height: 44px;
    border-radius: 12px;
  }
  
  .bubble-icon {
    font-size: 1.1em;
    width: 20px;
    height: 20px;
    min-width: 20px;
    min-height: 20px;
    max-width: 20px;
    max-height: 20px;
  }
  
  .bubble-content {
    height: 36px;
  }
  
  .bubble-text {
    font-size: 0.75rem;
    line-height: 1.3;
    letter-spacing: 0.25px;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    padding: 0.25rem 0;
  }
}

@media (max-width: 480px) {
  .hud {
    gap: 0.55rem;
    padding: 0.5rem 0.65rem;
    height: 52px;
    border-radius: 18px;
  }
  
  .pet {
    width: 44px;
    height: 44px;
    min-width: 44px;
    min-height: 44px;
    max-width: 44px;
    max-height: 44px;
  }
  
  .pet::before {
    inset: -4px;
  }
  
  .bubble {
    padding: 0.3rem 0.55rem;
    height: 40px;
    border-radius: 11px;
  }
  
  .bubble-icon {
    font-size: 1.05em;
    width: 18px;
    height: 18px;
    min-width: 18px;
    min-height: 18px;
    max-width: 18px;
    max-height: 18px;
  }
  
  .bubble-content {
    height: 32px;
  }
  
  .bubble-text {
    font-size: 0.7rem;
    line-height: 1.25;
    letter-spacing: 0.2px;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    padding: 0.2rem 0;
  }
  
  .bubble-progress {
    height: 2.5px;
  }
}

/* 🎮 performance tuning */
.hud,
.pet,
.bubble {
  will-change: transform, box-shadow;
}

/* 🌟 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .hud::before,
  .pet::before,
  .bubble::before,
  .bubble-icon,
  .bubble-progress {
    animation: none !important;
  }
  
  .hud,
  .pet,
  .bubble {
    transition: none !important;
  }
}
</style>
<template>
  <v-dialog
    v-model="isOpen"
    max-width="700px"
    max-height="90vh"
    transition="dialog-bottom-transition"
    :scrim="true"
    persistent
    scrollable
    class="timezone-modal-wrapper"
  >
    <div class="timezone-compare-modal-aaa" role="dialog" aria-modal="true" aria-labelledby="timezone-modal-title">
      <!-- 🎮 背景特效层 -->
      <div class="modal-background-effects">
        <div class="cosmic-particles"></div>
        <div class="energy-waves"></div>
        <div class="hologram-grid"></div>
      </div>

      <!-- 🎯 关闭按钮 -->
      <button 
        class="close-btn-aaa" 
        @click="closeModal" 
        @keydown.enter="closeModal"
        @keydown.space.prevent="closeModal"
        aria-label="Close timezone comparison modal"
        tabindex="0"
      >
        <span class="close-icon">✕</span>
        <div class="btn-glow"></div>
      </button>

      <!-- 📜 Scrollable Content Container -->
      <div class="modal-content-scrollable">
        <!-- 🎮 标题区 -->
        <div class="modal-header-aaa">
          <div class="title-icon-badge" aria-hidden="true">🌍</div>
          <h2 id="timezone-modal-title" class="modal-title-aaa">Time Zone Sync</h2>
          <p class="modal-subtitle">Your Love Across Time & Space</p>
        </div>      <!-- 🕐 双时钟对比区 - 精准游戏化 -->
      <div class="dual-clock-display">
        <!-- 左侧：Your Time -->
        <div class="clock-card your-clock">
          <div class="card-glow"></div>
          <div class="clock-label">
            <span class="label-icon">👤</span>
            <span class="label-text">You</span>
          </div>
          <div class="large-time-display">{{ formattedYourTime }}</div>
          <div class="timezone-badge">{{ yourTimezone }}</div>
          <div class="date-display">{{ formattedYourDate }}</div>
          
          <!-- 🎮 实时时钟表盘 -->
          <div class="mini-clock-dial">
            <div class="clock-center"></div>
            <div v-for="i in 12" :key="`your-${i}`" class="clock-tick" :style="getTickStyle(i)"></div>
            <div class="clock-hand hour-hand" :style="{ transform: `rotate(${yourHourRotation}deg)` }"></div>
            <div class="clock-hand minute-hand" :style="{ transform: `rotate(${yourMinuteRotation}deg)` }"></div>
          </div>
        </div>

        <!-- 🎯 中间：时差指示器 -->
        <div class="time-diff-indicator">
          <div class="diff-icon-container">
            <div class="pulse-ring"></div>
            <div class="diff-icon">⏱️</div>
          </div>
          <div class="diff-value">{{ timeDifferenceText }}</div>
          <div class="diff-label">Time Difference</div>
          
          <!-- 🎮 连接线动画 -->
          <div class="connection-line">
            <div class="line-glow"></div>
            <div class="line-particles">
              <span v-for="i in 5" :key="i" class="particle" :style="{ '--delay': `${i * 0.2}s` }"></span>
            </div>
          </div>
        </div>

        <!-- 右侧：Partner Time -->
        <div class="clock-card partner-clock">
          <div class="card-glow"></div>
          <div class="clock-label">
            <span class="label-icon">💝</span>
            <span class="label-text">Partner</span>
          </div>
          <div class="large-time-display">{{ formattedPartnerTime }}</div>
          <div class="timezone-badge partner-badge">{{ partnerTimezone }}</div>
          <div class="date-display">{{ formattedPartnerDate }}</div>
          
          <!-- 🎮 实时时钟表盘 -->
          <div class="mini-clock-dial">
            <div class="clock-center"></div>
            <div v-for="i in 12" :key="`partner-${i}`" class="clock-tick" :style="getTickStyle(i)"></div>
            <div class="clock-hand hour-hand" :style="{ transform: `rotate(${partnerHourRotation}deg)` }"></div>
            <div class="clock-hand minute-hand" :style="{ transform: `rotate(${partnerMinuteRotation}deg)` }"></div>
          </div>
        </div>
      </div>

      <!-- 🎮 智能建议区 - Kinny游戏化提示 -->
      <div class="kinny-suggestions">
        <div class="suggestion-header">
          <span class="kinny-avatar">🐾</span>
          <span class="suggestion-title">Kinny's Perfect Time Sync</span>
        </div>
        
        <div class="suggestion-cards">
          <!-- 🎯 晚上通话时间 -->
          <div class="suggestion-card">
            <div class="card-icon">🌙</div>
            <div class="card-content">
              <h4>Your Evening (8pm)</h4>
              <p class="highlight-time">{{ bestCallTime }}</p>
              <span class="card-hint">Good time to connect</span>
            </div>
          </div>

          <!-- 🎯 睡觉时间对比 -->
          <div class="suggestion-card">
            <div class="card-icon">😴</div>
            <div class="card-content">
              <h4>Your Bedtime (11pm)</h4>
              <p class="highlight-time">{{ sleepScheduleHint }}</p>
              <span class="card-hint">Don't disturb then</span>
            </div>
          </div>

          <!-- 🎯 当前状态或午餐时间 -->
          <div class="suggestion-card">
            <div class="card-icon">{{ partnerIsOnline ? '🟢' : '�️' }}</div>
            <div class="card-content">
              <h4>{{ partnerIsOnline ? 'Online Status' : 'Your Lunch (12pm)' }}</h4>
              <p class="highlight-time">{{ gameTogetherTime }}</p>
              <span class="card-hint">{{ partnerIsOnline ? 'Available now' : 'Midday reference' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 🎯 快速转换器 -->
      <div class="quick-converter">
        <div class="converter-title">Quick Time Converter</div>
        <div class="converter-input-row">
          <div class="time-input-group">
            <label>If it's</label>
            <input 
              v-model="convertHour" 
              type="number" 
              min="0" 
              max="23" 
              class="time-input"
              placeholder="14"
            />
            <span>:00 for you</span>
          </div>
          <div class="arrow-icon">→</div>
          <div class="converted-result">
            <span>It's <strong>{{ convertedPartnerTime }}</strong> for partner</span>
          </div>
        </div>
      </div>

        <!-- 🎮 关闭按钮 -->
        <div class="modal-footer">
          <button 
            class="action-btn-aaa" 
            @click="closeModal"
            @keydown.enter="closeModal"
            @keydown.space.prevent="closeModal"
            tabindex="0"
          >
            <span class="btn-text">Got It!</span>
            <div class="btn-shine"></div>
          </button>
        </div>
      </div>
      <!-- End of scrollable content -->
    </div>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

interface Props {
  modelValue: boolean
  yourTimezone: string
  partnerTimezone: string
  partnerIsOnline?: boolean  // 🎯 伴侣是否在线
  partnerName?: string       // 🎯 伴侣名字
}

const props = withDefaults(defineProps<Props>(), {
  partnerIsOnline: false,
  partnerName: 'Partner'
})
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 当前时间（每秒更新）
const currentTime = ref(new Date())
let intervalId: number | null = null

// 🎯 格式化时间显示
const formattedYourTime = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.yourTimezone }))
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: true 
    })
  } catch (e) {
    return 'N/A'
  }
})

const formattedPartnerTime = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.partnerTimezone }))
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: true 
    })
  } catch (e) {
    return 'N/A'
  }
})

// 🎯 格式化日期
const formattedYourDate = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.yourTimezone }))
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    })
  } catch (e) {
    return 'N/A'
  }
})

const formattedPartnerDate = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.partnerTimezone }))
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    })
  } catch (e) {
    return 'N/A'
  }
})

// 🎯 计算时差
const timeDifferenceHours = computed(() => {
  try {
    const yourDate = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.yourTimezone }))
    const partnerDate = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.partnerTimezone }))
    const diffMs = partnerDate.getTime() - yourDate.getTime()
    return Math.round(diffMs / (1000 * 60 * 60))
  } catch (e) {
    return 0
  }
})

const timeDifferenceText = computed(() => {
  const diff = timeDifferenceHours.value
  if (diff === 0) return 'Same Time! 🎉'
  const absDiff = Math.abs(diff)
  const ahead = diff > 0 ? 'ahead' : 'behind'
  return `${absDiff} hour${absDiff !== 1 ? 's' : ''} ${ahead}`
})

// 🎯 时钟指针角度计算
const yourHourRotation = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.yourTimezone }))
    const hours = date.getHours() % 12
    const minutes = date.getMinutes()
    return (hours * 30) + (minutes * 0.5)
  } catch (e) {
    return 0
  }
})

const yourMinuteRotation = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.yourTimezone }))
    return date.getMinutes() * 6
  } catch (e) {
    return 0
  }
})

const partnerHourRotation = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.partnerTimezone }))
    const hours = date.getHours() % 12
    const minutes = date.getMinutes()
    return (hours * 30) + (minutes * 0.5)
  } catch (e) {
    return 0
  }
})

const partnerMinuteRotation = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.partnerTimezone }))
    return date.getMinutes() * 6
  } catch (e) {
    return 0
  }
})

// 🎯 刻度位置计算
const getTickStyle = (index: number) => {
  const angle = (index * 30) - 90
  const radius = 42
  const x = 50 + radius * Math.cos(angle * Math.PI / 180)
  const y = 50 + radius * Math.sin(angle * Math.PI / 180)
  return {
    left: `${x}%`,
    top: `${y}%`
  }
}

// 🎮 Kinny智能建议 - 精准改善：简单实用，基于真实数据
const bestCallTime = computed(() => {
  const diff = timeDifferenceHours.value
  
  // 🎯 简单直接：你8pm时她几点
  if (diff === 0) {
    return 'Your 8pm = Their 8pm ✨'
  } else if (diff > 0) {
    const theirTime = (20 + diff) % 24
    return `Your 8pm = Their ${theirTime > 12 ? theirTime - 12 : theirTime}${theirTime >= 12 ? 'pm' : 'am'}`
  } else {
    const theirTime = (20 + diff + 24) % 24
    return `Your 8pm = Their ${theirTime > 12 ? theirTime - 12 : theirTime}${theirTime >= 12 ? 'pm' : 'am'}`
  }
})

const sleepScheduleHint = computed(() => {
  const diff = timeDifferenceHours.value
  
  // 🎯 实用提醒：你睡觉时她几点
  if (diff === 0) {
    return 'Same time - easy! 😴'
  } else if (diff > 0) {
    const theirTime = (23 + diff) % 24
    return `Your 11pm = Their ${theirTime > 12 ? theirTime - 12 : theirTime}${theirTime >= 12 ? 'pm' : 'am'}`
  } else {
    const theirTime = (23 + diff + 24) % 24
    return `Your 11pm = Their ${theirTime > 12 ? theirTime - 12 : theirTime}${theirTime >= 12 ? 'pm' : 'am'}`
  }
})

const gameTogetherTime = computed(() => {
  // 🎯 显示伴侣当前状态（如果在线）
  if (props.partnerIsOnline) {
    return `${props.partnerName} is online NOW! 🟢`
  }
  
  // 🎯 否则显示午餐时间对比
  const diff = timeDifferenceHours.value
  if (diff === 0) {
    return 'Your 12pm = Their 12pm'
  } else if (diff > 0) {
    const theirTime = (12 + diff) % 24
    return `Your 12pm = Their ${theirTime > 12 ? theirTime - 12 : theirTime}${theirTime >= 12 ? 'pm' : 'am'}`
  } else {
    const theirTime = (12 + diff + 24) % 24
    return `Your 12pm = Their ${theirTime > 12 ? theirTime - 12 : theirTime}${theirTime >= 12 ? 'pm' : 'am'}`
  }
})

// 🎯 快速时间转换
const convertHour = ref(14)
const convertedPartnerTime = computed(() => {
  try {
    const hour = parseInt(convertHour.value.toString()) || 0
    const adjustedHour = hour + timeDifferenceHours.value
    const finalHour = ((adjustedHour % 24) + 24) % 24
    const period = finalHour >= 12 ? 'PM' : 'AM'
    const displayHour = finalHour % 12 || 12
    return `${displayHour}:00 ${period}`
  } catch (e) {
    return 'N/A'
  }
})

// 🎯 关闭Modal
const closeModal = () => {
  isOpen.value = false
}

// 🎯 Keyboard accessibility - ESC key to close
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && isOpen.value) {
    closeModal()
  }
}

// 🎯 Focus management for accessibility
const focusFirstElement = () => {
  // Wait for next tick to ensure DOM is updated
  setTimeout(() => {
    const closeBtn = document.querySelector('.close-btn-aaa') as HTMLElement
    if (closeBtn) {
      closeBtn.focus()
    }
  }, 100)
}

// 🎯 Watch for modal open/close to manage focus and track events
watch(isOpen, (newValue) => {
  if (newValue) {
    // Modal opened - focus first interactive element
    focusFirstElement()
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden'
  } else {
    // Modal closed - restore body scroll
    document.body.style.overflow = ''
  }
})

// 生命周期
onMounted(() => {
  intervalId = window.setInterval(() => {
    currentTime.value = new Date()
  }, 1000)
  
  // Add keyboard listener for ESC key
  window.addEventListener('keydown', handleKeyDown)
  
  // If modal is already open on mount, manage focus
  if (isOpen.value) {
    focusFirstElement()
    document.body.style.overflow = 'hidden'
  }
})

onUnmounted(() => {
  if (intervalId !== null) {
    clearInterval(intervalId)
  }
  
  // Clean up keyboard listener
  window.removeEventListener('keydown', handleKeyDown)
  
  // Restore body scroll on unmount
  document.body.style.overflow = ''
})
</script>

<style scoped lang="scss">
// 🎮 AAA级时区对比Modal - Kinny游戏化体验
.timezone-modal-wrapper :deep(.v-overlay__scrim) {
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(12px);
}

.timezone-compare-modal-aaa {
  position: relative;
  background: linear-gradient(145deg, 
    rgba(15, 10, 30, 0.98) 0%,
    rgba(25, 15, 45, 0.96) 50%,
    rgba(35, 20, 55, 0.98) 100%
  );
  border-radius: 28px;
  border: 3px solid rgba(255, 182, 193, 0.4);
  box-shadow: 
    0 25px 80px rgba(0, 0, 0, 0.6),
    inset 0 2px 0 rgba(255, 255, 255, 0.15),
    0 0 100px rgba(255, 107, 157, 0.3);
  padding: 0;
  overflow: hidden;
  animation: modalSlideIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

// 🎯 Scrollable content container - 精准弹性高度设计
.modal-content-scrollable {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 32px;
  
  // 🎯 Custom scrollbar styling for better UX
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, 
      rgba(255, 107, 157, 0.5),
      rgba(255, 107, 157, 0.3)
    );
    border-radius: 4px;
    transition: background 0.3s ease;
    
    &:hover {
      background: linear-gradient(135deg, 
        rgba(255, 107, 157, 0.7),
        rgba(255, 107, 157, 0.5)
      );
    }
  }
  
  // Firefox scrollbar
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 107, 157, 0.5) rgba(255, 255, 255, 0.05);
}

@keyframes modalSlideIn {
  0% { 
    opacity: 0; 
    transform: translateY(50px) scale(0.9); 
  }
  100% { 
    opacity: 1; 
    transform: translateY(0) scale(1); 
  }
}

// 🎨 背景特效层
.modal-background-effects {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  border-radius: 28px;
}

.cosmic-particles {
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(2px 2px at 20% 30%, rgba(255, 255, 255, 0.3), transparent),
    radial-gradient(2px 2px at 60% 70%, rgba(255, 182, 193, 0.3), transparent),
    radial-gradient(1px 1px at 50% 50%, rgba(255, 107, 157, 0.3), transparent);
  background-size: 200px 200px;
  animation: particleFloat 20s linear infinite;
}

@keyframes particleFloat {
  0% { background-position: 0 0; }
  100% { background-position: 200px 200px; }
}

.energy-waves {
  position: absolute;
  inset: -50%;
  background: conic-gradient(from 0deg,
    transparent 0deg,
    rgba(255, 107, 157, 0.1) 90deg,
    transparent 180deg,
    rgba(138, 180, 248, 0.1) 270deg,
    transparent 360deg
  );
  animation: energyRotate 15s linear infinite;
}

@keyframes energyRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.hologram-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255, 182, 193, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 182, 193, 0.05) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.3;
}

// 🎯 关闭按钮 - Fixed position, won't scroll
.close-btn-aaa {
  position: fixed;
  top: 16px;
  right: 16px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, 
    rgba(255, 107, 157, 0.2), 
    rgba(255, 107, 157, 0.1)
  );
  border: 2px solid rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1000;
  
  &:hover, &:focus {
    background: linear-gradient(135deg, 
      rgba(255, 107, 157, 0.4), 
      rgba(255, 107, 157, 0.2)
    );
    border-color: rgba(255, 107, 157, 0.6);
    transform: rotate(90deg) scale(1.1);
    outline: 2px solid rgba(255, 107, 157, 0.8);
    outline-offset: 2px;
  }
  
  &:focus-visible {
    outline: 3px solid rgba(255, 107, 157, 1);
    outline-offset: 3px;
  }
}

.close-icon {
  font-size: 20px;
  color: #ffffff;
  font-weight: 700;
}

// 🎮 标题区
.modal-header-aaa {
  text-align: center;
  margin-bottom: 32px;
  position: relative;
  z-index: 10;
}

.title-icon-badge {
  font-size: 48px;
  margin-bottom: 12px;
  filter: drop-shadow(0 4px 12px rgba(255, 182, 193, 0.6));
  animation: iconFloat 3s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-8px) scale(1.05); }
}

.modal-title-aaa {
  font-size: clamp(24px, 3vw, 32px);
  font-weight: 900;
  font-family: 'SF Pro Display', -apple-system, sans-serif;
  background: linear-gradient(135deg, 
    #ffffff, 
    rgba(255, 182, 193, 0.9),
    rgba(255, 107, 157, 0.9)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
  text-shadow: 0 4px 12px rgba(255, 107, 157, 0.4);
}

.modal-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
  letter-spacing: 1px;
}

// 🕐 双时钟对比区
.dual-clock-display {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 24px;
  margin-bottom: 32px;
  position: relative;
  z-index: 10;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

.clock-card {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.12) 0%,
    rgba(255, 182, 193, 0.08) 100%
  );
  border-radius: 20px;
  border: 2px solid rgba(255, 255, 255, 0.25);
  padding: 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(20px);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    border-color: rgba(255, 182, 193, 0.5);
    box-shadow: 
      0 12px 40px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.4);
  }
}

.card-glow {
  position: absolute;
  inset: -20px;
  background: radial-gradient(circle, rgba(255, 182, 193, 0.3) 0%, transparent 70%);
  filter: blur(20px);
  opacity: 0.5;
  animation: cardGlow 3s ease-in-out infinite;
}

@keyframes cardGlow {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.7; }
}

.clock-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.label-icon {
  font-size: 20px;
}

.large-time-display {
  font-size: clamp(20px, 3vw, 28px);
  font-weight: 900;
  font-family: 'SF Mono', monospace;
  color: #ffffff;
  text-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.6),
    0 0 20px rgba(255, 182, 193, 0.4);
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.timezone-badge {
  display: inline-block;
  padding: 6px 14px;
  background: linear-gradient(135deg, 
    rgba(255, 107, 157, 0.25),
    rgba(255, 107, 157, 0.15)
  );
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  font-size: 11px;
  font-weight: 800;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.partner-badge {
  background: linear-gradient(135deg, 
    rgba(138, 180, 248, 0.25),
    rgba(138, 180, 248, 0.15)
  );
}

.date-display {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 600;
  margin-bottom: 16px;
}

// 🎯 Mini时钟表盘
.mini-clock-dial {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, 
    rgba(255, 255, 255, 0.2),
    rgba(255, 182, 193, 0.1)
  );
  border: 2px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    inset 0 2px 8px rgba(0, 0, 0, 0.2),
    0 4px 12px rgba(0, 0, 0, 0.15);
}

.clock-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b9d, #ffa07a);
  box-shadow: 0 0 8px rgba(255, 107, 157, 0.6);
  z-index: 10;
}

.clock-tick {
  position: absolute;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.8);
  transform: translate(-50%, -50%);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.clock-hand {
  position: absolute;
  bottom: 50%;
  left: 50%;
  transform-origin: bottom center;
  border-radius: 999px;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.hour-hand {
  width: 3px;
  height: 28%;
  background: linear-gradient(to top, rgba(255, 107, 157, 0.9), rgba(255, 107, 157, 0.7));
  margin-left: -1.5px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.minute-hand {
  width: 2px;
  height: 38%;
  background: linear-gradient(to top, rgba(255, 160, 122, 0.95), rgba(255, 160, 122, 0.75));
  margin-left: -1px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
}

// 🎯 时差指示器
.time-diff-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  position: relative;
  
  @media (max-width: 768px) {
    order: -1;
    padding: 12px 0;
  }
}

.diff-icon-container {
  position: relative;
  margin-bottom: 12px;
}

.pulse-ring {
  position: absolute;
  inset: -8px;
  border: 2px solid rgba(255, 107, 157, 0.5);
  border-radius: 50%;
  animation: pulseRing 2s ease-in-out infinite;
}

@keyframes pulseRing {
  0%, 100% { 
    transform: scale(1); 
    opacity: 0.5; 
  }
  50% { 
    transform: scale(1.3); 
    opacity: 0; 
  }
}

.diff-icon {
  font-size: 36px;
  filter: drop-shadow(0 4px 12px rgba(255, 107, 157, 0.6));
}

.diff-value {
  font-size: 18px;
  font-weight: 900;
  color: #ffffff;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
  margin-bottom: 4px;
}

.diff-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.connection-line {
  display: none;
  @media (min-width: 769px) {
    display: block;
    position: absolute;
    top: 50%;
    left: -60px;
    right: -60px;
    height: 2px;
    background: linear-gradient(90deg, 
      transparent,
      rgba(255, 182, 193, 0.5) 30%,
      rgba(255, 182, 193, 0.5) 70%,
      transparent
    );
  }
}

.line-particles {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.particle {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 107, 157, 0.8);
  box-shadow: 0 0 8px rgba(255, 107, 157, 0.6);
  animation: particleMove 2s ease-in-out infinite;
  animation-delay: var(--delay);
}

@keyframes particleMove {
  0%, 100% { transform: translateX(-20px); opacity: 0; }
  50% { opacity: 1; }
}

// 🎮 Kinny建议区
.kinny-suggestions {
  background: linear-gradient(135deg, 
    rgba(138, 180, 248, 0.15),
    rgba(99, 102, 241, 0.1)
  );
  border-radius: 20px;
  border: 2px solid rgba(138, 180, 248, 0.3);
  padding: 20px;
  margin-bottom: 24px;
  position: relative;
  z-index: 10;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.kinny-avatar {
  font-size: 32px;
  filter: drop-shadow(0 2px 8px rgba(138, 180, 248, 0.6));
}

.suggestion-title {
  font-size: 18px;
  font-weight: 800;
  color: #ffffff;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
}

.suggestion-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.suggestion-card {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 12px;
  display: flex;
  gap: 10px;
  align-items: flex-start;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(138, 180, 248, 0.4);
    transform: translateY(-2px);
  }
}

.card-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  
  h4 {
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 4px 0;
  }
}

.highlight-time {
  font-size: 14px;
  font-weight: 800;
  color: rgba(138, 180, 248, 0.9);
  margin: 4px 0;
}

.card-hint {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

// 🎯 快速转换器
.quick-converter {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 16px;
  margin-bottom: 24px;
  position: relative;
  z-index: 10;
}

.converter-title {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.converter-input-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.time-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  
  label {
    font-weight: 600;
  }
}

.time-input {
  width: 60px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  color: #ffffff;
  font-size: 16px;
  font-weight: 700;
  text-align: center;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: rgba(255, 107, 157, 0.6);
    background: rgba(255, 255, 255, 0.15);
  }
}

.arrow-icon {
  font-size: 20px;
  color: rgba(255, 182, 193, 0.8);
}

.converted-result {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  
  strong {
    color: rgba(255, 107, 157, 0.9);
    font-weight: 900;
    font-size: 16px;
  }
}

// 🎮 底部按钮
.modal-footer {
  text-align: center;
  position: relative;
  z-index: 10;
}

.action-btn-aaa {
  position: relative;
  padding: 14px 40px;
  background: linear-gradient(135deg, 
    rgba(255, 107, 157, 0.9),
    rgba(255, 107, 157, 0.7)
  );
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-radius: 16px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 
    0 8px 24px rgba(255, 107, 157, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  
  &:hover {
    transform: translateY(-2px) scale(1.05);
    box-shadow: 
      0 12px 32px rgba(255, 107, 157, 0.5),
      inset 0 1px 0 rgba(255, 255, 255, 0.4);
    border-color: rgba(255, 255, 255, 0.6);
  }
  
  &:active {
    transform: translateY(0) scale(1);
  }
}

.btn-text {
  position: relative;
  z-index: 2;
  font-size: 16px;
  font-weight: 800;
  color: #ffffff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: 1px;
}

.btn-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.3), 
    transparent
  );
  animation: btnShine 3s ease-in-out infinite;
}

@keyframes btnShine {
  0%, 100% { left: -100%; }
  50% { left: 100%; }
}

// 📱 响应式tuning - 精准弹性设计
@media (max-width: 768px) {
  .timezone-compare-modal-aaa {
    max-height: 95vh;
    border-radius: 20px;
  }
  
  .modal-content-scrollable {
    padding: 24px 16px;
  }
  
  .close-btn-aaa {
    top: 12px;
    right: 12px;
    width: 36px;
    height: 36px;
  }
  
  .modal-header-aaa {
    margin-bottom: 20px;
  }
  
  .modal-title-aaa {
    font-size: 24px;
  }
  
  .dual-clock-display {
    margin-bottom: 20px;
  }
  
  .clock-card {
    padding: 14px;
  }
  
  .large-time-display {
    font-size: 20px;
  }
  
  .suggestion-cards {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .converter-input-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .kinny-suggestions {
    padding: 16px;
  }
  
  .quick-converter {
    padding: 14px;
  }
}

// 📱 Extra small screens
@media (max-width: 480px) {
  .timezone-compare-modal-aaa {
    max-height: 98vh;
    border-radius: 16px;
    border-width: 2px;
  }
  
  .modal-content-scrollable {
    padding: 20px 12px;
  }
  
  .title-icon-badge {
    font-size: 36px;
  }
  
  .modal-title-aaa {
    font-size: 20px;
  }
  
  .modal-subtitle {
    font-size: 12px;
  }
  
  .large-time-display {
    font-size: 18px;
  }
  
  .mini-clock-dial {
    width: 70px;
    height: 70px;
  }
  
  .diff-icon {
    font-size: 28px;
  }
  
  .diff-value {
    font-size: 16px;
  }
}

// 🎯 Landscape mode optimization
@media (max-height: 600px) and (orientation: landscape) {
  .timezone-compare-modal-aaa {
    max-height: 98vh;
  }
  
  .modal-content-scrollable {
    padding: 16px;
  }
  
  .modal-header-aaa {
    margin-bottom: 16px;
  }
  
  .dual-clock-display {
    margin-bottom: 16px;
  }
  
  .kinny-suggestions {
    padding: 14px;
  }
  
  .suggestion-cards {
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }
  
  .quick-converter {
    padding: 12px;
  }
  
  .modal-footer {
    margin-top: 16px;
  }
}
</style>

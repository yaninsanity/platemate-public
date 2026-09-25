<template>
  <Teleport to="body">
    <div class="slot-machine-overlay" v-if="isVisible" @click.self="onOverlayClick">
      <div class="slot-machine-container">
      <!-- 🎰 Header -->
      <div class="slot-machine-header">
        <h1 class="slot-title">🐾 Kinny is finding foods</h1>
        <p class="slot-subtitle" :class="{ 'cooldown-notice': onCooldown }">
          {{ onCooldown ? 'Kinny is resting!' : 'Help Kinny find delicious foods!' }}
        </p>
      </div>
      
      <!-- ⏰ Cooldown Display -->
      <div v-if="onCooldown" class="cooldown-display">
        <div class="cooldown-card">
          <div class="cooldown-icon">😴</div>
          <div class="cooldown-text">
            <h3>Kinny is Resting</h3>
            <div class="cooldown-timer">{{ cooldownTime }}</div>
            <p class="cooldown-hint">Kinny will find more foods soon!</p>
          </div>
        </div>
        
    <div v-if="slotPreview" class="preview-reward">
          <div class="preview-card">
      <div class="preview-icon">🧭</div>
            <div class="preview-text">
              <h4>Next Adventure</h4>
              <div class="preview-fruit">�️ Kinny will find food</div>
              <div class="preview-name">Delicious Kinny Food is waiting!</div>
            </div>
          </div>
        </div>
        
        <button @click="onClose" class="cooldown-close-btn">
          <span>🐾</span> Got it!
        </button>
      </div>
      
      <!-- 🎰 Slot Machine -->
      <div v-else>
        <!-- 💡 清晰的提示信息 -->
        <div v-if="!showResult" class="game-hint">
          <div class="hint-icon">🎯</div>
          <div class="hint-text">
            <strong>Kinny is searching for 3 foods!</strong>
            <p>Watch carefully to see what Kinny finds...</p>
          </div>
        </div>
        
        <!-- 🎯 3-Slot Reels - HIDE when results show -->
        <div v-if="!showResult" class="slot-reels-container">
          <div class="slot-reels">
            <div 
              v-for="(reel, index) in reels" 
              :key="index"
              class="slot-reel"
              :class="{
                'spinning': !reel.stopped && isSpinning,
                'stopped': reel.stopped,
                'winning': reel.isWinning && showResult,
                'no-reward': reel.showNoReward && showResult
              }"
            >
              <!-- Reel Frame -->
              <div class="reel-frame" :class="{ 'frame-glow': reel.stopped && showResult }"></div>
              
              <!-- Reel Symbols -->
              <div 
                class="reel-symbols" 
                :style="{ 
                  transform: reel.stopped 
                    ? `translateY(${reel.position}px)` 
                    : `translateY(${reel.position}px)` 
                }"
              >
                <div 
                  v-for="(symbol, symbolIndex) in reel.symbols" 
                  :key="symbolIndex"
                  class="symbol"
                  :class="{
                    'final-symbol': reel.finalSymbolIndex === symbolIndex && reel.stopped,
                    'winning-symbol': reel.isWinning && reel.finalSymbolIndex === symbolIndex && showResult
                  }"
                >
                  {{ symbol }}
                </div>
              </div>
              
              <!-- Reel Label - 更清晰的标签 -->
              <div class="reel-label">
                <span v-if="!reel.stopped">🔍</span>
                <span v-else-if="reel.isWinning">✅</span>
                <span v-else>—</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 🎯 SIMPLE Result Display -->
        <div v-if="showResult" class="result-display-simple">
          
          <!-- Jackpot Badge (if applicable) -->
          <div v-if="isJackpot" class="jackpot-badge">
            🎉 JACKPOT! 🎉
          </div>
          
          <!-- Simple: You Got -->
          <div class="simple-reward-card">
            <div class="reward-title">You Got:</div>
            
            <div 
              v-for="reward in winningSlots.filter(s => s.amount > 0)" 
              :key="reward.slot_id"
              class="simple-reward-item"
            >
              <div class="reward-emoji-big">{{ reward.emoji }}</div>
              <div class="reward-info">
                <div class="reward-name-big">{{ reward.name }}</div>
                <div class="reward-amount-big">× {{ reward.amount }}</div>
              </div>
            </div>
          </div>

        </div>
        
        <!-- 🎮 Loading State -->
        <div v-else-if="isSpinning" class="spinning-display">
          <h2 class="rolling-text">
            Kinny is searching<span class="dots"><span class="animated-dots">...</span></span>
          </h2>
          <p>🐾 Watch Kinny explore!</p>
        </div>
        
        <!-- 🎯 Actions -->
        <div v-if="showResult" class="slot-actions">
          <button 
            @click="onClose" 
            class="claim-btn"
            :class="{ 'jackpot': isJackpot }"
          >
            <span v-if="isJackpot">🎉</span>
            <span v-else>✨</span>
            {{ isJackpot ? 'Amazing! Kinny is so happy!' : 'Add to inventory' }}
          </button>
        </div>
      </div>
    </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

// 🎰 Slot结果接口
interface SlotResult {
  slot_id: number
  has_reward: boolean
  food_type?: string
  name?: string
  emoji: string
  amount: number
  base_amount?: number
  multiplier?: number
  bonus_text?: string
  effect?: string
}

// 🎯 预览接口
interface SlotPreview {
  next_reward_locked: boolean
  next_possible_reward: string
  next_possible_emoji: string
  next_possible_amount: number
  preview_message: string
  cooldown_display: boolean
}

// 🎰 动画配置
interface SlotAnimation {
  num_slots: number
  winning_slots: number
  spin_duration: number
  reel_stop_delays: number[]
  celebration_duration: number
  jackpot_mode: boolean
}

// 🎯 转轮接口
interface Reel {
  symbols: string[]
  stopped: boolean
  position: number
  isWinning: boolean
  showNoReward: boolean
  finalSymbolIndex: number
  winAmount: number
  bonusText?: string
  multiplier?: number
  multiplierClass?: string
}

interface Props {
  isVisible: boolean
  slotResults?: SlotResult[]
  slotAnimation?: SlotAnimation
  slotPreview?: SlotPreview
  onCooldown?: boolean
  cooldownTime?: string
  totalSpins?: number
}

interface Emits {
  (e: 'close'): void
  (e: 'claim'): void
  (e: 'refresh-inventory'): void
}

const props = withDefaults(defineProps<Props>(), {
  isVisible: false,
  slotResults: () => [],
  slotAnimation: () => ({
    num_slots: 3,
    winning_slots: 0,
    spin_duration: 3000,
    reel_stop_delays: [1000, 2000, 3000],
    celebration_duration: 2000,
    jackpot_mode: false
  }),
  slotPreview: undefined,
  onCooldown: false,
  cooldownTime: '',
  totalSpins: 0
})

const emit = defineEmits<Emits>()

// 🎰 状态
const isSpinning = ref(true)
const showResult = ref(false)
// 🎨 性能模式 - minimal: 最少动画, balanced: 平衡, full: 全部动画
const performanceMode = ref('minimal') // 默认使用最少动画以提升性能

// 🎰 转轮
const foodEmojis = ['🍎', '🍌', '🍊', '🍓', '🍇', '🍉', '🍍', '🍒']
const reels = ref<Reel[]>([
  { 
    symbols: [...foodEmojis, ...foodEmojis],
    stopped: false,
    position: 0,
    isWinning: false,
    showNoReward: false,
  finalSymbolIndex: 0,
    winAmount: 0,
  bonusText: '',
  multiplier: 0,
    multiplierClass: 'normal'
  },
  { 
    symbols: [...foodEmojis, ...foodEmojis],
    stopped: false,
    position: 0,
    isWinning: false,
    showNoReward: false,
    finalSymbolIndex: 0,
    winAmount: 0,
    multiplierClass: 'normal'
  },
  { 
    symbols: [...foodEmojis, ...foodEmojis],
    stopped: false,
    position: 0,
    isWinning: false,
    showNoReward: false,
    finalSymbolIndex: 0,
    winAmount: 0,
    multiplierClass: 'normal'
  }
])

// 🎯 computed
const winningSlots = computed(() => {
  return (props.slotResults || []).filter(slot => slot.has_reward)
})

const totalWinningSlots = computed(() => {
  return winningSlots.value.length
})

const isJackpot = computed(() => {
  return props.slotAnimation?.jackpot_mode || totalWinningSlots.value >= 3
})

const totalFruitsFound = computed(() => {
  // 总数由后端写入第一个正数amount的slot
  const firstSlot = winningSlots.value.find(slot => (slot.amount || 0) > 0)
  return firstSlot ? firstSlot.amount : 0
})

// 🎰 启动动画 - performance tuning版本
const startSlotMachine = () => {
  if (props.onCooldown) return
  
  // 减少日志输出以提升性能
  if (import.meta.env.DEV) {
    console.log('🎰 Starting slot machine')
  }
  
  isSpinning.value = true
  showResult.value = false
  
  // 重置转轮 - 从随机位置开始，营造真实感
  reels.value.forEach((reel, index) => {
    reel.stopped = false
    reel.isWinning = false
    reel.showNoReward = false
    // 随机起始位置，但会精确停在目标位置
    reel.position = -(Math.random() * 500 + 100) // 随机起始偏移
    reel.winAmount = 0
    reel.bonusText = ''
    reel.multiplier = 0
    reel.multiplierClass = 'normal'
  })
  
  // 🎯 处理后端返回的结果 - 这是预定的结局
  const slotResults = props.slotResults || []
  console.log('🎰 [Animation] ========== SLOT MACHINE START ==========')
  console.log('🎰 [Animation] Backend returned slotResults:', JSON.stringify(slotResults, null, 2))
  console.log('🎰 [Animation] Emojis in order:', slotResults.map(r => `[${r.slot_id}] ${r.emoji} (${r.food_type}) amount=${r.amount}`))
  console.log('🎰 [Animation] Food emojis array:', foodEmojis)
  console.log('🎰 [Animation] isJackpot:', props.slotAnimation?.jackpot_mode)
  console.log('🎰 [Animation] Total fruits:', slotResults.reduce((sum, r) => sum + r.amount, 0))
  
  for (let index = 0; index < 3; index++) {
    const slotResult = slotResults[index]
    const reel = reels.value[index]
    
    if (slotResult && slotResult.has_reward) {
      // 有奖励
      reel.isWinning = true
      reel.showNoReward = false
      reel.winAmount = slotResult.amount
      reel.bonusText = slotResult.bonus_text
      reel.multiplier = slotResult.multiplier
      reel.multiplierClass = slotResult.multiplier === 3 ? 'jackpot' : (slotResult.multiplier === 2 ? 'double' : 'normal')
      
      // settle on the final symbol using the second group, indices 8-15, to avoid the edges
      const emojiIndex = foodEmojis.findIndex(emoji => emoji === slotResult.emoji)
      reel.finalSymbolIndex = emojiIndex !== -1 ? emojiIndex + 8 : 8 // 使用第二组符号
    } else {
      // 无奖励（这在新系统中不应该发生）
      reel.isWinning = false
      reel.showNoReward = true
      reel.winAmount = 0
      reel.finalSymbolIndex = Math.floor(Math.random() * foodEmojis.length) + 8
    }
  }
  
  // 逐个停止转轮 - 统一且快速的动画
  const delays = [600, 1000, 1400] // 统一的间隔，更快更清晰
  delays.forEach((delay, index) => {
    setTimeout(() => {
      if (reels.value[index]) {
        const reel = reels.value[index]
        
        // 🎯 统一动画：所有转轮相同的旋转次数
        const symbolHeight = 60
        const extraSpins = 1.5 // 统一1.5圈，快速且清晰
        const extraDistance = extraSpins * symbolHeight * 16
        
        // 计算最终停止位置
        const targetPosition = -(reel.finalSymbolIndex * symbolHeight - 60)
        
        // 先快速转到多圈后的位置
        reel.position = targetPosition - extraDistance
        
        // set the final position one frame later, so the transition runs
        requestAnimationFrame(() => {
          reel.position = targetPosition
          reel.stopped = true
        })
        
        // 最后一个转轮停止后立即显示结果
        if (index === 2) {
          setTimeout(() => {
            isSpinning.value = false
            showResult.value = true
          }, 300) // 更快显示结果，减少等待
        }
      }
    }, delay)
  })
}

const onClose = () => {
  console.log('🎰 [SlotMachinePerfect] Closing and claiming')
  
  // 如果有奖励，触发库存刷新
  if (winningSlots.value.length > 0) {
    emit('refresh-inventory')
  }
  
  emit('close')
}

const getBonusClass = (multiplier?: number) => {
  if (multiplier === 3) return 'jackpot-bonus'
  if (multiplier === 2) return 'double-bonus'
  return 'normal-bonus'
}

const onOverlayClick = (e: Event) => {
  if (showResult.value || props.onCooldown) {
    onClose()
  }
}

// 🎯 生命周期
onMounted(() => {
  console.log('🎰 [SlotMachinePerfect] Mounted:', { 
    visible: props.isVisible, 
    cooldown: props.onCooldown,
    results: props.slotResults?.length 
  })
  // 仅当可见、非冷却且有结果时启动
  if (props.isVisible && !props.onCooldown && (props.slotResults?.length || 0) > 0) {
    startSlotMachine()
  }
})

// 监听变化
watch(() => props.isVisible, (newVal) => {
  if (newVal) {
    if (props.onCooldown) {
      // 冷却中不启动动画
      isSpinning.value = false
      showResult.value = false
    } else if ((props.slotResults?.length || 0) > 0) {
      startSlotMachine()
    }
  }
})

watch(() => props.slotResults, (newVal) => {
  if (props.isVisible && !props.onCooldown && newVal && newVal.length > 0) {
    startSlotMachine()
  }
})

watch(() => props.onCooldown, (newVal) => {
  if (!props.isVisible) return
  if (newVal) {
    isSpinning.value = false
    showResult.value = false
  } else if ((props.slotResults?.length || 0) > 0) {
    startSlotMachine()
  }
})
</script>

<style scoped>

/* 🛠️ Universal Fixes - Prevent ALL Overlapping */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0 auto;
}

.result-display * {
  max-width: 100%;
}

.slot-machine-overlay {
  position: fixed !important;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(15px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 15000 !important;
  animation: fadeIn 0.3s ease;
  isolation: isolate; /* 创建新的层叠上下文 */
  contain: layout style paint; /* 隔离布局、样式和绘制 */
}

.slot-machine-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 24px;
  padding: 32px;
  max-width: 600px;
  width: 95vw;
  max-height: 90vh; /* 限制最大高度，防止超出屏幕 */
  border: 3px solid #ffd700;
  box-shadow: 
    0 0 50px rgba(255, 215, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  text-align: center;
  animation: slideIn 0.5s ease;
  position: relative;
  overflow-y: auto; /* 允许垂直滚动 */
  overflow-x: hidden; /* 水平方向隐藏 */
  /* 美化滚动条 */
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 215, 0, 0.5) rgba(0, 0, 0, 0.2);
}

/* Webkit浏览器滚动条样式 */
.slot-machine-container::-webkit-scrollbar {
  width: 8px;
}

.slot-machine-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.slot-machine-container::-webkit-scrollbar-thumb {
  background: rgba(255, 215, 0, 0.5);
  border-radius: 4px;
}

.slot-machine-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 215, 0, 0.7);
}

/* Removed shimmer animation for performance - was causing lag */

.slot-machine-header {
  margin-bottom: 28px;
  position: relative;
  z-index: 1;
}

.slot-title {
  font-size: 28px;
  font-weight: 800;
  color: #ffd700;
  margin-bottom: 12px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5), 0 0 25px rgba(255, 215, 0, 0.7);
  /* Removed titleGlow animation for performance */
}

.slot-subtitle {
  color: #e2e8f0;
  font-size: 16px;
  font-weight: 500;
}

.slot-subtitle.cooldown-notice {
  color: #ffa726;
  font-weight: 600;
  /* 移除无限动画以提升性能 */
}

/* 💡 游戏提示 - 清晰的目标说明 */
.game-hint {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.15) 100%);
  border: 2px solid rgba(59, 130, 246, 0.4);
  border-radius: 16px;
  padding: 16px 20px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  animation: hintFadeIn 0.5s ease;
}

@keyframes hintFadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.hint-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.hint-text {
  text-align: left;
  flex: 1;
}

.hint-text strong {
  display: block;
  font-size: 16px;
  color: #60a5fa;
  margin-bottom: 4px;
}

.hint-text p {
  font-size: 14px;
  color: #cbd5e1;
  margin: 0;
}

/* 🎰 冷却状态 */
.cooldown-display {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
}

.cooldown-card {
  background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
  border: 2px solid #ffa726;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  max-width: 400px;
}

.cooldown-icon {
  font-size: 48px;
  /* 移除旋转动画以提升性能 */
}

.cooldown-text h3 {
  color: #ffa726;
  font-size: 18px;
  margin-bottom: 8px;
}

.cooldown-timer {
  color: #fff;
  font-size: 24px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
}

.cooldown-hint {
  color: #cbd5e0;
  font-size: 14px;
  margin-top: 8px;
}

.preview-reward {
  background: linear-gradient(135deg, #553c9a 0%, #6b46c1 100%);
  border: 2px solid #8b5cf6;
  border-radius: 12px;
  padding: 16px;
  width: 100%;
  max-width: 300px;
}

.preview-card {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-icon {
  font-size: 32px;
  /* Removed float animation for performance */
}

.preview-text h4 {
  color: #a78bfa;
  font-size: 14px;
  margin-bottom: 4px;
}

.preview-fruit {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}

.preview-name {
  color: #e9d5ff;
  font-size: 12px;
}

.cooldown-close-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.cooldown-close-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
}

/* 🎰 转轮容器 */
.slot-reels-container {
  margin: 24px 0;
  position: relative;
  padding: 20px 0;
  width: 100%;
  clear: both;
  display: block;
}

/* 🎯 Winning Line Indicator */
.winning-line {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  pointer-events: none;
  z-index: 10;
  opacity: 0.3;
  transition: all 0.5s ease;
}

.winning-line.line-active {
  opacity: 1;
  filter: drop-shadow(0 0 15px rgba(255, 215, 0, 0.75));
  /* Removed linePulse animation for performance */
}

.line-arrow {
  font-size: 32px;
  color: #ffd700;
  text-shadow: 0 0 15px rgba(255, 215, 0, 0.8);
  /* Removed arrowBlink animation for performance */
}

.line-text {
  font-size: 16px;
  font-weight: 700;
  color: #ffd700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  white-space: nowrap;
}

.line-center {
  flex: 1;
  height: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 215, 0, 0.8) 10%, 
    rgba(255, 215, 0, 1) 50%, 
    rgba(255, 215, 0, 0.8) 90%, 
    transparent 100%
  );
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.6);
  margin: 0 -10px;
}

.slot-reels {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin: 0 auto;
  max-width: 480px;
  position: relative;
  z-index: 5;
}

.slot-reel {
  background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
  border: 3px solid #4a5568;
  border-radius: 16px;
  width: 120px;
  height: 180px;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.5s ease;
  box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.5);
}

/* Reel Frame - highlights the winning line area */
.reel-frame {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: calc(100% - 10px);
  height: 70px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  pointer-events: none;
  z-index: 2;
  transition: all 0.5s ease;
}

.reel-frame.frame-glow {
  border-color: rgba(255, 215, 0, 0.8);
  box-shadow: 
    0 0 20px rgba(255, 215, 0, 0.4),
    inset 0 0 20px rgba(255, 215, 0, 0.2);
  /* Removed frameGlow animation for performance */
}

.slot-reel.spinning {
  border-color: #ffd700;
  box-shadow: 
    0 0 25px rgba(255, 215, 0, 0.6), 
    inset 0 0 35px rgba(0, 0, 0, 0.6),
    0 4px 15px rgba(0, 0, 0, 0.4);
  /* Removed reelSpinGlow animation for performance */
}

.slot-reel.stopped {
  border-color: #68d391;
  animation: reelStopBounce 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes reelStopBounce {
  0% { 
    transform: scale(1); 
    border-color: #ffd700;
  }
  30% { 
    transform: scale(1.08); 
    border-color: #ffd700;
  }
  50% { 
    transform: scale(0.95); 
    border-color: #68d391;
  }
  70% { 
    transform: scale(1.02); 
  }
  100% { 
    transform: scale(1); 
    border-color: #68d391;
  }
}

.slot-reel.winning {
  border-color: #ffd700;
  background: linear-gradient(135deg, #2d3748 0%, #744210 50%, #1a202c 100%);
  box-shadow: 0 0 40px rgba(255, 215, 0, 0.9);
  /* Removed winningPulse infinite animation for performance */
}

.slot-reel.no-reward {
  border-color: #e53e3e;
  background: linear-gradient(135deg, #2d3748 0%, #742a2a 50%, #1a202c 100%);
}

.reel-symbols {
  position: absolute;
  top: 60px;
  left: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  transition: transform 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94); /* 缩短时间 */
  will-change: transform; /* performance tuning提示 */
}

.slot-reel.spinning .reel-symbols {
  /* 简化动画 - 使用 transform 而不是复杂动画 */
  animation: symbolSpinFast 0.1s linear infinite; /* 稍微放慢 */
}

.slot-reel.stopped .reel-symbols {
  /* 精确停止 - 缩短过渡时间 */
  transition: transform 0.8s cubic-bezier(0.25, 0.1, 0.25, 1); /* 从1.2s减到0.8s */
  animation: none;
}

@keyframes symbolSpinFast {
  from { transform: translateY(0px); }
  to { transform: translateY(-60px); }
}

.symbol {
  font-size: 52px;
  height: 60px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  /* 移除过渡以提升性能 */
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

/* 旋转时的符号模糊效果 - 营造速度感 */
.slot-reel.spinning .symbol {
  filter: blur(2px) drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  opacity: 0.7;
}

.symbol.final-symbol {
  transform: scale(1.25);
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.5)) !important;
  opacity: 1 !important;
  z-index: 3;
}

.symbol.winning-symbol {
  transform: scale(1.4);
  text-shadow: 
    0 0 25px rgba(255, 215, 0, 0.9),
    0 0 50px rgba(255, 215, 0, 0.7),
    0 5px 10px rgba(0, 0, 0, 0.55);
  filter: drop-shadow(0 0 15px rgba(255, 215, 0, 0.75));
  z-index: 4 !important;
  /* Removed symbolWin and symbolGlow infinite animations for performance */
}

.reel-label {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.7);
  color: #e2e8f0;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.win-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  background: linear-gradient(135deg, #ffd700 0%, #f59e0b 100%);
  border-radius: 8px;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  transform: scale(1.03);
  /* Removed winBounce animation for performance */
}

.win-amount {
  color: #1a202c;
  font-size: 12px;
  font-weight: 700;
}

.bonus-multiplier {
  position: absolute;
  bottom: -25px;
  left: 50%;
  transform: translateX(-50%);
  padding: 3px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 700;
  text-align: center;
  white-space: nowrap;
  /* Removed bonusFloat animation for performance */
}

.bonus-multiplier.normal {
  background: rgba(59, 130, 246, 0.9);
  color: white;
  border: 1px solid #3b82f6;
}

.bonus-multiplier.double {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border: 2px solid #fbbf24;
  text-shadow: 0 0 10px rgba(251, 191, 36, 0.8);
  /* Removed bonusDouble animation for performance */
}

.bonus-multiplier.jackpot {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 50%, #991b1b 100%);
  color: #fef2f2;
  border: 2px solid #f87171;
  text-shadow: 0 0 15px rgba(248, 113, 113, 1);
  box-shadow: 0 0 20px rgba(220, 38, 38, 0.6);
  /* Removed bonusJackpot animation for performance */
}

.no-reward-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(229, 62, 62, 0.9);
  border-radius: 50%;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.no-reward-text {
  font-size: 24px;
  color: white;
}

/* 🎯 结果显示 - 紧凑设计 */
.result-display {
  margin: 20px 0;
  animation: resultSlideIn 0.8s ease;
  position: relative;
  width: 100%;
  clear: both;
  overflow: visible;
}

@keyframes resultSlideIn {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* � 转轮结果行 - 紧凑横向布局 */
.reel-results-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.results-label {
  font-size: 16px;
  font-weight: 700;
  color: #ffd700;
  margin-right: 12px;
  white-space: nowrap;
}

.reel-symbols {
  display: flex;
  gap: 8px;
  flex: 1;
  justify-content: flex-end;
}

/* 🎁 实际奖励 - 紧凑卡片布局 */
.actual-rewards {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(5, 150, 105, 0.25) 100%);
  border: 3px solid #10b981;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);
  animation: rewardsPop 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes rewardsPop {
  0% { transform: scale(0.9); opacity: 0; }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}

.rewards-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  justify-content: center;
}

.rewards-icon {
  font-size: 22px;
  /* Removed iconBounce animation for performance */
}

.rewards-title {
  font-size: 18px;
  font-weight: 800;
  color: #10b981;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.rewards-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.reward-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  border: 2px solid rgba(16, 185, 129, 0.3);
  transition: all 0.3s ease;
}

.reward-card:hover {
  transform: translateY(-2px);
  border-color: #10b981;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
}

.reward-emoji {
  font-size: 36px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.reward-amount {
  font-size: 18px;
  font-weight: 800;
  color: #ffd700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.reward-name {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
}

.jackpot-banner {
  background: linear-gradient(135deg, #ffd700 0%, #f59e0b 50%, #d97706 100%);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 0 30px rgba(255, 215, 0, 0.8);
  /* Removed jackpotGlow animation for performance */
}

.jackpot-text {
  font-size: 24px;
  font-weight: 800;
  color: #1a202c;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);
}

.jackpot-subtitle {
  font-size: 16px;
  color: #744210;
  font-weight: 600;
  margin-top: 4px;
}

/* 🎁 新的奖励展示样式 - 清晰紧凑 */
.rewards-display {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
  border: 2px solid #10b981;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  animation: rewardsPop 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.rewards-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.reward-item {
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.reward-item:hover {
  transform: translateX(4px);
  border-color: #10b981;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
}

.reward-item.jackpot {
  border-color: #ffd700;
  background: rgba(255, 215, 0, 0.1);
}

.reward-emoji-large {
  font-size: 48px;
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.reward-details {
  flex: 1;
  text-align: left;
  min-width: 0;
}

.reward-name-large {
  font-size: 18px;
  font-weight: 700;
  color: #ffd700;
  margin-bottom: 6px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.reward-amount-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.amount-value {
  font-size: 20px;
  font-weight: 800;
  color: #68d391;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.bonus-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.bonus-badge.normal-bonus {
  background: #3b82f6;
  color: white;
}

.bonus-badge.double-bonus {
  background: #f59e0b;
  color: white;
}

.bonus-badge.jackpot-bonus {
  background: #dc2626;
  color: white;
}

.reward-effect-text {
  font-size: 13px;
  color: #a0aec0;
  font-style: italic;
}

.rewards-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.summary-content {
  font-size: 15px;
  color: #e2e8f0;
  font-weight: 500;
  line-height: 1.5;
}

.summary-content strong {
  color: #ffd700;
  font-size: 18px;
  font-weight: 800;
}

.result-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
  margin-bottom: 20px;
}

.result-card {
  background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
  border: 2px solid #68d391;
  border-radius: 16px;
  padding: 20px;
  min-width: 160px;
  animation: cardPop 0.6s ease;
}

.result-card.jackpot {
  border-color: #ffd700;
  background: linear-gradient(135deg, #744210 0%, #2d3748 50%, #1a202c 100%);
}

@keyframes cardPop {
  0% { transform: scale(0.8); opacity: 0; }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}

.result-emoji {
  font-size: 56px;
  margin-bottom: 12px;
  /* Removed emojiDance animation for performance */
}

.result-text h3 {
  color: #ffd700;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
}

.result-amount-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.result-amount {
  color: #68d391;
  font-size: 16px;
  font-weight: 600;
}

.bonus-text {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  text-align: center;
}

.bonus-text.normal-bonus {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.bonus-text.double-bonus {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  /* Removed bonusTextGlow animation for performance */
}

.bonus-text.jackpot-bonus {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.1);
  /* Removed bonusTextJackpot animation for performance */
}

.result-effect {
  color: #a0aec0;
  font-size: 14px;
}

.result-summary {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-title {
  color: #ffd700;
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 8px;
}

.summary-text {
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 500;
  /* Removed sparkle animation for performance */
}

/* 🎮 加载状态 */
.spinning-display {
  margin: 40px 0;
  animation: fadeIn 0.5s ease;
}

.rolling-text {
  color: #ffd700;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 16px;
}

.dots {
  display: inline-block;
}

.animated-dots {
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0%, 20% { color: rgba(0,0,0,0); text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0); }
  40% { color: #ffd700; text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0); }
  60% { text-shadow: .25em 0 0 #ffd700, .5em 0 0 rgba(0,0,0,0); }
  80%, 100% { text-shadow: .25em 0 0 #ffd700, .5em 0 0 #ffd700; }
}

/* 🎰 操作按钮 - 固定底部区域 */
.slot-actions {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 2px solid rgba(255, 215, 0, 0.3);
  position: sticky;
  bottom: 0;
  background: linear-gradient(to top, #1a1a2e 80%, transparent);
  padding-bottom: 8px;
}

.claim-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 16px;
  padding: 18px 40px;
  color: white;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.claim-btn.jackpot {
  background: linear-gradient(135deg, #ffd700 0%, #f59e0b 100%);
  color: #1a202c;
  /* Removed jackpotButton animation for performance */
}

.claim-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
}

.claim-btn.jackpot:hover {
  box-shadow: 0 8px 20px rgba(255, 215, 0, 0.4);
}

/* 📊 统计 */
.slot-stats {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.stats-text {
  color: #a0aec0;
  font-size: 14px;
}

.stats-number {
  color: #68d391;
  font-weight: 600;
}

.win-rate {
  color: #ffd700;
  font-weight: 600;
}

/* 🎯 响应式 */
@media (max-width: 640px) {
  .slot-machine-container {
    padding: 20px;
    width: 98vw;
  }
  
  .slot-reels {
    gap: 8px;
  }
  
  .slot-reel {
    width: 90px;
    height: 140px;
  }
  
  .symbol {
    font-size: 36px;
    height: 50px;
  }
  
  .result-cards {
    gap: 12px;
  }
  
  .result-card {
    min-width: 140px;
    padding: 16px;
  }
  
  .result-emoji {
    font-size: 42px;
  }
}

/* � New Main Reward Card - AAA Quality Display */
.main-reward-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 3px solid rgba(255, 215, 0, 0.4);
  border-radius: 20px;
  padding: 24px;
  margin: 20px 0;
  animation: rewardReveal 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.reward-header-big {
  text-align: center;
  margin-bottom: 20px;
}

.reward-title-big {
  font-size: 24px;
  font-weight: 800;
  color: #ffd700;
  text-shadow: 0 2px 8px rgba(255, 215, 0, 0.5);
  display: inline-block;
}

.reward-content-big {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.reward-item-big {
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.4s ease;
}

.reward-item-big.jackpot-glow {
  border-color: #ffd700;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.2) 0%, rgba(255, 140, 0, 0.1) 100%);
  box-shadow: 0 4px 20px rgba(255, 215, 0, 0.4);
}

.reward-emoji-huge {
  font-size: 72px;
  flex-shrink: 0;
  width: 90px;
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  animation: emojiPop 0.6s ease;
}

.reward-info-big {
  flex: 1;
  text-align: left;
}

.reward-name-huge {
  font-size: 28px;
  font-weight: 800;
  color: #ffd700;
  margin-bottom: 10px;
  text-shadow: 0 3px 6px rgba(0, 0, 0, 0.6);
  line-height: 1.2;
}

.reward-amount-huge {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.amount-text {
  font-size: 32px;
  font-weight: 900;
  color: #68d391;
  text-shadow: 0 3px 8px rgba(104, 211, 145, 0.6);
}

.bonus-label {
  font-size: 13px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 8px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.bonus-label.normal-bonus {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
}

.bonus-label.double-bonus {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4);
}

.bonus-label.jackpot-bonus {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.4);
}

.reward-summary-big {
  text-align: center;
  font-size: 18px;
  color: #e2e8f0;
  font-weight: 600;
  padding: 16px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.reward-summary-big strong {
  color: #ffd700;
  font-size: 22px;
  font-weight: 900;
  text-shadow: 0 2px 4px rgba(255, 215, 0, 0.5);
}

/* �🎯 动画 */

/* 🎯 ULTRA-CLEAR RESULT DISPLAY STYLES */
.search-results-card {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.15) 100%);
  border: 3px solid rgba(59, 130, 246, 0.5);
  border-radius: 20px;
  padding: 24px;
  margin: 0 0 24px 0;
  animation: slideIn 0.6s ease;
  position: relative;
  z-index: 1;
  clear: both;
}

.step-header {
  font-size: 20px;
  font-weight: 800;
  color: #60a5fa;
  text-align: center;
  margin-bottom: 20px;
  text-shadow: 0 2px 6px rgba(96, 165, 250, 0.5);
}

.search-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  width: 100%;
  max-width: 100%;
  position: relative;
}

.search-box {
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 16px;
  text-align: center;
  box-sizing: border-box;
  overflow: hidden;
  position: relative;
}

.search-label {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 600;
  margin-bottom: 12px;
  text-transform: uppercase;
}

.search-emoji-huge {
  font-size: 64px;
  margin: 12px 0;
}

.search-food-name {
  font-size: 16px;
  font-weight: 700;
  color: #e2e8f0;
  margin-top: 8px;
}

.connection-flow {
  text-align: center;
  margin: 24px 0;
  position: relative;
  z-index: 2;
  clear: both;
}

.flow-arrow {
  font-size: 32px;
  margin: 8px 0;
}

.flow-message {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.25) 0%, rgba(255, 140, 0, 0.2) 100%);
  border: 3px solid rgba(255, 215, 0, 0.6);
  border-radius: 16px;
  padding: 16px 20px;
  margin: 12px auto;
  max-width: 300px;
}

.flow-message strong {
  display: block;
  font-size: 20px;
  color: #ffd700;
  margin-bottom: 6px;
  text-shadow: 0 2px 8px rgba(255, 215, 0, 0.6);
}

.flow-message p {
  font-size: 15px;
  color: #fbbf24;
  margin: 0;
  font-weight: 600;
}

.you-got-card {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.15) 100%);
  border: 4px solid rgba(16, 185, 129, 0.6);
  border-radius: 24px;
  padding: 28px;
  margin: 24px 0 0 0;
  position: relative;
  z-index: 3;
  clear: both;
}

.step-header-big {
  font-size: 28px;
  font-weight: 900;
  color: #10b981;
  text-align: center;
  margin-bottom: 24px;
  text-shadow: 0 3px 10px rgba(16, 185, 129, 0.6);
}

.reward-mega-box {
  background: rgba(0, 0, 0, 0.4);
  border: 3px solid rgba(255, 255, 255, 0.25);
  border-radius: 20px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
  box-sizing: border-box;
  position: relative;
  width: 100%;
  max-width: 100%;
}

.reward-mega-box.jackpot-glow-mega {
  border-color: #ffd700;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.3) 0%, rgba(255, 140, 0, 0.2) 100%);
  box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
}

.reward-emoji-ultra {
  font-size: 80px;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.reward-text-section {
  flex: 1;
  text-align: left;
}

.reward-name-ultra {
  font-size: 32px;
  font-weight: 900;
  color: #ffd700;
  margin-bottom: 12px;
  text-shadow: 0 3px 10px rgba(255, 215, 0, 0.6);
}

.reward-quantity-ultra {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}

.qty-number {
  font-size: 48px;
  font-weight: 900;
  color: #10b981;
  text-shadow: 0 4px 12px rgba(16, 185, 129, 0.7);
}

.qty-text {
  font-size: 20px;
  font-weight: 600;
  color: #6ee7b7;
  text-transform: uppercase;
}

.bonus-tag-ultra {
  display: inline-block;
  font-size: 14px;
  font-weight: 800;
  padding: 8px 16px;
  border-radius: 10px;
  text-transform: uppercase;
}

.bonus-tag-ultra.normal-bonus {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.bonus-tag-ultra.double-bonus {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.bonus-tag-ultra.jackpot-bonus {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: white;
}

.final-action-prompt {
  text-align: center;
  font-size: 18px;
  color: #e2e8f0;
  font-weight: 600;
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.final-action-prompt strong {
  color: #ffd700;
  font-size: 24px;
  font-weight: 900;
}


@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@keyframes rewardReveal {
  0% {
    opacity: 0;
    transform: scale(0.8) translateY(30px);
  }
  60% {
    transform: scale(1.05) translateY(-5px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes emojiPop {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}



/* 🎯 ULTRA-SIMPLE Result Display */
.result-display-simple {
  margin: 30px 0;
  animation: fadeIn 0.5s ease;
  width: 100%;
  clear: both;
  display: block;
  position: relative;
  z-index: 1;
}

.jackpot-badge {
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  font-size: 24px;
  font-weight: 900;
  padding: 16px;
  border-radius: 16px;
  margin-bottom: 24px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(255, 215, 0, 0.5);
  animation: pulse 1s ease infinite;
}

.simple-reward-card {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(5, 150, 105, 0.2) 100%);
  border: 4px solid #10b981;
  border-radius: 24px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.reward-title {
  font-size: 32px;
  font-weight: 900;
  color: #10b981;
  text-align: center;
  margin-bottom: 28px;
  text-shadow: 0 2px 10px rgba(16, 185, 129, 0.6);
}

.simple-reward-item {
  background: rgba(0, 0, 0, 0.4);
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 16px;
}

.reward-emoji-big {
  font-size: 80px;
  flex-shrink: 0;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.reward-info {
  flex: 1;
  text-align: left;
}

.reward-name-big {
  font-size: 28px;
  font-weight: 800;
  color: #ffd700;
  margin-bottom: 8px;
  text-shadow: 0 2px 8px rgba(255, 215, 0, 0.5);
}

.reward-amount-big {
  font-size: 40px;
  font-weight: 900;
  color: #10b981;
  text-shadow: 0 3px 10px rgba(16, 185, 129, 0.6);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .simple-reward-item {
    flex-direction: column;
    text-align: center;
    padding: 20px;
  }
  
  .reward-emoji-big {
    font-size: 64px;
    width: 80px;
    height: 80px;
  }
  
  .reward-info {
    text-align: center;
  }
  
  .reward-name-big {
    font-size: 22px;
  }
  
  .reward-amount-big {
    font-size: 32px;
  }
}


/* 📱 Mobile Fixes - Prevent Overlapping */
@media (max-width: 768px) {
  .search-results-card {
    padding: 20px;
    margin-bottom: 20px;
  }
  
  .search-grid {
    grid-template-columns: 1fr !important;
    gap: 12px;
  }
  
  .search-box {
    padding: 16px;
  }
  
  .search-emoji-huge {
    font-size: 48px;
  }
  
  .you-got-card {
    padding: 20px;
    margin-top: 20px;
  }
  
  .reward-mega-box {
    flex-direction: column;
    text-align: center;
    gap: 16px;
    padding: 20px;
  }
  
  .reward-emoji-ultra {
    font-size: 64px;
    width: 80px;
    height: 80px;
    margin: 0 auto;
  }
  
  .reward-text-section {
    text-align: center;
  }
}

</style>

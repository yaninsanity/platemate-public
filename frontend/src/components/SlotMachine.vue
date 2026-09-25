<template>
  <div class="slot-machine-overlay" v-if="isVisible" @click.self="onOverlayClick">
    <div class="slot-machine-container">
      <div class="slot-machine-header">
        <h2 class="slot-title">🎰 Triple Fruit Slots!</h2>
        <p class="slot-subtitle" v-if="!onCooldown">Spinning for up to 3 different fruits...</p>
        <p class="slot-subtitle cooldown-notice" v-else>⏱️ Recharging... Next spin available in: {{ cooldownTime }}</p>
      </div>
      
      <!-- 🎰 冷却状态显示 -->
      <div class="cooldown-display" v-if="onCooldown">
        <div class="cooldown-card">
          <div class="cooldown-icon">⏰</div>
          <div class="cooldown-text">
            <h3>Slot Machine Recharging</h3>
            <p class="cooldown-timer">{{ cooldownTime }}</p>
            <p class="cooldown-hint">Come back in {{ cooldownTime }} for your next fruit harvest!</p>
          </div>
        </div>
        <!-- 🎯 显示预览奖励 -->
        <div class="preview-reward" v-if="slotPreview && slotPreview.next_reward_locked">
          <div class="preview-card">
            <div class="preview-icon">🔮</div>
            <div class="preview-text">
              <h4>Next Locked Reward</h4>
              <div class="preview-fruit">
                {{ slotPreview.next_possible_emoji }} × {{ slotPreview.next_possible_amount }}
              </div>
              <p class="preview-name">{{ slotPreview.next_possible_reward }}</p>
            </div>
          </div>
        </div>
        <button @click="onClose" class="cooldown-close-btn">
          <span>✅</span>
          Got it!
        </button>
      </div>
      
      <!-- 🎰 3-slot老虎机转轮 -->
      <div class="slot-reels-container" v-if="!onCooldown">
        <div class="slot-reels">
          <div 
            v-for="(reel, index) in reels" 
            :key="index"
            class="slot-reel"
            :class="{ 
              'spinning': isSpinning, 
              'stopped': reel.stopped,
              'winning': reel.isWinning,
              'no-reward': reel.showNoReward
            }"
          >
            <div class="reel-symbols" :style="{ transform: `translateY(${reel.position}px)` }">
              <div 
                v-for="(symbol, symbolIndex) in reel.symbols" 
                :key="symbolIndex"
                class="symbol"
                :class="{ 
                  'final-symbol': reel.stopped && symbolIndex === reel.finalSymbolIndex,
                  'winning-symbol': reel.stopped && reel.isWinning && symbolIndex === reel.finalSymbolIndex
                }"
              >
                {{ symbol }}
              </div>
            </div>
            
            <!-- 转轮标签 -->
            <div class="reel-label">Slot {{ index + 1 }}</div>
            
            <!-- 获奖指示器 - 增强倍数显示 -->
            <div class="win-indicator" v-if="reel.stopped && reel.isWinning">
              <div class="win-sparkle">✨</div>
              <div class="win-amount">×{{ reel.winAmount }}</div>
              <!-- 🎯 新增：倍数奖励特效 -->
              <div v-if="reel.bonusText" class="bonus-multiplier" :class="reel.multiplierClass">
                {{ reel.bonusText }}
              </div>
            </div>
            
            <!-- 无奖励指示器 -->
            <div class="no-reward-indicator" v-if="reel.stopped && reel.showNoReward">
              <div class="no-reward-text">❌</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 🎯 获奖结果显示 -->
      <div class="result-display" v-if="showResult && !onCooldown">
        <!-- JACKPOT 模式 -->
        <div class="jackpot-banner" v-if="isJackpot">
          <div class="jackpot-text">🎊 JACKPOT! 🎊</div>
          <div class="jackpot-subtitle">{{ winningSlots.length }} out of 3 slots won!</div>
        </div>
        
        <!-- 获奖结果卡片 -->
        <div class="result-cards">
          <div 
            v-for="(slot, index) in winningSlots" 
            :key="index"
            class="result-card"
            :class="{ 'jackpot': isJackpot }"
          >
            <div class="result-emoji">{{ slot.emoji }}</div>
            <div class="result-text">
              <h3>{{ slot.name }}</h3>
              <div class="result-amount-container">
                <p class="result-amount">×{{ slot.amount }}</p>
                <!-- 🎯 新增：显示倍数奖励信息 -->
                <p v-if="slot.bonus_text" class="bonus-text" :class="getBonusClass(slot.multiplier)">
                  {{ slot.bonus_text }}
                </p>
              </div>
              <p class="result-effect">{{ slot.effect }}</p>
            </div>
          </div>
        </div>
        
        <!-- 总结信息 -->
        <div class="result-summary">
          <h3 class="summary-title">
            🎉 You won {{ totalWinningSlots }} out of 3 slots!
          </h3>
          <p class="summary-text" v-if="isJackpot">
            💎 JACKPOT BONUS: Multiple fruit types harvested!
          </p>
        </div>
      </div>
      
      <!-- 🎰 操作按钮 -->
      <div class="slot-actions" v-if="!onCooldown">
        <button 
          v-if="showResult" 
          @click="onClose"
          class="claim-btn"
          :class="{ 'jackpot': isJackpot }"
        >
          <span>🎁</span>
          {{ isJackpot ? 'Claim JACKPOT!' : 'Claim Your Fruits!' }}
        </button>
        <div v-else class="rolling-text">
          <span class="dots">Rolling for fruits</span><span class="animated-dots">...</span>
        </div>
      </div>
      
      <!-- 🎯 统计信息 -->
      <div class="slot-stats" v-if="totalSpins > 0">
        <p class="stats-text">
          🎰 Total Spins: <span class="stats-number">{{ totalSpins }}</span> 
          | 🏆 Avg Win: <span class="win-rate">{{ averageWinRate }}%</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

// 🎰 老虎机slot结果接口 - 支持新的倍数奖励系统
interface SlotResult {
  slot_id: number
  has_reward: boolean
  food_type?: string
  name?: string
  emoji: string
  amount: number
  base_amount?: number      // 🎯 新增：基础奖励数量
  multiplier?: number       // 🎯 新增：倍数 (1, 2, 3)
  bonus_text?: string       // 🎯 新增：倍数文本 ("", "DOUBLE! ×2", "JACKPOT! ×3")
  effect?: string
}

// 🎯 预览奖励接口
interface SlotPreview {
  next_reward_locked: boolean
  next_possible_reward: string
  next_possible_emoji: string
  next_possible_amount: number
  preview_message: string
  cooldown_display: boolean
}

// 🎰 老虎机动画配置
interface SlotAnimation {
  num_slots: number
  winning_slots: number
  spin_duration: number
  reel_stop_delays: number[]
  celebration_duration: number
  jackpot_mode: boolean
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
  (e: 'refresh-inventory'): void  // 🎯 新增：关闭时刷新库存
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

// 🎰 老虎机状态
const isSpinning = ref(true)
const showResult = ref(false)

// 🎰 转轮接口 - 支持倍数奖励显示
interface Reel {
  symbols: string[]
  stopped: boolean
  position: number
  isWinning: boolean
  showNoReward: boolean
  finalSymbolIndex: number
  winAmount: number
  bonusText?: string         // 🎯 新增：倍数文本 ("DOUBLE! ×2", "JACKPOT! ×3")
  multiplier?: number        // 🎯 新增：倍数值 (1, 2, 3)
  multiplierClass?: string   // 🎯 新增：倍数CSS类 (normal, double, jackpot)
}

// 🎰 老虎机转轮
const foodEmojis = ['🍎', '🍌', '🍊', '🍓', '🍇', '🍉', '🍍', '🍒']
const reels = ref<Reel[]>([
  { 
    symbols: [...foodEmojis, ...foodEmojis, ...foodEmojis], 
    stopped: false, 
    position: 0, 
    isWinning: false, 
    showNoReward: false, 
    finalSymbolIndex: 0, 
    winAmount: 0,
    bonusText: '',
    multiplier: 1,
    multiplierClass: 'normal'
  },
  { 
    symbols: [...foodEmojis, ...foodEmojis, ...foodEmojis], 
    stopped: false, 
    position: 0, 
    isWinning: false, 
    showNoReward: false, 
    finalSymbolIndex: 0, 
    winAmount: 0,
    bonusText: '',
    multiplier: 1,
    multiplierClass: 'normal'
  },
  { 
    symbols: [...foodEmojis, ...foodEmojis, ...foodEmojis], 
    stopped: false, 
    position: 0, 
    isWinning: false, 
    showNoReward: false, 
    finalSymbolIndex: 0, 
    winAmount: 0,
    bonusText: '',
    multiplier: 1,
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
  return props.slotAnimation?.jackpot_mode || totalWinningSlots.value >= 2
})

const averageWinRate = computed(() => {
  if (props.totalSpins === 0) return 0
  // 假设平均每次获得1.5个slot
  return Math.round((totalWinningSlots.value / 3) * 100)
})

// 🎰 启动老虎机动画
const startSlotMachine = () => {
  if (props.onCooldown) return
  
  console.log('🎰 [SlotMachine] Starting 3-slot animation with results:', props.slotResults)
  
  isSpinning.value = true
  showResult.value = false
  
  // 重置转轮状态
  reels.value.forEach((reel, index) => {
    reel.stopped = false
    reel.isWinning = false
    reel.showNoReward = false
    reel.position = 0
    
    // 设置随机初始位置制造转动效果
    reel.position = -(Math.random() * 200)
  })
  
  // 🎯 精准改善：即使没有结果也要正确处理
  const slotResults = props.slotResults || []
  console.log('🎰 [SlotMachine] Processing slot results:', slotResults.length, 'results')
  
  // 根据后端结果设置每个转轮的最终状态
  for (let index = 0; index < 3; index++) {
    const reel = reels.value[index]
    const slotResult = slotResults[index]
    
    if (slotResult && slotResult.has_reward) {
      // 有奖励的slot
      reel.isWinning = true
      reel.winAmount = slotResult.amount
      
      // 🎯 新增：设置倍数奖励数据
      reel.multiplier = slotResult.multiplier || 1
      reel.bonusText = slotResult.bonus_text || ''
      
      // 🎯 设置倍数CSS类用于特效
      if (slotResult.multiplier === 3) {
        reel.multiplierClass = 'jackpot'
      } else if (slotResult.multiplier === 2) {
        reel.multiplierClass = 'double'
      } else {
        reel.multiplierClass = 'normal'
      }
      
      // 找到对应emoji在symbols中的位置
      const emojiIndex = reel.symbols.findIndex(symbol => symbol === slotResult.emoji)
      if (emojiIndex !== -1) {
        reel.finalSymbolIndex = emojiIndex
      } else {
        // 如果找不到，添加到symbols中
        reel.symbols[foodEmojis.length] = slotResult.emoji
        reel.finalSymbolIndex = foodEmojis.length
      }
    } else {
      // 无奖励的slot或没有数据
      reel.showNoReward = true
      reel.bonusText = ''
      reel.multiplier = 1
      reel.multiplierClass = 'normal'
      // 设置一个随机的水果作为最终显示
      reel.finalSymbolIndex = Math.floor(Math.random() * foodEmojis.length)
    }
  }
  
  // 使用后端配置的时间延迟逐个停止转轮
  const delays = props.slotAnimation?.reel_stop_delays || [1000, 2000, 3000]
  
  delays.forEach((delay, index) => {
    setTimeout(() => {
      if (index < reels.value.length) {
        const reel = reels.value[index]
        reel.stopped = true
        
        // 计算最终位置，让目标emoji显示在中央
        const symbolHeight = 60 // 每个symbol的高度
        reel.position = -(reel.finalSymbolIndex * symbolHeight)
        
        console.log(`🎰 [SlotMachine] Reel ${index + 1} stopped at position ${reel.position}`)
        
        // 如果是最后一个转轮，开始显示结果
        if (index === reels.value.length - 1) {
          isSpinning.value = false
          console.log('🎰 [SlotMachine] All reels stopped!')
          
          // 延迟显示结果，增加戏剧效果
          setTimeout(() => {
            showResult.value = true
            console.log('🎰 [SlotMachine] Showing results with', totalWinningSlots.value, 'winning slots')
          }, 500)
        }
      }
    }, delay)
  })
}

const onClose = () => {
  console.log('🎰 [SlotMachine] Closing and claiming prizes')
  
  // 🎯 如果有获奖结果，触发库存刷新
  if (winningSlots.value.length > 0) {
    console.log('🎰 [SlotMachine] Triggering inventory refresh after claiming prizes')
    emit('refresh-inventory')
  }
  
  emit('close')
}

// 🎯 新增：获取倍数奖励CSS类
const getBonusClass = (multiplier?: number) => {
  if (multiplier === 3) return 'jackpot-bonus'
  if (multiplier === 2) return 'double-bonus'
  return 'normal-bonus'
}

const onOverlayClick = (e: Event) => {
  // 只有在显示结果或冷却状态时才允许点击关闭
  if (showResult.value || props.onCooldown) {
    onClose()
  }
}

// 🎯 生命周期
onMounted(() => {
  console.log('🎰 [SlotMachine] Component mounted. Visible:', props.isVisible, 'OnCooldown:', props.onCooldown)
  console.log('🎰 [SlotMachine] Slot results:', props.slotResults)
  console.log('🎰 [SlotMachine] Animation config:', props.slotAnimation)
  
  // 🎯 animate whenever visible and not on cooldown
  if (props.isVisible && !props.onCooldown) {
    startSlotMachine()
  }
})

// 监听props变化
watch(() => props.isVisible, (newVal) => {
  console.log('🎰 [SlotMachine] Visibility changed to:', newVal)
  if (newVal && !props.onCooldown) {
    startSlotMachine()
  }
})

watch(() => props.slotResults, (newVal) => {
  console.log('🎰 [SlotMachine] Slot results changed:', newVal)
  if (props.isVisible && !props.onCooldown) {
    startSlotMachine()
  }
})

watch(() => props.onCooldown, (newVal) => {
  console.log('🎰 [SlotMachine] Cooldown state changed to:', newVal)
  // leaving cooldown while visible starts the animation
  if (!newVal && props.isVisible) {
    startSlotMachine()
  }
})
</script>

<style scoped>
.slot-machine-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(15px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 15000;
  animation: fadeIn 0.3s ease;
}

.slot-machine-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 24px;
  padding: 32px;
  max-width: 600px;
  width: 95vw;
  border: 3px solid #ffd700;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.6),
    0 0 20px rgba(255, 215, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  text-align: center;
  animation: slideIn 0.5s ease;
  position: relative;
  overflow: hidden;
}

.slot-machine-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(255, 215, 0, 0.1) 50%, transparent 70%);
  animation: shimmer 3s ease-in-out infinite;
  pointer-events: none;
}

@keyframes shimmer {
  0%, 100% { transform: translateX(-100%); }
  50% { transform: translateX(100%); }
}

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
  text-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.5),
    0 0 20px rgba(255, 215, 0, 0.6);
  animation: titleGlow 2s ease-in-out infinite alternate;
}

@keyframes titleGlow {
  from { text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5), 0 0 20px rgba(255, 215, 0, 0.6); }
  to { text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5), 0 0 30px rgba(255, 215, 0, 0.8); }
}

.slot-subtitle {
  color: #e2e8f0;
  font-size: 16px;
  font-weight: 500;
}

.slot-subtitle.cooldown-notice {
  color: #ffa726;
  font-weight: 600;
  animation: pulse 2s ease-in-out infinite;
}

/* 🎰 冷却状态样式 */
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
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  animation: float 2s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
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

/* 🎰 3-slot转轮容器 */
.slot-reels-container {
  margin: 24px 0;
  position: relative;
}

.slot-reels {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin: 0 auto;
  max-width: 480px;
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
}

.slot-reel.spinning {
  border-color: #ffd700;
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
  animation: reelSpin 0.1s linear infinite;
}

@keyframes reelSpin {
  0% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.5); }
  50% { box-shadow: 0 0 30px rgba(255, 215, 0, 0.8); }
  100% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.5); }
}

.slot-reel.stopped {
  border-color: #68d391;
  animation: reelStop 0.5s ease;
}

@keyframes reelStop {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.slot-reel.winning {
  border-color: #ffd700;
  background: linear-gradient(135deg, #2d3748 0%, #744210 50%, #1a202c 100%);
  box-shadow: 0 0 30px rgba(255, 215, 0, 0.8);
  animation: winningPulse 1s ease-in-out infinite;
}

@keyframes winningPulse {
  0%, 100% { box-shadow: 0 0 30px rgba(255, 215, 0, 0.8); }
  50% { box-shadow: 0 0 50px rgba(255, 215, 0, 1); }
}

.slot-reel.no-reward {
  border-color: #e53e3e;
  background: linear-gradient(135deg, #2d3748 0%, #742a2a 50%, #1a202c 100%);
}

.reel-symbols {
  position: relative;
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.slot-reel.spinning .reel-symbols {
  animation: symbolSpin 0.1s linear infinite;
}

@keyframes symbolSpin {
  from { transform: translateY(0px); }
  to { transform: translateY(-60px); }
}

.symbol {
  font-size: 48px;
  height: 60px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.symbol.final-symbol {
  transform: scale(1.2);
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
}

.symbol.winning-symbol {
  animation: symbolWin 1s ease-in-out infinite;
}

@keyframes symbolWin {
  0%, 100% { 
    transform: scale(1.2); 
    text-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
  }
  50% { 
    transform: scale(1.4); 
    text-shadow: 0 0 30px rgba(255, 215, 0, 1);
  }
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
  animation: winBounce 0.6s ease-in-out infinite;
}

@keyframes winBounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.win-sparkle {
  font-size: 12px;
}

.win-amount {
  color: #1a202c;
  font-size: 12px;
  font-weight: 700;
}

/* 🎯 新增：倍数奖励特效样式 */
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
  animation: bonusFloat 2s ease-in-out infinite;
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
  animation: bonusDouble 1.5s ease-in-out infinite;
  text-shadow: 0 0 10px rgba(251, 191, 36, 0.8);
}

.bonus-multiplier.jackpot {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 50%, #991b1b 100%);
  color: #fef2f2;
  border: 2px solid #f87171;
  animation: bonusJackpot 1s ease-in-out infinite;
  text-shadow: 0 0 15px rgba(248, 113, 113, 1);
  box-shadow: 0 0 20px rgba(220, 38, 38, 0.6);
}

@keyframes bonusFloat {
  0%, 100% { 
    transform: translateX(-50%) translateY(0px); 
    opacity: 0.9;
  }
  50% { 
    transform: translateX(-50%) translateY(-3px); 
    opacity: 1;
  }
}

@keyframes bonusDouble {
  0%, 100% { 
    transform: translateX(-50%) scale(1); 
    box-shadow: 0 0 15px rgba(251, 191, 36, 0.6);
  }
  50% { 
    transform: translateX(-50%) scale(1.1); 
    box-shadow: 0 0 25px rgba(251, 191, 36, 0.9);
  }
}

@keyframes bonusJackpot {
  0%, 100% { 
    transform: translateX(-50%) scale(1) rotate(0deg); 
    box-shadow: 0 0 20px rgba(220, 38, 38, 0.6);
  }
  25% { 
    transform: translateX(-50%) scale(1.15) rotate(1deg); 
    box-shadow: 0 0 30px rgba(220, 38, 38, 0.8);
  }
  75% { 
    transform: translateX(-50%) scale(1.15) rotate(-1deg); 
    box-shadow: 0 0 30px rgba(220, 38, 38, 0.8);
  }
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

/* 🎯 结果显示样式 */
.result-display {
  margin: 24px 0;
  animation: resultSlideIn 0.8s ease;
}

@keyframes resultSlideIn {
  from { 
    opacity: 0; 
    transform: translateY(30px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

.jackpot-banner {
  background: linear-gradient(135deg, #ffd700 0%, #f59e0b 50%, #d97706 100%);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 20px;
  animation: jackpotGlow 1s ease-in-out infinite alternate;
}

@keyframes jackpotGlow {
  from { box-shadow: 0 0 20px rgba(255, 215, 0, 0.6); }
  to { box-shadow: 0 0 40px rgba(255, 215, 0, 1); }
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
  animation: emojiDance 2s ease-in-out infinite;
}

@keyframes emojiDance {
  0%, 100% { transform: rotate(0deg) scale(1); }
  25% { transform: rotate(-5deg) scale(1.05); }
  75% { transform: rotate(5deg) scale(1.05); }
}

.result-text h3 {
  color: #ffd700;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
}

.result-amount {
  color: #68d391;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

/* 🎯 新增：倍数奖励容器样式 */
.result-amount-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

/* 🎯 新增：倍数奖励文本样式 */
.bonus-text {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 6px;
  margin: 0;
  text-align: center;
  animation: bonusTextGlow 2s ease-in-out infinite;
}

.bonus-text.normal-bonus {
  background: rgba(59, 130, 246, 0.8);
  color: #bfdbfe;
  border: 1px solid #3b82f6;
}

.bonus-text.double-bonus {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #fef3c7;
  border: 1px solid #fbbf24;
  text-shadow: 0 0 8px rgba(251, 191, 36, 0.8);
}

.bonus-text.jackpot-bonus {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: #fee2e2;
  border: 1px solid #f87171;
  text-shadow: 0 0 10px rgba(248, 113, 113, 1);
  animation: bonusTextJackpot 1.5s ease-in-out infinite;
}

@keyframes bonusTextGlow {
  0%, 100% { 
    opacity: 0.9;
    transform: scale(1);
  }
  50% { 
    opacity: 1;
    transform: scale(1.05);
  }
}

@keyframes bonusTextJackpot {
  0%, 100% { 
    opacity: 0.9;
    transform: scale(1);
    box-shadow: 0 0 8px rgba(220, 38, 38, 0.6);
  }
  50% { 
    opacity: 1;
    transform: scale(1.1);
    box-shadow: 0 0 15px rgba(220, 38, 38, 0.9);
  }
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
  animation: sparkle 2s ease-in-out infinite;
}

@keyframes sparkle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* 🎰 操作按钮 */
.slot-actions {
  margin: 24px 0;
}

.claim-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 16px;
  padding: 16px 32px;
  color: white;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 200px;
  justify-content: center;
}

.claim-btn.jackpot {
  background: linear-gradient(135deg, #ffd700 0%, #f59e0b 100%);
  color: #1a202c;
  animation: jackpotButton 1s ease-in-out infinite;
}

@keyframes jackpotButton {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 8px 25px rgba(255, 215, 0, 0.4);
  }
  50% { 
    transform: scale(1.05);
    box-shadow: 0 12px 35px rgba(255, 215, 0, 0.6);
  }
}

.claim-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 30px rgba(16, 185, 129, 0.4);
}

.claim-btn.jackpot:hover {
  box-shadow: 0 12px 35px rgba(255, 215, 0, 0.6);
}

.rolling-text {
  color: #e2e8f0;
  font-size: 18px;
  font-weight: 500;
}

.dots {
  color: #68d391;
}

.animated-dots {
  animation: dots 1.5s ease-in-out infinite;
}

@keyframes dots {
  0%, 20% { opacity: 0; }
  50% { opacity: 1; }
  100% { opacity: 0; }
}

/* 🎯 统计信息 */
.slot-stats {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 12px 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.stats-text {
  color: #a0aec0;
  font-size: 14px;
  margin: 0;
}

.stats-number {
  color: #ffd700;
  font-weight: 700;
}

.win-rate {
  color: #68d391;
  font-weight: 700;
}

/* 🎯 responsive layout */
@media (max-width: 640px) {
  .slot-machine-container {
    padding: 20px;
    margin: 16px;
  }
  
  .slot-title {
    font-size: 24px;
  }
  
  .slot-reels {
    gap: 12px;
  }
  
  .slot-reel {
    width: 100px;
    height: 150px;
  }
  
  .symbol {
    font-size: 36px;
    height: 50px;
  }
  
  .result-cards {
    flex-direction: column;
    align-items: center;
  }
  
  .result-card {
    min-width: 140px;
  }
}

/* 🎯 动画效果 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { 
    opacity: 0; 
    transform: translateY(-50px) scale(0.9); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0) scale(1); 
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>

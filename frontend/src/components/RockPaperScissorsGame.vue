<template>
  <div class="rps-overlay" v-if="isVisible">
    <div class="rps-container" @click.stop>
      <!-- Game Header with Battle PNG -->
      <div class="game-header">
        <div class="header-left">
          <div class="header-content">
            <img src="/assets/spr.png" alt="Battle Arena" class="header-sprite" />
            <h2 class="game-title">🤖 CHALLENGE KINNY</h2>
          </div>
        </div>
        <!-- Hunger Status Display -->
        <div class="hunger-status">
          <div class="hunger-info">
            <span class="hunger-icon">🍽️</span>
            <span class="hunger-value" :class="{ 'low-hunger': currentHunger <= 20, 'critical-hunger': !canPlayGame }">
              {{ currentHunger }}%
            </span>
          </div>
          <div class="game-cost-info">
            <span class="cost-text">Game costs {{ GAME_HUNGER_COST }} hunger</span>
          </div>
        </div>
        <button class="close-btn" @click="closeGame">✕</button>
      </div>

      <!-- Fast Arena -->
      <div class="fast-arena">
        <!-- Player Section -->
        <div class="player-section">
          <div class="player-label">YOU</div>
          <div class="choice-display" :class="{ 'choice-locked': isPlaying }">
            <div class="choice-emoji player-choice">{{ choices[playerChoice].emoji }}</div>
            <div class="choice-ring" v-if="isPlaying"></div>
          </div>
        </div>

        <!-- VS Countdown -->
        <div class="vs-divider">
          <div class="countdown-display" v-if="isCountdown">
            <div class="countdown-timer">
              <div class="timer-text">{{ countdown.toFixed(2) }}s</div>
              <div class="timer-bar">
                <div class="timer-progress" :style="{ width: (countdown / 8.88 * 100) + '%' }"></div>
              </div>
            </div>
            <div class="countdown-ring"></div>
          </div>
          <div class="vs-text" v-else>VS</div>
          <div class="battle-energy" v-if="isPlaying">
            <img src="/assets/spr.png" alt="Battle" class="battle-sprite" />
            <span v-for="i in 8" :key="i" class="energy-spark">⚡</span>
          </div>
        </div>

        <!-- Kinny Section -->
        <div class="player-section">
          <div class="player-label">KINNY</div>
          <div class="choice-display kinny-display" :class="{ 'choice-locked': isPlaying }">
            <!-- Slot Machine Animation for Kinny -->
            <div class="kinny-slot-machine" v-if="isCountdown || isPlaying">
              <div class="slot-reel" :class="{ 
                'slot-spinning': isCountdown, 
                'slot-stopping': slotStopping 
              }">
                <div class="slot-symbol">✊</div>
                <div class="slot-symbol">👋</div>
                <div class="slot-symbol">✌️</div>
                <div class="slot-symbol">✊</div>
                <div class="slot-symbol">👋</div>
                <div class="slot-symbol">✌️</div>
                <div class="slot-symbol">✊</div>
                <div class="slot-symbol">👋</div>
                <div class="slot-symbol">✌️</div>
              </div>
              <div class="slot-window"></div>
            </div>
            <!-- Final Kinny Choice -->
            <div v-else class="choice-emoji kinny-choice">
              {{ petChoice ? getKinnyEmoji(petChoice) : '🤖' }}
            </div>
            <div class="choice-ring" v-if="isPlaying"></div>
          </div>
        </div>
      </div>

      <!-- Energy Warning -->
      <div class="energy-warning" v-if="energyWarning">
        <div class="warning-icon">⚠️</div>
        <div class="warning-text">{{ energyWarning }}</div>
      </div>

      <!-- Fast Choice Buttons -->
      <div class="fast-choices" v-if="!gameResult">
        <button 
          v-for="(choice, key) in choices" 
          :key="key"
          class="fast-btn"
          :class="{ 
            'btn-selected': playerChoice === key,
            'btn-disabled': (isCountdown && countdown <= 1) || !canPlayGame
          }"
          @click="selectChoice(key as ChoiceType)"
          :disabled="!canPlayGame"
        >
        >
          <div class="btn-glow"></div>
          <div class="btn-emoji">{{ choice.emoji }}</div>
          <div class="btn-ring" v-if="playerChoice === key"></div>
        </button>
      </div>
    </div>

    <!-- 🏆 使用新的独立游戏结果组件 -->
    <GameResultModal
      :isVisible="gameResult !== null"
      :result="gameResult || 'lose'"
      :playerChoice="choices[playerChoice].emoji"
      :kinnyChoice="petChoice ? getKinnyEmoji(petChoice) : '🤖'"
      :hungerCost="GAME_HUNGER_COST"
      :foodReward="lastFoodReward"
      :canPlayAgain="canPlayGame"
      @close="closeGame"
      @playAgain="startNewRound"
      @needFood="$emit('close')"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { usePetStore } from '@/stores/petStore'
import GameResultModal from './GameResultModal.vue'

interface FoodReward {
  type: string
  display: string
  amount: number
}

interface GameEmits {
  close: []
  gameEnd: [result: 'win' | 'lose' | 'draw', points: number, hungerCost: number]
}

interface Props {
  isVisible: boolean
  currentHunger?: number  // 添加hunger prop
}

const props = defineProps<Props>()
const emit = defineEmits<GameEmits>()

// Pet store for hunger management - 统一数据源
const petStore = usePetStore()

type ChoiceType = 'rock' | 'paper' | 'scissors'

interface Choice {
  emoji: string
  name: string
  beats: ChoiceType
}

const choices: Record<ChoiceType, Choice> = {
  rock: { emoji: '✊', name: 'Rock', beats: 'scissors' },
  paper: { emoji: '👋', name: 'Paper', beats: 'rock' },
  scissors: { emoji: '✌️', name: 'Scissors', beats: 'paper' }
}

// Fast Game State
const playerChoice = ref<ChoiceType>('scissors')
const petChoice = ref<ChoiceType | null>(null)
const isCountdown = ref(false)
const lastFoodReward = ref<FoodReward | null>(null)
const isPlaying = ref(false)
const slotStopping = ref(false)
const gameResult = ref<'win' | 'lose' | 'draw' | null>(null)
const countdown = ref(8.88)

// 🔧 精准定时器管理 - 防止后台扣血
const activeTimers = ref<Set<ReturnType<typeof setTimeout>>>(new Set())
const activeIntervals = ref<Set<ReturnType<typeof setInterval>>>(new Set())
const isComponentActive = ref(true)
// 🆕 AbortController 用于取消异步操作 - 最佳实践
const activeAbortController = ref<AbortController | null>(null)

// Hunger management - 精准获取实时数据
const GAME_HUNGER_COST = 8  // Playing costs 8 hunger points
// WIN_HUNGER_REWARD removed: a win grants food only, never hunger as well, so rewards do not stack
const currentHunger = computed(() => {
  // 优先使用prop传入的值，否则从store获取最新值
  if (props.currentHunger !== undefined) {
    return props.currentHunger
  }
  return petStore.pet?.status?.hunger ?? 0
})
const hungerAfterGame = computed(() => {
  // win or lose, only the game cost is deducted; winning is rewarded through the food inventory
  return Math.max(0, currentHunger.value - GAME_HUNGER_COST)
})
const canPlayGame = computed(() => currentHunger.value >= GAME_HUNGER_COST)

// Computed Properties
const resultClass = computed(() => {
  switch (gameResult.value) {
    case 'win': return 'result-win'
    case 'lose': return 'result-lose'
    case 'draw': return 'result-draw'
    default: return ''
  }
})

const resultIcon = computed(() => {
  switch (gameResult.value) {
    case 'win': return '🎉'
    case 'lose': return '😅'
    case 'draw': return '🤝'
    default: return ''
  }
})

const resultMessage = computed(() => {
  switch (gameResult.value) {
    case 'win': return 'VICTORY!'
    case 'lose': return 'DEFEAT!'
    case 'draw': return 'DRAW!'
    default: return ''
  }
})

const pointsMessage = computed(() => {
  const points = calculatePoints()
  if (points > 0) {
    return `+${points} PTS`
  } else {
    return '+10 PTS'
  }
})

const hungerMessage = computed(() => {
  // 所有情况都只显示游戏成本，胜利奖励通过食物显示
  return `-${GAME_HUNGER_COST} HUNGER`
})

const rewardMessage = computed(() => {
  if (gameResult.value === 'win') {
    return '� Victory Treat: Food Reward!'
  } else if (gameResult.value === 'draw') {
    return '🤝 Fair Play'
  } else {
    return '💪 Try Again!'
  }
})

const energyWarning = computed(() => {
  if (!canPlayGame.value) {
    return "Your pet is too tired to play! Feed first."
  } else if (currentHunger.value <= 20) {
    return "Warning: Your pet is getting hungry!"
  }
  return ""
})

// 🔧 安全定时器函数 - 防止内存泄漏和后台执行
function safeSetTimeout(callback: () => void, delay: number): ReturnType<typeof setTimeout> | null {
  if (!isComponentActive.value) {
    console.log('[Game] 🛑 Blocked setTimeout - component inactive')
    return null
  }
  
  const timerId = setTimeout(() => {
    activeTimers.value.delete(timerId)
    // 🆕 执行前再次检查组件状态和中断信号
    if (isComponentActive.value && (!activeAbortController.value || !activeAbortController.value.signal.aborted)) {
      callback()
    } else {
      console.log('[Game] 🛑 Skipped setTimeout callback - component inactive or aborted')
    }
  }, delay)
  
  activeTimers.value.add(timerId)
  return timerId
}

function safeSetInterval(callback: () => void, delay: number): ReturnType<typeof setInterval> | null {
  if (!isComponentActive.value) {
    console.log('[Game] 🛑 Blocked setInterval - component inactive')
    return null
  }
  
  const intervalId = setInterval(() => {
    // 🆕 每次执行前检查组件状态和中断信号
    if (!isComponentActive.value || (activeAbortController.value && activeAbortController.value.signal.aborted)) {
      clearInterval(intervalId)
      activeIntervals.value.delete(intervalId)
      console.log('[Game] 🛑 Cleared setInterval - component inactive or aborted')
      return
    }
    callback()
  }, delay)
  
  activeIntervals.value.add(intervalId)
  return intervalId
}

function clearAllTimers() {
  // 清理所有活跃的定时器
  activeTimers.value.forEach(timerId => {
    clearTimeout(timerId)
  })
  activeTimers.value.clear()
  
  // 清理所有活跃的间隔器
  activeIntervals.value.forEach(intervalId => {
    clearInterval(intervalId)
  })
  activeIntervals.value.clear()
  
  // 🆕 取消所有进行中的异步操作 - 最佳实践
  if (activeAbortController.value && !activeAbortController.value.signal.aborted) {
    activeAbortController.value.abort('Component destroyed or reset')
    console.log('[Game] 🛑 Aborted ongoing async operations')
  }
  activeAbortController.value = null
}

// 🆕 游戏状态验证工具函数 - 最佳实践
function isGameOperationSafe(): boolean {
  const isSafe = isComponentActive.value && 
                (!activeAbortController.value || !activeAbortController.value.signal.aborted)
  
  if (!isSafe) {
    console.log('[Game] 🛑 Game operation not safe:', {
      componentActive: isComponentActive.value,
      hasAbortController: !!activeAbortController.value,
      isAborted: activeAbortController.value?.signal.aborted
    })
  }
  
  return isSafe
}

function logGameState(context: string) {
  console.log(`[Game] 📊 ${context}:`, {
    componentActive: isComponentActive.value,
    isCountdown: isCountdown.value,
    isPlaying: isPlaying.value,
    gameResult: gameResult.value,
    activeTimersCount: activeTimers.value.size,
    activeIntervalsCount: activeIntervals.value.size,
    hasAbortController: !!activeAbortController.value,
    isAborted: activeAbortController.value?.signal.aborted
  })
}

// Helper function for Kinny's emoji
function getKinnyEmoji(choice: ChoiceType): string {
  const kinnyEmojiMap: Record<ChoiceType, string> = {
    rock: '✊',
    paper: '👋', 
    scissors: '✌️'
  }
  return kinnyEmojiMap[choice] || '🤖'
}

// 🍎 食物奖励辅助函数
function getFoodDisplay(foodType: string): string {
  const foodDisplayMap: Record<string, string> = {
    'apple': '🍎 Fresh Apple',
    'banana': '🍌 Sweet Banana', 
    'orange': '🍊 Juicy Orange',
    'strawberry': '🍓 Sweet Strawberry',
    'grapes': '🍇 Purple Grapes',
    'watermelon': '🍉 Watermelon Slice',
    'pineapple': '🍍 Tropical Pineapple',
    'cherry': '🍒 Sweet Cherry',
    'peach': '🍑 Ripe Peach',
    'mango': '🥭 Sweet Mango',
    'kiwi': '🥝 Kiwi Fruit'
  }
  return foodDisplayMap[foodType] || `🍎 ${foodType}`
}

function getFoodAmount(result: string): number {
  switch (result) {
    case 'win': return 1
    case 'lose': return 0
    case 'draw': return 0
    default: return 0
  }
}

// Fast Game Logic
function selectChoice(choice: ChoiceType) {
  // 🆕 严格的状态检查 - 最佳实践
  if (!isComponentActive.value) {
    console.log('[Game] 🛑 Choice selection blocked - component inactive')
    return
  }
  
  if (isCountdown.value && countdown.value <= 1) return
  if (!canPlayGame.value) return  // Prevent playing if hunger too low
  
  // 🆕 检查是否有进行中的异步操作
  if (activeAbortController.value && !activeAbortController.value.signal.aborted) {
    console.log('[Game] 🛑 Choice selection blocked - async operation in progress')
    return
  }
  
  playerChoice.value = choice
  
  if (!isCountdown.value && !isPlaying.value) {
    startFastGame()
  }
}

function startFastGame() {
  if (!isGameOperationSafe()) {
    logGameState('startFastGame blocked')
    return
  }
  
  logGameState('startFastGame starting')
  isCountdown.value = true
  countdown.value = 8.88
  
  const countdownInterval = safeSetInterval(() => {
    countdown.value = Math.max(0, countdown.value - 0.1)
    if (countdown.value <= 0) {
      // 安全清理这个特定的interval
      if (countdownInterval) {
        clearInterval(countdownInterval)
        activeIntervals.value.delete(countdownInterval)
      }
      playGame()
    }
  }, 100)
}

function playGame() {
  if (!isGameOperationSafe()) {
    logGameState('playGame blocked')
    return
  }
  
  logGameState('playGame starting')
  isCountdown.value = false
  isPlaying.value = true
  
  safeSetTimeout(() => {
    if (!isGameOperationSafe()) return
    slotStopping.value = true
  }, 200)
  
  safeSetTimeout(async () => {
    if (!isGameOperationSafe()) return
    
    const petChoices: ChoiceType[] = ['rock', 'paper', 'scissors']
    petChoice.value = petChoices[Math.floor(Math.random() * petChoices.length)]
    
    safeSetTimeout(async () => {
      if (!isGameOperationSafe()) {
        logGameState('playGame final stage blocked')
        return
      }
      
      slotStopping.value = false
      
      let result: 'win' | 'lose' | 'draw'
      if (playerChoice.value === petChoice.value) {
        result = 'draw'
      } else if (choices[playerChoice.value].beats === petChoice.value) {
        result = 'win'
      } else {
        result = 'lose'
      }
      
      gameResult.value = result
      
      // 🔗 Call backend API for game result and hunger management
      // 🚨 关键：只有组件活跃时才调用API
      if (!isComponentActive.value) {
        console.log('[Game] 🛑 Component destroyed, skipping API call to prevent background deduction')
        return
      }
      
      // 🆕 a fresh AbortController for this call
      activeAbortController.value = new AbortController()
      const currentAbortController = activeAbortController.value
      
      try {
        // 🆕 双重保护：组件状态 + AbortController
        if (!isComponentActive.value || currentAbortController.signal.aborted) {
          console.log('[Game] 🛑 Component destroyed or operation aborted before API call')
          return
        }
        
        const gameResponse = await petStore.playGame('rock-paper-scissors', result, GAME_HUNGER_COST)
        
        // 🚨 API调用后再次检查组件状态和中断信号
        if (!isComponentActive.value || currentAbortController.signal.aborted) {
          console.log('[Game] 🛑 Component destroyed or operation aborted after API call, not updating UI')
          return
        }
        
        if (gameResponse?.success) {
          console.log('[Game] 🎮 Backend response:', gameResponse)
          console.log('[Game] 🏆 Result:', gameResponse.result) 
          console.log('[Game] 🍎 Food reward:', gameResponse.foodReward)
          
          // 📦 精准食物奖励追踪：确保胜利时显示奖励
          if (gameResponse.result === 'win') {
            if (gameResponse.foodReward) {
              lastFoodReward.value = {
                type: gameResponse.foodReward,
                display: getFoodDisplay(gameResponse.foodReward),
                amount: getFoodAmount(gameResponse.result)
              }
              console.log('🎁 ✅ Food reward successfully set:', lastFoodReward.value)
            } else {
              console.log('🎁 ⚠️ Win but no food reward from backend!')
              // 即使后端没有返回，也设置一个默认奖励确保UI显示
              lastFoodReward.value = {
                type: 'apple',
                display: getFoodDisplay('apple'),
                amount: 1
              }
            }
          } else {
            lastFoodReward.value = null
            console.log('🎁 ❌ No food reward for result:', gameResponse.result)
          }
          
          // Backend已经处理了hunger变化，UI只显示结果
        } else {
          console.error('[Game] Backend error:', gameResponse?.error)
          if (gameResponse?.error?.includes('not enough hunger')) {
            // 饥饿值不足，重置游戏状态
            resetGame()
            return
          }
        }
      } catch (error) {
        // 🆕 检查是否是主动取消的操作
        if (currentAbortController.signal.aborted) {
          console.log('[Game] 🛑 API call was aborted, not processing error')
          return
        }
        
        console.error('[Game] API call failed:', error)
        
        // 🚨 错误处理时也要检查组件状态
        if (!isComponentActive.value) {
          console.log('[Game] 🛑 Component destroyed during error handling')
          return
        }
        
        // 🔄 Fallback: 如果API失败，使用本地饥饿值管理
        if (petStore.pet?.status) {
          // win or lose, only the game cost is deducted; winning is rewarded through the food inventory
          petStore.pet.status.hunger = Math.max(0, 
            petStore.pet.status.hunger - GAME_HUNGER_COST)
        }
      } finally {
        // 🆕 清理 AbortController - 最佳实践
        if (activeAbortController.value === currentAbortController) {
          activeAbortController.value = null
        }
      }
      
      // 🚨 最后检查组件状态和中断信号再更新UI
      if (!isComponentActive.value || (activeAbortController.value && activeAbortController.value.signal.aborted)) {
        console.log('[Game] 🛑 Component destroyed or operation aborted before UI update')
        return
      }
      
      isPlaying.value = false
      
      // Emit game end with hunger cost information
      emit('gameEnd', result, calculatePoints(), GAME_HUNGER_COST)
      
      // 🎯 移除自动关闭 - 让玩家自主控制游戏体验
    }, 600)
  }, 400)
}

function calculatePoints(): number {
  switch (gameResult.value) {
    case 'win': return Math.floor(Math.random() * 30) + 40
    case 'lose': return Math.floor(Math.random() * 10) + 5
    case 'draw': return 10
    default: return 0
  }
}

function startNewRound() {
  // 检查组件状态和饥饿值
  if (!isComponentActive.value || !canPlayGame.value) {
    return
  }
  
  // 平滑重置游戏状态
  resetGameForNewRound()
  
  // 确保状态完全重置后再开始新游戏
  nextTick(() => {
    if (!isComponentActive.value) return  // 🔧 再次检查组件状态
    
    safeSetTimeout(() => {
      if (isComponentActive.value) {  // 🔧 最终检查
        startFastGame()
      }
    }, 200) // 减少延迟，提升连续游戏体验
  })
}

// 新增：专门为新回合设计的重置函数
function resetGameForNewRound() {
  // 只重置必要的游戏状态，保持UI连贯性
  playerChoice.value = 'scissors'
  petChoice.value = null
  gameResult.value = null
  isCountdown.value = false
  isPlaying.value = false
  slotStopping.value = false
  countdown.value = 8.88
  
  // 🔧 精准清理定时器，避免暴力清理
  clearAllTimers()
}

function resetGame() {
  // 使用强制重置确保完全清理
  forceCompleteReset()
}

function closeGame() {
  // 🔧 标记组件为非活跃状态，阻止后台操作
  isComponentActive.value = false
  
  // 强制完全重置确保下次是全新游戏
  forceCompleteReset()
  emit('close')
}

function forceCompleteReset() {
  // 🔧 立即标记组件为非活跃状态
  isComponentActive.value = false
  
  // 🔧 精准清理所有定时器和异步操作
  clearAllTimers()
  
  // 强制完全重置所有状态并flush渲染
  playerChoice.value = 'scissors'
  petChoice.value = null
  gameResult.value = null
  isCountdown.value = false
  isPlaying.value = false
  slotStopping.value = false
  countdown.value = 8.88
  lastFoodReward.value = null  // 🆕 清理食物奖励状态
  
  // 强制触发reactivity更新
  nextTick(() => {
    // 确保DOM完全更新
    // 🔧 重新激活组件状态，为下次使用做准备
    isComponentActive.value = true
    // 🆕 重置 AbortController
    activeAbortController.value = null
  })
}

onMounted(() => {
  // 🔧 确保组件状态为活跃
  isComponentActive.value = true
  
  // 确保每次打开都是全新状态
  forceCompleteReset()
  
  safeSetTimeout(() => {
    if (isComponentActive.value && !gameResult.value && !isCountdown.value && !isPlaying.value) {
      startFastGame()
    }
  }, 300)
})

// 🔧 组件销毁时的精准清理
onUnmounted(() => {
  console.log('[Game] 🗑️ Component unmounting, cleaning up all timers')
  isComponentActive.value = false
  clearAllTimers()
})

// Watch for visibility changes to reset state
watch(() => props.isVisible, (newVisible) => {
  if (newVisible) {
    // 🔧 重新激活组件
    isComponentActive.value = true
    
    // 每次显示时都重置状态，确保全新游戏体验
    forceCompleteReset()
    
    safeSetTimeout(() => {
      if (isComponentActive.value && !gameResult.value && !isCountdown.value && !isPlaying.value) {
        startFastGame()
      }
    }, 300)
  } else {
    // 🔧 组件隐藏时立即停止所有活动
    isComponentActive.value = false
    clearAllTimers()
  }
})
</script>

<style scoped>
.rps-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(15px);
  animation: overlaySlideIn 0.3s ease-out;
}

.rps-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 24px;
  padding: 20px;
  max-width: 420px;
  width: 90vw;
  box-shadow: 
    0 25px 80px rgba(0, 0, 0, 0.6),
    0 0 40px rgba(59, 130, 246, 0.3);
  border: 2px solid rgba(59, 130, 246, 0.4);
  position: relative;
  overflow: hidden;
  animation: containerBounceIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.rps-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.2) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(168, 85, 247, 0.15) 0%, transparent 50%);
  pointer-events: none;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  position: relative;
}

/* Hunger Status Styles */
.hunger-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 12px;
  padding: 8px 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.hunger-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.hunger-icon {
  font-size: 16px;
}

.hunger-value {
  font-size: 14px;
  font-weight: bold;
  color: #4ade80;
  transition: color 0.3s ease;
}

.hunger-value.low-hunger {
  color: #fbbf24;
}

.hunger-value.critical-hunger {
  color: #ef4444;
  animation: hungerPulse 1s infinite;
}

.game-cost-info {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
}

.cost-text {
  font-style: italic;
}

@keyframes hungerPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.header-sprite {
  width: 120px;
  height: 120px;
  object-fit: contain;
  animation: headerSpriteGlow 2s ease-in-out infinite;
  filter: drop-shadow(0 0 35px rgba(59, 130, 246, 1.2)) drop-shadow(0 0 70px rgba(168, 85, 247, 0.8));
  background: none !important;
  background-color: transparent !important;
  background-image: none !important;
  border: none !important;
  box-shadow: none !important;
  opacity: 1;
  z-index: 10;
  position: relative;
  image-rendering: -webkit-optimize-contrast;
  mix-blend-mode: screen;
}

.game-title {
  color: #3b82f6;
  font-size: 18px;
  font-weight: 900;
  margin: 0;
  text-shadow: 0 0 20px rgba(59, 130, 246, 0.8), 0 0 40px rgba(168, 85, 247, 0.6);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  text-align: center;
  white-space: nowrap;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(239, 68, 68, 0.2);
  border: 2px solid rgba(239, 68, 68, 0.4);
  color: #ef4444;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: bold;
  z-index: 1000;
  font-size: 18px;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  transform: scale(1.1);
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.5);
}

.fast-arena {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 20px 0;
  position: relative;
}

.player-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.player-label {
  color: #3b82f6;
  font-size: 12px;
  font-weight: 900;
  margin-bottom: 8px;
  text-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
  letter-spacing: 2px;
  text-transform: uppercase;
}

.choice-display {
  width: 90px;
  height: 90px;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid rgba(59, 130, 246, 0.3);
  backdrop-filter: blur(10px);
  position: relative;
  transition: all 0.3s ease;
}

.choice-display.choice-locked {
  border-color: #3b82f6;
  box-shadow: 0 0 30px rgba(59, 130, 246, 0.6);
  animation: choiceLocked 0.5s ease-out;
}

.choice-emoji {
  font-size: 36px;
  transition: all 0.2s ease;
}

.player-choice {
  animation: playerPulse 0.8s ease-in-out infinite;
}

.kinny-choice {
  animation: kinnyPulse 0.8s ease-in-out infinite;
}

.kinny-slot-machine {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 50%;
}

.slot-reel {
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: transform 0.1s ease;
}

.slot-reel.slot-spinning {
  animation: slotSpinFast 0.2s linear infinite;
  opacity: 0.9;
  filter: blur(1px);
}

.slot-reel.slot-stopping {
  animation: slotSpinSlow 2s ease-out forwards;
  opacity: 1;
  filter: blur(0px);
}

.slot-symbol {
  font-size: 36px;
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

.slot-window {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 3px solid rgba(59, 130, 246, 0.6);
  border-radius: 50%;
  box-shadow: 
    inset 0 0 20px rgba(0, 0, 0, 0.3),
    0 0 30px rgba(59, 130, 246, 0.4);
  pointer-events: none;
  background: 
    linear-gradient(to bottom, 
      transparent 0%, 
      rgba(0, 0, 0, 0.1) 30%, 
      transparent 70%, 
      transparent 100%);
}

.choice-ring {
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  bottom: -5px;
  border: 3px solid #3b82f6;
  border-radius: 50%;
  animation: ringSpin 1s linear infinite;
}

.vs-divider {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  margin: 0 20px;
}

.countdown-display {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.countdown-timer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.timer-text {
  color: #f59e0b;
  font-size: 24px;
  font-weight: 900;
  text-shadow: 0 0 20px rgba(245, 158, 11, 0.8);
  font-family: 'Courier New', monospace;
  letter-spacing: 1px;
  min-width: 80px;
  text-align: center;
}

.timer-bar {
  width: 100px;
  height: 6px;
  background: rgba(245, 158, 11, 0.2);
  border-radius: 3px;
  overflow: hidden;
  border: 1px solid rgba(245, 158, 11, 0.4);
}

.timer-progress {
  height: 100%;
  background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%);
  border-radius: 3px;
  transition: width 0.1s linear;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.6);
}

.countdown-ring {
  position: absolute;
  width: 120px;
  height: 120px;
  border: 3px solid transparent;
  border-top-color: #f59e0b;
  border-radius: 50%;
  animation: countdownSpin 1s linear infinite;
  opacity: 0.7;
}

.vs-text {
  color: #10b981;
  font-size: 18px;
  font-weight: 900;
  text-shadow: 0 0 15px rgba(16, 185, 129, 0.6);
  letter-spacing: 2px;
}

.battle-energy {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.battle-sprite {
  width: 140px;
  height: 140px;
  object-fit: contain;
  animation: spriteGlow 0.6s ease-in-out infinite;
  filter: drop-shadow(0 0 40px rgba(59, 130, 246, 1.5)) drop-shadow(0 0 80px rgba(168, 85, 247, 1.2));
  transform-origin: center;
  background: none !important;
  background-color: transparent !important;
  background-image: none !important;
  border: none !important;
  box-shadow: none !important;
  mix-blend-mode: screen;
  opacity: 1;
  z-index: 5;
  image-rendering: -webkit-optimize-contrast;
}

.energy-spark {
  position: absolute;
  font-size: 14px;
  color: #f59e0b;
  animation: energySpark 0.4s ease-in-out infinite;
}

.energy-spark:nth-child(1) { animation-delay: 0s; transform: translate(-30px, -20px); }
.energy-spark:nth-child(2) { animation-delay: 0.05s; transform: translate(25px, -25px); }
.energy-spark:nth-child(3) { animation-delay: 0.1s; transform: translate(-20px, 15px); }
.energy-spark:nth-child(4) { animation-delay: 0.15s; transform: translate(30px, 10px); }
.energy-spark:nth-child(5) { animation-delay: 0.2s; transform: translate(0px, -35px); }
.energy-spark:nth-child(6) { animation-delay: 0.25s; transform: translate(-35px, 0px); }
.energy-spark:nth-child(7) { animation-delay: 0.3s; transform: translate(20px, 25px); }
.energy-spark:nth-child(8) { animation-delay: 0.35s; transform: translate(-15px, -30px); }

/* Energy Warning Styles */
.energy-warning {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(239, 68, 68, 0.2);
  border: 2px solid #ef4444;
  border-radius: 12px;
  padding: 12px 16px;
  margin: 16px 0;
  animation: warningPulse 2s infinite;
}

.warning-icon {
  font-size: 20px;
}

.warning-text {
  color: #fecaca;
  font-weight: 600;
  font-size: 14px;
  text-align: center;
}

@keyframes warningPulse {
  0%, 100% { 
    border-color: #ef4444;
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  }
  50% { 
    border-color: #dc2626;
    box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
  }
}

.fast-choices {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin: 20px 0;
}

.fast-btn {
  background: rgba(59, 130, 246, 0.1);
  border: 2px solid rgba(59, 130, 246, 0.3);
  border-radius: 20px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 70px;
  min-height: 70px;
  position: relative;
  overflow: hidden;
  /* 移动端触摸tuning */
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.fast-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 10px 30px rgba(59, 130, 246, 0.4);
}

.fast-btn:active {
  transform: translateY(-1px) scale(1.02);
  transition: all 0.1s ease;
}

.fast-btn.btn-selected {
  background: rgba(59, 130, 246, 0.3);
  border-color: #3b82f6;
  box-shadow: 0 0 25px rgba(59, 130, 246, 0.6);
  transform: scale(1.1);
}

.fast-btn.btn-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  pointer-events: none;
}

.btn-glow {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 70%);
  border-radius: 20px;
  opacity: 0;
  transition: all 0.3s ease;
}

.fast-btn.btn-selected .btn-glow {
  opacity: 1;
  animation: glowPulse 1s ease-in-out infinite;
}

.btn-emoji {
  font-size: 28px;
  z-index: 2;
}

.btn-ring {
  position: absolute;
  top: -3px;
  left: -3px;
  right: -3px;
  bottom: -3px;
  border: 2px solid #3b82f6;
  border-radius: 20px;
  animation: btnRingSpin 1s linear infinite;
}

.instant-result {
  text-align: center;
  margin: 20px 0;
  animation: resultBlast 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.result-blast {
  margin-bottom: 16px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 2px solid transparent;
}

.result-blast.result-win {
  border-color: #10b981;
  box-shadow: 0 0 30px rgba(16, 185, 129, 0.4);
}

.result-blast.result-lose {
  border-color: #ef4444;
  box-shadow: 0 0 30px rgba(239, 68, 68, 0.4);
}

.result-blast.result-draw {
  border-color: #f59e0b;
  box-shadow: 0 0 30px rgba(245, 158, 11, 0.4);
}

.result-icon {
  font-size: 40px;
  margin-bottom: 8px;
  animation: resultIconBounce 0.6s ease-out;
}

.result-text {
  font-size: 24px;
  font-weight: 900;
  margin-bottom: 4px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  letter-spacing: 1px;
}

.result-win .result-text { color: #10b981; }
.result-lose .result-text { color: #ef4444; }
.result-draw .result-text { color: #f59e0b; }

.result-score {
  color: #ffffff;
  font-size: 18px;
  font-weight: bold;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
  margin-bottom: 8px;
}

.hunger-cost-display {
  color: #fbbf24;
  font-size: 14px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  margin-bottom: 8px;
  opacity: 0.9;
}

.hunger-cost-display.hunger-gain {
  color: #4ade80;
  animation: hungerGain 0.8s ease-out;
}

.reward-message {
  color: #fcd34d;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  margin-bottom: 8px;
  animation: rewardGlow 1s ease-in-out infinite alternate;
}

@keyframes hungerGain {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); color: #22c55e; }
  100% { transform: scale(1); }
}

@keyframes rewardGlow {
  from { text-shadow: 0 0 5px rgba(252, 211, 77, 0.5); }
  to { text-shadow: 0 0 15px rgba(252, 211, 77, 0.8); }
}

/* 🎉 胜利庆祝动画 */
.victory-celebration {
  margin: 12px 0;
  text-align: center;
  animation: celebrationBurst 0.8s ease-out;
}

.celebration-stars {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.star {
  font-size: 16px;
  animation: starTwinkle 1.5s ease-in-out infinite;
  display: inline-block;
}

.star:nth-child(1) { animation-delay: 0s; }
.star:nth-child(2) { animation-delay: 0.1s; }
.star:nth-child(3) { animation-delay: 0.2s; }
.star:nth-child(4) { animation-delay: 0.3s; }
.star:nth-child(5) { animation-delay: 0.4s; }
.star:nth-child(6) { animation-delay: 0.5s; }
.star:nth-child(7) { animation-delay: 0.6s; }
.star:nth-child(8) { animation-delay: 0.7s; }

.victory-message {
  color: #fbbf24;
  font-size: 14px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1px;
  animation: victoryGlow 1s ease-in-out infinite alternate;
}

@keyframes celebrationBurst {
  0% {
    opacity: 0;
    transform: scale(0.5);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes starTwinkle {
  0%, 100% {
    transform: scale(1) rotate(0deg);
    opacity: 0.7;
  }
  25% {
    transform: scale(1.3) rotate(90deg);
    opacity: 1;
  }
  50% {
    transform: scale(0.8) rotate(180deg);
    opacity: 0.8;
  }
  75% {
    transform: scale(1.2) rotate(270deg);
    opacity: 1;
  }
}

@keyframes victoryGlow {
  from { 
    text-shadow: 0 0 10px rgba(251, 191, 36, 0.6);
    color: #fbbf24;
  }
  to { 
    text-shadow: 0 0 20px rgba(251, 191, 36, 1);
    color: #fcd34d;
  }
}

.hunger-after {
  color: #94a3b8;
  font-size: 12px;
  text-align: center;
  margin-top: 8px;
  font-style: italic;
}

.result-details {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.match-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 16px;
  color: #e5e7eb;
}

.you-played {
  color: #3b82f6;
  font-weight: bold;
}

.vs-separator {
  color: #6b7280;
  font-size: 14px;
}

.kinny-played {
  color: #f59e0b;
  font-weight: bold;
}

.result-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.rapid-play-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 16px 32px;
  border-radius: 20px;
  font-size: 16px;
  font-weight: 900;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
  display: flex;
  align-items: center;
  gap: 10px;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  margin-bottom: 12px;
  position: relative;
  overflow: hidden;
}

.rapid-play-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  transition: left 0.6s ease;
}

.rapid-play-btn:hover::before {
  left: 100%;
}

.rapid-play-btn:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 12px 35px rgba(16, 185, 129, 0.6);
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.rapid-play-btn.btn-disabled {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4);
  cursor: not-allowed;
  animation: pulseWarning 2s ease-in-out infinite;
}

.rapid-play-btn.btn-disabled:hover {
  transform: none;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4);
}

.rapid-play-btn.btn-disabled::before {
  display: none;
}

@keyframes pulseWarning {
  0%, 100% { 
    box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4);
  }
  50% { 
    box-shadow: 0 8px 25px rgba(239, 68, 68, 0.7);
  }
}

.btn-spark {
  animation: sparkRotate 1s linear infinite;
}

.manual-close-btn {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 15px rgba(75, 85, 99, 0.3);
  display: flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.manual-close-btn:hover {
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 6px 20px rgba(75, 85, 99, 0.4);
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
}

.btn-icon {
  font-size: 12px;
  opacity: 0.8;
}

/* Animations */
@keyframes overlaySlideIn {
  0% { opacity: 0; }
  100% { opacity: 1; }
}

@keyframes containerBounceIn {
  0% { opacity: 0; transform: scale(0.8) translateY(50px); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}

@keyframes choiceLocked {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

@keyframes playerPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

@keyframes kinnyPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

@keyframes slotSpinFast {
  0% { transform: translateY(0); }
  100% { transform: translateY(-90px); }
}

@keyframes slotSpinSlow {
  0% { 
    transform: translateY(-90px); 
    animation-timing-function: linear;
  }
  20% { 
    transform: translateY(-180px); 
    animation-timing-function: ease-out;
  }
  40% { 
    transform: translateY(-270px); 
    animation-timing-function: ease-out;
  }
  60% { 
    transform: translateY(-360px); 
    animation-timing-function: ease-out;
  }
  80% { 
    transform: translateY(-405px); 
    animation-timing-function: ease-out;
  }
  90% { 
    transform: translateY(-425px); 
    animation-timing-function: ease-out;
  }
  95% { 
    transform: translateY(-435px); 
    animation-timing-function: ease-out;
  }
  100% { 
    transform: translateY(-450px); 
    animation-timing-function: ease-out;
  }
}

@keyframes slotSpin {
  0% { transform: translateY(0); }
  100% { transform: translateY(-90px); }
}

@keyframes slotStop {
  0% { transform: translateY(-90px) scale(0.8); }
  50% { transform: translateY(-45px) scale(1.2); }
  100% { transform: translateY(0) scale(1); }
}

@keyframes ringSpin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes countdownSpin {
  0% { transform: rotate(0deg); opacity: 0.4; }
  100% { transform: rotate(360deg); opacity: 0.8; }
}

@keyframes spriteGlow {
  0%, 100% { 
    transform: scale(1) rotate(0deg); 
    filter: drop-shadow(0 0 15px rgba(59, 130, 246, 0.8)) drop-shadow(0 0 30px rgba(168, 85, 247, 0.4)); 
  }
  25% { 
    transform: scale(1.1) rotate(2deg); 
    filter: drop-shadow(0 0 25px rgba(59, 130, 246, 1)) drop-shadow(0 0 40px rgba(168, 85, 247, 0.6)); 
  }
  50% { 
    transform: scale(1.15) rotate(0deg); 
    filter: drop-shadow(0 0 30px rgba(59, 130, 246, 1.2)) drop-shadow(0 0 50px rgba(168, 85, 247, 0.8)); 
  }
  75% { 
    transform: scale(1.1) rotate(-2deg); 
    filter: drop-shadow(0 0 25px rgba(59, 130, 246, 1)) drop-shadow(0 0 40px rgba(168, 85, 247, 0.6)); 
  }
}

@keyframes energySpark {
  0%, 100% { opacity: 0; transform: scale(0.5); }
  50% { opacity: 1; transform: scale(1.2); }
}

@keyframes glowPulse {
  0%, 100% { opacity: 0.3; transform: scale(0.95); }
  50% { opacity: 0.7; transform: scale(1.05); }
}

@keyframes btnRingSpin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes resultBlast {
  0% { opacity: 0; transform: scale(0.5) rotate(-10deg); }
  70% { transform: scale(1.1) rotate(5deg); }
  100% { opacity: 1; transform: scale(1) rotate(0deg); }
}

@keyframes resultIconBounce {
  0% { transform: scale(0) rotate(180deg); }
  60% { transform: scale(1.3) rotate(-10deg); }
  100% { transform: scale(1) rotate(0deg); }
}

@keyframes sparkRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes headerSpriteGlow {
  0%, 100% { 
    transform: scale(1); 
    filter: drop-shadow(0 0 10px rgba(59, 130, 246, 0.6)); 
  }
  50% { 
    transform: scale(1.05); 
    filter: drop-shadow(0 0 15px rgba(59, 130, 246, 0.9)); 
  }
}

/* Force transparent PNG rendering */
img[src*="spr.png"] {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  border: none !important;
  mix-blend-mode: screen;
}

@media (max-width: 480px) {
  .rps-container {
    padding: 12px;
    max-height: 95vh;
    overflow-y: auto;
  }
  
  .game-header {
    flex-direction: column;
    gap: 12px;
    padding: 16px;
  }
  
  .header-left .header-content {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
  
  .game-title {
    font-size: 18px;
    letter-spacing: 1px;
  }
  
  .header-sprite {
    width: 60px;
    height: 60px;
  }
  
  .hunger-status {
    flex-direction: row;
    gap: 12px;
    width: 100%;
    justify-content: center;
  }
  
  .hunger-info {
    font-size: 14px;
  }
  
  .game-cost-info {
    font-size: 12px;
  }
  
  .close-btn {
    position: absolute;
    top: 12px;
    right: 12px;
    width: 32px;
    height: 32px;
    font-size: 16px;
  }
  
  .fast-arena {
    padding: 20px 12px;
    gap: 16px;
  }
  
  .choice-display {
    width: 65px;
    height: 65px;
  }
  
  .choice-emoji {
    font-size: 26px;
  }
  
  .player-label {
    font-size: 12px;
    margin-bottom: 8px;
  }
  
  .slot-symbol {
    font-size: 26px;
    height: 65px;
  }
  
  .vs-text {
    font-size: 14px;
  }
  
  .countdown-timer .timer-text {
    font-size: 18px;
  }
  
  .timer-bar {
    width: 70px;
    height: 4px;
  }
  
  .countdown-ring {
    width: 90px;
    height: 90px;
  }
  
  .battle-sprite {
    width: 70px;
    height: 70px;
  }
  
  .energy-spark {
    font-size: 12px;
  }
  
  .fast-choices {
    gap: 16px;
    padding: 0 12px;
  }
  
  .fast-btn {
    min-width: 55px;
    min-height: 55px;
    padding: 10px;
  }
  
  .btn-emoji {
    font-size: 22px;
  }
  
  .energy-warning {
    margin: 12px;
    padding: 12px 16px;
    font-size: 14px;
  }
  
  .warning-icon {
    font-size: 18px;
  }
  
  /* 🎮 移动端游戏化结果展示tuning */
  .hunger-status {
    padding: 6px 10px;
  }
  
  .hunger-value {
    font-size: 12px;
  }
  
  .game-cost-info {
    font-size: 9px;
  }
}
</style>

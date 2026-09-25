<template>
  
  <v-app class="home" :style="homeBackgroundStyle">
    <!-- 🎮 双人都在线时的全屏爱心特效 -->
    <div v-if="bothOnline" class="love-screen-effect">
      <div v-for="i in 20" :key="i" class="floating-heart" :style="getHeartStyle(i)">💗</div>
    </div>

    <!-- Main Game Stage -->
    <section class="game-stage">
      <!-- 🎮 顶部：Logo（隐藏以避免遮挡对话） -->
      <!-- <div class="logo-container" @click="goToRecipes">
        <img src="/assets/logo4.png" alt="PlateMate Logo" class="logo clickable-logo" />
      </div> -->

      <!-- 🎮 横向布局：左2按钮 + 中间Arena + 右2按钮 -->
      <div class="horizontal-game-layout">
        <!-- 左侧：2个按钮 -->
        <div class="side-controls left-controls">
          <button 
            class="game-btn-aaa feed-btn-aaa"
            @click="handleFeed"
            :class="{ 'btn-pulsing': isHungry }"
          >
            <div class="btn-bg-aaa"></div>
            <div class="btn-glow-aaa"></div>
            <div class="btn-ripple-aaa"></div>
            <div class="btn-content-aaa">
              <div class="btn-icon-aaa">
                <img src="/assets/feed.png" alt="Feed" class="btn-icon-img-aaa" />
              </div>
              <div class="btn-label-aaa">Feed</div>
              <div class="feed-inventory-badge-aaa" v-if="totalInventory > 0" aria-label="Total food inventory">
                <div class="badge-glow-aaa"></div>
                <div class="badge-count-aaa">{{ totalInventory }}</div>
                <div class="badge-icon-aaa">🍕</div>
              </div>
            </div>
          </button>

          <button 
            class="game-btn-aaa play-btn-aaa"
            @click="handlePlay"
          >
            <div class="btn-bg-aaa"></div>
            <div class="btn-glow-aaa"></div>
            <div class="btn-ripple-aaa"></div>
            <div class="btn-content-aaa">
              <div class="btn-icon-aaa">
                <img src="/assets/play.png" alt="Play" class="btn-icon-img-aaa" />
              </div>
              <div class="btn-label-aaa">Play</div>
            </div>
          </button>
        </div>

        <!-- 中间：Arena -->
        <div class="center-arena-zone">
          <!-- Pet Arena -->
          <div class="pet-arena">
        <!-- Enhanced Background Effects -->
        <div class="arena-bg">
          <div class="arena-rings">
            <div class="ring ring-1"></div>
            <div class="ring ring-2"></div>
            <div class="ring ring-3"></div>
          </div>
          <div class="particle" v-for="i in 15" :key="i" 
               :style="{ 
                 left: Math.random() * 100 + '%',
                 top: Math.random() * 100 + '%',
                 animationDelay: Math.random() * 5 + 's',
                 '--random-x': (Math.random() - 0.5) * 100 + 'px',
                 '--random-y': (Math.random() - 0.5) * 100 + 'px'
               }"></div>
        </div>
        
        <!-- Pet Container -->
        <div class="pet-container">
          <div class="pet-aura"></div>
          <PetStage :status="petStore.petStatus" :size="petSize" bg="transparent" />
          
          <!-- Enhanced Pet Dialogue -->
          <div 
            class="pet-dialogue" 
            :class="{ 'dialogue-active': showBubble }"
            @click="openKinnyModal"
          >
            <div class="dialogue-wrapper">
              <div class="dialogue-bg"></div>
              <div class="dialogue-content">
                <div class="dialogue-text">{{ currentLine }}</div>
                <div class="dialogue-progress" :style="{ width: dialogueProgress + '%' }"></div>
              </div>
              <div class="dialogue-tail"></div>
            </div>
          </div>
        </div> <!-- 结束 pet-container -->
        </div> <!-- 结束 pet-arena -->
      </div> <!-- 结束 center-arena-zone -->

        <!-- 右侧：2个按钮 -->
        <div class="side-controls right-controls">
          <button 
            class="game-btn-aaa recipe-btn-aaa"
            @click="goToRecipes"
          >
            <div class="btn-bg-aaa"></div>
            <div class="btn-glow-aaa"></div>
            <div class="btn-ripple-aaa"></div>
            <div class="btn-content-aaa">
              <div class="btn-icon-aaa">
                <img src="/assets/recipe.png" alt="Recipe" class="btn-icon-img-aaa" />
              </div>
              <div class="btn-label-aaa">Recipe</div>
            </div>
          </button>

          <button 
            class="game-btn-aaa battle-btn-aaa"
            @click="goToMemories"
          >
            <div class="btn-bg-aaa"></div>
            <div class="btn-glow-aaa"></div>
            <div class="btn-ripple-aaa"></div>
            <div class="btn-content-aaa">
              <div class="btn-icon-aaa">
                <img src="/assets/battle.png" alt="Battle" class="btn-icon-img-aaa" />
              </div>
              <div class="btn-label-aaa">Battle</div>
            </div>
          </button>
        </div>
      </div> <!-- end horizontal-game-layout -->

      <!-- 🎯 底部：头像 + 时钟 + 弧线（最小风险改动：移到最下面） -->
      <div class="avatar-row-bottom">
        <!-- 🎯 left clock, the user timezone: show the zone, not the username -->
        <CoupleTimeClock 
          :timezone="selfTimezone"
          class="left-clock"
          @click="handleClockClick"
        />

        <!-- 左头像 -->
        <div 
          class="game-avatar left-avatar"
          :class="{ 
            'online': selfIsOnline, 
            'offline': !selfIsOnline,
            'both-online': bothOnline
          }"
          @click="goToProfile(selfId)"
        >
          <div class="avatar-glow"></div>
          <img :src="selfAvatar" :alt="selfName" class="avatar-img" />
          <div class="avatar-name">{{ selfName }}</div>
          <div class="status-indicator"></div>
        </div>

        <!-- 🎯 SVG圆弧连接线 -->
        <svg class="avatar-arc-connector" viewBox="0 0 200 100" preserveAspectRatio="none">
          <defs>
            <!-- 粉色渐变（双人在线） -->
            <linearGradient id="pinkGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#ff6b9d;stop-opacity:1" />
              <stop offset="50%" style="stop-color:#ffa07a;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#ff6b9d;stop-opacity:1" />
            </linearGradient>
            
            <!-- 绿色渐变（单人在线） -->
            <linearGradient id="greenGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#4ade80;stop-opacity:1" />
              <stop offset="50%" style="stop-color:#86efac;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#4ade80;stop-opacity:1" />
            </linearGradient>

            <!-- 发光滤镜 -->
            <filter id="arcGlow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          
          <!-- 圆弧路径 -->
          <path 
            class="arc-path"
            :class="{ 'both-online': bothOnline, 'single-online': !bothOnline }"
            d="M 10 80 Q 100 -20, 190 80"
            fill="none"
            :stroke="bothOnline ? 'url(#pinkGradient)' : 'url(#greenGradient)'"
            stroke-width="4"
            stroke-linecap="round"
            filter="url(#arcGlow)"
          />
          
          <!-- 动态光点 -->
          <circle class="arc-dot" r="6" fill="#ffffff">
            <animateMotion
              dur="3s"
              repeatCount="indefinite"
              path="M 10 80 Q 100 -20, 190 80"
            />
          </circle>
        </svg>

        <!-- 右头像 -->
        <div 
          class="game-avatar right-avatar"
          :class="{ 
            'online': partnerIsOnline, 
            'offline': !partnerIsOnline,
            'both-online': bothOnline
          }"
          @click="goToProfile(partnerId)"
        >
          <div class="avatar-glow"></div>
          <img :src="partnerAvatar" :alt="partnerName" class="avatar-img" />
          <div class="avatar-name">{{ partnerName }}</div>
          <div class="status-indicator"></div>
        </div>

        <!-- 🎯 right clock, the partner timezone: show the zone, not the username -->
        <CoupleTimeClock 
          :timezone="partnerTimezone"
          class="right-clock"
          @click="handleClockClick"
        />
      </div>

    </section>

    <!-- 🎮 时区对比Modal - Kinny游戏化体验 -->
    <TimezoneCompareModal
      v-model="showTimezoneModal"
      :your-timezone="selfTimezone"
      :partner-timezone="partnerTimezone"
      :partner-is-online="partnerIsOnline"
      :partner-name="partnerName"
    />

    <!-- Optimized Recipe Challenge Panel -->
    <!-- <div class="recipe-panel" :class="{ 'panel-expanded': showRecipePanel }">
      <div class="panel-handle" @click="toggleRecipePanel">
        <div class="handle-indicator"></div>
      </div>
      
      <div class="panel-header">
        <div class="panel-title">
          <div class="title-icon">🎯</div>
          <h3>Roundly Quest</h3>
        </div>
        <div class="panel-status">
          <span class="status-badge">{{ recipesStore.dice?.balance || 3 }} dice left</span>
        </div>
      </div>
      
      <div class="panel-content">
        <div class="quest-description">
          <p>Roll the dice to discover this round's cooking challenge!!!!!!</p>
        </div>
        <RoundlyRecipe 
          :show-instructions="false"
          :show-dice="true"
          :show-tasks="true"
          @recipe-rolled="onRecipeRolled"
        /> -->

        <!-- Redirect to instructions & post -->
        <!-- <div class="text-center">
          <button class="instructions-btn" @click="router.push('/diary')">
            Let's Cook 🍳  
          </button>
        </div>
      </div>
    </div> -->

    <!-- Enhanced Game Feedback -->
    <div v-if="feedbackText" class="game-feedback" :class="feedbackType">
      <div class="feedback-bg"></div>
      <div class="feedback-content">
        <div class="feedback-icon">
          <span v-if="feedbackType === 'success'">✨</span>
          <span v-else-if="feedbackType === 'warning'">⚠️</span>
          <span v-else-if="feedbackType === 'levelup'">🎉</span>
          <span v-else>ℹ️</span>
        </div>
        <div class="feedback-text">{{ feedbackText }}</div>
      </div>
    </div>

    <!-- Enhanced Combo System -->
    <div v-if="comboCount > 1" class="combo-display">
      <div class="combo-bg"></div>
      <div class="combo-content">
        <div class="combo-text">{{ comboCount }}x COMBO!</div>
        <div class="combo-multiplier">+{{ comboMultiplier }}x bonus</div>
      </div>
    </div>

    <!-- Enhanced Level Up Effect -->
    <div v-if="showLevelUp" class="levelup-effect">
      <div class="levelup-bg"></div>
      <div class="levelup-content">
        <div class="levelup-text">LEVEL UP!</div>
        <div class="levelup-score">+{{ levelUpBonus }} pts</div>
      </div>
    </div>

    <!-- Rock Paper Scissors Game -->
    <RockPaperScissorsGame 
      :is-visible="showRPSGame"
      @close="closeRPSGame"
      @game-end="handleRPSGameEnd"
    />

    <!-- Feed Panel -->
    <FeedPanel 
      v-model="showFeedPanel"
      :current-hunger="petStore.health || 0"
      @feed="handleFeedComplete"
    />

    <!-- 🎮 Kinny对话Modal - 点击对话框打开 -->
    <KinnyDialogueModal
      v-model="showKinnyModal"
      :pet-status="petStore.petStatus"
      :message="String(currentLine)"
    />
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import PetStage from '@/components/PetStage.vue'
import PetPrompt from '@/components/PetPrompt.vue'
import RoundlyRecipe from '@/components/RoundlyRecipe.vue'
import RockPaperScissorsGame from '@/components/RockPaperScissorsGame.vue'
import FeedPanel from '@/components/FeedPanel.vue'
import KinnyDialogueModal from '@/components/KinnyDialogueModal.vue'
import CoupleTimeClock from '@/components/CoupleTimeClock.vue' // 🎯 新增：情侣时钟组件
import TimezoneCompareModal from '@/components/TimezoneCompareModal.vue' // 🎮 新增：时区对比Modal
// Feed UI now lives in BaseHeader; no local FeedIsland/InventoryTotal here
import { usePetStore } from '@/stores/petStore'
import { useRecipesStore } from '@/stores/recipeStore'
import { useSystemStore } from '@/stores/systemStore'
import { useUserStore } from '@/stores/userStore'
import { createBackgroundManager } from '@/utils/backgroundManager'
import { trackCheckTimeLag } from '@/utils/analytics' // 📊 Analytics tracking
import defaultAvatar from '@/assets/default-avatar.png'

const ORIGIN = import.meta.env.VITE_API_BASE_URL?.replace('/api', '') || location.origin
const fix = (u?: string) => {
  if (!u) return ''
  if (u.startsWith('http')) {
    // Handle various source URLs:
    // - web:911 (docker container)
    // - localhost:911 (local dev)
    // - <PRODUCTION_HOST>:911 (production)
    return u.replace(
      /^https?:\/\/(web|localhost|45\.79\.163\.242):\d+/i, 
      ORIGIN
    )
  }
  // For relative URLs, prepend with correct origin
  return ORIGIN + u
}

/* ——— Router ——— */
const router = useRouter()

/* ——— 🎯 iOS原生交互体验tuning ——— */
const isMobile = ref(false)
const isIOS = ref(false)
const supportsTouch = ref(false)
const lastTouchTime = ref(0)

/* ——— Responsive Design ——— */
const { mobile, height } = useDisplay()

// 🎮 AAA工业级：宠物响应式尺寸 - 完美填充Arena
const petSize = computed(() => {
  // Check both mobile width and height constraints
  if (mobile.value || height.value < 700) {
    return 340
  }
  return 500
})

/* ——— Stores ——— */
const petStore = usePetStore()
const recipesStore = useRecipesStore()
const systemStore = useSystemStore()
const userStore = useUserStore()

/* ——— 🎮 情侣双人头像系统 ——— */
const selfId = computed(() => userStore.user?.id ?? 0)
const selfName = computed(() => userStore.user?.username ?? 'You')
const selfAvatar = computed(() => fix(userStore.user?.avatar_url ?? undefined) || defaultAvatar)
const selfIsOnline = computed(() => {
  const isOnline = (userStore.user as any)?.is_online
  console.log('🎮 Self Online Status:', isOnline, 'User:', userStore.user)
  // when is_online is undefined, assume true; the current user is necessarily online
  return isOnline !== false
})

const partnerId = computed(() => {
  const members = userStore.couple?.members || []
  return members.find((m: any) => m.id !== selfId.value)?.id ?? 0
})
const partnerName = computed(() => {
  const members = userStore.couple?.members || []
  return members.find((m: any) => m.id !== selfId.value)?.username ?? 'Partner'
})
const partnerAvatar = computed(() => {
  const members = userStore.couple?.members || []
  const partner = members.find((m: any) => m.id !== selfId.value)
  return fix(partner?.avatar_url ?? undefined) || defaultAvatar
})
const partnerIsOnline = computed(() => {
  const members = userStore.couple?.members || []
  const partner = members.find((m: any) => m.id !== selfId.value)
  const isOnline = (partner as any)?.is_online
  console.log('🎮 Partner Online Status:', isOnline, 'Partner:', partner)
  return isOnline === true // 严格检查true
})

// 🎯 时区数据（从profile读取）
const selfTimezone = computed(() => userStore.user?.timezone || 'UTC')
const partnerTimezone = computed(() => {
  const members = userStore.couple?.members || []
  const partner = members.find((m: any) => m.id !== selfId.value)
  return (partner as any)?.timezone || 'UTC'
})

const bothOnline = computed(() => {
  const both = selfIsOnline.value && partnerIsOnline.value
  console.log('🎮 Both Online:', both, 'Self:', selfIsOnline.value, 'Partner:', partnerIsOnline.value)
  return both
})

/* ——— Navigation Functions ——— */
function goToProfile(userId: number) {
  console.log('🎮 Click Avatar - User ID:', userId)
  console.log('✅ Navigating to /profile (your profile page)')
  triggerHapticFeedback('light')
  // 🎯 ProfileView shows only the current user; viewing others is not supported
  router.push('/profile')
}

/* ——— 爱心特效位置生成 ——— */
function getHeartStyle(index: number) {
  const left = Math.random() * 100
  const delay = Math.random() * 3
  const duration = 3 + Math.random() * 2
  return {
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`
  }
}

/* 🎮 统一背景管理 - 每次进入页面随机选择 */
const bgManager = createBackgroundManager()
const homeBackgroundStyle = computed(() => {
  const style = bgManager.getStyle(0.2)  // 轻度渐变叠加
  return {
    ...style,
    minHeight: '100vh',
    position: 'relative',
    overflow: 'hidden',
    padding: 'env(safe-area-inset-top) 0 env(safe-area-inset-bottom)',
  }
})

/* ——— Enhanced Game State ——— */
const foodCount = ref(6)
const gameScore = ref(1250)
const showBubble = ref(true)
const showRecipePanel = ref(false)
const showFeedPanel = ref(false)
const showKinnyModal = ref(false)
const showTimezoneModal = ref(false) // 🎮 时区对比Modal状态

// 🎯 点击时钟按钮 - Track用户查看时差行为
const handleClockClick = () => {
  // 计算时差
  const now = new Date()
  const yourTime = new Date(now.toLocaleString('en-US', { timeZone: selfTimezone.value }))
  const partnerTime = new Date(now.toLocaleString('en-US', { timeZone: partnerTimezone.value }))
  const timeDiff = Math.round((yourTime.getTime() - partnerTime.getTime()) / (1000 * 60 * 60))
  
  // 📊 Track点击事件
  trackCheckTimeLag(
    selfTimezone.value,
    partnerTimezone.value,
    Math.abs(timeDiff),
    partnerIsOnline.value
  )
  
  // 打开modal
  showTimezoneModal.value = true
}

/* ——— Inventory Management ——— */
type InventoryItem = { quantity?: number } & Record<string, any>
const totalInventory = computed(() => {
  const items = (petStore.foodInventory as InventoryItem[] | undefined) ?? []
  return items.reduce((sum, item) => sum + (Number(item?.quantity) || 0), 0)
})

/* ——— Rock Paper Scissors Game ——— */
const showRPSGame = ref(false)
const comboCount = ref(0)
const comboMultiplier = ref(1)
const showLevelUp = ref(false)
const levelUpBonus = ref(0)
const dialogueProgress = ref(0)
const isHungry = ref(false)
let comboTimer: NodeJS.Timeout | null = null
let progressTimer: NodeJS.Timeout | null = null

/* ——— Computed Properties ——— */
const diceBalance = computed(() => recipesStore.dice?.balance || 3)

/* ——— Pet Dialogue System ——— */
const lines = computed(() => {
  if (petStore.stateMessages.length > 0) {
    return petStore.stateMessages
  } else {
    return ['Welcome to the game! Start your cooking journey! 🍳']
  }
})
const idx = ref(0)
const currentLine = computed(() => lines.value[idx.value])

function nextLine() {
  idx.value = (idx.value + 1) % lines.value.length
  dialogueProgress.value = 0
  showBubble.value = true
  startProgressTimer()
}

function startProgressTimer() {
  if (progressTimer) clearInterval(progressTimer)
  
  // 🎯 从SystemConfig获取动态时长（秒 → milliseconds), UI fallback: 60秒
  const durationMs = (systemStore.petPromptDisplaySeconds ?? 60) * 1000
  const updateInterval = 100 // 更新频率100ms
  const incrementPerInterval = (100 / durationMs) * updateInterval
  
  progressTimer = setInterval(() => {
    dialogueProgress.value += incrementPerInterval
    if (dialogueProgress.value >= 100) {
      nextLine()
    }
  }, updateInterval)
}

/* ——— 🎮 Kinny对话Modal ——— */
function openKinnyModal() {
  // 🎯 触觉反馈 - 提升互动体验
  triggerHapticFeedback('medium')
  
  // 🎮 游戏音效（未来可添加）
  // playSound('dialogue_open')
  
  // 打开Modal
  showKinnyModal.value = true
  
  // 暂停对话进度
  if (progressTimer) clearInterval(progressTimer)
  
  // 临时隐藏对话框，避免重叠
  showBubble.value = false
  
  // Modal关闭时恢复对话框
  setTimeout(() => {
    if (!showKinnyModal.value) {
      showBubble.value = true
      startProgressTimer()
    }
  }, 300)
}

/* ——— Enhanced Game Actions ——— */
function handleFeed() {
  // 🎯 iOShaptic feedback
  triggerHapticFeedback('light')
  
  // Open FeedPanel instead of directly feeding
  showFeedPanel.value = true
  
  // Show feedback for button click
  showFeedback('Select food to feed your pet! 🍽️', 'info')
  
  // 🎯 iOSnative press animation
  animateButtonPress('.feed-btn')
}

// Handle feed completion from FeedPanel
function handleFeedComplete(food: any, newHunger: number) {
  // Decrease food count when actually feeding
  if (foodCount.value > 0) {
    foodCount.value--
  }
  
  isHungry.value = false
  
  // Combo system
  comboCount.value++
  comboMultiplier.value = Math.min(comboCount.value, 5)
  
  const basePoints = 15
  const totalPoints = basePoints * comboMultiplier.value
  gameScore.value += totalPoints
  
  // Enhanced feedback
  if (comboCount.value > 1) {
    showFeedback(`Yummy! +${totalPoints} pts (${comboCount.value}x combo!)`, 'success')
  } else {
    showFeedback(`Yummy! +${totalPoints} pts`, 'success')
  }
  
  // Level up check
  if (gameScore.value % 500 === 0) {
    triggerLevelUp()
  }
  
  // Reset combo timer
  if (comboTimer) clearTimeout(comboTimer)
  comboTimer = setTimeout(() => {
    comboCount.value = 0
    comboMultiplier.value = 1
  }, 3000)
  
  // Auto-refill food occasionally
  if (foodCount.value === 0 && Math.random() > 0.7) {
    setTimeout(() => {
      foodCount.value = 3
      showFeedback('Food refilled! 🍕', 'info')
    }, 2000)
  }
}

function handlePlay() {
  // 🎯 iOShaptic feedback
  triggerHapticFeedback('medium')
  
  // Immediate visual feedback before starting game
  petStore.setAnimation('hype')
  
  // 🎯 iOSnative press animation
  animateButtonPress('.play-btn')
  
  // Start Rock Paper Scissors game with slight delay for animation
  setTimeout(() => {
    showRPSGame.value = true
  }, 200)
}

function handleRPSGameEnd(result: 'win' | 'lose' | 'draw', points: number, hungerCost: number) {
  // 🎯 精准改善：移除自动关闭，让用户手动控制游戏面板
  // showRPSGame.value = false  // ❌ 移除这行，不要自动关闭
  console.log('[HomeView] RPS游戏结束，但面板保持打开状态:', result, points, '消耗饥饿值:', hungerCost)
  
  // Add points to score
  gameScore.value += points
  
  // Select animation based on result
  let animations: string[] = []
  let outcomes: string[] = []
  
  switch (result) {
    case 'win':
      // Victory animations - more energetic
      animations = ['dance', 'hype', 'skill', 'boxing', 'arise']
      outcomes = [
        `🎉 VICTORY! +${points} pts`,
        `🏆 EXCELLENT! +${points} pts`, 
        `⚡ PERFECT WIN! +${points} pts`,
        `🔥 UNSTOPPABLE! +${points} pts`,
        `🌟 LEGENDARY! +${points} pts`
      ]
      break
      
    case 'lose':
      // Consolation animations - gentler  
      animations = ['gesture', 'run', 'running']
      outcomes = [
        `😅 TRY AGAIN! +${points} pts`,
        `💪 KEEP GOING! +${points} pts`,
        `🎯 ALMOST! +${points} pts`,
        `🌈 EXPERIENCE +1! +${points} pts`
      ]
      break
      
    case 'draw':
      // Balanced animations
      animations = ['dance', 'gesture', 'skill']
      outcomes = [
        `🤝 BALANCED! +${points} pts`,
        `⚖️ EVEN MATCH! +${points} pts`,
        `🎭 GREAT SYNC! +${points} pts`
      ]
      break
  }
  
  // Trigger random animation from result category
  const randomAnimation = animations[Math.floor(Math.random() * animations.length)]
  petStore.setAnimation(randomAnimation)
  
  // Show feedback
  const randomOutcome = outcomes[Math.floor(Math.random() * outcomes.length)]
  showFeedback(randomOutcome, result === 'win' ? 'success' : result === 'lose' ? 'error' : 'info')
  
  // Return to idle after animation
  setTimeout(() => {
    petStore.resetAnimation()
  }, 2500)
  
  // Bonus chance for wins
  if (result === 'win' && Math.random() > 0.7) {
    setTimeout(() => {
      const bonusPoints = 30
      gameScore.value += bonusPoints
      showFeedback(`🎁 WIN BONUS! +${bonusPoints} pts`, 'levelup')
    }, 1500)
  }
}

function closeRPSGame() {
  showRPSGame.value = false
}

function toggleRecipePanel() {
  // 🎯 iOShaptic feedback
  triggerHapticFeedback('light')
  
  showRecipePanel.value = !showRecipePanel.value
  if (showRecipePanel.value) {
    // 🎯 iOSnative press animation
    animateButtonPress('.recipe-btn')
    showFeedback('Get ready to cook something amazing! 👩‍🍳✨', 'info')
  }
}

function onRecipeRolled(recipe: any) {
  gameScore.value += 50
  showFeedback('New quest discovered! +50 pts', 'success')
}

function triggerLevelUp() {
  levelUpBonus.value = 100
  showLevelUp.value = true
  setTimeout(() => {
    showLevelUp.value = false
  }, 3000)
}

/* ——— Navigation ——— */
function goToRecipes() {
  // 🎯 iOShaptic feedback
  triggerHapticFeedback('light')
  animateButtonPress('.recipe-btn')
  router.push('/roundly-quest')
}
function goToMemories() {
  // 🎯 iOShaptic feedback
  triggerHapticFeedback('light')
  animateButtonPress('.memories-btn')
  router.push('/battle_history')
}

/* ——— Enhanced Feedback System ——— */
const feedbackText = ref('')
const feedbackType = ref('success')
let feedbackTimeout: NodeJS.Timeout | null = null

function showFeedback(text: string, type: string) {
  feedbackText.value = text
  feedbackType.value = type
  
  if (feedbackTimeout) clearTimeout(feedbackTimeout)
  feedbackTimeout = setTimeout(() => {
    feedbackText.value = ''
  }, 2500)
}

/* ——— 🎯 iOS原生交互体验函数 ——— */
function triggerHapticFeedback(type: 'light' | 'medium' | 'heavy' = 'light') {
  // iOS Safari haptic feedback
  if (isIOS.value && (window as any).navigator?.vibrate) {
    const patterns = {
      light: [10],
      medium: [20],
      heavy: [30, 10, 30]
    }
    ;(window as any).navigator.vibrate(patterns[type])
  }
  
  // 通用vibration API fallback
  if (navigator.vibrate) {
    const patterns = {
      light: 10,
      medium: 20,
      heavy: [30, 10, 30]
    }
    navigator.vibrate(patterns[type])
  }
}

function animateButtonPress(selector: string) {
  const button = document.querySelector(selector) as HTMLElement
  if (!button) return
  
  // 🎯 iOSnative button animation: scale down quickly, then spring back
  button.style.transition = 'transform 0.1s cubic-bezier(0.25, 0.46, 0.45, 0.94)'
  button.style.transform = 'scale(0.95)'
  
  setTimeout(() => {
    button.style.transition = 'transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
    button.style.transform = 'scale(1)'
    
    // 清理样式
    setTimeout(() => {
      button.style.transition = ''
      button.style.transform = ''
    }, 300)
  }, 100)
}

function addTouchInteraction(element: HTMLElement) {
  if (!supportsTouch.value) return
  
  let touchStartTime = 0
  
  element.addEventListener('touchstart', (e) => {
    touchStartTime = Date.now()
    // iOS级按下效果
    element.style.transform = 'scale(0.97)'
    element.style.transition = 'transform 0.1s ease-out'
    
    // 防止双击缩放
    const currentTime = Date.now()
    if (currentTime - lastTouchTime.value < 300) {
      e.preventDefault()
    }
    lastTouchTime.value = currentTime
  }, { passive: false })
  
  element.addEventListener('touchend', () => {
    // Spring back动画
    element.style.transform = 'scale(1)'
    element.style.transition = 'transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
    
    setTimeout(() => {
      element.style.transition = ''
      element.style.transform = ''
    }, 200)
  })
  
  element.addEventListener('touchcancel', () => {
    element.style.transform = 'scale(1)'
    element.style.transition = 'transform 0.1s ease-out'
  })
}

/* ——— Lifecycle ——— */
let dialogueInterval: NodeJS.Timeout | null = null
let hungerTimer: NodeJS.Timeout | null = null

onMounted(async () => {
  // 🎯 预加载SystemConfig - 确保配置可用
  try {
    await systemStore.fetchSystemConfig()
  } catch (error) {
    console.error('Failed to load system config:', error)
  }
  
  // 🎯 iOS设备和移动端检测
  const detectDevice = () => {
    isMobile.value = window.innerWidth <= 768
    isIOS.value = /iPad|iPhone|iPod/.test(navigator.userAgent)
    supportsTouch.value = 'ontouchstart' in window
  }
  
  detectDevice()
  
  // 🎯 从SystemConfig获取对话轮询时间（秒 → milliseconds), UI fallback: 60秒
  const dialogueDurationMs = (systemStore.petPromptDisplaySeconds ?? 60) * 1000
  
  // mobile performance：检测设备能力
  const mobileDevice = window.innerWidth <= 768
  const isLowPerformance = navigator.hardwareConcurrency < 4 || 
                          /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  
  if (mobileDevice || isLowPerformance) {
    // 减少动画频率
    document.documentElement.style.setProperty('--animation-duration', '0.15s')
    
    // 🎯 为所有游戏按钮添加iOS级交互
    setTimeout(() => {
      const gameButtons = document.querySelectorAll('.game-btn')
      gameButtons.forEach(button => {
        addTouchInteraction(button as HTMLElement)
      })
      
      // 🎯 宠物竞技场添加触摸交互
      const petArena = document.querySelector('.pet-arena')
      if (petArena && supportsTouch.value) {
        addTouchInteraction(petArena as HTMLElement)
      }
    }, 100)
    
    // Start dialogue progress
    startProgressTimer()
    
    // 🎯 Auto-cycle dialogue - duration comes from SystemConfig
    dialogueInterval = setInterval(() => {
      nextLine()
    }, dialogueDurationMs)
    
    // Hunger system (移动端降频)
    hungerTimer = setInterval(() => {
      if (foodCount.value > 0 && Math.random() > 0.8) {
        isHungry.value = true
        setTimeout(() => {
          isHungry.value = false
        }, 5000)
      }
    }, dialogueDurationMs + 3000)
  } else {
    // 桌面端正常性能
    // Start dialogue progress
    startProgressTimer()
    
    // 🎯 Auto-cycle dialogue - duration comes from SystemConfig
    dialogueInterval = setInterval(() => {
      nextLine()
    }, dialogueDurationMs)
    
    // Hunger system
    hungerTimer = setInterval(() => {
      if (foodCount.value > 0 && Math.random() > 0.7) {
        isHungry.value = true
        setTimeout(() => {
          isHungry.value = false
        }, 5000)
      }
    }, 15000)
  }
})

onUnmounted(() => {
  if (dialogueInterval) clearInterval(dialogueInterval)
  if (feedbackTimeout) clearTimeout(feedbackTimeout)
  if (comboTimer) clearTimeout(comboTimer)
  if (progressTimer) clearInterval(progressTimer)
  if (hungerTimer) clearInterval(hungerTimer)
})

/* ——— 🎮 Watch Modal State - 恢复对话框 ——— */
watch(showKinnyModal, (newVal) => {
  if (!newVal) {
    // Modal关闭时恢复对话框
    setTimeout(() => {
      showBubble.value = true
      startProgressTimer()
    }, 300)
  }
})
</script>

<style scoped lang="scss">
// Import cute fonts
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Fredoka+One&display=swap');

// Enhanced theme variables (mobile tuning)
$primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
$success-gradient: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
$warning-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
$levelup-gradient: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%);
$game-shadow: 0 15px 50px rgba(0, 0, 0, 0.2);
$game-shadow-hover: 0 25px 80px rgba(0, 0, 0, 0.3);

// Cute font family
$cute-font: 'Nunito', 'Fredoka One', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

// mobile performance开关
@media (max-width: 768px) {
  :root {
    --enable-heavy-animations: 0; /* 禁用重型动画 */
    --enable-blur-effects: 0;      /* 禁用模糊效果 */
    --animation-duration: 0.2s;    /* 加速动画 */
    
    /* 🎯 iOS原生动画曲线 */
    --ios-ease-out: cubic-bezier(0.25, 0.46, 0.45, 0.94);
    --ios-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
    --ios-ease-in-out: cubic-bezier(0.645, 0.045, 0.355, 1);
  }
}

@media (min-width: 769px) {
  :root {
    --enable-heavy-animations: 1;
    --enable-blur-effects: 1;
    --animation-duration: 0.5s;
  }
}

// 🎮 情侣双人头像系统样式
/* ——— 🎮 全屏爱心特效（双人都在线时） ——— */
.love-screen-effect {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 50;
  overflow: hidden;
}

.floating-heart {
  position: absolute;
  top: 100%;
  font-size: 24px;
  opacity: 0;
  animation: floatUpHeart 5s ease-in infinite;
  filter: drop-shadow(0 0 8px rgba(255, 105, 180, 0.6));
  
  @media (max-width: 768px) {
    font-size: 20px;
  }
}

@keyframes floatUpHeart {
  0% {
    top: 100%;
    opacity: 0;
    transform: translateX(0) scale(0.5);
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    top: -10%;
    opacity: 0;
    transform: translateX(calc(var(--x-drift, 0) * 50px)) scale(1.2);
  }
}

/* ——— 🎮 游戏对称布局：上2头像 + 下4按钮 ——— */
.game-ui-symmetry {
  width: 100%;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  
  /* 🎮 Web端：更宽的控制面板 */
  @media (min-width: 1200px) {
    max-width: clamp(480px, 42vw, 600px);
    gap: clamp(20px, 2.5vh, 32px);
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    max-width: clamp(440px, 50vw, 520px);
    gap: clamp(18px, 2.2vh, 28px);
  }
  
  /* Tablet */
  @media (max-width: 768px) {
    max-width: 100%;
    gap: clamp(14px, 2vh, 22px);
  }
  
  /* Mobile */
  @media (max-width: 480px) {
    gap: clamp(12px, 1.8vh, 18px);
  }
}

/* 🎯 bottom avatar row: avatars align with the buttons on X, clocks sit at the outer edges */
.avatar-row-bottom {
  display: flex;
  justify-content: space-between; /* 🎯 两端对齐：时钟在最左最右 */
  align-items: center;
  width: 100%;
  max-width: 100%;
  margin-top: 3vh;
  padding: 0 clamp(20px, 3vw, 60px); /* 🎯 左右padding，时钟推到边缘 */
  position: relative;
  
  /* 🎯 桌面端：头像与按钮精准对齐 */
  @media (min-width: 1200px) {
    margin-top: 4vh;
    padding: 0 clamp(40px, 4vw, 80px); /* 🎯 与按钮列padding一致 */
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    margin-top: 3.5vh;
    padding: 0 clamp(30px, 3.5vw, 60px);
  }
  
  /* 🎯 移动端：隐藏时钟，头像居中 */
  @media (max-width: 768px) {
    margin-top: 2vh;
    justify-content: center;
    gap: clamp(30px, 5vw, 50px);
    padding: 0;
    
    .left-clock,
    .right-clock {
      display: none;
    }
  }
  
  /* 🎯 时钟与头像间距 */
  .left-clock {
    margin-right: clamp(15px, 2vw, 30px);
  }
  
  .right-clock {
    margin-left: clamp(15px, 2vw, 30px);
  }
  
  /* 🎯 头像容器：保持固定间距 */
  .game-avatar {
    margin: 0 clamp(20px, 2.5vw, 40px);
  }
}

.avatar-row {
  display: flex; /* 🎯 Flex布局保持居中 */
  justify-content: center; /* 🎯 居中对齐（修复拉宽问题） */
  align-items: center;
  gap: clamp(25px, 3.5vw, 50px); /* 🎯 拉开间距，游戏级呼吸感 */
  width: 100%; /* 🎯 全宽 */
  max-width: 100%; /* 🎯 限制最大宽度 */
  margin-top: 0;
  padding: 0; /* 🎯 零内边距 */
  position: relative; /* 🎯 为圆弧定位准备 */
  
  /* 🎮 AAA工业级：头像极限上升tuning 
   * 📍 Y轴层级保证：
   *   - Logo: margin-bottom: 2vh (物理位置最高)
   *   - Avatar: margin-top: -6vh (上移到Logo之下)
   *   - Prompt: position:fixed, top:0, height:40vh (覆盖屏幕上方40%)
   *   - Z-index: Logo(800) < Avatar(850) < Prompt(900)
   *   - 物理Y轴: Logo最上 > Avatar中间 > Prompt浮层
   * 🎯 Avatarphysically below the prompt, and a lower z-index keeps the prompt on top
   */
  @media (min-width: 1200px) {
    margin-bottom: -3vh;
    margin-top: -6vh; /* 🎯 raised 6vh to sit under the logo and inside the prompt area, with a low z-index so it never covers it */
    gap: clamp(35px, 4vw, 60px); /* 🎯 桌面端宽敞间距 */
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    margin-bottom: -2.5vh;
    margin-top: -5vh;
    gap: clamp(30px, 3.5vw, 50px);
  }
  
  /* 🎯 移动端：隐藏时钟，只显示头像 */
  @media (max-width: 768px) {
    gap: clamp(30px, 5vw, 50px);
    
    .left-clock,
    .right-clock {
      display: none; /* 🎯 移动端隐藏时钟 */
    }
  }
}

// 🎯 SVG圆弧连接线（头像之间）
.avatar-arc-connector {
  position: absolute;
  width: clamp(140px, 18vw, 220px);
  height: clamp(70px, 9vw, 110px);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 840; /* 🎯 低于头像(850)，作为背景装饰 */
  pointer-events: none;
  opacity: 0.9;
  
  @media (max-width: 768px) {
    width: clamp(120px, 25vw, 180px);
    height: clamp(60px, 12vw, 90px);
  }
}

// 🎯 圆弧路径动画
.arc-path {
  stroke-dasharray: 300;
  stroke-dashoffset: 300;
  animation: drawArc 2s ease-out forwards;
  
  &.both-online {
    filter: drop-shadow(0 0 8px rgba(255, 107, 157, 0.6));
  }
  
  &.single-online {
    filter: drop-shadow(0 0 8px rgba(74, 222, 128, 0.6));
  }
}

@keyframes drawArc {
  to {
    stroke-dashoffset: 0;
  }
}

// 🎯 动态光点
.arc-dot {
  filter: drop-shadow(0 0 6px rgba(255, 255, 255, 0.8));
}

.game-avatar {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 850;
  flex: 0 0 auto; /* 🎯 不伸缩，固定尺寸 */
  
  /* 🎯 AAA美学：精准X轴对齐 */
  @media (min-width: 769px) {
    margin: 0;
    padding: 0;
  }
  
  /* 🎯 左头像：对齐左按钮中心 */
  &.left-avatar {
    transform-origin: center; /* 🎯 中心对齐 */
  }
  
  /* 🎯 右头像：对齐右按钮中心 */
  &.right-avatar {
    transform-origin: center; /* 🎯 中心对齐 */
  }
  
  .avatar-glow {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    opacity: 0;
    transition: all 0.4s ease;
    pointer-events: none;
    
    /* 🎮 Web端：更大的光晕 */
    @media (min-width: 769px) {
      width: clamp(100px, 12vh, 130px);
      height: clamp(100px, 12vh, 130px);
    }
    
    @media (max-width: 768px) {
      width: 90px;
      height: 90px;
    }
    
    @media (max-width: 480px) {
      width: 75px;
      height: 75px;
    }
  }
  
  .avatar-img {
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid rgba(255, 255, 255, 0.3);
    display: block;
    transition: all 0.4s ease;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    position: relative;
    z-index: 1;
    
    /* 🎮 AAA弹性：头像自适应尺寸，为prompt留空间 */
    @media (min-width: 1200px) {
      width: clamp(100px, 10vh, 120px); /* 🎯 110→100px，减小10%为prompt留空间 */
      height: clamp(100px, 10vh, 120px);
      border-width: 4px; /* 🎯 边框缩小，更精致 */
    }
    
    @media (min-width: 769px) and (max-width: 1199px) {
      width: clamp(90px, 9.5vh, 110px); /* 🎯 95→90px，弹性tuning */
      height: clamp(90px, 9.5vh, 110px);
      border-width: 4px;
    }
    
    @media (max-width: 768px) {
      width: 68px;
      height: 68px;
      border-width: 3px;
    }
    
    @media (max-width: 480px) {
      width: 58px;
      height: 58px;
      border-width: 2.5px;
    }
    
    @media (max-width: 360px) {
      width: 52px;
      height: 52px;
      border-width: 2px;
    }
  }
  
  .avatar-name {
    text-align: center;
    font-weight: 700; /* 🎯 600→700，更清晰 */
    color: rgba(255, 255, 255, 0.95);
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
    transition: all 0.3s ease;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    letter-spacing: 0.3px;
    
    /* 🎮 Web端：弹性字体 */
    @media (min-width: 1200px) {
      font-size: clamp(14px, 1.6vh, 17px); /* 🎯 稍小，为prompt让路 */
      margin-top: clamp(7px, 1vh, 10px); /* 🎯 紧凑间距 */
      max-width: clamp(100px, 14vw, 130px);
    }
    
    @media (min-width: 769px) and (max-width: 1199px) {
      font-size: clamp(13px, 1.5vh, 15px);
      margin-top: clamp(6px, 1vh, 9px);
      max-width: clamp(90px, 11vw, 110px);
    }
    
    @media (max-width: 768px) {
      font-size: 13px;
      margin-top: 6px;
      max-width: 90px;
    }
    
    @media (max-width: 480px) {
      font-size: 12px;
      margin-top: 5px;
      max-width: 75px;
    }
    
    @media (max-width: 360px) {
      font-size: 11px;
      margin-top: 4px;
      max-width: 65px;
    }
  }
  
  .status-indicator {
    position: absolute;
    border-radius: 50%;
    border: 2.5px solid white;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    z-index: 2;
    
    /* 🎮 Web端：弹性状态指示器 */
    @media (min-width: 1200px) {
      width: clamp(20px, 2.2vh, 24px); /* 🎯 稍小配合头像 */
      height: clamp(20px, 2.2vh, 24px);
      border-width: 3px;
      top: clamp(2px, 0.4vh, 4px);
      right: calc(50% - clamp(40px, 4.5vh, 48px)); /* 🎯 动态定位 */
    }
    
    @media (min-width: 769px) and (max-width: 1199px) {
      width: clamp(18px, 2vh, 22px);
      height: clamp(18px, 2vh, 22px);
      border-width: 3px;
      top: clamp(2px, 0.3vh, 3px);
      right: calc(50% - clamp(36px, 4vh, 42px)); /* 🎯 动态定位 */
    }
    
    @media (max-width: 768px) {
      width: 18px;
      height: 18px;
      border-width: 2.5px;
      top: 2px;
      right: calc(50% - 34px);
    }
    
    @media (max-width: 480px) {
      width: 16px;
      height: 16px;
      border-width: 2px;
      top: 1px;
      right: calc(50% - 29px);
    }
    
    @media (max-width: 360px) {
      width: 14px;
      height: 14px;
      border-width: 2px;
      top: 1px;
      right: calc(50% - 26px);
    }
  }
  
  /* ——— 在线状态：绿色 ——— */
  &.online {
    .status-indicator {
      background: linear-gradient(135deg, #22c55e, #16a34a);
      box-shadow: 0 0 16px rgba(34, 197, 94, 0.7), 0 2px 8px rgba(0, 0, 0, 0.4);
      animation: pulseGreen 2s ease-in-out infinite;
    }
    
    .avatar-img {
      border-color: rgba(34, 197, 94, 0.7);
    }
    
    .avatar-glow {
      opacity: 0.5;
      background: radial-gradient(circle, rgba(34, 197, 94, 0.4), transparent);
      animation: glowPulse 2s ease-in-out infinite;
    }
  }
  
  /* ——— 离线状态：灰色 ——— */
  &.offline {
    .status-indicator {
      background: linear-gradient(135deg, #9ca3af, #6b7280);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    
    .avatar-img {
      border-color: rgba(156, 163, 175, 0.5);
      opacity: 0.75;
    }
    
    .avatar-name {
      color: rgba(255, 255, 255, 0.65);
    }
  }
  
  /* ——— 双人都在线：粉色特效 ——— */
  &.both-online {
    .status-indicator {
      background: linear-gradient(135deg, #ff69b4, #ff1493);
      box-shadow: 0 0 20px rgba(255, 105, 180, 0.9), 0 2px 8px rgba(0, 0, 0, 0.4);
      animation: pulsePink 1.5s ease-in-out infinite;
    }
    
    .avatar-img {
      border-color: rgba(255, 105, 180, 0.8);
      box-shadow: 0 0 24px rgba(255, 105, 180, 0.7);
    }
    
    .avatar-glow {
      opacity: 0.7;
      background: radial-gradient(circle, rgba(255, 105, 180, 0.5), transparent);
      animation: glowPinkPulse 1.5s ease-in-out infinite;
    }
    
    .avatar-name {
      color: #ffb3d9;
      text-shadow: 0 0 12px rgba(255, 105, 180, 0.8);
      font-weight: 700;
    }
  }
  
  /* ——— Hover 效果 ——— */
  &:hover {
    transform: translateY(-4px) scale(1.05);
    
    .avatar-img {
      box-shadow: 0 8px 24px rgba(255, 255, 255, 0.4);
      transform: scale(1.05);
    }
    
    .avatar-glow {
      opacity: 0.8 !important;
      transform: translate(-50%, -50%) scale(1.2);
    }
  }
  
  &:active {
    transform: translateY(-2px) scale(1.02);
  }
}

/* ——— 🎮 动画关键帧 ——— */
@keyframes pulseGreen {
  0%, 100% {
    box-shadow: 0 0 16px rgba(34, 197, 94, 0.6);
    transform: scale(1);
  }
  50% {
    box-shadow: 0 0 24px rgba(34, 197, 94, 0.9);
    transform: scale(1.1);
  }
}

@keyframes pulsePink {
  0%, 100% {
    box-shadow: 0 0 20px rgba(255, 105, 180, 0.8);
    transform: scale(1);
  }
  50% {
    box-shadow: 0 0 32px rgba(255, 105, 180, 1);
    transform: scale(1.15);
  }
}

@keyframes glowPulse {
  0%, 100% {
    opacity: 0.3;
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    opacity: 0.6;
    transform: translate(-50%, -50%) scale(1.2);
  }
}

@keyframes glowPinkPulse {
  0%, 100% {
    opacity: 0.5;
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    opacity: 0.9;
    transform: translate(-50%, -50%) scale(1.3);
  }
}

.avatar-glow {
  position: absolute;
  inset: -15px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(168, 230, 207, 0.4) 0%, transparent 70%);
  opacity: 0;
  transition: all 0.4s ease;
  pointer-events: none;
  z-index: 0;
}

.avatar-ring {
  position: absolute;
  inset: -8px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: none;
  z-index: 1;
}

.avatar-wrapper {
  position: relative;
  width: 70px;
  height: 70px;
  border-radius: 50%;
  border: 4px solid rgba(255, 255, 255, 0.5);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  backdrop-filter: blur(15px);
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
  z-index: 2;
  
  @media (max-width: 480px) {
    width: 60px;
    height: 60px;
    border-width: 3px;
  }
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.online-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.5);
  z-index: 3;
  
  @media (max-width: 480px) {
    width: 14px;
    height: 14px;
    border-width: 2px;
  }
}

.online-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.4);
  animation: pulseOnline 2s ease-in-out infinite;
}

@keyframes pulseOnline {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.5);
    opacity: 0;
  }
}

@keyframes onlineGlow {
  0%, 100% {
    opacity: 0.4;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.15);
  }
}

.avatar-label {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 6px;
  font-size: 0.75rem;
  font-weight: 800;
  color: white;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
  white-space: nowrap;
  background: rgba(0, 0, 0, 0.3);
  padding: 4px 10px;
  border-radius: 12px;
  backdrop-filter: blur(8px);
  pointer-events: none;
  
  @media (max-width: 480px) {
    font-size: 0.7rem;
    padding: 3px 8px;
  }
}

// 爱心连接器
.love-connector {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  opacity: 0.3;
  transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: none;
  
  &.active {
    opacity: 1;
    transform: scale(1.1);
    
    .connector-heart {
      animation: heartBeat 1.2s ease-in-out infinite;
      filter: drop-shadow(0 0 20px rgba(255, 107, 157, 0.8));
    }
    
    .love-particles {
      opacity: 1;
      
      .love-particle {
        animation: particleFloat 3s ease-in-out infinite;
      }
    }
    
    .energy-wave {
      animation: energyWave 2s ease-in-out infinite;
    }
  }
  
  @media (max-width: 480px) {
    width: 60px;
    height: 60px;
  }
}

.connector-heart {
  font-size: 3rem;
  filter: drop-shadow(0 4px 12px rgba(255, 107, 157, 0.4));
  transition: all 0.3s ease;
  z-index: 2;
  
  @media (max-width: 480px) {
    font-size: 2.5rem;
  }
}

@keyframes heartBeat {
  0%, 100% {
    transform: scale(1);
  }
  14% {
    transform: scale(1.15);
  }
  28% {
    transform: scale(1);
  }
  42% {
    transform: scale(1.15);
  }
  70% {
    transform: scale(1);
  }
}

.love-particles {
  position: absolute;
  inset: -20px;
  opacity: 0;
  transition: opacity 0.6s ease;
  pointer-events: none;
}

.love-particle {
  position: absolute;
  font-size: 1.2rem;
  opacity: 0;
  
  @for $i from 1 through 8 {
    &:nth-child(#{$i}) {
      $angle: ($i - 1) * 45deg;
      $distance: 40px;
      left: calc(50% + #{cos($angle) * $distance});
      top: calc(50% + #{sin($angle) * $distance});
      animation-delay: #{$i * 0.15}s;
    }
  }
}

@keyframes particleFloat {
  0%, 100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.5);
  }
  50% {
    opacity: 0.8;
    transform: translate(-50%, -50%) translateY(-10px) scale(1);
  }
}

.energy-wave {
  position: absolute;
  inset: -10px;
  border: 2px solid rgba(255, 107, 157, 0.6);
  border-radius: 50%;
  opacity: 0;
}

@keyframes energyWave {
  0% {
    opacity: 0.8;
    transform: scale(0.8);
  }
  100% {
    opacity: 0;
    transform: scale(1.5);
  }
}

.home {
  /* 🎮 the background is injected by homeBackgroundStyle, chosen at random*/
  font-family: $cute-font;
  
  // Enhanced dynamic background (mobile tuning)
  &::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
      radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.12) 0%, transparent 50%),
      radial-gradient(circle at 40% 60%, rgba(255, 255, 255, 0.08) 0%, transparent 50%),
      radial-gradient(circle at 60% 40%, rgba(255, 255, 255, 0.06) 0%, transparent 50%);
    pointer-events: none;
    
    // mobile performance
    @media (max-width: 768px) {
      animation: none;
      background: radial-gradient(circle at 60% 40%, rgba(255, 255, 255, 0.06) 0%, transparent 50%);
    }
    
    @media (min-width: 769px) {
      animation: backgroundShift 15s ease-in-out infinite;
    }
  }
  
  &::after {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      linear-gradient(45deg, rgba(255, 255, 255, 0.03) 0%, transparent 50%),
      linear-gradient(-45deg, rgba(255, 255, 255, 0.02) 0%, transparent 50%);
    pointer-events: none;
    
    // mobile performance
    @media (max-width: 768px) {
      animation: none;
      background: linear-gradient(-45deg, rgba(255, 255, 255, 0.02) 0%, transparent 50%);
      opacity: 0.8;
    }
    
    @media (min-width: 769px) {
      animation: overlayShift 20s ease-in-out infinite reverse;
    }
  }
}

@keyframes backgroundShift {
  0%, 100% { transform: translateY(0px) rotate(0deg) scale(1); }
  33% { transform: translateY(-30px) rotate(1deg) scale(1.02); }
  66% { transform: translateY(20px) rotate(-0.5deg) scale(0.98); }
}

@keyframes overlayShift {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}

// Enhanced Game HUD
.game-hud {
  position: fixed;
  top: env(safe-area-inset-top, 20px);
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  justify-content: space-between;
  padding: 0 24px;
  pointer-events: none;
  
  @media (max-width: 480px) {
    padding: 0 16px;
  }
}

.hud-item {
  position: relative;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.3));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255, 255, 255, 0.5);
  border-radius: 30px;
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  
  @media (max-width: 480px) {
    padding: 12px 16px;
    border-radius: 25px;
  }
}

.hud-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  right: -50%;
  bottom: -50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.2) 0%, transparent 70%);
  animation: hudGlow 3s ease-in-out infinite;
}

@keyframes hudGlow {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 0.7; transform: scale(1.2); }
}

.hud-icon {
  font-size: 22px;
  filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.3));
  z-index: 2;
  
  @media (max-width: 480px) {
    font-size: 20px;
  }
}

.hud-value {
  font-size: 20px;
  font-weight: 900;
  color: #ffffff;
  text-shadow: 0 3px 10px rgba(0, 0, 0, 0.5);
  min-width: 32px;
  text-align: center;
  font-family: $cute-font;
  letter-spacing: 1px;
  z-index: 2;
  
  @media (max-width: 480px) {
    font-size: 18px;
    min-width: 28px;
  }
}

// 🎮 AAA工业级Game Stage：零滚动完美视口适配
.game-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start; /* 🎯 向上对齐，不居中 */
  height: 100vh; /* 🎯 固定100vh，零滚动 */
  max-height: 100vh; /* 🎯 防止溢出 */
  overflow: hidden; /* 🎯 禁止滚动 */
  padding: clamp(6px, 0.6vh, 10px) clamp(20px, 2vw, 40px); /* 🎯 更紧凑顶部 */
  position: relative;
  gap: 0; /* 🎯 AAA美学：零gap，完全靠负margin控制 */
  background: radial-gradient(ellipse at center, rgba(168, 230, 207, 0.08) 0%, transparent 70%);
  
  /* 🎮 Web端：AAA零滚动布局 */
  @media (min-width: 1200px) {
    padding: clamp(8px, 0.8vh, 12px) clamp(30px, 3vw, 60px); /* 🎯 顶部极致压缩 */
    gap: 0; /* 🎯 零gap美学 */
    max-width: 1920px;
    margin: 0 auto;
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    padding: clamp(6px, 0.7vh, 12px) clamp(24px, 2.5vw, 48px); /* 🎯 顶部更紧 */
    gap: 0; /* 🎯 零gap美学 */
  }
  
  /* Tablettuning */
  @media (max-width: 768px) {
    justify-content: flex-start;
    padding: 16px 24px; /* 🎯 减少顶部padding */
    gap: clamp(12px, 1.6vh, 20px); /* 移动端保留gap */
  }
  
  /* Mobiletuning */
  @media (max-width: 480px) {
    min-height: calc(100vh - 70px); /* 为header留空间 */
    padding: 16px 20px;
    gap: clamp(12px, 1.8vh, 20px);
  }
  
  /* Small Mobiletuning */
  @media (max-width: 360px) {
    padding: 12px 16px;
    gap: clamp(10px, 1.5vh, 16px);
  }
}

// 🎮 AAA工业级横向布局：零滚动三栏设计
.horizontal-game-layout {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 100%;
  margin-top: 65px; /* 🎯 零margin，配合Logo负margin */
  flex: 1; /* 🎯 自适应剩余空间 */
  min-height: 0; /* 🎯 允许收缩 */
  position: relative;
  
  /* 🎮 Web端：紧凑黄金比例 */
  @media (min-width: 1200px) {
    gap: clamp(20px, 2.5vw, 40px); /* 紧凑间距 */
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    gap: clamp(16px, 2vw, 32px);
  }
  
  /* Tablet/Mobile：改回垂直布局 */
  @media (max-width: 768px) {
    flex-direction: column;
    gap: clamp(16px, 2.5vh, 32px);
  }
}

// 🚀 游戏级按钮列 - 专业美工设计
.side-controls {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  z-index: 200; /* 确保可见 */
  
  /* 🎮 AAA工业级：响应式按钮 */
  @media (min-width: 1200px) {
    gap: clamp(12px, 5vh, 48px);
    
    .game-btn-aaa {
      width: clamp(110px, 12vh, 140px); /* 🎯 响应式尺寸 */
      height: clamp(110px, 12vh, 140px);
    }
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    gap: clamp(12px, 5vh, 48px);
    
    .game-btn-aaa {
      width: clamp(95px, 11vh, 120px);
      height: clamp(95px, 11vh, 120px);
    }
  }
  
  /* Mobile：改为横向排列 */
  @media (max-width: 768px) {
    flex-direction: row;
    width: 100%;
    gap: clamp(12px, 2vw, 20px);
    justify-content: space-evenly;
    
    .game-btn-aaa {
      width: clamp(85px, 20vw, 110px);
      height: clamp(85px, 20vw, 110px);
    }
  }
}

// 🎮 AAA工业级Arena区域：零滚动核心焦点
.center-arena-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start; /* 🎯 精准调整：向上对齐，头像更高 */
  flex-shrink: 1; /* 🎯 允许收缩适应视口 */
  flex-grow: 1; /* 🎯 占满剩余空间 */
  min-height: 0; /* 🎯 允许收缩 */
  position: relative;
  z-index: 100;
  max-height: 100%; /* 🎯 不超出父容器 */
  overflow: visible; /* 🎯 允许对话框超出显示 */
  
  /* 🎮 Web端：极致紧凑设计 */
  @media (min-width: 1200px) {
    gap: clamp(2px, 0.4vh, 6px); /* 🎯 更紧凑，头像向上靠 */
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    gap: clamp(2px, 0.3vh, 5px); /* 🎯 更紧凑 */
  }
  
  @media (max-width: 768px) {
    width: 100%;
    gap: clamp(10px, 1.5vh, 18px);
    justify-content: center; /* 移动端居中 */
  }
}

// Enhanced Pet arena - 🎮 AAA级视觉焦点：更大更醒目
.pet-arena {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  margin-top: 0.5vh; /* 🎯 减小margin，对话框已经降低 */
  margin-bottom: 0;
  flex-shrink: 0; /* Web端不收缩，保持视觉冲击力 */
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 1; /* 确保对话框可见 */
  overflow: visible; /* 🎯 确保对话框可以显示在arena之外 */
  
  /* 🎮 AAA工业级：Arena响应式尺寸 - 完美视口适配 */
  @media (min-width: 1200px) {
    max-width: min(55vh, 700px); /* 🎯 55vh或700px取小值 */
    max-height: 55vh; /* 🎯 限制高度 */
    width: min(55vh, 700px);
    height: min(55vh, 700px);
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    max-width: min(50vh, 600px);
    max-height: 50vh;
    width: min(50vh, 600px);
    height: min(50vh, 600px);
  }
  
  /* Tablettuning */
  @media (max-width: 768px) {
    max-width: clamp(340px, 45vh, 420px);
    flex-shrink: 1;
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
    user-select: none;
    
    &:active {
      transform: scale(0.98);
      transition: transform 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    }
  }
  
  /* Mobiletuning */
  @media (max-width: 480px) {
    max-width: clamp(300px, 50vh, 360px);
  }
  
  /* Small Mobiletuning */
  @media (max-width: 360px) {
    max-width: clamp(260px, 52vh, 320px);
  }
  
  /* Web端 Hover 效果 */
  @media (hover: hover) {
    &:hover {
      transform: scale(1.02);
      filter: brightness(1.05);
      
      .arena-bg {
        box-shadow: 
          inset 0 0 100px rgba(255, 255, 255, 0.25),
          0 40px 120px rgba(168, 230, 207, 0.4);
      }
    }
  }
}

.arena-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 50%;
  background: 
    radial-gradient(circle at center, rgba(255, 255, 255, 0.25) 0%, transparent 70%),
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.2) 0%, transparent 60%),
    radial-gradient(circle at 70% 70%, rgba(255, 255, 255, 0.15) 0%, transparent 50%);
  backdrop-filter: blur(30px);
  border: 3px solid rgba(255, 255, 255, 0.5);
  box-shadow: 
    inset 0 0 80px rgba(255, 255, 255, 0.2),
    0 30px 100px rgba(0, 0, 0, 0.25);
  animation: arenaGlow 8s ease-in-out infinite;
  overflow: hidden;
}

.arena-rings {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
}

.ring {
  position: absolute;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  animation: ringRotate 20s linear infinite;
}

.ring-1 {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  animation-direction: normal;
}

.ring-2 {
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  animation-direction: reverse;
  animation-duration: 25s;
}

.ring-3 {
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  animation-direction: normal;
  animation-duration: 30s;
}

@keyframes ringRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes arenaGlow {
  0%, 100% { 
    box-shadow: 
      inset 0 0 80px rgba(255, 255, 255, 0.2),
      0 30px 100px rgba(0, 0, 0, 0.25);
  }
  50% { 
    box-shadow: 
      inset 0 0 120px rgba(255, 255, 255, 0.3),
      0 35px 120px rgba(0, 0, 0, 0.3);
  }
}

.particle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.4) 70%, transparent 100%);
  border-radius: 50%;
  animation: particleFloat 6s ease-in-out infinite;
}

@keyframes particleFloat {
  0%, 100% { 
    transform: translate(0, 0) scale(0.5); 
    opacity: 0.4; 
  }
  50% { 
    transform: translate(var(--random-x), var(--random-y)) scale(1.2); 
    opacity: 1; 
  }
}

.pet-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: petFloat 5s ease-in-out infinite;
}

.pet-aura {
  position: absolute;
  width: 120%;
  height: 120%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  border-radius: 50%;
  animation: auraGlow 4s ease-in-out infinite;
}

@keyframes auraGlow {
  0%, 100% { opacity: 0.3; transform: scale(0.9); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

@keyframes petFloat {
  0%, 100% { transform: translate(-50%, -50%) translateY(0px); }
  50% { transform: translate(-50%, -50%) translateY(-15px); }
}

// 🎮 专业游戏对话框 - 精准定位，确保完全可见且位置合适
.pet-dialogue {
  position: absolute;
  top: -20px; /* 🎯 精准改善：dialogue位置再下来，更接近pet */
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  z-index: 500;
  cursor: pointer;
  
  &.dialogue-active {
    opacity: 1;
    transform: translateX(-50%) translateY(0px); /* 🎯 完全取消向上偏移 */
    pointer-events: auto;
  }
  
  /* 🎮 优雅悬停效果 - 微妙的视觉反馈 */
  &:hover .dialogue-wrapper {
    transform: translateY(-2px);
  }
  
  &:hover .dialogue-bg {
    border-color: rgba(168, 230, 207, 0.6);
    box-shadow: 
      0 18px 60px rgba(0, 0, 0, 0.3),
      0 0 30px rgba(168, 230, 207, 0.3);
  }
  
  &:hover .dialogue-tail {
    filter: drop-shadow(0 4px 8px rgba(168, 230, 207, 0.3));
  }
  
  /* 🎯 按压效果 */
  &:active .dialogue-wrapper {
    transform: translateY(0) scale(0.98);
  }
  
  @media (max-width: 768px) {
    top: -15px; /* 🎯 移动端dialogue位置再下来 */
    
    &.dialogue-active {
      transform: translateX(-50%) translateY(0px);
    }
  }
  
  @media (max-width: 480px) {
    top: -10px; /* 🎯 小屏幕dialogue更接近pet */
    
    &.dialogue-active {
      transform: translateX(-50%) translateY(0px);
    }
  }
}

.dialogue-wrapper {
  position: relative;
  max-width: 380px; /* � 减小宽度，确保不超出屏幕 */
  min-width: 260px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  /* 🎯 适中字体大小 */
  font-size: clamp(14px, 1.1vw, 16px);
  
  @media (max-width: 768px) {
    max-width: 320px;
    min-width: 240px;
  }
  
  @media (max-width: 480px) {
    max-width: 280px;
    min-width: 220px;
  }
}

.dialogue-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.98) 0%, 
    rgba(255, 255, 255, 0.95) 50%,
    rgba(255, 255, 255, 0.92) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 2px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.25);
  transition: all 0.3s ease; /* 🎮 流畅过渡 */
}

.dialogue-content {
  position: relative;
  padding: 16px 20px;
  z-index: 2;
}

.dialogue-text {
  font-size: clamp(17px, min(1.4vw, 2.8vh), 21px); /* 🎮 AAA终极：响应宽高 */
  font-weight: 700; /* 更粗 */
  color: #2c3e50;
  font-family: $cute-font;
  text-align: center;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
  line-height: 1.5;
  margin-bottom: 10px;
  
  @media (max-width: 480px) {
    font-size: 15px;
  }
}

.dialogue-progress {
  height: 4px; /* 更粗进度条 */
  background: linear-gradient(90deg, #4ecdc4, #44a08d);
  border-radius: 2px;
  transition: width 0.1s linear;
  box-shadow: 0 2px 5px rgba(78, 205, 196, 0.7);
}

.dialogue-tail {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 12px solid transparent;
  border-right: 12px solid transparent;
  border-top: 12px solid rgba(255, 255, 255, 0.95);
  filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.15));
  transition: all 0.3s ease;
}

// 🎮 AAA级游戏控制面板 - 单行布局不挡住logo
.game-controls-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  width: 100%;
  position: relative;
  z-index: 400;
  
  /* 🎮 Web端：更大的按钮和间距 */
  @media (min-width: 1200px) {
    gap: clamp(20px, 2.5vh, 32px);
    max-width: clamp(480px, 42vw, 600px);
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    gap: clamp(18px, 2.2vh, 28px);
    max-width: clamp(440px, 48vw, 540px);
  }
  
  /* Tablettuning */
  @media (max-width: 768px) {
    gap: clamp(16px, 2vh, 24px);
    max-width: 100%;
  }
  
  /* Mobiletuning */
  @media (max-width: 480px) {
    gap: clamp(12px, 1.8vh, 18px);
  }
  
  /* Small Mobiletuning */
  @media (max-width: 360px) {
    gap: clamp(10px, 1.5vh, 14px);
  }
}

/* Feed strip centered under dialogue */
/* feed strip removed: handled by BaseHeader */

// Instruction Button
.instructions-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  align-self: center;
  margin-top: 1rem;
  color: #fff;
  border: none;
  border-radius: 0.8rem;
  font-weight: 700;
  padding: 0.62rem 1.8rem;
  font-size: 0.92rem;
  box-shadow: 0 6px 16px rgba(124, 58, 237, 0.35);
  transition: transform 0.2s, box-shadow 0.2s;
}

// 🎮 AAA级游戏按钮 - 单行布局不挡logo
.game-btn-aaa {
  position: relative;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  overflow: visible;
  aspect-ratio: 1 / 1;
  flex-shrink: 0;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 4px 16px rgba(0, 0, 0, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.2),
    inset 0 -2px 0 rgba(0, 0, 0, 0.3);
  
  /* 🎮 Web端：更大更震撼 */
  @media (min-width: 1200px) {
    width: clamp(115px, 12vh, 140px);
    height: clamp(115px, 12vh, 140px);
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    
    &:hover {
      transform: translateY(-8px) scale(1.1);
      box-shadow: 
        0 16px 50px rgba(0, 0, 0, 0.6),
        0 8px 24px rgba(0, 0, 0, 0.5),
        inset 0 2px 0 rgba(255, 255, 255, 0.35),
        inset 0 -2px 0 rgba(0, 0, 0, 0.35);
    }
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    width: clamp(105px, 11vh, 125px);
    height: clamp(105px, 11vh, 125px);
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    
    &:hover {
      transform: translateY(-7px) scale(1.08);
      box-shadow: 
        0 14px 45px rgba(0, 0, 0, 0.55),
        0 7px 22px rgba(0, 0, 0, 0.45),
        inset 0 2px 0 rgba(255, 255, 255, 0.3),
        inset 0 -2px 0 rgba(0, 0, 0, 0.3);
    }
  }
  
  /* Tablettuning */
  @media (max-width: 768px) {
    width: clamp(90px, 10vh, 105px);
    height: clamp(90px, 10vh, 105px);
    transition: transform var(--animation-duration) var(--ios-ease-out);
    will-change: transform;
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
    
    &:active {
      transform: scale(0.92);
      transition: transform 0.1s var(--ios-ease-out);
    }
  }
  
  /* Mobiletuning */
  @media (max-width: 480px) {
    width: clamp(78px, 9vh, 88px);
    height: clamp(78px, 9vh, 88px);
  }
  
  /* Small Mobiletuning */
  @media (max-width: 360px) {
    width: clamp(70px, 8.5vh, 80px);
    height: clamp(70px, 8.5vh, 80px);
  }
}

// AAA级按钮背景
.btn-bg-aaa {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

// AAA级按钮光晕
.btn-glow-aaa {
  position: absolute;
  inset: -20px;
  border-radius: 50%;
  opacity: 0;
  filter: blur(20px);
  transition: opacity 0.4s ease;
  pointer-events: none;
}

.game-btn-aaa:hover .btn-glow-aaa {
  opacity: 0.8;
}

// AAA级涟漪效果
.btn-ripple-aaa {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  overflow: hidden;
  pointer-events: none;
}

// AAA级按钮内容
.btn-content-aaa {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  z-index: 2;
}

// AAA级按钮图标
.btn-icon-aaa {
  width: 50%;
  height: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4));
  transition: transform 0.3s ease;
}

.game-btn-aaa:hover .btn-icon-aaa {
  transform: scale(1.1) translateY(-2px);
}

.btn-icon-img-aaa {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

// AAA级按钮标签
.btn-label-aaa {
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.8),
    0 0 8px rgba(0, 0, 0, 0.4);
  
  @media (min-width: 769px) {
    font-size: 0.8rem;
  }
  
  @media (max-width: 480px) {
    font-size: 0.7rem;
  }
}

// 按钮脉动动画
.btn-pulsing {
  animation: btnPulseAAA 1.5s ease-in-out infinite;
}

@keyframes btnPulseAAA {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 
      0 8px 32px rgba(0, 0, 0, 0.4),
      0 4px 16px rgba(0, 0, 0, 0.3);
  }
  50% { 
    transform: scale(1.06);
    box-shadow: 
      0 12px 40px rgba(0, 0, 0, 0.5),
      0 6px 20px rgba(0, 0, 0, 0.4);
  }
}

// 旧按钮样式（保留兼容性）
.btn-glow {
  position: absolute;
  top: -20px;
  left: -20px;
  right: -20px;
  bottom: -20px;
  border-radius: 50%;
  opacity: 0;
  transition: all 0.5s ease;
}

.game-btn:hover .btn-glow {
  opacity: 0.6;
}

.btn-ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.5s ease;
  pointer-events: none;
}

.game-btn:active .btn-ripple {
  width: 160px;
  height: 160px;
}

.btn-content {
  position: relative;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px; // Reduced gap
  height: 100%;
  
  @media (max-width: 480px) {
    gap: 6px;
  }
}

.btn-icon {
  color: #ffffff;
  filter: drop-shadow(0 5px 12px rgba(0, 0, 0, 0.6));

  width: 48px; // match button size tweak
  height: 48px;
  
  @media (max-width: 480px) {
  width: 36px;
  height: 36px;
  }
  
  @media (max-width: 360px) {
    width: 32px;
    height: 32px;
  }
  
  .secondary-controls & {
    width: 36px;
    height: 36px;
    
    @media (max-width: 480px) {
      width: 36px;
      height: 36px;
    }
  }
}

.btn-label {
  font-size: 15px; // small tweak to reduce wrap
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: #ffffff;
  text-shadow: 0 4px 8px rgba(0, 0, 0, 0.7);
  font-family: $cute-font;
  
  @media (max-width: 480px) {
  font-size: 12px;
  }
  
  @media (max-width: 360px) {
    font-size: 11px;
  }
  
  .secondary-controls & {
    font-size: 11px;
    letter-spacing: 1px;
    
    @media (max-width: 480px) {
      font-size: 10px;
    }
  }
}

.btn-count {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #ff4757, #ff6b7a);
  border: 3px solid #ffffff;
  border-radius: 50%;
  pointer-events: none; /* keep visuals from intercepting */
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 900;
  color: #ffffff;
  text-shadow: 0 3px 6px rgba(0, 0, 0, 0.7);
  box-shadow: 0 8px 20px rgba(255, 71, 87, 0.6);
  animation: countPulse 1.5s ease-in-out infinite;
  font-family: $cute-font;
  
  @media (max-width: 480px) {
    width: 28px;
    height: 28px;
    font-size: 14px;
    top: -10px;
    right: -10px;
    border-width: 2px;
  }
}

@keyframes countPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

/* 🎯 AAAfeed inventory badge, tuned for a 2x2 grid */
.feed-inventory-badge-aaa {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, 
    #4ecdc4 0%, 
    #5fd8cf 50%,
    #4ecdc4 100%
  );
  border: 3px solid rgba(255, 255, 255, 0.98);
  z-index: 1000;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: visible;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  will-change: transform;
  
  @media (min-width: 769px) {
    animation: feedInventoryPulseAAA 2.5s ease-in-out infinite;
    backdrop-filter: blur(10px);
    box-shadow: 
      0 10px 30px rgba(78, 205, 196, 0.8),
      0 0 0 3px rgba(78, 205, 196, 0.5),
      inset 0 2px 0 rgba(255, 255, 255, 0.6),
      0 0 50px rgba(78, 205, 196, 0.4);
  }
  
  @media (max-width: 768px) {
    width: 38px;
    height: 38px;
    top: -8px;
    right: -8px;
    animation: feedInventoryPulseAAA 2.5s ease-in-out infinite;
    backdrop-filter: none;
    box-shadow: 
      0 6px 16px rgba(78, 205, 196, 0.6),
      inset 0 2px 0 rgba(255, 255, 255, 0.5);
  }
  
  @media (max-width: 480px) {
    width: 34px;
    height: 34px;
    top: -6px;
    right: -6px;
  }
  
  @media (max-width: 360px) {
    width: 30px;
    height: 30px;
    top: -5px;
    right: -5px;
  }
}

.badge-glow-aaa {
  position: absolute;
  inset: -60%;
  background: radial-gradient(circle, 
    rgba(78, 205, 196, 0.5) 0%, 
    transparent 70%
  );
  animation: badgeGlowAAA 3s ease-in-out infinite;
  filter: blur(12px);
}

@keyframes badgeGlowAAA {
  0%, 100% { 
    opacity: 0.6; 
    transform: scale(1);
  }
  50% { 
    opacity: 1; 
    transform: scale(1.2);
  }
}

.badge-count-aaa {
  font-size: 15px;
  font-weight: 900;
  color: #ffffff;
  text-shadow: 
    0 2px 6px rgba(0, 0, 0, 0.9),
    0 0 10px rgba(78, 205, 196, 0.9);
  line-height: 1;
  margin-bottom: 1px;
  letter-spacing: 0.5px;
  z-index: 2;
  
  @media (max-width: 480px) {
    font-size: 13px;
  }
  
  @media (max-width: 360px) {
    font-size: 11px;
  }
}

.badge-icon-aaa {
  font-size: 11px;
  line-height: 1;
  opacity: 0.95;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.7));
  z-index: 2;
  
  @media (max-width: 480px) {
    font-size: 10px;
  }
  
  @media (max-width: 360px) {
    font-size: 9px;
  }
}

@keyframes feedInventoryPulseAAA {
  0%, 100% { 
    transform: scale(1) rotate(0deg); 
  }
  50% { 
    transform: scale(1.12) rotate(5deg);
  }
}

/* 旧badge样式（保留兼容性） */
.feed-inventory-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 50%, #4ecdc4 100%);
  border: 3px solid rgba(255, 255, 255, 0.95);
  z-index: 1000;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: visible;
  font-family: 'Nunito', -apple-system, BlinkMacSystemFont, sans-serif;
  will-change: transform;
  
  // mobile performance
  @media (max-width: 768px) {
    animation: feedInventoryPulseMobile 2.5s ease-in-out infinite;
    backdrop-filter: none; // 移动端禁用模糊
    box-shadow: 
      0 4px 12px rgba(78, 205, 196, 0.5),
      inset 0 2px 0 rgba(255, 255, 255, 0.5);
  }
  
  @media (min-width: 769px) {
    animation: feedInventoryPulse 2.5s ease-in-out infinite;
    backdrop-filter: blur(8px);
    box-shadow: 
      0 8px 25px rgba(78, 205, 196, 0.7),
      0 0 0 2px rgba(78, 205, 196, 0.4),
      inset 0 2px 0 rgba(255, 255, 255, 0.5),
      0 0 40px rgba(78, 205, 196, 0.3);
  }
  
  @media (max-width: 480px) {
    width: 36px;
    height: 36px;
    top: -6px;
    right: -6px;
  }
  
  @media (max-width: 360px) {
    width: 32px;
    height: 32px;
    top: -5px;
    right: -5px;
  }
}

.badge-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  right: -50%;
  bottom: -50%;
  background: radial-gradient(circle, rgba(78, 205, 196, 0.4) 0%, transparent 70%);
  animation: badgeGlow 3s ease-in-out infinite;
}

.badge-count {
  font-size: 14px;
  font-weight: 900;
  color: #ffffff;
  text-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.8),
    0 0 8px rgba(78, 205, 196, 0.8);
  line-height: 1;
  margin-bottom: 1px;
  letter-spacing: 0.5px;
  z-index: 2;
  
  @media (max-width: 480px) {
    font-size: 12px;
  }
  
  @media (max-width: 360px) {
    font-size: 11px;
  }
}

.badge-icon {
  font-size: 10px;
  line-height: 1;
  opacity: 0.9;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.6));
  z-index: 2;
  
  @media (max-width: 480px) {
    font-size: 9px;
  }
  
  @media (max-width: 360px) {
    font-size: 8px;
  }
}

@keyframes feedInventoryPulse {
  0%, 100% { 
    transform: scale(1) rotate(0deg); 
    box-shadow: 
      0 8px 25px rgba(78, 205, 196, 0.7),
      0 0 0 2px rgba(78, 205, 196, 0.4),
      inset 0 2px 0 rgba(255, 255, 255, 0.5);
  }
  50% { 
    transform: scale(1.08) rotate(1deg); 
    box-shadow: 
      0 12px 35px rgba(78, 205, 196, 0.9),
      0 0 0 3px rgba(78, 205, 196, 0.6),
      inset 0 2px 0 rgba(255, 255, 255, 0.7);
  }
}

// 移动端简化badge动画
@keyframes feedInventoryPulseMobile {
  0%, 100% { 
    transform: scale(1);
  }
  50% { 
    transform: scale(1.03);
  }
}

@keyframes badgeGlow {
  0%, 100% { opacity: 0.6; transform: scale(0.8) rotate(0deg); }
  50% { opacity: 1; transform: scale(1.2) rotate(180deg); }
}

// 🎮 AAA级按钮颜色主题 - 游戏化渐变
.feed-btn-aaa .btn-bg-aaa {
  background: linear-gradient(135deg, 
    #ff6b6b 0%, 
    #ff8787 50%,
    #ffa5a5 100%
  );
}

.feed-btn-aaa .btn-glow-aaa {
  background: radial-gradient(circle, 
    rgba(255, 107, 107, 0.6) 0%, 
    rgba(255, 107, 107, 0.3) 50%,
    transparent 70%
  );
}

.play-btn-aaa .btn-bg-aaa {
  background: linear-gradient(135deg, 
    #4ecdc4 0%, 
    #5fd8cf 50%,
    #78e3da 100%
  );
}

.play-btn-aaa .btn-glow-aaa {
  background: radial-gradient(circle, 
    rgba(78, 205, 196, 0.6) 0%,
    rgba(78, 205, 196, 0.3) 50%,
    transparent 70%
  );
}

.recipe-btn-aaa .btn-bg-aaa {
  background: linear-gradient(135deg, 
    #fdcb6e 0%, 
    #fdd689 50%,
    #fee1a4 100%
  );
}

.recipe-btn-aaa .btn-glow-aaa {
  background: radial-gradient(circle, 
    rgba(253, 203, 110, 0.6) 0%,
    rgba(253, 203, 110, 0.3) 50%,
    transparent 70%
  );
}

.battle-btn-aaa .btn-bg-aaa {
  background: linear-gradient(135deg, 
    #fd79a8 0%, 
    #fd90b8 50%,
    #fda7c8 100%
  );
}

.battle-btn-aaa .btn-glow-aaa {
  background: radial-gradient(circle, 
    rgba(253, 121, 168, 0.6) 0%,
    rgba(253, 121, 168, 0.3) 50%,
    transparent 70%
  );
}

// 旧按钮样式（保留兼容性）
.feed-btn .btn-bg {
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);
}

.feed-btn .btn-glow {
  background: radial-gradient(circle, rgba(255, 107, 107, 0.4) 0%, transparent 70%);
}

.play-btn .btn-bg {
  background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
}

.play-btn .btn-glow {
  background: radial-gradient(circle, rgba(78, 205, 196, 0.4) 0%, transparent 70%);
}

.recipe-btn .btn-bg {
  background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
}

.recipe-btn .btn-glow {
  background: radial-gradient(circle, rgba(253, 203, 110, 0.4) 0%, transparent 70%);
}

.memories-btn .btn-bg {
  background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%);
}

.memories-btn .btn-glow {
  background: radial-gradient(circle, rgba(253, 121, 168, 0.4) 0%, transparent 70%);
}

/* about button removed per UX request */

.btn-icon-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

// Logo - 🎮 AAA终极：可点击导航到Recipe
.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  flex-shrink: 0;
  order: -1;
  cursor: pointer; /* 🎯 可点击提示 */
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 800; /* 🎯 低于头像(850)和对话框(900) */
  position: relative; /* 🎯 确保z-index生效 */
  
  /* 微妙的浮动动画 */
  animation: logoFloat 6s ease-in-out infinite;
  
  /* 🎯 点击反馈 */
  &:active {
    transform: scale(0.98);
  }
  
  @media (min-width: 1200px) {
    padding: 0;
    margin-bottom: 2vh; /* 🎯 0→2vh，Logo继续下移 */
    flex-shrink: 0;
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    padding: 0;
    margin-bottom: 2.5vh; /* 🎯 0.5vh→2.5vh，Logo继续下移 */
    flex-shrink: 0;
  }
  
  @media (max-width: 768px) {
    padding: 0;
    margin-bottom: clamp(8px, 1.2vh, 16px);
  }
  
  @media (max-width: 480px) {
    margin-bottom: clamp(6px, 1vh, 12px);
  }
}

.logo {
  width: 100%;
  height: auto;
  object-fit: contain;
  filter: drop-shadow(0 4px 20px rgba(168, 230, 207, 0.3));
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  
  /* 🎮 AAA工业级：Logo 2倍巨大tuning */
  @media (min-width: 1200px) {
    max-width: clamp(1100px, 84vw, 1440px); /* 🎯 550→1100px, 720→1440px，2倍放大 */
    max-height: 28vh; /* 🎯 14vh→28vh，2倍放大 */
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    max-width: clamp(1000px, 88vw, 1300px); /* 🎯 500→1000px, 650→1300px，2倍放大 */
    max-height: 32vh; /* 🎯 16vh→32vh，2倍放大 */
  }
  
  /* Tablet */
  @media (max-width: 768px) {
    max-width: clamp(320px, 55vw, 400px);
  }
  
  /* Mobile */
  @media (max-width: 480px) {
    max-width: clamp(280px, 65vw, 340px);
  }
  
  /* Small Mobile */
  @media (max-width: 360px) {
    max-width: clamp(240px, 70vw, 300px);
  }
  
  /* 🎯 可点击Logo - Hover效果 */
  &.clickable-logo {
    cursor: pointer;
    
    &:hover {
      transform: scale(1.05) translateY(-4px);
      filter: drop-shadow(0 8px 35px rgba(168, 230, 207, 0.7));
    }
    
    &:active {
      transform: scale(1.02) translateY(-2px);
    }
  }
  
  &:hover {
    transform: scale(1.02) translateY(-2px);
    filter: drop-shadow(0 6px 28px rgba(168, 230, 207, 0.5));
  }
}

@keyframes logoFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

// Optimized Recipe panel
// .recipe-panel {
//   position: fixed;
//   bottom: 0;
//   left: 0;
//   right: 0;
//   background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0.95));
//   backdrop-filter: blur(35px);
//   border-top-left-radius: 25px; // Smaller radius
//   border-top-right-radius: 25px;
//   box-shadow: 0 -20px 80px rgba(0, 0, 0, 0.25);
//   transform: translateY(calc(100% - 70px)); // Smaller collapsed height
//   transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
//   z-index: 50;
//   max-height: 50vh; // Limit max height
  
//   &.panel-expanded {
//     transform: translateY(0);
//   }
  
//   @media (max-width: 480px) {
//     max-height: 45vh; // Smaller on mobile
//     transform: translateY(calc(100% - 60px));
//   }
// }

// .panel-handle {
//   display: flex;
//   justify-content: center;
//   padding: 12px 0; // Smaller padding
//   cursor: pointer;
// }

// .handle-indicator {
//   width: 50px; // Smaller
//   height: 5px;
//   background: rgba(0, 0, 0, 0.3);
//   border-radius: 3px;
//   transition: all 0.4s ease;
  
//   .recipe-panel:hover & {
//     background: rgba(0, 0, 0, 0.5);
//     width: 60px;
//   }
// }

// .panel-header {
//   padding: 20px 24px; // Smaller padding
//   display: flex;
//   justify-content: space-between;
//   align-items: center;
//   border-bottom: 2px solid rgba(0, 0, 0, 0.1);
  
//   .panel-title {
//     display: flex;
//     align-items: center;
//     gap: 15px;
    
//     .title-icon {
//       font-size: 28px; // Smaller
//       filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
//     }
    
//     h3 {
//       margin: 0;
//       font-size: 22px; // Smaller
//       font-weight: 900;
//       color: #2c3e50;
//       font-family: $cute-font;
//     }
//   }
// }

// .panel-status {
//   .status-badge {
//     background: linear-gradient(135deg, #667eea, #764ba2);
//     color: #ffffff;
//     padding: 8px 16px; // Smaller padding
//     border-radius: 20px;
//     font-size: 14px; // Smaller font
//     font-weight: 800;
//     text-transform: uppercase;
//     letter-spacing: 1px;
//     box-shadow: 0 6px 15px rgba(102, 126, 234, 0.4);
//     font-family: $cute-font;
//   }
// }

// .panel-content {
//   padding: 0 24px 24px; // Smaller padding
//   max-height: 35vh; // Smaller max height
//   overflow-y: auto;
  
//   &::-webkit-scrollbar {
//     width: 8px; // Smaller scrollbar
//   }
  
//   &::-webkit-scrollbar-track {
//     background: rgba(0, 0, 0, 0.1);
//     border-radius: 4px;
//   }
  
//   &::-webkit-scrollbar-thumb {
//     background: rgba(0, 0, 0, 0.4);
//     border-radius: 4px;
    
//     &:hover {
//       background: rgba(0, 0, 0, 0.5);
//     }
//   }
  
//   @media (max-width: 480px) {
//     max-height: 30vh;
//   }
// }

// .quest-description {
//   margin-bottom: 20px;
  
//   p {
//     font-size: 16px;
//     color: #2c3e50;
//     font-family: $cute-font;
//     font-weight: 600;
//     text-align: center;
//     margin: 0;
//     line-height: 1.5;
//   }
  
//   @media (max-width: 480px) {
//     p {
//       font-size: 14px;
//     }
//   }
// }

// Enhanced feedback system
.game-feedback {
  position: fixed;
  top: 35%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 300;
  animation: feedbackBounce 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  
  .feedback-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0.95));
    backdrop-filter: blur(30px);
    border-radius: 30px;
    border: 3px solid rgba(255, 255, 255, 0.6);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
  }
  
  .feedback-content {
    position: relative;
    padding: 25px 35px;
    display: flex;
    align-items: center;
    gap: 18px;
    z-index: 2;
  }
  
  &.success .feedback-bg {
    border-color: #4ecdc4;
    box-shadow: 0 20px 60px rgba(78, 205, 196, 0.5);
  }
  
  &.warning .feedback-bg {
    border-color: #ff6b6b;
    box-shadow: 0 20px 60px rgba(255, 107, 107, 0.5);
  }
  
  &.info .feedback-bg {
    border-color: #74b9ff;
    box-shadow: 0 20px 60px rgba(116, 185, 255, 0.5);
  }
  
  &.levelup .feedback-bg {
    border-color: #fd79a8;
    box-shadow: 0 20px 60px rgba(253, 121, 168, 0.6);
    background: linear-gradient(135deg, rgba(253, 121, 168, 0.2), rgba(253, 203, 110, 0.2));
  }
}

@keyframes feedbackBounce {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.6);
  }
  60% {
    transform: translate(-50%, -50%) scale(1.15);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

.feedback-icon {
  font-size: 32px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4));
}

.feedback-text {
  font-size: 20px;
  font-weight: 800;
  color: #2c3e50;
  font-family: $cute-font;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

// Enhanced Combo display
.combo-display {
  position: fixed;
  top: 25%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 250;
  animation: comboShow 1s cubic-bezier(0.4, 0, 0.2, 1);
  
  .combo-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(253, 121, 168, 0.2), rgba(253, 203, 110, 0.2));
    backdrop-filter: blur(25px);
    border-radius: 25px;
    border: 2px solid rgba(253, 121, 168, 0.5);
    box-shadow: 0 15px 50px rgba(253, 121, 168, 0.4);
  }
  
  .combo-content {
    position: relative;
    padding: 20px 30px;
    text-align: center;
    z-index: 2;
  }
  
  .combo-text {
    font-size: 36px;
    font-weight: 900;
    color: #fd79a8;
    text-shadow: 0 4px 15px rgba(253, 121, 168, 0.8);
    margin-bottom: 8px;
    font-family: 'Fredoka One', $cute-font;
    letter-spacing: 3px;
  }
  
  .combo-multiplier {
    font-size: 22px;
    font-weight: 800;
    color: #fdcb6e;
    text-shadow: 0 3px 10px rgba(253, 203, 110, 0.8);
    font-family: $cute-font;
  }
}

@keyframes comboShow {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.4);
  }
  60% {
    transform: translate(-50%, -50%) scale(1.4);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

// Enhanced Level up effect
.levelup-effect {
  position: fixed;
  top: 30%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 350;
  animation: levelupShow 3.5s cubic-bezier(0.4, 0, 0.2, 1);
  
  .levelup-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(253, 121, 168, 0.25), rgba(253, 203, 110, 0.25));
    backdrop-filter: blur(30px);
    border-radius: 30px;
    border: 3px solid rgba(253, 121, 168, 0.6);
    box-shadow: 0 25px 80px rgba(253, 121, 168, 0.6);
  }
  
  .levelup-content {
    position: relative;
    padding: 30px 40px;
    text-align: center;
    z-index: 2;
  }
  
  .levelup-text {
    font-size: 54px;
    font-weight: 900;
    background: linear-gradient(135deg, #fd79a8, #fdcb6e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 12px;
    font-family: 'Fredoka One', $cute-font;
    letter-spacing: 4px;
    filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.4));
  }
  
  .levelup-score {
    font-size: 28px;
    font-weight: 900;
    color: #fdcb6e;
    text-shadow: 0 4px 12px rgba(253, 203, 110, 0.8);
    font-family: $cute-font;
  }
}

@keyframes levelupShow {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.4);
  }
  25% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.3);
  }
  85% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.7);
  }
}

// Accessibility & performance
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* 🎯 iOS特有tuning */
@supports (-webkit-touch-callout: none) {
  .home {
    /* iOS Safari 特有tuning */
    -webkit-overflow-scrolling: touch;
    -webkit-tap-highlight-color: transparent;
  }
  
  .game-btn, .pet-arena {
    /* iOS 防止双击缩放 */
    touch-action: manipulation;
    -webkit-user-select: none;
    user-select: none;
  }
  
  /* iOS 状态栏适配 */
  .game-hud {
    top: max(env(safe-area-inset-top), 20px);
  }
}

/* 🎯 高分辨率屏幕tuning */
@media (-webkit-min-device-pixel-ratio: 2) {
  .game-btn {
    /* Retina 屏幕tuning */
    transform: translateZ(0);
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
  }
}
</style>
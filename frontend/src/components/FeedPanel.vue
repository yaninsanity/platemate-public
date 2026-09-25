<template>
  <v-dialog
    v-model="isOpen"
    :max-width="isMobile ? '100%' : '900'"
    persistent
    :style="{ zIndex: 10000 }"
  >
    <div class="feed-panel-overlay" @click="closePanel">
      <div class="feed-panel" @click.stop>
        <!-- 顶部标题 - 精简设计 -->
        <div class="panel-header">
          <div class="kinny-avatar-section">
            <div class="kinny-svg-container" :class="{ 
              eating: isEating, 
              hungry: kinnyState === 'hungry',
              excited: kinnyState === 'excited', 
              satisfied: kinnyState === 'satisfied' 
            }">
              <img src="/assets/kinnyfeed.png" alt="Kinny" class="kinny-face-img" />
              
              <!-- 喂食效果 -->
              <div class="kinny-effects-layer" aria-hidden="true">
                <div
                  v-for="v in vegWaves"
                  :key="v.id"
                  class="veg-wave"
                  :style="{ 
                    transform: `translate(${v.left}px, ${v.top}px)`, 
                    opacity: v.opacity, 
                    fontSize: v.size + 'px' 
                  }"
                >
                  {{ v.emoji }}
                </div>
              </div>
            </div>

            <div class="hunger-info-compact">
              <div class="hunger-value" :class="hungerStatusClass">{{ currentHunger }}%</div>
              <div class="hunger-label">{{ hungerStatusText }}</div>
            </div>
          </div>
          
          <button class="close-btn" @click="closePanel">
            <v-icon color="white" size="20">mdi-close</v-icon>
          </button>
        </div>

        <!-- 🎯 精准改善：Checkin状态弹窗 -->
        <div v-if="showCheckinDialog" class="checkin-dialog-overlay" @click="closeCheckinDialog">
          <div class="checkin-dialog" @click.stop>
            <div class="dialog-header">
              <h3 class="dialog-title">{{ checkinDialogData.title }}</h3>
              <button class="dialog-close" @click="closeCheckinDialog">×</button>
            </div>
            <div class="dialog-content">
              <div class="dialog-icon">{{ checkinDialogData.icon }}</div>
              <p class="dialog-message">{{ checkinDialogData.message }}</p>
              <div v-if="checkinDialogData.countdown" class="dialog-countdown">
                <span class="countdown-label">Next checkin available in:</span>
                <span class="countdown-time">{{ checkinDialogData.countdown }}</span>
              </div>
            </div>
            <div class="dialog-actions">
              <button class="dialog-btn primary" @click="closeCheckinDialog">
                {{ checkinDialogData.buttonText }}
              </button>
            </div>
          </div>
        </div>

        <!-- 🎯 食物管理 - 精准改善：清晰的AAA游戏界面 -->

       

        <div class="food-inventory-section-modern">
          <!-- 🎯 Kinny Food large card with the richer interaction -->
          <div class="kinny-food-card-mega" :class="{ 'card-glow': isFeeding }">
            <!-- Food Icon & Info with partner comparison -->
            <div class="kinny-header-row">
              <div 
                class="kinny-icon-mega" 
                :class="{ 
                  'icon-bounce': isFeeding,
                  'icon-hungry': aggregatedQuantity === 0 
                }"
              >
                🍽️
              </div>
              <div class="kinny-info-column">
                <h2 class="kinny-title">Kinny Food</h2>
                <div class="kinny-stock-comparison">
                  <!-- Your inventory -->
                  <div class="stock-you">
                    <span class="stock-label">You:</span>
                    <span class="stock-number">{{ aggregatedQuantity }}</span>
                  </div>
                  <!-- VS divider -->
                  <span class="vs-divider">VS</span>
                  <!-- Partner inventory -->
                  <div class="stock-partner">
                    <span class="stock-label">Partner:</span>
                    <span class="stock-number">{{ partnerTotalQuantity }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 🎯 Couple Storage Breakdown - You vs Partner -->
            <div v-if="aggregatedQuantity > 0 || partnerTotalQuantity > 0" class="couple-storage-breakdown">
              <!-- Your Storage -->
              <div class="storage-column your-storage">
                <div class="storage-header">
                  <span class="storage-icon">👤</span>
                  <span class="storage-label">Your Storage</span>
                </div>
                <div class="fruits-grid-fixed">
                  <div 
                    v-for="fruit in yourFruitBreakdown" 
                    :key="`your-${fruit.type}`"
                    class="fruit-item-aaa"
                    :class="{ 'has-quantity': fruit.quantity > 0 }"
                  >
                    <div class="fruit-shine"></div>
                    <span class="fruit-emoji">{{ fruit.emoji }}</span>
                    <span class="fruit-count">{{ fruit.quantity }}</span>
                  </div>
                </div>
              </div>

              <!-- VS Divider -->
              <div class="storage-divider">
                <div class="divider-icon">⚡</div>
              </div>

              <!-- Partner Storage -->
              <div class="storage-column partner-storage">
                <div class="storage-header partner-header-with-button">
                  <div class="header-left">
                  <span class="storage-icon">👥</span>
                  <span class="storage-label">Partner's Storage</span>
                  </div>
                  
                  <!-- 🎯 Notify Partner Button (Right Corner) - Only show if user has a couple -->
                  <button
                    v-if="hasCouple"
                    class="notify-partner-btn notify-corner-btn"
                    @click="notifyPartnerAboutFood"
                    :disabled="isSendingNotification"
                    :class="{ 'is-sending': isSendingNotification }"
                  >
                    <span class="notify-icon">{{ isSendingNotification ? '⏳' : '📱' }}</span>
                    <span class="notify-text">
                      {{ isSendingNotification ? 'Sending...' : 'Notify 💝' }}
                    </span>
                  </button>
                </div>
                <div class="fruits-grid-fixed">
                  <div 
                    v-for="fruit in partnerFruitBreakdown" 
                    :key="`partner-${fruit.type}`"
                    class="fruit-item-aaa"
                    :class="{ 'has-quantity': fruit.quantity > 0 }"
                  >
                    <div class="fruit-shine"></div>
                    <span class="fruit-emoji">{{ fruit.emoji }}</span>
                    <span class="fruit-count">{{ fruit.quantity }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 🎯 primary action: feed Kinny, with the richer interaction -->
            <button
              class="feed-kinny-mega-btn"
              @click="feedKinnyWithAnimation()"
              :disabled="isFeeding || aggregatedQuantity <= 0"
              :class="{ 
                'is-feeding': isFeeding, 
                'out-of-stock': aggregatedQuantity === 0,
                'btn-pulse': aggregatedQuantity > 0 && !isFeeding
              }"
            >
              <span class="feed-icon">{{ isFeeding ? '⏳' : '🍽️' }}</span>
              <span class="feed-text">{{ isFeeding ? 'Feeding...' : 'Feed Kinny' }}</span>
              <span class="feed-effect">+10 Energy</span>
            </button>

            <!-- 空状态提示 -->
            <div v-if="aggregatedQuantity === 0" class="empty-hint">
              <span class="hint-icon">🎮</span>
              <span class="hint-text">Play games or collect rewards to get food!</span>
            </div>
          </div>

          <!-- 🎯 统一的次要动作栏 -->
          <div class="secondary-actions-unified">
            <!-- Collect Reward -->
            <button 
              class="action-btn-unified collect-btn"
              @click="performCheckinWithSlotMachine"
              :disabled="!petStore?.slotMachine.canSpin || isCheckingIn"
              :class="{ 
                'is-active': petStore?.slotMachine.canSpin && !isCheckingIn,
                'is-loading': isCheckingIn
              }"
            >
              <span class="btn-icon-unified">{{ isCheckingIn ? '⏳' : '🎁' }}</span>
              <span class="btn-text-unified">
                {{ isCheckingIn ? 'Collecting...' : 
                   petStore?.slotMachine.canSpin ? 'Collect Reward' : 'Recharging' }}
              </span>
              <span v-if="!petStore?.slotMachine.canSpin && petStore?.slotMachine.cooldownRemaining" 
                    class="btn-countdown">
                {{ petStore?.slotMachine.cooldownRemaining }}
              </span>
            </button>

            <!-- Harvest All -->
            <button 
              class="action-btn-unified harvest-btn"
              @click="harvestAllFoods"
              :disabled="isHarvesting || harvestableCount === 0"
              :class="{ 
                'is-active': harvestableCount > 0,
                'is-loading': isHarvesting
              }"
            >
              <span class="btn-icon-unified">{{ isHarvesting ? '⏳' : '🌾' }}</span>
              <span class="btn-text-unified">
                {{ isHarvesting ? 'Harvesting...' : harvestableCount > 0 ? `Harvest ${harvestableCount}` : 'Harvest All' }}
              </span>
            </button>
          </div>
        </div>

        <!-- 🎯 食物获得方式说明 - 移动到下方并改善布局 -->
        <div class="food-system-info-bottom">
          <div class="system-header">
            <h3 class="system-title">🎮 How to Get Food</h3>
          </div>
          <div class="system-methods-grid-compact">
            <div class="method-card-small">
              <div class="method-icon">🎰</div>
              <div class="method-content">
                <div class="method-title">Checkin</div>
                <div class="method-desc">Every 2h</div>
              </div>
            </div>
            <div class="method-card-small">
              <div class="method-icon">✂️</div>
              <div class="method-content">
                <div class="method-title">Play Game</div>
                <div class="method-desc">Win rewards</div>
              </div>
            </div>
            <div class="method-card-small">
              <div class="method-icon">📝</div>
              <div class="method-content">
                <div class="method-title">Share Your Cooking</div>
                <div class="method-desc">Post stories</div>
              </div>
            </div>
            <div class="method-card-small">
              <div class="method-icon">💬</div>
              <div class="method-content">
                <div class="method-title">Comments</div>
                <div class="method-desc">3+ rewards</div>
              </div>
            </div>
          </div>
          
          
        </div>

        <!-- 喂食动画层：食物飞入嘴里 - 🎯 performance tuning：使用transform -->
        <div class="feed-animations" aria-hidden="true">
          <div
            v-for="a in animations"
            :key="a.id"
            :id="'fly-'+a.id"
            class="fly-food"
            :style="{ 
              transform: `translate(${a.left}px, ${a.top}px)`, 
              opacity: a.opacity 
            }"
          >
            <span class="food-emoji-flying">{{ a.icon }}</span>
          </div>
        </div>

        <!-- Emoji particle layer: stars/hearts that pop from the mouth when food is eaten -->
        <div class="emoji-layer" aria-hidden="true">
          <div
            v-for="e in emojiParticles"
            :key="e.id"
            class="emoji-particle"
            :style="{ 
              transform: `translate(${e.left}px, ${e.top}px) rotate(${e.rotation}deg)`, 
              opacity: e.opacity, 
              fontSize: e.size + 'px'
            }"
          >
            {{ e.emoji }}
          </div>
        </div>

        <!-- 装饰性粒子效果 -->
        <div class="particles">
          <div v-for="i in 12" :key="i" class="particle" :style="getParticleStyle(i)"></div>
        </div>
      </div>
    </div>
  </v-dialog>
  
  <!-- 🎰 老虎机动画 -->
  <SlotMachinePerfect
    :isVisible="petStore?.slotMachine.isVisible || false"
    :slotResults="petStore?.slotMachine.slotResults || petStore?.checkinResponse?.slot_results"
    :slotAnimation="petStore?.slotMachine.slotAnimation || petStore?.checkinResponse?.slot_animation"
    :slotPreview="petStore?.slotMachine.slotPreview || petStore?.checkinResponse?.slot_preview"
    :onCooldown="!petStore?.slotMachine.canSpin"
    :cooldownTime="petStore?.slotMachine.cooldownRemaining || ''"
    :totalSpins="petStore?.slotMachine.totalSpins || 0"
    @close="petStore?.closeSlotMachine()"
    @refresh-inventory="refreshFoodInventory"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { usePetStore } from '@/stores/petStore'
import SlotMachinePerfect from './SlotMachinePerfect.vue'

// Lazily access the Pet store at runtime to avoid calling usePetStore() during module
// evaluation (which runs before Pinia is installed in main.ts).
let _petStore: any = null
function getPetStore() {
  if (!_petStore) {
    try {
      _petStore = usePetStore()
    } catch (error) {
      console.warn('[FeedPanel] Failed to init pet store:', error)
      return null
    }
  }
  return _petStore
}

interface FoodItem {
  id: string
  name: string
  icon: string
  hunger: number
  cost?: number
  premium?: boolean
  food_type?: string  // 添加食物类型字段用于库存系统
  quantity?: number   // 添加数量字段
  // 🎯 新增：情侣库存对比字段
  partner_quantity?: number
  total_quantity?: number
  can_use?: boolean
  can_harvest?: boolean
  advantage?: 'self' | 'partner' | 'equal'
}

interface InventoryItem {
  food_type: string
  food_display: string
  quantity: number
  can_harvest: boolean
  last_harvest: string | null
}

/* ---------- Stores ---------- */
// NOTE: use getPetStore() when you need to call store methods to ensure Pinia is active.

/* ---------- Props & Emits ---------- */
const props = defineProps<{
  modelValue: boolean
  currentHunger: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'feed': [food: FoodItem, newHunger: number]
}>()

/* ---------- Reactive State ---------- */
// 🎯 mobile performance：设备检测
/* ───────────── iOS原生级移动端性能检测 ───────────── */
const isMobile = ref(false)
const isLowPerformance = ref(false)

// 🎯 动态性能监控
const frameRate = ref(60)
const frameCount = ref(0)
const lastFrameTime = ref(performance.now())
const performanceDowngrade = ref(false) // 动态降级标志

// 🎯 移动端DOM缓存tuning
const cachedElements = ref({
  kinnyContainer: null as HTMLElement | null,
  feedButtons: [] as HTMLElement[]
})

const isIOS = ref(false)
const isAndroid = ref(false)
const devicePixelRatio = ref(1)
const isRetina = ref(false)
const supportsHardwareAcceleration = ref(true)

// 🎯 访问PetStore
const petStore = computed(() => getPetStore())

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isFeeding = ref(false)
const isHarvesting = ref(false)
const isCheckingIn = ref(false)
const hasCheckedInToday = ref(false)

// 🎯 check-in dialog system
const showCheckinDialog = ref(false)
const checkinDialogData = ref({
  title: '',
  icon: '',
  message: '',
  countdown: '',
  buttonText: 'OK'
})

// 🎯 精准改善：Checkin状态管理
const checkinStatus = ref({
  hasCheckedIn: false,
  canCheckin: true,
  nextCheckinTime: null as string | null,
  nextCheckinCountdown: ''
})

// 🎯 精准改善：倒计时定时器
const checkinCountdownTimer = ref<NodeJS.Timeout | null>(null)

// Fruit harvest system - claim fruits first, then feed
const availableFruits = ref<FoodItem[]>([])
const harvestCooldown = ref(0)

// 从store获取真实库存数据
const foodInventory = computed(() => getPetStore().foodInventory as InventoryItem[] || [])
const totalFoodItems = computed(() => getPetStore().totalFoodItems || 0)

// 🎯 新增：情侣双方库存对比数据
const coupleInventoryComparison = ref<any>(null)
const showCoupleComparison = ref(true) // 🎯 精准改善：默认显示both模式

// 转换库存数据为FoodItem格式
const inventoryFoodItems = computed((): FoodItem[] => {
  return foodInventory.value
    .filter((item: InventoryItem) => item.quantity > 0)
    .map((item: InventoryItem) => ({
      id: item.food_type,
      name: item.food_display,
      icon: item.food_display.split(' ')[0], // 提取emoji
      hunger: 10, // 每个食物恢复10点
      quantity: item.quantity,
      food_type: item.food_type
    }))
})

// 🎯 精准改善：获取所有食物类型（包含0数量的）- 移除"More items"限制
const allFoodItems = computed((): FoodItem[] => {
  if (!coupleInventoryComparison.value) return inventoryFoodItems.value
  
  return coupleInventoryComparison.value.comparison.map((comp: any) => ({
    id: comp.food_type,
    name: comp.food_display,
    icon: comp.food_display.split(' ')[0],
    hunger: 10,
    quantity: comp.self_quantity,
    partner_quantity: comp.partner_quantity,
    total_quantity: comp.total_quantity,
    can_use: comp.can_use,
    can_harvest: comp.can_harvest,
    advantage: comp.advantage,
    food_type: comp.food_type
  }))
})

/* ---------- Animation state for flying food ---------- */
const animations = ref<Array<{ id: number; icon: string; left: number; top: number; opacity: number }>>([])
let animSeq = 1
const isEating = ref(false)
const kinnyState = ref('normal') // 新增状态：normal, hungry, excited, eating, satisfied

// Emoji particle system (stars, hearts, sparkles)
const emojiParticles = ref<Array<{ id: number; emoji: string; left: number; top: number; opacity: number; size: number; rotation: number }>>([])
let emojiSeq = 1

function spawnEmojiParticles(centerX: number, centerY: number, count = 12) {
  // 🎯 mobile performance：智能粒子数量控制
  let optimizedCount = count
  if (isLowPerformance.value) {
    optimizedCount = Math.min(count, 3) // 低性能设备最多3个
  } else if (isMobile.value) {
    optimizedCount = Math.min(count, 6) // 移动设备最多6个
  }
  
  console.log('✨ Spawning', optimizedCount, 'emoji particles at mouth:', centerX, centerY)
  
  const emojis = ['✨', '💫', '⭐', '💖', '💛', '🌟']
  
  // � 使用批量DOM更新减少重排
  const fragment = document.createDocumentFragment()
  
  for (let i = 0; i < optimizedCount; i++) {
    const id = emojiSeq++
    
    // 创建更自然的爆炸分布
    const angle = (Math.PI * 2 * i) / optimizedCount + (Math.random() - 0.5) * 0.4
    const left = centerX + Math.cos(angle) * (6 + Math.random() * 8)
    const top = centerY + Math.sin(angle) * (6 + Math.random() * 8)
    const size = isLowPerformance.value ? 14 : (16 + Math.round(Math.random() * 12))
    const rotation = Math.round((Math.random() - 0.5) * 90)
    const emoji = emojis[Math.floor(Math.random() * emojis.length)]
    
    emojiParticles.value.push({ 
      id, 
      emoji, 
      left, 
      top, 
      opacity: 1, 
      size, 
      rotation 
    })
    
    console.log(`🎊 Launching emoji ${i+1}: ${emoji}`)

    // 🎯 tuning动画性能：使用更短的动画时间和更少的计算
    const duration = isLowPerformance.value ? 600 : (700 + Math.round(Math.random() * 300))
    const delay = i * (isLowPerformance.value ? 50 : 30)
    const baseDistance = isLowPerformance.value ? 15 : 20
    const finalDistance = baseDistance + Math.random() * (isLowPerformance.value ? 20 : 30)
    const startTime = performance.now() + delay
    
    // 🎯 transform rather than left/top, so the GPU does the work
    function step(now: number) {
      if (now < startTime) {
        requestAnimationFrame(step)
        return
      }
      
      const t = Math.min(1, (now - startTime) / duration)
      const ease = 1 - Math.pow(1 - t, 2) // 更简单的缓动函数
      const a = emojiParticles.value.find(x => x.id === id)
      
      if (a) {
        // 更复杂的运动轨迹
        const explosionX = Math.cos(angle) * finalDistance * ease
        const explosionY = Math.sin(angle) * finalDistance * ease
        
        // 添加重力效果
        const gravity = t * t * 20
        
        // 添加旋转和缩放效果
        const scale = 1 + Math.sin(t * Math.PI) * 0.3
        const rotationOffset = t * 180
        
        a.left = left + explosionX
        a.top = top + explosionY + gravity
        a.opacity = 1 - ease
        a.size = size * scale
        a.rotation = rotation + rotationOffset
        
        // console.log(`✨ Emoji ${emoji} progress: ${(t*100).toFixed(1)}%`)
      }
      
      if (t < 1) {
        requestAnimationFrame(step)
      } else {
        console.log(`💥 Emoji ${emoji} animation complete!`)
        setTimeout(() => {
          const idx = emojiParticles.value.findIndex(x => x.id === id)
          if (idx >= 0) {
            emojiParticles.value.splice(idx, 1)
            console.log(`🗑️ Removed emoji ${emoji}`)
          }
        }, 100)
      }
    }
    requestAnimationFrame(step)
  }
  
  console.log('🎊 All emoji particles launched!')
}

/* Veg-wave system: small vegetables from the right travel left toward kinny for extra gamey feel */
const vegWaves = ref<Array<{ id: number; emoji: string; left: number; top: number; opacity: number; size: number }>>([])
let vegSeq = 1

function spawnVegWave(count = 8) {
  // 🎯 mobile performance：智能数量控制
  let optimizedCount = count
  if (isLowPerformance.value) {
    optimizedCount = Math.min(count, 3) // 低性能设备最少
  } else if (isMobile.value) {
    optimizedCount = Math.min(count, 4) // 移动设备适中
  }
  
  console.log('🌊 Spawning', optimizedCount, 'vegetable wave particles')
  
  // 计算Kinny容器位置
  const kinnyContainer = document.querySelector('.kinny-svg-container') as HTMLElement | null
  const kinnyRect = kinnyContainer ? kinnyContainer.getBoundingClientRect() : { left: 100, top: 100, width: 200, height: 80 }
  const emojis = ['🥕','🥦','🍅','🌽','🍆','🥬']
  
  for (let i = 0; i < optimizedCount; i++) {
    const id = vegSeq++
    const size = isLowPerformance.value ? 16 : (16 + Math.round(Math.random() * 12))
    
    // 🎯 简化计算：使用固定偏移而不是复杂随机值
    const left = kinnyRect.left + kinnyRect.width + 25 + (i % 3) * 15
    const top = kinnyRect.top + (i % 3) * (kinnyRect.height / 3)
    const emoji = emojis[i % emojis.length] // 避免重复随机计算
    
    vegWaves.value.push({ id, emoji, left, top, opacity: 1, size })
    console.log(`🥕 Launching veggie ${i+1}: ${emoji}`)

    // 🎯 performance tuning：预计算固定值
    const targetX = kinnyRect.left + kinnyRect.width * 0.5
    const targetY = kinnyRect.top + kinnyRect.height * 0.6
    const duration = isLowPerformance.value ? 500 : (700 + Math.round(Math.random() * 200))
    const delay = i * (isLowPerformance.value ? 100 : 80)
    const startLeft = left
    const startTop = top
    
    setTimeout(() => {
      const startTime = performance.now()
      
      function step(now: number) {
        const t = Math.min(1, (now - startTime) / duration)
        // 🎯 简化动画曲线：线性插值而不是复杂缓动
        const ease = isLowPerformance.value ? t : (1 - Math.pow(1 - t, 2))
        const a = vegWaves.value.find(x => x.id === id)
        
        if (a) {
          // 🎯 条件性波浪效果：低性能设备不使用
          const waveOffset = isLowPerformance.value ? 0 : Math.sin(ease * Math.PI * 2) * 10
          a.left = startLeft + (targetX - startLeft) * ease
          a.top = startTop + (targetY - startTop) * ease + waveOffset
          a.opacity = 1 - ease * 0.5
          
          // 🎯 简化尺寸变化：低性能设备保持固定大小
          if (!isLowPerformance.value) {
            a.size = size * (1 + Math.sin(ease * Math.PI) * 0.1)
          }
        }
        
        if (t < 1) {
          requestAnimationFrame(step)
        } else {
          console.log(`🎯 Veggie ${emoji} reached target!`)
          // 🎯 立即清理，不延迟
          const idx = vegWaves.value.findIndex(x => x.id === id)
          if (idx >= 0) {
            vegWaves.value.splice(idx, 1)
            console.log(`🗑️ Removed veggie ${emoji}`)
          }
        }
      }
      requestAnimationFrame(step)
    }, delay)
  }
  
  console.log('🌊 All veggie waves launched!')
}

function spawnFeedAnimations(food: FoodItem, count = 6) {
  // 🎯 performance tuning combining static and runtime detection
  const effectiveLowPerf = isLowPerformance.value || performanceDowngrade.value
  let optimizedCount = count
  
  if (effectiveLowPerf) {
    optimizedCount = Math.min(count, 2) // 低性能设备最少
  } else if (isMobile.value) {
    optimizedCount = Math.min(count, 3) // 移动设备适中
  }
  
  console.log('🚀 Spawning', optimizedCount, 'flying food animations for:', food.name, 
              effectiveLowPerf ? '(performance mode)' : '')
  
  // 🎯 mobile tuning：使用缓存的DOM元素或快速查询
  let startRect, targetRect
  
  if (cachedElements.value.kinnyContainer) {
    // 使用缓存的kinny容器
    targetRect = cachedElements.value.kinnyContainer.getBoundingClientRect()
  } else {
    // 缓存kinny容器
    const target = document.querySelector('.kinny-svg-container') as HTMLElement
    if (target) {
      cachedElements.value.kinnyContainer = target
      targetRect = target.getBoundingClientRect()
    } else {
      targetRect = { left: window.innerWidth/2, top: 100, width: 80, height: 40 }
    }
  }
  
  // 按钮位置查询（较少缓存因为可能滚动）
  const btn = document.querySelector(`[data-food-id="${food.id}"]`)
  startRect = btn ? (btn as HTMLElement).getBoundingClientRect() : { left: 100, top: 200, width: 40, height: 40 }
  
  // 预计算目标位置
  const targetX = targetRect.left + targetRect.width * 0.5
  const targetY = targetRect.top + targetRect.height * 0.6

  for (let i = 0; i < optimizedCount; i++) {
    const id = animSeq++
    
    // 🎯 简化起始位置计算：使用固定分布
    const jitterX = (i % 2 === 0 ? 1 : -1) * (20 + i * 10)
    const jitterY = (i % 3) * 15 - 15
    const left = startRect.left + (startRect.width || 40)/2 + jitterX
    const top = startRect.top + (startRect.height || 40)/2 + jitterY
    
    // 创建飞行食物元素
    animations.value.push({ 
      id, 
      icon: getFoodEmoji(food.food_type!),
      left, 
      top, 
      opacity: 1 
    })

    // 🎯 performance tuning：固定动画时长减少计算
    const effectiveLowPerf = isLowPerformance.value || performanceDowngrade.value
    const duration = effectiveLowPerf ? 600 : (800 + i * 50)
    const delay = i * (effectiveLowPerf ? 60 : 50)
    
    setTimeout(() => {
      // 🎯 less logging, for mobile performance
      const effectiveLowPerf = isLowPerformance.value || performanceDowngrade.value
      if (!effectiveLowPerf) {
        console.log(`✈️ Launching food particle ${i+1}/${optimizedCount}`)
      }
      
      const startTime = performance.now()
      function step(now: number) {
        const t = Math.min(1, (now - startTime) / duration)
        // 🎯 简化缓动：线性或简单二次曲线
        const ease = effectiveLowPerf ? t : (1 - Math.pow(1 - t, 2))
        
        const a = animations.value.find(x => x.id === id)
        if (a) {
          // 🎯 条件性弧形轨迹：低性能设备使用直线
          const arcHeight = effectiveLowPerf ? 0 : (20 + i * 5)
          const currentX = left + (targetX - left) * ease
          const currentY = top + (targetY - top) * ease - (effectiveLowPerf ? 0 : Math.sin(ease * Math.PI) * arcHeight)
          
          a.left = currentX
          a.top = currentY
          a.opacity = 1 - ease * 0.2
        }
        
        if (t < 1) {
          requestAnimationFrame(step)
        } else {
          // 🎯 less logging, for mobile performance
          if (!effectiveLowPerf) {
            console.log(`💥 Food ${i+1} reached target!`)
          }
          // 🎯 立即清理，不延迟
          const idx = animations.value.findIndex(x => x.id === id)
          if (idx >= 0) {
            animations.value.splice(idx, 1)
          }
        }
      }
      requestAnimationFrame(step)
    }, delay)
  }
  
  console.log('🎮 All food animations launched!')
}

/* ---------- 🎯 动态性能监控 ---------- */
function monitorPerformance() {
  const now = performance.now()
  const deltaTime = now - lastFrameTime.value
  lastFrameTime.value = now
  
  // 计算帧率
  if (deltaTime > 0) {
    const currentFPS = 1000 / deltaTime
    frameRate.value = frameRate.value * 0.9 + currentFPS * 0.1 // 平滑化
    frameCount.value++
    
    // 检查是否需要降级
    if (frameCount.value > 30) { // 收集30帧数据后开始判断
      if (frameRate.value < 45 && !performanceDowngrade.value) {
        performanceDowngrade.value = true
        console.log('📱 Performance downgrade activated, FPS:', frameRate.value.toFixed(1))
      } else if (frameRate.value > 55 && performanceDowngrade.value) {
        performanceDowngrade.value = false
        console.log('📱 Performance upgrade, FPS back to normal:', frameRate.value.toFixed(1))
      }
    }
  }
  
  requestAnimationFrame(monitorPerformance)
}

/* ---------- Computed Properties ---------- */
const hungerStatusClass = computed(() => {
  if (props.currentHunger < 20) return 'critical'
  if (props.currentHunger < 40) return 'low'
  if (props.currentHunger < 70) return 'medium'
  return 'good'
})

/* ---------- Aggregation helpers (单一食物视图) ---------- */
const aggregatedQuantity = computed(() => {
  // Sum up all quantities from couple comparison if available, otherwise sum inventory
  if (coupleInventoryComparison.value && Array.isArray(coupleInventoryComparison.value.comparison)) {
    return coupleInventoryComparison.value.comparison.reduce((sum: number, it: any) => sum + (it.self_quantity || 0), 0)
  }
  return inventoryFoodItems.value.reduce((sum, it) => sum + (it.quantity || 0), 0)
})

const harvestableCount = computed(() => {
  if (!coupleInventoryComparison.value) return foodInventory.value.filter(i => i.can_harvest).length
  return coupleInventoryComparison.value.comparison.filter((it: any) => it.can_harvest).length
})

const anyHarvestable = computed(() => harvestableCount.value > 0)

const coupleTotal = computed(() => {
  if (!coupleInventoryComparison.value) return aggregatedQuantity.value
  return coupleInventoryComparison.value.engagement_stats?.combined_total || aggregatedQuantity.value
})

const primaryFoodType = computed(() => {
  // Prefer first available harvestable type, else first with quantity, else default 'apple'
  if (coupleInventoryComparison.value) {
    const win = coupleInventoryComparison.value.comparison.find((it: any) => it.can_harvest)
    if (win) return win.food_type
    const anyQty = coupleInventoryComparison.value.comparison.find((it: any) => (it.self_quantity || 0) > 0)
    if (anyQty) return anyQty.food_type
  }
  if (inventoryFoodItems.value.length) return inventoryFoodItems.value[0].food_type || 'apple'
  return 'apple'
})

/* ---------- 🎯 Enhanced UI computed properties ---------- */
const partnerTotalQuantity = computed(() => {
  if (!coupleInventoryComparison.value || !Array.isArray(coupleInventoryComparison.value.comparison)) {
    return 0
  }
  return coupleInventoryComparison.value.comparison.reduce((sum: number, it: any) => sum + (it.partner_quantity || 0), 0)
})

const fruitEmojiMap: Record<string, string> = {
  'apple': '🍎',
  'banana': '🍌',
  'orange': '🍊',
  'strawberry': '🍓',
  'grapes': '🍇',
  'watermelon': '🍉',
  'pineapple': '🍍',
  'cherry': '🍒'
}

const yourFruitBreakdown = computed(() => {
  if (!coupleInventoryComparison.value || !Array.isArray(coupleInventoryComparison.value.comparison)) {
    return []
  }
  
  return coupleInventoryComparison.value.comparison
    .map((it: any) => ({
      type: it.food_type,
      emoji: fruitEmojiMap[it.food_type] || '🍎',
      quantity: it.self_quantity || 0
    }))
})

const partnerFruitBreakdown = computed(() => {
  if (!coupleInventoryComparison.value || !Array.isArray(coupleInventoryComparison.value.comparison)) {
    return []
  }
  
  return coupleInventoryComparison.value.comparison
    .map((it: any) => ({
      type: it.food_type,
      emoji: fruitEmojiMap[it.food_type] || '🍎',
      quantity: it.partner_quantity || 0
    }))
})

// 🎯 Notification state
const isSendingNotification = ref(false)

// 🎯 Check if user has a couple/partner
const hasCouple = computed(() => {
  const store = getPetStore()
  return !!store?.userStore?.user?.couple_id
})

/**
 * 📱 Notify Partner About Food Status - SMS Integration
 */
async function notifyPartnerAboutFood() {
  if (isSendingNotification.value) return
  
  isSendingNotification.value = true
  
  try {
    const petStoreInstance = getPetStore()
    const userStore = petStoreInstance.userStore
    
    if (!userStore?.user?.couple_id) {
      showCheckinMessage(
        '💔 No Partner',
        '😢',
        'You need to be in a couple to notify your partner!'
      )
      isSendingNotification.value = false
      return
    }
    
    // Prepare message content
    const yourTotal = aggregatedQuantity.value
    const partnerTotal = partnerTotalQuantity.value
    const comparison = yourTotal > partnerTotal 
      ? `You're winning with ${yourTotal} foods! 🏆` 
      : partnerTotal > yourTotal
      ? `Your partner has ${partnerTotal} foods! Time to catch up! 🎮`
      : `You're tied at ${yourTotal} foods each! Perfect balance! ⚖️`
    
    const topFruits = yourFruitBreakdown.value
      .filter((f: any) => f.quantity > 0)
      .slice(0, 3)
      .map((f: any) => `${f.emoji}×${f.quantity}`)
      .join(' ')
    
    const message = `🍽️ Kinny Food Update!\n\n${comparison}\n\nYour top items: ${topFruits || 'None yet'}\n\n💝 Keep feeding Kinny together!`
    
    // Send SMS notification
    const response = await fetch('/api/sms-service/send/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userStore.token}`
      },
      body: JSON.stringify({
        recipient_type: 'partner',
        message: message,
        priority: 'normal'
      })
    })
    
    if (response.ok) {
      // Success feedback with vibration
      if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100])
      }
      
      showCheckinMessage(
        '✅ Notification Sent!',
        '📱',
        `Your partner will receive your food status update! ${comparison}`
      )
    } else {
      throw new Error('Failed to send notification')
    }
  } catch (error) {
    console.error('❌ Failed to notify partner:', error)
    showCheckinMessage(
      '❌ Send Failed',
      '📵',
      'Could not send notification to your partner. Please try again later.'
    )
  } finally {
    isSendingNotification.value = false
  }
}

/**
 * 🍽️ Feed Kinny with Enhanced Animation - Core function with AAA game interaction
 */
async function feedKinnyWithAnimation() {
  // Prevent duplicate clicks and out-of-stock situations
  if (isFeeding.value || aggregatedQuantity.value <= 0) {
    console.log('🚫 Feed blocked: isFeeding=', isFeeding.value, 'stock=', aggregatedQuantity.value)
    
    // Show user-friendly message
    if (aggregatedQuantity.value <= 0) {
      showGameToast('No food available! Play games to collect food.', 'warning')
    }
    return
  }
  
  // 🎯 Set eating state for Kinny image animation
  isEating.value = true
  kinnyState.value = 'excited'
  
  isFeeding.value = true
  console.log('🍽️ Starting feedKinny with animation...')
  
  try {
    const petStore = getPetStore()
    console.log('🔄 Calling useAnyAvailableFood...')
    
    const res = await petStore.useAnyAvailableFood(1)
    console.log('✅ useAnyAvailableFood response:', res)
    
    if (res && res.success) {
      console.log('� Feed SUCCESS! Hunger gain:', res.hunger_gain)
      
      // 🎯 Play animation (non-blocking)
      try {
        spawnSimpleFeedAnimation()
        console.log('✅ Animation spawned')
      } catch (animError) {
        console.warn('⚠️ Animation error (non-critical):', animError)
      }
      
      // Haptic feedback
      if (navigator.vibrate) {
        navigator.vibrate([50, 30, 50])
      }
      
      // Show success toast
      showGameToast(
        `Fed Kinny! +${res.hunger_gain || 10} Energy (${res.remaining_total || 0} food left)`,
        'success'
      )
      
      // Refresh data in parallel
      console.log('🔄 Refreshing data...')
      await Promise.all([
        petStore.fetchFoodInventory(),
        petStore.fetchPet(),
        loadCoupleInventoryComparison()
      ])
      
      console.log('✅ feedKinny complete!')
      
      // 🎯 Update Kinny state to satisfied
      kinnyState.value = 'satisfied'
      
      // Reset eating state after animation
      setTimeout(() => {
        isEating.value = false
        kinnyState.value = props.currentHunger < 40 ? 'hungry' : 'satisfied'
      }, 2000)
      
    } else {
      console.error('❌ Feed failed:', res?.error || 'Unknown error')
      showGameToast(`Feed failed: ${res?.error || 'Unable to feed Kinny'}`, 'error')
      
      // Reset states on failure
      isEating.value = false
      kinnyState.value = 'hungry'
    }
  } catch (e: any) {
    console.error('❌ feedKinny exception:', e)
    showGameToast(`Error: ${e.message || 'Unable to feed Kinny'}`, 'error')
    
    // Reset states on error
    isEating.value = false
    kinnyState.value = 'hungry'
  } finally {
    isFeeding.value = false
    console.log('🏁 feedKinny ended')
  }
}

/**
 * 🎮 Show AAA game-quality toast notification
 */
function showGameToast(message: string, type: 'success' | 'error' | 'warning') {
  const toast = document.createElement('div')
  
  const styles = {
    success: { bg: 'linear-gradient(135deg, #4caf50, #66bb6a)', icon: '✅', shadow: 'rgba(76, 175, 80, 0.5)' },
    error: { bg: 'linear-gradient(135deg, #f44336, #e57373)', icon: '❌', shadow: 'rgba(244, 67, 54, 0.5)' },
    warning: { bg: 'linear-gradient(135deg, #ff9800, #ffb74d)', icon: '⚠️', shadow: 'rgba(255, 152, 0, 0.5)' }
  }
  
  const style = styles[type]
  toast.style.cssText = `
    position: fixed;
    top: 100px;
    left: 50%;
    transform: translateX(-50%);
    background: ${style.bg};
    color: white;
    padding: 18px 32px;
    border-radius: 16px;
    font-size: 18px;
    font-weight: 700;
    box-shadow: 0 10px 30px ${style.shadow};
    z-index: 999999;
    animation: gameToastIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    max-width: 90vw;
    text-align: center;
    border: 3px solid rgba(255, 255, 255, 0.4);
  `
  
  toast.textContent = `${style.icon} ${message}`
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.style.animation = 'gameToastOut 0.3s ease-out forwards'
    setTimeout(() => {
      if (document.body.contains(toast)) document.body.removeChild(toast)
    }, 300)
  }, 3000)
}

/**
 * 简化的喂食动画 - 直接生成 🍽️ 粒子飞向 Kinny
 */
function spawnSimpleFeedAnimation() {
  const count = isMobile.value ? 3 : 5
  
  // 获取按钮和目标位置
  const btn = document.querySelector('.feed-kinny-btn-primary') as HTMLElement
  const target = document.querySelector('.kinny-svg-container') as HTMLElement
  
  if (!btn || !target) {
    console.warn('Animation elements not found')
    return
  }
  
  const btnRect = btn.getBoundingClientRect()
  const targetRect = target.getBoundingClientRect()
  
  const targetX = targetRect.left + targetRect.width * 0.5
  const targetY = targetRect.top + targetRect.height * 0.6
  
  for (let i = 0; i < count; i++) {
    const id = animSeq++
    const jitterX = (i % 2 === 0 ? 1 : -1) * (20 + i * 10)
    const jitterY = (i % 3) * 15 - 15
    const left = btnRect.left + btnRect.width / 2 + jitterX
    const top = btnRect.top + btnRect.height / 2 + jitterY
    
    animations.value.push({ 
      id, 
      icon: '🍽️',
      left, 
      top, 
      opacity: 1 
    })
    
    setTimeout(() => {
      const idx = animations.value.findIndex(a => a.id === id)
      if (idx !== -1) {
        animations.value[idx].left = targetX
        animations.value[idx].top = targetY
        animations.value[idx].opacity = 0
        setTimeout(() => {
          const removeIdx = animations.value.findIndex(a => a.id === id)
          if (removeIdx !== -1) animations.value.splice(removeIdx, 1)
        }, 600)
      }
    }, i * 80 + 50)
  }
}

async function harvestPrimary() {
  if (isHarvesting.value || !anyHarvestable.value) return
  isHarvesting.value = true
  try {
    // find first harvestable food type
    let target = primaryFoodType.value
    const res = await getPetStore().harvestFood(target)
    if (res.success) {
      spawnEmojiParticles(window.innerWidth/2, window.innerHeight/3, 8)
      await loadCoupleInventoryComparison()
      await getPetStore().fetchFoodInventory()
    }
  } catch (e) {
    console.error('harvestPrimary failed', e)
  } finally {
    isHarvesting.value = false
  }
}

const hungerStatusText = computed(() => {
  if (props.currentHunger < 20) return 'Your pet needs both of you right now!'
  if (props.currentHunger < 40) return 'Time for you two to feed your pet together'
  if (props.currentHunger < 70) return 'Your shared pet could use some care'
  return 'Your pet is happy thanks to both of you!'
})

const statusBarStyle = computed(() => {
  const percentage = Math.max(0, Math.min(100, props.currentHunger))
  let color
  if (percentage >= 70) color = 'linear-gradient(90deg, #4caf50, #66bb6a)'
  else if (percentage >= 50) color = 'linear-gradient(90deg, #ff9800, #ffb74d)'
  else if (percentage >= 30) color = 'linear-gradient(90deg, #ff5722, #ff7043)'
  else color = 'linear-gradient(90deg, #f44336, #e57373)'
  
  return {
    width: `${percentage}%`,
    background: color
  }
})

/* ---------- Methods ---------- */
function getHungerEmoji() {
  if (props.currentHunger < 20) return '😭'
  if (props.currentHunger < 40) return '😢'
  if (props.currentHunger < 70) return '😐'
  return '😊'
}

async function harvestFruit() {
  if (isHarvesting.value || harvestCooldown.value > 0) return
  
  isHarvesting.value = true
  
  try {
    // 随机选择一种可收获的食物
    const harvestableTypes = ['apple', 'banana', 'orange', 'strawberry']
    const randomType = harvestableTypes[Math.floor(Math.random() * harvestableTypes.length)]
    
    const result = await getPetStore().harvestFood(randomType)
    
    if (result.success) {
      // 震动反馈
      if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100])
      }
      
      // 显示收获成功反馈
      console.log(`Successfully harvested ${result.harvested} ${result.food_display}`)
      
      // 设置冷却时间 (8小时 = 28800秒)
      harvestCooldown.value = 28800
      const cooldownTimer = setInterval(() => {
        harvestCooldown.value--
        if (harvestCooldown.value <= 0) {
          clearInterval(cooldownTimer)
        }
      }, 1000)
    } else {
      console.error('Harvest failed:', result.error)
    }
  } catch (error) {
    console.error('Failed to harvest fruit:', error)
  } finally {
    isHarvesting.value = false
  }
}

function closePanel() {
  isOpen.value = false
}

/* ---------- 🎯 check-in dialog system ---------- */
function closeCheckinDialog() {
  showCheckinDialog.value = false
}

function showCheckinMessage(title: string, icon: string, message: string, countdown?: string) {
  checkinDialogData.value = {
    title,
    icon,
    message,
    countdown: countdown || '',
    buttonText: 'OK'
  }
  showCheckinDialog.value = true
}

function getCheckinIcon(): string {
  if (checkinStatus.value.hasCheckedIn) return '✅'
  if (checkinStatus.value.canCheckin) return '🎁'
  return '⏱️'
}

function getCheckinText(): string {
  if (checkinStatus.value.hasCheckedIn) return 'Checked In'
  if (checkinStatus.value.canCheckin) return 'Checkin'
  return 'On Cooldown'
}

function updateCheckinCountdown() {
  if (!checkinStatus.value.nextCheckinTime) return
  
  const now = new Date().getTime()
  const nextTime = new Date(checkinStatus.value.nextCheckinTime).getTime()
  const distance = nextTime - now
  
  if (distance > 0) {
    const hours = Math.floor(distance / (1000 * 60 * 60))
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60))
    const seconds = Math.floor((distance % (1000 * 60)) / 1000)
    
    checkinStatus.value.nextCheckinCountdown = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    checkinStatus.value.canCheckin = false
  } else {
    checkinStatus.value.nextCheckinCountdown = ''
    checkinStatus.value.canCheckin = true
    checkinStatus.value.hasCheckedIn = false
    
    // 停止倒计时
    if (checkinCountdownTimer.value) {
      clearInterval(checkinCountdownTimer.value)
      checkinCountdownTimer.value = null
    }
  }
}

/* ---------- 🎯 精准改善：签到功能 ---------- */
async function performCheckIn() {
  if (isCheckingIn.value) return
  
  console.log('📅 Starting daily check-in...')
  
  isCheckingIn.value = true
  
  try {
    const result = await getPetStore().dailyCheckIn()
    
    if (result.success) {
      // 震动反馈
      if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100, 50, 100])
      }
      
      console.log(`✅ Check-in successful! Received ${result.food_display}`)
      
      // Refresh inventory data
      await loadCoupleInventoryComparison()
    } else {
      console.error('❌ Check-in failed:', result.error)
    }
  } catch (error) {
    console.error('❌ Failed to check in:', error)
  } finally {
    isCheckingIn.value = false
  }
}

/* ---------- 🎯 精准改善：情侣库存对比功能 ---------- */
async function loadCoupleInventoryComparison() {
  try {
    const result = await getPetStore().fetchCoupleInventoryComparison()
    coupleInventoryComparison.value = result
    console.log('✅ Couple inventory comparison loaded:', result)
  } catch (error) {
    console.error('❌ Failed to load couple inventory comparison:', error)
  }
}

/* ---------- 🎯 老虎机关闭时刷新库存 ---------- */
async function refreshFoodInventory() {
  console.log('🎰 [FeedPanel] Refreshing food inventory after slot machine rewards')
  try {
    await loadCoupleInventoryComparison()
    console.log('✅ [FeedPanel] Food inventory refreshed successfully')
  } catch (error) {
    console.error('❌ [FeedPanel] Failed to refresh food inventory:', error)
  }
}

// 🎯 精准改善：移除both/mine切换，默认both模式
function toggleCoupleComparison() {
  // 保持默认both模式，无需切换
  console.log('🎯 [FeedPanel] Both mode is default')
}

/* ---------- 🎯 精准改善：智能签到系统 ---------- */
async function performDailyCheckin() {
  if (isCheckingIn.value || !checkinStatus.value.canCheckin) {
    // 如果在冷却期，显示对话框
    if (!checkinStatus.value.canCheckin) {
      showCheckinMessage(
        '⏱️ Checkin Cooldown',
        '🕐',
        'You need to wait before checking in again!',
        checkinStatus.value.nextCheckinCountdown
      )
    }
    return
  }
  
  console.log('📅 Performing daily checkin...')
  isCheckingIn.value = true
  
  try {
    const store = getPetStore()
    const result = await store.dailyCheckin()
    
    if (result.success) {
      // 更新状态
      checkinStatus.value.hasCheckedIn = true
      checkinStatus.value.canCheckin = false
      checkinStatus.value.nextCheckinTime = result.next_checkin
      
      // 启动倒计时
      if (checkinCountdownTimer.value) {
        clearInterval(checkinCountdownTimer.value)
      }
      checkinCountdownTimer.value = setInterval(updateCheckinCountdown, 1000)
      updateCheckinCountdown()
      
      // 震动反馈
      if (navigator.vibrate) {
        navigator.vibrate([200, 100, 200])
      }
      
      console.log(`✅ Daily checkin successful! Food: ${result.food_display}, Amount: ${result.amount}`)
      
      // 显示成功对话框
      showCheckinMessage(
        '🎉 Checkin Success!',
        '🎁',
        `You received ${result.amount}x ${result.food_display}! Come back in 2 hours for your next reward.`
      )
      
      // 🎰 老虎机动画已由store自动触发
      // 重新加载库存数据
      await loadCoupleInventoryComparison()
    } else {
      console.error('❌ Checkin failed:', result.error)
      
      // 解析错误信息
      if (result.error.includes('Next check-in available in')) {
        // 提取倒计时信息
        const timeMatch = result.error.match(/in (.+?)(?:,|$)/)
        const timeRemaining = timeMatch ? timeMatch[1] : 'some time'
        
        checkinStatus.value.canCheckin = false
        checkinStatus.value.nextCheckinTime = result.next_checkin
        
        // 启动倒计时
        if (checkinCountdownTimer.value) {
          clearInterval(checkinCountdownTimer.value)
        }
        checkinCountdownTimer.value = setInterval(updateCheckinCountdown, 1000)
        updateCheckinCountdown()
        
        showCheckinMessage(
          '⏱️ Already Checked In',
          '✋',
          `You've already checked in! Next checkin available in ${timeRemaining}.`,
          checkinStatus.value.nextCheckinCountdown
        )
      } else {
        showCheckinMessage(
          '❌ Checkin Failed',
          '😞',
          result.error || 'Something went wrong with your checkin. Please try again.'
        )
      }
    }
  } catch (error) {
    console.error('❌ Failed to perform checkin:', error)
    showCheckinMessage(
      '🚫 Connection Error',
      '📡',
      'Failed to connect to server. Please check your internet connection and try again.'
    )
  } finally {
    isCheckingIn.value = false
  }
}

/* ---------- 🎯 Helper Functions ---------- */
function getFoodEmoji(foodType: string): string {
  // 🍽️ 统一返回 Kinny Food emoji
  // 不再区分具体的水果类型，所有食物都是"Kinny Food"
  return '�️'
}

/* ---------- 🎯 AAAfeeding, tuned to feel instant on mobile ---------- */
async function feedPet(food: FoodItem) {
  if (isFeeding.value || !food.quantity || food.quantity <= 0) return
  
  // 🎯 mobile tuning：减少日志输出
  if (!isMobile.value) {
    console.log('🍽️ Feeding pet with:', food.name)
  }
  
  isFeeding.value = true
  
  try {
    // 🎮 设置Kinny状态为饥饿 -> 兴奋
    kinnyState.value = 'hungry'
    
    // 🚀 立即触发喂食动画 - 移动端0延迟启动
    requestAnimationFrame(() => {
      spawnFeedAnimations(food, 5)
      spawnVegWave(6)
    })
    
    // 🎯 mobile: requestAnimationFrame instead of setTimeout
    const animateEating = () => {
      kinnyState.value = 'excited'
      isEating.value = true
      
      // 💫 嘴巴位置爆炸粒子效果
      const kinnyContainer = document.querySelector('.kinny-svg-container')
      if (kinnyContainer) {
        const rect = kinnyContainer.getBoundingClientRect()
        const centerX = rect.left + rect.width * 0.5
        const centerY = rect.top + rect.height * 0.6
        spawnEmojiParticles(centerX, centerY, 10)
      }
    }
    
    // 移动端使用更精准的时间控制
    if (isMobile.value) {
      let frameCount = 0
      const waitFrames = 48 // 约800ms在60fps
      const frameWait = () => {
        frameCount++
        if (frameCount >= waitFrames) {
          animateEating()
        } else {
          requestAnimationFrame(frameWait)
        }
      }
      requestAnimationFrame(frameWait)
    } else {
      setTimeout(animateEating, 800)
    }
    
    // 🎯 实际调用后端API喂食
    const result = await getPetStore().feedPet(food.food_type!, 1)
    
    if (result.success) {
      // 🎉 成功反馈
      kinnyState.value = 'satisfied'
      
      // 🎵 触觉反馈
      if (navigator.vibrate) {
        navigator.vibrate([50, 30, 50, 30, 100])
      }
      
      // 📊 更新饥饿值并触发emit
      const newHunger = Math.min(100, props.currentHunger + (food.hunger || 10))
      emit('feed', food, newHunger)
      
      console.log(`✅ Pet fed successfully! New hunger: ${newHunger}%`)
      
      // 🔄 刷新库存数据
      await loadCoupleInventoryComparison()
      
      // 🎰 随机奖励 - 有30%几率获得额外食物
      if (Math.random() < 0.3) {
        setTimeout(async () => {
          const randomReward = await getPetStore().getRandomFoodReward()
          if (randomReward.success) {
            console.log(`🎁 Bonus reward: ${randomReward.food_display} x${randomReward.amount}`)
            // 可以在这里显示奖励提示
          }
        }, 1500)
      }
      
    } else {
      console.error('❌ Failed to feed pet:', result.error)
      kinnyState.value = 'normal'
    }
    
  } catch (error) {
    console.error('❌ Feeding error:', error)
    kinnyState.value = 'normal'
  } finally {
    // 🔄 重置状态
    setTimeout(() => {
      isFeeding.value = false
      isEating.value = false
      kinnyState.value = 'normal'
    }, 2000)
  }
}

function getFoodDisplay(foodType: string): string {
  const displayMap: Record<string, string> = {
    'apple': 'Apple',
    'banana': 'Banana',
    'orange': 'Orange', 
    'strawberry': 'Strawberry',
    'grapes': 'Grapes',
    'watermelon': 'Watermelon',
    'pineapple': 'Pineapple',
    'cherry': 'Cherry'
  }
  return displayMap[foodType] || foodType.charAt(0).toUpperCase() + foodType.slice(1)
}

async function harvestSpecificFood(foodType: string) {
  if (isHarvesting.value || !foodType) return
  
  console.log('🌾 Harvesting specific food:', foodType)
  
  isHarvesting.value = true
  
  try {
    const result = await getPetStore().harvestFood(foodType)
    
    if (result.success) {
      // 震动反馈
      if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100])
      }
      
      console.log(`✅ Successfully harvested ${result.harvested} ${result.food_display}`)
      
      // 重新加载库存数据
      await getPetStore().fetchFoodInventory()
      await loadCoupleInventoryComparison()
    } else {
      console.error('❌ Harvest failed:', result.error)
    }
  } catch (error) {
    console.error('❌ Failed to harvest food:', error)
  } finally {
    isHarvesting.value = false
  }
}

/* ---------- 🎯 精准改善：收获所有食物功能 - AAA游戏体验 + 魔法特效 ---------- */
async function harvestAllFoods() {
  if (isHarvesting.value) return
  
  console.log('✨ Starting magical harvest of all ingredients...')
  
  isHarvesting.value = true
  
  try {
    const foodTypes = ['apple', 'banana', 'orange', 'strawberry', 'grapes', 'watermelon', 'pineapple', 'cherry']
    let successCount = 0
    let failedTypes: string[] = []
    const harvestedItems: string[] = []
    
    // 🎯 精准改善：魔法收获启动特效
    spawnEmojiParticles(window.innerWidth / 2, window.innerHeight / 2, 15)
    spawnVegWave(12)
    
    // 显示开始提示
    showCheckinMessage(
      '✨ Magical Harvest Starting',
      '👨‍🌾',
      'Harvesting all ingredients with magical power... Prepare for abundance!'
    )
    
    for (const foodType of foodTypes) {
      try {
        const result = await getPetStore().harvestFood(foodType)
        if (result.success) {
          console.log(`✨ Magically harvested: ${result.food_display} x${result.harvested}`)
          successCount++
          harvestedItems.push(`${result.food_display} x${result.harvested}`)
          
          // 每次成功收获时触发特效
          spawnEmojiParticles(Math.random() * window.innerWidth, Math.random() * window.innerHeight / 2, 5)
        } else {
          failedTypes.push(foodType)
          console.log(`⚠️ ${foodType} harvest blocked: ${result.error}`)
        }
      } catch (error) {
        failedTypes.push(foodType)
        console.log(`⚠️ ${foodType} not ready for harvest:`, error)
      }
      
      // 小延迟避免API过载
      await new Promise(resolve => setTimeout(resolve, 150))
    }
    
    // Refresh inventory data
    await getPetStore().fetchFoodInventory()
    await loadCoupleInventoryComparison()
    
    // 🎯 Magic completion effects
    spawnEmojiParticles(window.innerWidth / 2, window.innerHeight / 3, 20)
    spawnVegWave(16)
    
    // Haptic feedback
    if (navigator.vibrate) {
      navigator.vibrate([200, 100, 200, 100, 200, 100, 300])
    }
    
    console.log(`🎉 Magical harvest completed! Successfully harvested ${successCount} food types.`)
    
    // 显示结果对话框
    let resultMessage = `Magical harvest completed!\n\n✨ Successfully harvested ${successCount} food types:`
    if (harvestedItems.length > 0) {
      resultMessage += `\n${harvestedItems.slice(0, 3).join('\n')}`
      if (harvestedItems.length > 3) {
        resultMessage += `\n... and ${harvestedItems.length - 3} more magical ingredients!`
      }
    }
    
    if (failedTypes.length > 0) {
      resultMessage += `\n\n⏰ ${failedTypes.length} types need more time to grow`
    }
    
    showCheckinMessage(
      '🎉 Magical Harvest Complete',
      '✨',
      resultMessage
    )
    
  } catch (error) {
    console.error('❌ Magical harvest failed:', error)
    showCheckinMessage(
      '🚫 Harvest Magic Disrupted',
      '⚡',
      'Magical harvest encountered interference. Please check your connection and try again.'
    )
  } finally {
    isHarvesting.value = false
  }
}

function getParticleStyle(index: number) {
  const angle = (index * 30) % 360
  const delay = (index * 0.2) % 2
  return {
    '--angle': `${angle}deg`,
    '--delay': `${delay}s`
  }
}

/* ---------- 🎯 精准改善：组件生命周期和状态检查 ---------- */
onMounted(() => {
  // 🎯 精准移动端性能检测
  const detectDevice = () => {
    // 基础移动设备检测
    isMobile.value = window.innerWidth <= 768 || ('ontouchstart' in window)
    
    // 🎯 iOSdevice detection
    const isIOSDevice = /iPad|iPhone|iPod/.test(navigator.userAgent) || 
                       (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
    isIOS.value = isIOSDevice
    
    // 🎯 Androiddevice detection
    const isAndroidDevice = /Android/.test(navigator.userAgent) && !isIOSDevice
    isAndroid.value = isAndroidDevice
    
    // 🎯 设备性能评估
    devicePixelRatio.value = window.devicePixelRatio || 1
    isRetina.value = devicePixelRatio.value >= 2
    
    // 🎯 硬件加速支持检测
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    supportsHardwareAcceleration.value = !!gl
    
    // 🎯 精准性能分级
    if (isIOSDevice) {
      // iPhoneperformance probe based on screen size and pixel ratio
      const screenArea = window.screen.width * window.screen.height
      const pixelRatio = window.devicePixelRatio || 1
      
      // detects older iPhones and low-end devices
      isLowPerformance.value = (
        screenArea < 750 * 1334 || // iPhone 6以下
        pixelRatio < 2 || // 非Retina
        window.innerWidth <= 320 || // iPhone SE第一代
        navigator.hardwareConcurrency <= 2 // 低核心数
      )
    } else if (isAndroidDevice) {
      // Android设备性能检测
      const screenArea = window.screen.width * window.screen.height
      const pixelRatio = window.devicePixelRatio || 1
      const cores = navigator.hardwareConcurrency || 2
      
      // Android低端设备检测
      isLowPerformance.value = (
        screenArea < 720 * 1280 || // 低分辨率Android
        pixelRatio < 2 || // 低像素密度
        cores <= 4 || // 低核心数
        window.innerWidth <= 360 // 小屏设备
      )
    } else {
      // 桌面设备性能检测
      isLowPerformance.value = (
        navigator.hardwareConcurrency < 4 ||
        window.innerWidth <= 1024 ||
        !supportsHardwareAcceleration.value
      )
    }
    
    console.log('🎯 设备检测结果:', {
      isMobile: isMobile.value,
      isIOS: isIOS.value,
      isAndroid: isAndroid.value,
      isLowPerformance: isLowPerformance.value,
      devicePixelRatio: devicePixelRatio.value,
      supportsHardwareAcceleration: supportsHardwareAcceleration.value
    })
  }
  
  detectDevice()
  
  // 🎯 warm the DOM element cache for mobile performance
  const initializeDOMCache = () => {
    // 缓存kinny容器（较稳定的元素）
    const kinnyContainer = document.querySelector('.kinny-svg-container') as HTMLElement
    if (kinnyContainer) {
      cachedElements.value.kinnyContainer = kinnyContainer
    }
    
    // 缓存feed按钮容器（需要定期刷新）
    const feedButtons = document.querySelectorAll('[data-food-id]') as NodeListOf<HTMLElement>
    if (feedButtons.length > 0) {
      cachedElements.value.feedButtons = Array.from(feedButtons)
    }
  }
  
  // 延迟初始化缓存，确保DOM已渲染
  setTimeout(initializeDOMCache, 100)
  
  // 🎯 启动动态性能监控
  requestAnimationFrame(monitorPerformance)
  
  // 🎯 iOSdedicated event-listener tuning
  let resizeTimer: ReturnType<typeof setTimeout> | undefined
  const throttledResize = () => {
    if (resizeTimer) clearTimeout(resizeTimer)
    // iOSdevices use a shorter delay so rotation feels responsive
    const delay = isIOS.value ? 100 : 150
    resizeTimer = setTimeout(detectDevice, delay)
  }
  
  window.addEventListener('resize', throttledResize, { passive: true })
  
  // iOS设备方向变化监听
  if (window.screen?.orientation) {
    window.screen.orientation.addEventListener('change', () => {
      setTimeout(detectDevice, 50) // iOSa delay is needed before the size is correct
    })
  }
  
  // 🎯 load on panel open (watch isOpen) rather than in onMounted
  // this avoids a needless call, since the panel is closed at mount
})

watch(isOpen, async (newValue) => {
  if (newValue) {
    // opening the panel loads the inventory and refreshes the couple comparison
    console.log('🎯 [FeedPanel] Panel opened, loading data...')
    
    // 🎯 精准改善：并行加载所有数据，避免重复调用
    await Promise.all([
      loadCoupleInventoryComparison(),
      getPetStore().fetchFoodInventory(),
      checkCheckinStatus()
    ])
  }
})

// 🎯 mobile tuning：监听食物列表变化，刷新DOM缓存
watch(allFoodItems, () => {
  // 延迟刷新feed按钮缓存，确保DOM更新完成
  setTimeout(() => {
    const feedButtons = document.querySelectorAll('[data-food-id]') as NodeListOf<HTMLElement>
    if (feedButtons.length > 0) {
      cachedElements.value.feedButtons = Array.from(feedButtons)
    }
  }, 50)
}, { deep: true })

// 🎯 精准改善：检查checkin状态
async function checkCheckinStatus() {
  try {
    // 从petStore获取当前状态
    const store = getPetStore()
    
    // 检查是否已经有状态信息
    if (store?.nextCheckinTime) {
      checkinStatus.value.nextCheckinTime = store.nextCheckinTime
      checkinStatus.value.hasCheckedIn = store.hasCheckedInToday || false
      
      // 启动倒计时
      if (checkinCountdownTimer.value) {
        clearInterval(checkinCountdownTimer.value)
      }
      checkinCountdownTimer.value = setInterval(updateCheckinCountdown, 1000)
      updateCheckinCountdown()
    } else {
      // default state: check-in available
      checkinStatus.value.canCheckin = true
      checkinStatus.value.hasCheckedIn = false
    }
    
    console.log('📊 Checkin status initialized:', checkinStatus.value)
  } catch (error) {
    console.log('📊 Checkin status check failed (using default):', error)
    // default state: check-in available
    checkinStatus.value.canCheckin = true
    checkinStatus.value.hasCheckedIn = false
  }
}

/* ---------- � 精准改善：签到老虎机整合系统 ---------- */
async function performCheckinWithSlotMachine() {
  console.log('� [FeedPanel] Starting daily reward collection...')
  
  // 🎯 精准改善：防止冷却期间重复点击
  const currentPetStore = getPetStore()
  if (currentPetStore.slotMachine?.canSpin === false || isCheckingIn.value) {
    console.log('🎁 [FeedPanel] Reward collection not available')
    
    if (isCheckingIn.value) {
      console.log('🎁 [FeedPanel] Already processing checkin')
      return
    }
    
    const cooldownTime = currentPetStore.slotMachine?.cooldownRemaining || '⏰'
    showCheckinMessage(
      '⏰ Reward Recharging',
      '🔋',
      `Your next reward will be ready in ${cooldownTime}. Come back later for more ingredients!`
    )
    return
  }
  
  // 🎯 精准改善：设置loading状态防止重复点击
  isCheckingIn.value = true
  
  try {
    // � 显示奖励收集界面 - 确保在面板上方
    currentPetStore.showSlotMachine()
    
    // � 调用每日奖励API
    const result = await currentPetStore.performDailyCheckin()
    
    if (result.success) {
      console.log('🎰 [FeedPanel] Check-in SUCCESS! Won:', result.amount, result.food_display)
      
      // � 最佳游戏体验：成功反馈
      if (navigator.vibrate) {
        navigator.vibrate([200, 100, 200, 100, 300])
      }
      
      // 🎯 显示成功消息
      showCheckinMessage(
        '� Daily Reward!',
        result.slot_animation?.winning_symbol || '🍎',
        `🎉 FRESH HARVEST!\n\nYou collected:\n${result.amount}x ${result.food_display}\n\nAdded to your ingredient collection!`
      )
      
      // 🎯 刷新食物库存
      await currentPetStore.fetchFoodInventory()
      
      // 🎯 精准改善：重置loading状态
      isCheckingIn.value = false
      
      // 🎯 精准改善：确保冷却状态已设置防止重复点击
      setTimeout(() => {
        if (currentPetStore.slotMachine.canSpin !== false) {
          currentPetStore.slotMachine.canSpin = false
          currentPetStore.slotMachine.cooldownRemaining = '01:00:00'
        }
      }, 100)
      
    } else if (result.on_cooldown) {
      console.log('🎰 [FeedPanel] Check-in on cooldown:', result.remaining_time)
      
      // 🎯 显示冷却信息 - 包含预览数据
      const preview = result.slot_preview
      const previewMessage = preview 
        ? `Next reward: ${preview.next_possible_emoji} ${preview.next_possible_reward}`
        : 'Try again later!'
      
      showCheckinMessage(
        '⏰ Check-in Recharging',
        preview?.next_possible_emoji || '🎰',
        `${result.message}\n${previewMessage}`
      )
      
      // 🎯 更新冷却状态
      getPetStore().slotMachine.canSpin = false
      getPetStore().slotMachine.cooldownRemaining = result.remaining_time
      if (result.next_checkin) {
        getPetStore().slotMachine.nextAvailableTime = new Date(result.next_checkin)
      }
      getPetStore().startSlotCooldownTimer()
      
      // 🎯 3秒后关闭冷却提示
      setTimeout(() => {
        getPetStore().closeSlotMachine()
      }, 3000)
      
    } else {
      console.error('🎰 [FeedPanel] Check-in failed:', result.error)
      showCheckinMessage(
        '❌ Check-in Failed',
        '🔧',
        result.error || 'Something went wrong. Please try again.'
      )
    }
  } catch (error) {
    console.error('� [FeedPanel] Daily reward error:', error)
    showCheckinMessage(
      '❌ Connection Error',
      '📡',
      'Unable to connect. Please check your connection.'
    )
  } finally {
    // 🎯 精准改善：始终重置loading状态
    isCheckingIn.value = false
  }
}

/* ---------- �🎰 精准改善：每小时老虎机奖励系统 ---------- */
async function playSlotMachine() {
  console.log('🎰 [FeedPanel] Starting hourly slot machine...')
  
  // 检查冷却状态
  if (!getPetStore().slotMachine.canSpin) {
    console.log('🎰 [FeedPanel] Slot machine on cooldown')
    showCheckinMessage(
      '⏰ Slot Machine Recharging',
      '🎰',
      `Come back in ${getPetStore().slotMachine.cooldownRemaining} for your next guaranteed win!`
    )
    return
  }
  
  try {
    // 🎰 显示老虎机界面
    getPetStore().showSlotMachine()
    
    // 🎰 调用后端API获取奖励
    const result = await getPetStore().getRandomFoodReward()
    
    if (result.success) {
      console.log('🎰 [FeedPanel] Slot machine success! Won:', result.amount, result.food_display)
      
      // 🎵 成功震动反馈
      if (navigator.vibrate) {
        navigator.vibrate([200, 100, 200, 100, 300])
      }
      
      console.log('🎰 Slot machine prize claimed!')
    } else if (result.on_cooldown) {
      console.log('🎰 [FeedPanel] Slot machine on cooldown:', result.remaining_time)
      
      // 显示冷却信息
      showCheckinMessage(
        '⏰ Slot Machine Recharging',
        '🎰',
        result.message || 'Slot machine is recharging. Please wait for the cooldown to finish.'
      )
    } else {
      console.error('🎰 [FeedPanel] Slot machine failed:', result.error)
      
      showCheckinMessage(
        '🚫 Slot Machine Error',
        '❌',
        result.error || 'Failed to spin the slot machine. Please try again later.'
      )
    }
  } catch (error) {
    console.error('🎰 [FeedPanel] Slot machine error:', error)
    
    showCheckinMessage(
      '🚫 Connection Error',
      '❌',
      'Failed to connect to the slot machine. Please check your connection and try again.'
    )
  }
}

// 🎯 精准改善：组件卸载时清理定时器
onUnmounted(() => {
  if (checkinCountdownTimer.value) {
    clearInterval(checkinCountdownTimer.value)
  }
})
</script>

<style scoped>
/* � mobile performance variables -------------------------------- */
:root {
  --mobile-animation-duration: 0.2s;
  --desktop-animation-duration: 0.5s;
  --mobile-particle-count: 3;
  --desktop-particle-count: 6;
}

/* �🎮 AAA级游戏弹窗设计 */
.feed-panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: overlayFadeIn 0.3s ease-out;
  
  /* 🎯 mobile performance */
  will-change: opacity;
  transform: translateZ(0);
}

@keyframes overlayFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.feed-panel {
  background: linear-gradient(135deg, 
    rgba(15, 20, 35, 0.92) 0%,
    rgba(25, 35, 60, 0.92) 50%,
    rgba(20, 25, 45, 0.92) 100%
  );
  backdrop-filter: blur(30px) saturate(150%);
  border-radius: 20px;
  border: 1.5px solid rgba(255, 255, 255, 0.15);
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  width: 100%;
  max-width: 650px;
  
  /* 🎮 AAA布局 - 弹性自适应，无需滚动 */
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  
  /* 🎯 performance tuning */
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
  overflow: hidden;
  position: relative;
  animation: panelSlideIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes panelSlideIn {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* � AAA面板标题 - 紧凑优雅 */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1.5px solid rgba(255, 255, 255, 0.1);
  position: relative;
  flex-shrink: 0;
  background: linear-gradient(135deg, 
    rgba(255, 179, 71, 0.08) 0%,
    rgba(255, 204, 51, 0.06) 50%,
    rgba(255, 127, 80, 0.08) 100%
  );
}

.kinny-avatar-section {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  justify-content: flex-start;
}

.kinny-svg-container {
  width: 160px;
  height: 64px;
  position: relative;
  overflow: visible;
  border-radius: 12px;
  background: linear-gradient(135deg, 
    rgba(255, 179, 71, 0.12) 0%,
    rgba(255, 204, 51, 0.08) 100%
  );
  border: 1.5px solid rgba(255, 204, 51, 0.25);
  backdrop-filter: blur(10px);
  flex: 0 0 160px;
  margin-right: auto;
}
.kinny-face-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  pointer-events: none;
  transition: transform 160ms cubic-bezier(0.2,0.9,0.2,1), filter 160ms ease;
}

.kinny-cute-svg {
  width: 100%;
  height: 100%;
  animation: kinnyFloat 3s ease-in-out infinite;
}

@keyframes kinnyFloat {
  0%, 100% { 
    transform: translateY(0px) translateZ(0);
  }
  50% { 
    transform: translateY(-3px) translateZ(0);
  }
}

.kinny-text {
  animation: textGlow 2s ease-in-out infinite alternate;
}

@keyframes textGlow {
  from { filter: url(#glow) drop-shadow(0 0 10px #FFB347); }
  to { filter: url(#glow) drop-shadow(0 0 20px #FF7F50); }
}

.ear-left, .ear-right {
  animation: earWiggle 2s ease-in-out infinite;
  transform-origin: bottom center;
}

.ear-left {
  animation-delay: 0s;
}

.ear-right {
  animation-delay: 0.2s;
}

@keyframes earWiggle {
  0%, 100% { transform: rotate(0deg); }
  50% { transform: rotate(5deg); }
}

.heart-tail {
  animation: heartBeat 1.5s ease-in-out infinite;
  transform-origin: center;
}

@keyframes heartBeat {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.veggie-tomato, .veggie-carrot {
  animation: veggieBounce 2s ease-in-out infinite;
}

.veggie-tomato {
  animation-delay: 0.5s;
}

.veggie-carrot {
  animation-delay: 0.8s;
}

@keyframes veggieBounce {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-2px); }
}

.feed-status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  position: relative;
  border: 3px solid;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  margin-right: auto
}

.feed-status-indicator.good {
  background: rgba(76, 175, 80, 0.2);
  border-color: #4caf50;
  color: #4caf50;
}

.feed-status-indicator.medium {
  background: rgba(255, 152, 0, 0.2);
  border-color: #ff9800;
  color: #ff9800;
}

.feed-status-indicator.low {
  background: rgba(255, 87, 34, 0.2);
  border-color: #ff5722;
  color: #ff5722;
}

.feed-status-indicator.critical {
  background: rgba(244, 67, 54, 0.2);
  border-color: #f44336;
  color: #f44336;
  animation: criticalPulse 1.5s infinite;
}

@keyframes criticalPulse {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 0 20px rgba(244, 67, 54, 0.4);
  }
  50% { 
    transform: scale(1.1);
    box-shadow: 0 0 30px rgba(244, 67, 54, 0.7);
  }
}

.status-pulse {
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  bottom: -5px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.3;
  animation: statusPulseAnim 2s infinite;
}

@keyframes statusPulseAnim {
  0% { transform: scale(0.8); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 0.1; }
  100% { transform: scale(0.8); opacity: 0.5; }
}

.status-emoji {
  font-size: 24px;
  position: relative;
  z-index: 1;
  animation: emojiFloat 2s ease-in-out infinite;
}

@keyframes emojiFloat {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-2px) rotate(5deg); }
}

.close-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

/* 🎯 精准改善：Checkin对话框样式 - AAA游戏体验 */
.checkin-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 15000;
  animation: overlayFadeIn 0.3s ease-out;
}

.checkin-dialog {
  background: linear-gradient(135deg, 
    rgba(30, 35, 55, 0.98) 0%,
    rgba(45, 55, 85, 0.98) 50%,
    rgba(35, 45, 65, 0.98) 100%
  );
  backdrop-filter: blur(30px);
  border-radius: 20px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 
    0 30px 60px rgba(0, 0, 0, 0.6),
    0 0 0 1px rgba(255, 255, 255, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  width: 100%;
  max-width: 380px;
  margin: 20px;
  overflow: hidden;
  animation: dialogSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes dialogSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
}

.dialog-title {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.dialog-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.8);
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-close:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  transform: scale(1.1);
}

.dialog-content {
  padding: 20px 24px;
  text-align: center;
}

.dialog-icon {
  font-size: 48px;
  margin-bottom: 16px;
  animation: iconPulse 2s ease-in-out infinite;
}

@keyframes iconPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.dialog-message {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.5;
  margin: 0 0 16px 0;
  white-space: pre-line;
}

.dialog-countdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 16px;
}

.countdown-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.countdown-time {
  font-size: 18px;
  font-weight: 700;
  color: #ffd700;
  font-family: 'Courier New', monospace;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.dialog-actions {
  padding: 16px 24px 20px;
}

.dialog-btn {
  width: 100%;
  height: 44px;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.dialog-btn.primary {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.dialog-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4);
  background: linear-gradient(135deg, #45a049 0%, #4caf50 100%);
}

/* 💎 精简Header设计 */
.hunger-info-compact {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-left: 12px;
}

.hunger-value {
  font-size: 20px;
  font-weight: 900;
  text-shadow: 0 2px 4px rgba(0,0,0,0.8);
  color: white;
}

.hunger-value.critical { color: #f44336; }
.hunger-value.low { color: #ff5722; }
.hunger-value.medium { color: #ff9800; }
.hunger-value.good { color: #4caf50; }

.hunger-label {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255,255,255,0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 🍽️ 精简食物管理 */
.food-inventory-compact {
  padding: 16px 24px;
  background: rgba(0,0,0,0.15);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.inventory-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex: 0 0 auto;
}

.inventory-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.inventory-title {
  font-size: 14px;
  font-weight: 700;
  color: white;
}

.food-types-hint {
  font-size: 11px;
  color: rgba(255,255,255,0.6);
}

.harvest-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.2);
  background: rgba(76,175,80,0.2);
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.harvest-btn.ready {
  background: rgba(76,175,80,0.3);
  border-color: #4caf50;
  animation: harvestPulse 2s infinite;
}

.harvest-btn.growing {
  background: rgba(139,195,74,0.2);
  border-color: rgba(139,195,74,0.4);
  cursor: not-allowed;
  opacity: 0.7;
}

@keyframes harvestPulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 10px rgba(76,175,80,0.3); }
  50% { transform: scale(1.05); box-shadow: 0 0 20px rgba(76,175,80,0.5); }
}

.inventory-preview {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.fruit-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(255,255,255,0.1);
  border-radius: 12px;
  font-size: 12px;
  color: white;
}

.fruit-emoji {
  font-size: 14px;
}

.fruit-count {
  font-weight: 600;
  color: #4caf50;
}

.more-items {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  font-size: 11px;
  color: rgba(255,255,255,0.7);
}

/* 🚫 没有食物提示 */
.no-food-available {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  text-align: center;
  color: rgba(255,255,255,0.8);
}

.no-food-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.6;
}

.no-food-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 8px;
  color: white;
}

.no-food-hint {
  font-size: 13px;
  color: rgba(255,255,255,0.6);
  line-height: 1.4;
}

/* 📊 状态显示 */
.status-display {
  display: flex;
  align-items: center;
  padding: 20px 24px;
  gap: 16px;
  background: rgba(0, 0, 0, 0.2);
  margin: 0 24px 20px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.status-info {
  flex: 1;
}

.status-label {
  font-size: 12px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.status-bar {
  width: 100%;
  height: 12px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 8px;
}

.status-fill {
  height: 100%;
  border-radius: 5px;
  transition: all 0.4s ease;
  position: relative;
}

.status-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(to bottom, rgba(255,255,255,0.3), transparent);
  border-radius: 5px 5px 0 0;
}

.status-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.couple-care-hint {
  font-size: 12px;
  color: rgba(255, 182, 193, 0.9);
  font-weight: 600;
  margin-top: 4px;
  font-style: italic;
}

/* 🌱 Harvest Section - Mobile Optimized */
.harvest-section {
  margin: 0 24px 20px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(22, 163, 74, 0.1));
  border: 2px solid rgba(34, 197, 94, 0.2);
  border-radius: 16px;
  padding: 16px;
}

.harvest-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.harvest-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #22c55e;
}

.harvest-icon {
  font-size: 20px;
  animation: harvestGlow 2s ease-in-out infinite alternate;
}

@keyframes harvestGlow {
  from { filter: drop-shadow(0 0 5px rgba(34, 197, 94, 0.4)); }
  to { filter: drop-shadow(0 0 10px rgba(34, 197, 94, 0.7)); }
}

.harvest-cooldown {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  background: rgba(0, 0, 0, 0.2);
  padding: 4px 8px;
  border-radius: 8px;
}

.harvest-fruits {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.harvest-fruit-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(34, 197, 94, 0.2);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.harvest-fruit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.harvest-fruit-btn.ready {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
  animation: readyPulse 2s ease-in-out infinite;
}

@keyframes readyPulse {
  0%, 100% { 
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
  }
  50% { 
    box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.1);
  }
}

.harvest-fruit-btn.harvesting {
  background: rgba(251, 191, 36, 0.1);
  border-color: #fbbf24;
}

.fruit-preview {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fruit-emoji {
  font-size: 28px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.fruit-sparkles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.sparkle {
  position: absolute;
  font-size: 12px;
  animation: sparkleFloat 1.5s ease-in-out infinite;
}

.sparkle:nth-child(1) { top: -2px; left: -2px; animation-delay: 0s; }
.sparkle:nth-child(2) { top: -2px; right: -2px; animation-delay: 0.5s; }
.sparkle:nth-child(3) { bottom: -2px; left: 50%; animation-delay: 1s; }

@keyframes sparkleFloat {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

.harvest-info {
  flex: 1;
  text-align: left;
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.harvest-ready {
  color: #22c55e;
  animation: readyGlow 2s ease-in-out infinite alternate;
}

@keyframes readyGlow {
  from { text-shadow: 0 0 5px rgba(34, 197, 94, 0.3); }
  to { text-shadow: 0 0 10px rgba(34, 197, 94, 0.6); }
}

/* 🎮 食物指导区域 - AAA级游戏体验 */
.food-guide-section {
  margin: 0 24px 20px;
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.15) 0%,
    rgba(99, 102, 241, 0.15) 50%,
    rgba(139, 92, 246, 0.15) 100%
  );
  border: 2px solid rgba(59, 130, 246, 0.3);
  border-radius: 16px;
  padding: 16px;
  backdrop-filter: blur(10px);
}

.guide-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.guide-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #60a5fa;
}

.guide-icon {
  font-size: 20px;
  animation: guideGlow 2s ease-in-out infinite alternate;
}

@keyframes guideGlow {
  from { filter: drop-shadow(0 0 5px rgba(59, 130, 246, 0.4)); }
  to { filter: drop-shadow(0 0 10px rgba(59, 130, 246, 0.7)); }
}

.food-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
}

.stat-number {
  font-size: 20px;
  font-weight: 900;
  color: #60a5fa;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.game-tips {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.tip-icon {
  font-size: 16px;
  flex-shrink: 0;
  animation: tipPulse 2s ease-in-out infinite;
}

@keyframes tipPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.tip-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  line-height: 1.3;
}

.available-fruits {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 12px;
}

.fruits-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
  font-weight: 600;
}

.fruits-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.fruit-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 12px;
  font-size: 12px;
  color: #22c55e;
  font-weight: 600;
  backdrop-filter: blur(10px);
}

.fruit-emoji {
  font-size: 16px;
}

.fruit-name {
  font-weight: 600;
  color: white;
}

.fruit-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 700;
  color: white;
}

.no-inventory {
  text-align: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.7);
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  margin-top: 12px;
}

.no-inventory-text {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.no-inventory-hint {
  font-size: 12px;
  opacity: 0.8;
}

.fruit-badge img {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

/* Mobile optimizations for harvest section */
@media (max-width: 480px) {
  .harvest-section {
    margin: 0 16px 16px;
    padding: 12px;
  }
  
  .harvest-title {
    font-size: 14px;
  }
  
  .harvest-fruit-btn {
    padding: 10px 12px;
  }
  
  .fruit-preview {
    width: 32px;
    height: 32px;
  }
  
  .fruit-emoji {
    font-size: 24px;
  }
  
  .harvest-info {
    font-size: 13px;
  }
}

.status-value {
  font-size: 32px;
  font-weight: 900;
  padding: 12px 20px;
  border-radius: 16px;
  border: 2px solid;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
  min-width: 90px;
  text-align: center;
}

.status-value.good {
  color: #4caf50;
  border-color: #4caf50;
  background: rgba(76, 175, 80, 0.1);
  box-shadow: 0 0 20px rgba(76, 175, 80, 0.3);
}

.status-value.medium {
  color: #ff9800;
  border-color: #ff9800;
  background: rgba(255, 152, 0, 0.1);
  box-shadow: 0 0 20px rgba(255, 152, 0, 0.3);
}

.status-value.low {
  color: #ff5722;
  border-color: #ff5722;
  background: rgba(255, 87, 34, 0.1);
  box-shadow: 0 0 20px rgba(255, 87, 34, 0.3);
  animation: lowHungerPulse 2s infinite;
}

.status-value.critical {
  color: #f44336;
  border-color: #f44336;
  background: rgba(244, 67, 54, 0.2);
  box-shadow: 0 0 25px rgba(244, 67, 54, 0.5);
  animation: criticalHungerPulse 1.5s infinite;
}

@keyframes lowHungerPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

@keyframes criticalHungerPulse {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 0 25px rgba(244, 67, 54, 0.5);
  }
  50% { 
    transform: scale(1.05);
    box-shadow: 0 0 35px rgba(244, 67, 54, 0.8);
  }
}

/*  喂食按钮 */
.feed-actions {
  padding: 20px 24px 24px;
}

.feed-btn {
  width: 100%;
  height: 56px;
  background: linear-gradient(135deg, #2196f3, #1976d2);
  border: none;
  border-radius: 16px;
  color: white;
  font-size: 18px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 8px 25px rgba(33, 150, 243, 0.4);
  position: relative;
  overflow: hidden;
}

.feed-btn:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  box-shadow: none;
}

.feed-btn.selected {
  background: linear-gradient(135deg, #4caf50, #388e3c);
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4);
}

.feed-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(33, 150, 243, 0.6);
}

.feed-btn.selected:hover {
  box-shadow: 0 12px 35px rgba(76, 175, 80, 0.6);
}

.feed-btn.feeding {
  background: linear-gradient(135deg, #ff9800, #ffb74d);
  cursor: wait;
}

.rotating {
  animation: rotateLoading 1s linear infinite;
}

@keyframes rotateLoading {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ✨ 粒子效果 */
.particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: radial-gradient(circle, rgba(255,255,255,0.8), transparent);
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform-origin: 0 0;
  animation: particleFloat 3s linear infinite;
  animation-delay: var(--delay);
}

@keyframes particleFloat {
  0% {
    transform: translate(0, 0) rotate(var(--angle)) translateX(0);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translate(0, 0) rotate(var(--angle)) translateX(300px);
    opacity: 0;
  }
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

/* 📱 移动端适配 - 完全重构手机体验 */
@media (max-width: 480px) {
  /* 🎯 mobile performance：简化动画和特效 */
  .feed-panel-overlay {
    backdrop-filter: blur(10px); /* 减少模糊强度 */
  }
  
  .feed-panel {
    backdrop-filter: blur(15px); /* 减少模糊强度 */
    animation-duration: 0.2s; /* 加快动画速度 */
  }
  
  /* 🎯 粒子效果tuning */
  .emoji-particle {
    animation-duration: 1.2s; /* 缩短动画时长 */
  }
  
  .veg-wave {
    animation-duration: 1s; /* 缩短动画时长 */
  }
  
  .fly-food {
    animation-duration: 0.8s; /* 缩短飞行动画 */
  }
  
  /* 🎯 Kinny动画tuning */
  .kinny-svg-container {
    animation-duration: 2s; /* 减少浮动动画时长 */
  }
  
  .kinny-svg-container.eating {
    animation-duration: 0.5s; /* 快速吃饭动画 */
  }
}

/* 🎯 further tuning for low-powered devices */
@media (max-width: 480px) and (max-resolution: 150dpi) {
  /* 低分辨率设备：禁用复杂特效 */
  .guide-icon {
    animation: none;
  }
  
  .kinny-text {
    animation: none;
  }
  
  .emoji-particle,
  .veg-wave {
    display: none; /* 完全隐藏粒子效果 */
  }
}

/* 🎯 用户偏好减少动画 */
@media (prefers-reduced-motion: reduce) {
  .kinny-svg-container,
  .guide-icon,
  .kinny-text,
  .emoji-particle,
  .veg-wave,
  .fly-food {
    animation: none !important;
  }
  
  .feed-panel {
    animation-duration: 0.1s;
  }
}
  .feed-panel {
    margin: 6px;
    max-width: calc(100vw - 12px);
    max-height: 90vh;
    overflow-y: hidden; /* 🎯 精准改善：移除滚动，改用内部布局控制 */
    border-radius: 20px;
    display: flex;
    flex-direction: column;
  }
  
  .panel-header {
    padding: 12px 12px 10px; /* 🎯 精准改善：减少padding避免滚动 */
    flex-direction: column;
    gap: 10px; /* 🎯 减少间距 */
    align-items: flex-start;
    flex-shrink: 0; /* 🎯 防止压缩 */
  }
  
  .kinny-avatar-section {
    width: 100%;
    justify-content: space-between;
    align-items: center;
    flex-direction: row;
  }
  
  .kinny-svg-container {
    width: 120px;
    height: 50px;
    flex: 0 0 120px;
  }
  
  .feed-status-indicator {
    width: 45px;
    height: 45px;
  }
  
  .status-emoji {
    font-size: 18px;
  }
  
  .close-btn {
    position: absolute;
    top: 12px;
    right: 12px;
    width: 32px;
    height: 32px;
  }
  
  .status-display {
    margin: 0 16px 12px;
    padding: 12px;
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .status-value {
    font-size: 24px;
    padding: 8px 12px;
    min-width: 70px;
    order: -1;
  }
  
  .status-info {
    order: 1;
  }
  
  .status-label {
    font-size: 11px;
  }
  
  .status-text {
    font-size: 12px;
  }
  
  .couple-care-hint {
    font-size: 10px;
  }
  
  .harvest-section {
    margin: 0 16px 12px;
    padding: 12px;
  }
  
  .harvest-title {
    font-size: 14px;
  }
  
  .harvest-fruit-btn {
    padding: 10px 12px;
  }
  
  .fruit-preview {
    width: 32px;
    height: 32px;
  }
  
  .fruit-emoji {
    font-size: 20px;
  }
  
  .harvest-info {
    font-size: 12px;
  }
  
  .fruits-list {
    gap: 6px;
  }
  
  .fruit-badge {
    padding: 6px 8px;
    font-size: 11px;
  }
  
  .food-guide-section {
    margin: 0 16px 12px;
    padding: 12px;
  }
  
  .guide-title {
    font-size: 14px;
  }
  
  .food-stats {
    gap: 12px;
  }
  
  .stat-number {
    font-size: 16px;
  }
  
  .stat-label {
    font-size: 10px;
  }
  
  .tip-text {
    font-size: 11px;
  }
  
  .feed-actions {
    padding: 12px 16px 16px;
  }
  
  .feed-btn {
    height: 44px;
    font-size: 14px;
    border-radius: 12px;
  }
  
  /* 确保所有动画在手机上流畅 */
  .veg-wave { 
    font-size: 14px !important;
  }
  
  .emoji-particle {
    font-size: 12px !important;
  }
  
  .fly-food {
    width: 32px;
    height: 32px;
  }

  /* Flying food animation layer */
  .feed-animations {
    position: absolute;
    inset: 0;
    pointer-events: none;
  overflow: visible;
}
.fly-food {
  position: fixed; /* position relative to viewport so coordinates match getBoundingClientRect */
  width: 44px;
  height: 44px;
  z-index: 20000;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 🎯 mobile performance：启用GPU加速，避免使用transition */
  will-change: transform, opacity;
  transform: translateZ(0);
  backface-visibility: hidden;
}

/* 🎯 飞行食物emoji样式 - 修复丢失图片问题 */
.food-emoji-flying {
  font-size: 32px;
  filter: drop-shadow(0 6px 12px rgba(0,0,0,0.35));
  transform-origin: center;
  /* 🎯 mobile performance：启用GPU加速 */
  transform: translateZ(0);
  will-change: transform;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  /* 🎯 tuning渲染性能 */
  contain: layout style paint;
  pointer-events: none;
  animation: foodFloat 0.3s ease-in-out infinite alternate;
}

@keyframes foodFloat {
  from { transform: scale(1) rotate(-2deg) translateZ(0); }
  to { transform: scale(1.1) rotate(2deg) translateZ(0); }
}

/* Kinny gulp visual: enhanced scale and professional glow */
.kinny-svg-container.eating .kinny-face-img {
  transform: translateY(2px) scale(1.08);
  filter: drop-shadow(0 12px 32px rgba(255,179,71,0.6));
  transition: transform 140ms cubic-bezier(0.2, 0.9, 0.2, 1), filter 140ms ease;
  will-change: transform;
}

/* Kinny effects layer - contains all interactive effects within kinny container */
.kinny-effects-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: visible;
  z-index: 5;
}

/* AAA-Level Kinny Animation States */

/* Hunger bounce animation */
@keyframes kinny-hunger-bounce {
  0% { transform: scale(1.05) rotate(-2deg) translateY(0px); }
  100% { transform: scale(1.08) rotate(-2deg) translateY(-3px); }
}

/* Excited wiggle animation */
@keyframes kinny-excited-wiggle {
  0% { transform: scale(1.1) rotate(1deg); }
  25% { transform: scale(1.12) rotate(-0.5deg); }
  50% { transform: scale(1.1) rotate(1.5deg); }
  75% { transform: scale(1.12) rotate(-1deg); }
  100% { transform: scale(1.1) rotate(1deg); }
}

/* Enhanced eating chomp animation */
@keyframes kinny-eating-chomp {
  0% { transform: scale(1.15) rotate(0deg); }
  50% { transform: scale(1.2) rotate(0deg) translateY(-2px); }
  100% { transform: scale(1.15) rotate(0deg); }
}

/* Satisfied glow animation */
@keyframes kinny-satisfied-glow {
  0% { 
    transform: scale(1.08) rotate(-1deg); 
    filter: brightness(1.2) drop-shadow(0 0 10px #ffeb3b);
  }
  50% { 
    transform: scale(1.12) rotate(0deg); 
    filter: brightness(1.4) drop-shadow(0 0 15px #ffc107);
  }
  100% { 
    transform: scale(1.08) rotate(-1deg); 
    filter: brightness(1.2) drop-shadow(0 0 10px #ffeb3b);
  }
}

/* Return to normal animation */
@keyframes kinny-return-normal {
  0% { 
    transform: scale(1.08) rotate(-1deg); 
    filter: brightness(1.2);
  }
  100% { 
    transform: scale(1) rotate(0deg); 
    filter: brightness(1);
  }
}

/* Enhanced kinny container eating state with professional glow */
.kinny-svg-container.eating {
  box-shadow: 
    0 8px 32px rgba(255, 215, 120, 0.4),
    0 0 20px rgba(255, 179, 71, 0.3),
    inset 0 -6px 18px rgba(255,255,255,0.1);
  border-color: rgba(255, 179, 71, 0.6);
  transform: scale(1.02);
  transition: all 180ms cubic-bezier(0.2, 0.9, 0.2, 1);
}

/* AAA-Level Kinny State Styles */
.kinny-svg-container.hungry {
  filter: brightness(0.9) sepia(0.3) hue-rotate(20deg);
  box-shadow: 
    0 4px 16px rgba(255, 165, 0, 0.3),
    0 0 10px rgba(255, 140, 0, 0.2);
  border-color: rgba(255, 140, 0, 0.4);
}

.kinny-svg-container.excited {
  filter: brightness(1.3) saturate(1.4) drop-shadow(0 0 5px #ffeb3b);
  box-shadow: 
    0 6px 24px rgba(255, 235, 59, 0.4),
    0 0 15px rgba(255, 193, 7, 0.3);
  border-color: rgba(255, 193, 7, 0.5);
}

.kinny-svg-container.satisfied {
  filter: brightness(1.4) drop-shadow(0 0 15px #4caf50) saturate(1.2);
  box-shadow: 
    0 8px 32px rgba(76, 175, 80, 0.4),
    0 0 20px rgba(139, 195, 74, 0.3),
    inset 0 -6px 18px rgba(255,255,255,0.2);
  border-color: rgba(76, 175, 80, 0.6);
}

/* Veg-wave particles now positioned within kinny container */
.veg-wave {
  position: fixed;
  /* 🎯 mobile performance: transform only; transitions removed to avoid conflicts */
  will-change: transform, opacity;
  z-index: 10;
  text-shadow: 0 4px 12px rgba(0,0,0,0.35);
  /* 🎯 启用硬件加速 */
  backface-visibility: hidden;
  transform: translateZ(0);
  /* 🎯 tuning渲染性能 */
  contain: layout style paint;
  pointer-events: none;
}

/* Enhanced pop-in + slight bounce for veg emojis with professional timing */
@keyframes vegPop {
  0% { transform: translate(-50%, -50%) scale(0.6) translateZ(0); opacity: 0; }
  60% { transform: translate(-50%, -48%) scale(1.12) translateZ(0); opacity: 1; }
  100% { transform: translate(-50%, -50%) scale(1) translateZ(0); opacity: 1; }
}

/* 🎯 精准改善：情侣库存对比样式 */
.inventory-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 🎯 base styling for the check-in slot button */
.checkin-slot-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #FF6B35, #F7931E);
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(255, 107, 53, 0.3);
  min-height: 48px;
  width: 100%;
}

.checkin-slot-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 107, 53, 0.4);
}

.checkin-slot-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
}

.checkin-slot-btn.available {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}

.checkin-slot-btn.cooldown {
  background: linear-gradient(135deg, #9E9E9E, #757575);
  box-shadow: 0 2px 8px rgba(158, 158, 158, 0.3);
}

.checkin-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
}

.checkin-btn:hover {
  background: linear-gradient(135deg, #45a049, #4CAF50);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(76, 175, 80, 0.4);
}

/* 🎰 老虎机按钮样式 */
.slot-machine-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: #1a202c;
  border: none;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(255, 215, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.slot-machine-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.slot-machine-btn.available::before {
  animation: shimmer 2s ease-in-out infinite;
}

.slot-machine-btn:hover {
  background: linear-gradient(135deg, #FFA500, #FFD700);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(255, 215, 0, 0.5);
}

.slot-machine-btn:disabled {
  background: linear-gradient(135deg, #666, #888);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.slot-machine-btn.available {
  animation: availablePulse 3s ease-in-out infinite;
}

.slot-machine-btn.cooldown {
  background: linear-gradient(135deg, #ff7043, #ff5722);
  color: white;
}

.slot-icon {
  font-size: 14px;
  animation: slotSpin 2s ease-in-out infinite;
}

.slot-machine-btn.available .slot-icon {
  animation: slotSpinFast 1s linear infinite;
}

/* 🎯 精准改善：Loading状态样式 */
.checkin-slot-btn.loading {
  background: linear-gradient(135deg, #ffa726, #ff9800) !important;
  animation: loadingPulse 1s ease-in-out infinite;
  cursor: wait !important;
}

.checkin-slot-btn.loading .slot-icon {
  animation: slotSpinFast 0.5s linear infinite;
}

.checkin-slot-btn.loading .slot-text {
  opacity: 1;
  color: #ffffff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.9);
}

@keyframes loadingPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.slot-text {
  font-size: 11px;
  font-weight: 600;
  color: #ffffff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.9);
  letter-spacing: 0.3px;
}

.slot-countdown {
  position: absolute;
  bottom: -18px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 9px;
  color: #ff5722;
  font-weight: 700;
  background: rgba(0, 0, 0, 0.8);
  padding: 2px 6px;
  border-radius: 6px;
  white-space: nowrap;
  font-family: 'Courier New', monospace;
}

@keyframes shimmer {
  0% { left: -100%; }
  50% { left: 100%; }
  100% { left: 100%; }
}

@keyframes slotSpin {
  0% { transform: rotate(0deg); }
  25% { transform: rotate(90deg); }
  50% { transform: rotate(180deg); }
  75% { transform: rotate(270deg); }
  100% { transform: rotate(360deg); }
}

@keyframes slotSpinFast {
  0% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(180deg) scale(1.1); }
  100% { transform: rotate(360deg) scale(1); }
}

.checkin-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.checkin-btn.compact {
  padding: 8px 12px;
  font-size: 12px;
  height: auto;
  min-height: 36px;
  position: relative;
  overflow: hidden;
}

.checkin-btn.compact .checkin-icon {
  font-size: 16px;
}

.checkin-btn.compact .checkin-text {
  font-size: 11px;
  font-weight: 600;
}

/* 🎯 精准改善：Checkin按钮状态样式 */
.checkin-btn.compact.completed {
  background: linear-gradient(135deg, #4caf50, #45a049);
  color: white;
  cursor: default;
}

.checkin-btn.compact.available {
  background: linear-gradient(135deg, #2196f3, #1976d2);
  color: white;
  animation: availablePulse 2s ease-in-out infinite;
}

.checkin-btn.compact.cooldown {
  background: linear-gradient(135deg, #757575, #616161);
  color: rgba(255, 255, 255, 0.8);
  cursor: not-allowed;
}

.checkin-countdown {
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 8px;
  color: #ffd700;
  font-weight: 700;
  background: rgba(0, 0, 0, 0.7);
  padding: 1px 4px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

@keyframes availablePulse {
  0%, 100% { 
    box-shadow: 0 2px 4px rgba(33, 150, 243, 0.3);
  }
  50% { 
    box-shadow: 0 4px 12px rgba(33, 150, 243, 0.6);
    transform: translateY(-1px);
  }
}

.checkin-btn.completed {
  background: linear-gradient(135deg, #4caf50, #45a049);
  color: white;
}

/* 🎯 精准改善：统一游戏化按钮样式 */
.harvest-all-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
  min-height: 48px;
  width: 100%;
}

.harvest-all-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 50%, #c084fc 100%);
}

.harvest-all-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.harvest-all-btn.harvesting {
  background: linear-gradient(135deg, #059669, #10b981);
  animation: harvestingPulse 1.5s ease-in-out infinite;
}

@keyframes harvestingPulse {
  0%, 100% { 
    box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
    transform: scale(1);
  }
  50% { 
    box-shadow: 0 6px 16px rgba(16, 185, 129, 0.6);
    transform: scale(1.05);
  }
}

.harvest-all-btn .btn-icon {
  font-size: 14px;
  animation: iconSparkle 2s ease-in-out infinite;
}

.harvest-all-btn.harvesting .btn-icon {
  animation: iconSparkle 0.8s ease-in-out infinite;
}

@keyframes iconSparkle {
  0%, 100% { 
    transform: rotate(0deg) scale(1);
    filter: brightness(1);
  }
  25% { 
    transform: rotate(-5deg) scale(1.1);
    filter: brightness(1.2);
  }
  50% { 
    transform: rotate(0deg) scale(1.15);
    filter: brightness(1.4);
  }
  75% { 
    transform: rotate(5deg) scale(1.1);
    filter: brightness(1.2);
  }
}

.harvest-all-btn .btn-text {
  font-size: 11px;
  font-weight: 600;
  color: #ffffff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.9);
  letter-spacing: 0.3px;
}

.checkin-icon {
  font-size: 14px;
}

.checkin-text {
  font-size: 11px;
}

.comparison-toggle-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  color: white;
  font-size: 11px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}

.comparison-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.comparison-toggle-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.toggle-icon {
  font-size: 12px;
}

.toggle-text {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.couple-stats {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
}

/* 🎯 食物项增强样式 */
.food-item.self-advantage {
  border: 2px solid #4caf50;
  box-shadow: 0 0 12px rgba(76, 175, 80, 0.3);
}

.food-item.partner-advantage {
  border: 2px solid #ff9800;
  box-shadow: 0 0 12px rgba(255, 152, 0, 0.3);
}

.food-item.equal-advantage {
  border: 2px solid #2196f3;
  box-shadow: 0 0 12px rgba(33, 150, 243, 0.3);
}

.food-item.can-harvest {
  background: linear-gradient(135deg, rgba(255, 235, 59, 0.1), rgba(255, 193, 7, 0.1));
}

.food-quantity {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 4px;
}

.quantity-self,
.quantity-partner {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 9px;
}

.quantity-label {
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
}

.quantity-value {
  color: #ffffff;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.15);
  padding: 2px 8px;
  border-radius: 8px;
  min-width: 20px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.harvest-action {
  margin-top: 6px;
}

.mini-harvest-btn {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  background: linear-gradient(135deg, #ffeb3b, #ffc107);
  border: none;
  border-radius: 12px;
  color: #333;
  font-size: 8px;
  font-weight: 700;
  cursor: pointer;
  transition: all 200ms ease;
}

.mini-harvest-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.4);
}

.mini-harvest-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.mini-harvest-btn .harvest-icon {
  font-size: 10px;
}

.mini-harvest-btn .harvest-text {
  font-size: 8px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* Emoji particle layer - moved here for better organization */
.emoji-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 21000;
}
.emoji-particle {
  position: fixed;
  /* 🎯 mobile performance: transform only; transitions removed to avoid conflicts */
  will-change: transform, opacity;
  text-shadow: 0 6px 18px rgba(0,0,0,0.45);
  /* 🎯 启用硬件加速 */
  backface-visibility: hidden;
  transform: translateZ(0);
  /* 🎯 tuning渲染性能 */
  contain: layout style paint;
  pointer-events: none;
}

@media (max-width: 480px) {
  .kinny-svg-container {
    width: 140px; 
    height: 60px;
    flex: 0 0 30vw;
  }
  
  .kinny-avatar-section {
    gap: 12px;
  }
  
  .feed-status-indicator {
    width: 50px;
    height: 50px;
  }
  
  .veg-wave { 
    font-size: 16px !important;
  }
}

/* 🎯 新的食物库存界面 - AAA游戏体验 */
/* 🎯 食物获得方式说明 */
.food-system-info {
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(56, 142, 60, 0.1) 100%);
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 12px;
  margin-bottom: 16px;
}

.system-header .system-title {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 12px 0;
  text-align: center;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  line-height: 1.3;
}

.system-methods-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.method-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04));
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.3s ease;
  cursor: pointer;
}

.method-card:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.08));
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.method-card .method-icon {
  font-size: 24px;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.method-content {
  flex: 1;
}

.method-title {
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 2px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.method-desc {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.extra-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 12px;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(102, 187, 106, 0.15));
  border-radius: 8px;
  border: 1px solid rgba(76, 175, 80, 0.3);
  margin-top: 8px;
}

.hint-icon {
  font-size: 16px;
}

.hint-text {
  font-size: 12px;
  color: #ffffff;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.food-inventory-section {
  padding: 24px;
  background: linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.06) 100%);
  border-radius: 20px;
  margin-bottom: 20px;
  border: 1px solid rgba(255,255,255,0.15);
  min-width: 0;
  backdrop-filter: blur(10px);
}

/* � AAA食物管理区域 - 弹性自适应 */
.food-inventory-section-modern {
  padding: 18px 20px;
  background: transparent;
  margin: 0;
  border: none;
  backdrop-filter: none;
  box-shadow: none;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  
  /* 🎯 优雅滚动条 */
  scrollbar-width: thin;
  scrollbar-color: rgba(168, 230, 207, 0.3) transparent;
}

.food-inventory-section-modern::-webkit-scrollbar {
  width: 6px;
}

.food-inventory-section-modern::-webkit-scrollbar-track {
  background: transparent;
}

.food-inventory-section-modern::-webkit-scrollbar-thumb {
  background: rgba(168, 230, 207, 0.3);
  border-radius: 3px;
  transition: background 0.3s ease;
}

.food-inventory-section-modern::-webkit-scrollbar-thumb:hover {
  background: rgba(168, 230, 207, 0.5);
}

/* � AAA Kinny Food 卡片 - 紧凑优雅 */
.kinny-food-card-mega {
  position: relative;
  background: linear-gradient(145deg, 
    rgba(76, 175, 80, 0.14) 0%, 
    rgba(33, 150, 243, 0.11) 50%,
    rgba(76, 175, 80, 0.09) 100%);
  border-radius: 16px;
  padding: 14px 16px;
  margin-bottom: 12px;
  border: 2px solid rgba(76, 175, 80, 0.35);
  box-shadow: 
    0 3px 14px rgba(76, 175, 80, 0.2),
    0 1px 3px rgba(0, 0, 0, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  will-change: transform;
}

.kinny-food-card-mega::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(76, 175, 80, 0.5), 
    rgba(33, 150, 243, 0.5),
    transparent);
}

.kinny-food-card-mega.card-glow {
  border-color: rgba(255, 215, 0, 0.8);
  box-shadow: 
    0 12px 40px rgba(255, 215, 0, 0.4), 
    0 0 60px rgba(255, 215, 0, 0.2),
    inset 0 0 30px rgba(255, 215, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  animation: cardGlowPulse 1s ease-in-out infinite;
}

@keyframes cardGlowPulse {
  0%, 100% { 
    box-shadow: 
      0 12px 40px rgba(255, 215, 0, 0.4), 
      0 0 60px rgba(255, 215, 0, 0.2),
      inset 0 0 30px rgba(255, 215, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.15);
  }
  50% { 
    box-shadow: 
      0 16px 50px rgba(255, 215, 0, 0.6), 
      0 0 80px rgba(255, 215, 0, 0.3),
      inset 0 0 40px rgba(255, 215, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
}

.kinny-header-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.kinny-icon-mega {
  width: 48px;
  height: 48px;
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ff6b6b, #feca57, #48dbfb);
  border-radius: 12px;
  box-shadow: 0 3px 10px rgba(255, 107, 107, 0.3);
  animation: kinnyIconPulse 2.5s ease-in-out infinite;
  flex-shrink: 0;
  transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  will-change: transform;
}

.kinny-icon-mega.icon-bounce {
  animation: iconBounceActive 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
}

.kinny-icon-mega.icon-hungry {
  animation: iconShake 0.5s ease-in-out infinite;
  opacity: 0.6;
}

@keyframes kinnyIconPulse {
  0%, 100% { transform: scale(1) translateZ(0); }
  50% { transform: scale(1.05) translateZ(0); }
}

@keyframes iconBounceActive {
  0%, 100% { transform: scale(1) translateY(0) translateZ(0); }
  25% { transform: scale(1.1) translateY(-6px) translateZ(0); }
  50% { transform: scale(1.05) translateY(-3px) translateZ(0); }
  75% { transform: scale(1.1) translateY(-6px) translateZ(0); }
}

@keyframes iconShake {
  0%, 100% { transform: translateX(0) translateZ(0); }
  25% { transform: translateX(-3px) rotate(-3deg) translateZ(0); }
  75% { transform: translateX(3px) rotate(3deg) translateZ(0); }
}

.kinny-info-column {
  flex: 1;
  min-width: 0;
}

.kinny-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: -0.3px;
}

/* � AAA库存对比 - 紧凑设计 */
.kinny-stock-comparison {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 10px;
  backdrop-filter: blur(10px);
}

.stock-you,
.stock-partner {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stock-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.stock-number {
  font-size: 19px;
  font-weight: 700;
  color: #4caf50;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  min-width: 28px;
  text-align: center;
}

.stock-partner .stock-number {
  color: #ff9800;
}

.vs-divider {
  font-size: 12px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.35);
  padding: 0 3px;
}

/* � AAA情侣库存对比 - 紧凑优雅 */
.couple-storage-breakdown {
  position: relative;
  margin: 12px 0;
  display: flex;
  gap: 10px;
  align-items: stretch;
  padding: 12px;
  background: linear-gradient(145deg, 
    rgba(16, 185, 129, 0.12) 0%, 
    rgba(139, 92, 246, 0.12) 50%,
    rgba(16, 185, 129, 0.08) 100%);
  border-radius: 12px;
  border: 2px solid rgba(16, 185, 129, 0.3);
  box-shadow: 
    0 3px 12px rgba(16, 185, 129, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  animation: storageAppear 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  will-change: transform, opacity;
}

.couple-storage-breakdown::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1.5px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(16, 185, 129, 0.4), 
    rgba(139, 92, 246, 0.4),
    transparent);
}

@keyframes storageAppear {
  from { 
    opacity: 0; 
    transform: translateY(10px) scale(0.98) translateZ(0); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0) scale(1) translateZ(0); 
  }
}

.storage-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0; /* Prevent flex overflow */
}

.storage-header {
  position: relative;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.9px;
  padding: 10px 14px;
  background: linear-gradient(145deg, 
    rgba(0, 0, 0, 0.22) 0%, 
    rgba(0, 0, 0, 0.15) 100%);
  border-radius: 9px;
  text-align: center;
  box-shadow: 
    0 2px 6px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
  overflow: hidden;
}

.storage-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.15), 
    transparent);
}

.partner-header-with-button {
  display: flex !important;
  justify-content: center;
  align-items: center;
  text-align: left !important;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.your-storage .storage-header {
  color: #10b981;
  border: 1.5px solid rgba(16, 185, 129, 0.35);
}

.partner-storage .storage-header {
  color: #8b5cf6;
  border: 1.5px solid rgba(139, 92, 246, 0.35);
}

.storage-header:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.storage-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  flex-shrink: 0;
  font-size: 28px;
  animation: dividerPulse 2.8s ease-in-out infinite;
}

@keyframes dividerPulse {
  0%, 100% { 
    transform: scale(1) rotate(0deg);
    filter: drop-shadow(0 0 6px rgba(255, 215, 0, 0.4));
  }
  50% { 
    transform: scale(1.15) rotate(8deg);
    filter: drop-shadow(0 0 14px rgba(255, 215, 0, 0.7));
  }
}

/* � AAA水果库存 - 紧凑网格 */
.fruits-breakdown {
  margin: 14px 0;
  padding: 12px;
  background: rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.breakdown-title {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.75);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

/* 🎮 AAA固定4列网格 - 超紧凑优雅布局 */
.fruits-grid-fixed {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

/* 🎮 AAA水果卡片 - 游戏级质感 紧凑版 */
.fruit-item-aaa {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 6px;
  background: linear-gradient(145deg, 
    rgba(255, 255, 255, 0.08) 0%, 
    rgba(255, 255, 255, 0.02) 100%);
  border-radius: 9px;
  border: 1.5px solid rgba(255, 255, 255, 0.12);
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  will-change: transform;
}

.fruit-item-aaa::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.2), 
    transparent);
}

.fruit-shine {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, 
    transparent 30%, 
    rgba(255, 255, 255, 0.1) 50%, 
    transparent 70%);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.fruit-item-aaa.has-quantity {
  border-color: rgba(76, 175, 80, 0.45);
  background: linear-gradient(145deg, 
    rgba(76, 175, 80, 0.15) 0%, 
    rgba(76, 175, 80, 0.08) 100%);
  box-shadow: 
    0 3px 12px rgba(76, 175, 80, 0.25),
    inset 0 1px 0 rgba(76, 175, 80, 0.2);
}

.fruit-item-aaa:hover {
  transform: translateY(-2px) scale(1.03);
  border-color: rgba(76, 175, 80, 0.7);
  background: linear-gradient(145deg, 
    rgba(76, 175, 80, 0.22) 0%, 
    rgba(76, 175, 80, 0.12) 100%);
  box-shadow: 
    0 4px 14px rgba(76, 175, 80, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.fruit-item-aaa:hover .fruit-shine {
  transform: translateX(100%);
}

.fruit-item-aaa:active {
  transform: translateY(0) scale(1.01);
  box-shadow: 
    0 2px 6px rgba(76, 175, 80, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.fruit-emoji {
  font-size: 28px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  position: relative;
  z-index: 1;
}

/* 🎮 AAA通知按钮 - 紧凑优雅 */
.notify-partner-btn {
  margin-top: 12px;
  padding: 10px 22px;
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 50%, #3b82f6 100%);
  background-size: 200% 200%;
  color: white;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(236, 72, 153, 0.35);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  animation: gradientShift 3s ease infinite;
}

/* Corner button variant - compact size for header */
.notify-corner-btn {
  margin: 0 !important;
  padding: 6px 12px !important;
  font-size: 11px !important;
  letter-spacing: 0.8px !important;
  border-radius: 7px !important;
  box-shadow: 0 1px 6px rgba(236, 72, 153, 0.25) !important;
  white-space: nowrap;
}

.notify-corner-btn .notify-text {
  display: inline;
}

.notify-corner-btn .notify-icon {
  margin-right: 4px;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.notify-partner-btn:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 8px 25px rgba(236, 72, 153, 0.6);
  animation: gradientShift 1.5s ease infinite, btnPulse 0.6s ease;
}

@keyframes btnPulse {
  0%, 100% { transform: translateY(-3px) scale(1.05); }
  50% { transform: translateY(-3px) scale(1.08); }
}

.notify-partner-btn:active {
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 4px 15px rgba(236, 72, 153, 0.5);
}

/* Corner button hover - subtle movement */
.notify-corner-btn:hover {
  transform: translateY(-2px) scale(1.03) !important;
  box-shadow: 0 4px 15px rgba(236, 72, 153, 0.5) !important;
}

.notify-corner-btn:active {
  transform: translateY(0) scale(1.01) !important;
  box-shadow: 0 2px 8px rgba(236, 72, 153, 0.4) !important;
}

.notify-partner-btn.is-sending {
  opacity: 0.6;
  cursor: not-allowed;
  animation: none;
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.notify-partner-btn.is-sending::after {
  content: '';
  display: inline-block;
  margin-left: 8px;
  width: 12px;
  height: 12px;
  border: 2px solid white;
  border-top-color: transparent;
  border-radius: 50%;
  animation: btnSpinner 0.8s linear infinite;
}

@keyframes btnSpinner {
  to { transform: rotate(360deg); }
}

.fruit-count {
  font-size: 14px;
  font-weight: 700;
  color: #4caf50;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  position: relative;
  z-index: 1;
}

/* � AAA主喂食按钮 - 紧凑有力 */
.feed-kinny-mega-btn {
  width: 100%;
  height: 54px;
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  box-shadow: 0 3px 14px rgba(76, 175, 80, 0.45);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  will-change: transform;
}

.feed-kinny-mega-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.feed-kinny-mega-btn:hover:not(:disabled)::before {
  left: 100%;
}

.feed-kinny-mega-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 22px rgba(76, 175, 80, 0.6);
}

.feed-kinny-mega-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 3px 12px rgba(76, 175, 80, 0.45);
}

.feed-kinny-mega-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  background: linear-gradient(135deg, #757575 0%, #616161 100%);
}

.feed-kinny-mega-btn.is-feeding {
  background: linear-gradient(135deg, #ffa726 0%, #ff9800 100%);
  animation: feeding-pulse 1s ease-in-out infinite;
}

@keyframes feeding-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.015); }
}

.feed-kinny-mega-btn.out-of-stock {
  background: linear-gradient(135deg, #757575 0%, #616161 100%);
  cursor: not-allowed;
}

.feed-kinny-mega-btn.btn-pulse {
  animation: btnReadyPulse 2.5s ease-in-out infinite;
}

@keyframes btnReadyPulse {
  0%, 100% { 
    box-shadow: 0 4px 16px rgba(76, 175, 80, 0.45);
  }
  50% { 
    box-shadow: 0 6px 24px rgba(76, 175, 80, 0.7), 0 0 32px rgba(76, 175, 80, 0.35);
  }
}

.feed-icon {
  font-size: 40px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
}

.feed-text {
  font-size: 26px;
  font-weight: 800;
}

.feed-effect {
  font-size: 16px;
  font-weight: 600;
  opacity: 0.9;
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
}

/* Empty Hint */
.empty-hint {
  text-align: center;
  padding: 20px;
  margin-top: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 2px dashed rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.hint-icon {
  font-size: 32px;
}

.hint-text {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
}

/* � AAA次要动作栏 - 紧凑统一 */
.secondary-actions-unified {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.action-btn-unified {
  height: 46px;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.12) 0%, 
    rgba(255, 255, 255, 0.06) 100%);
  border: 1.5px solid rgba(255, 255, 255, 0.18);
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  will-change: transform;
}

.action-btn-unified:hover:not(:disabled) {
  transform: translateY(-1px) scale(1.01);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  border-color: rgba(255, 255, 255, 0.35);
}

.action-btn-unified:active:not(:disabled) {
  transform: translateY(0) scale(1);
}

.action-btn-unified:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.action-btn-unified.is-active {
  background: linear-gradient(135deg, #ffc107 0%, #ffa000 100%);
  border-color: rgba(255, 193, 7, 0.8);
  color: #fff;
  box-shadow: 0 3px 10px rgba(255, 193, 7, 0.35);
}

.action-btn-unified.collect-btn.is-active {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border-color: rgba(255, 107, 107, 0.8);
  box-shadow: 0 3px 10px rgba(255, 107, 107, 0.35);
}

.action-btn-unified.is-loading {
  background: linear-gradient(135deg, #ffa726 0%, #ff9800 100%);
  animation: action-btn-loading 1s ease-in-out infinite;
}

@keyframes action-btn-loading {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.btn-icon-unified {
  font-size: 18px;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.25));
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-text-unified {
  font-size: 12px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
}

.btn-countdown {
  position: absolute;
  top: 4px;
  right: 8px;
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  font-weight: 600;
}

/* 🎯 Modern Kinny Food Header */
.kinny-food-header-modern {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.15) 0%, rgba(33, 150, 243, 0.15) 100%);
  border-radius: 16px;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.kinny-icon-wrapper {
  flex-shrink: 0;
}

.kinny-food-icon-large {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  background: linear-gradient(135deg, #ff6b6b, #feca57, #48dbfb);
  border-radius: 20px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
  animation: foodIconPulse 2s ease-in-out infinite;
}

@keyframes foodIconPulse {
  0%, 100% { transform: scale(1); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); }
  50% { transform: scale(1.05); box-shadow: 0 12px 30px rgba(255, 107, 107, 0.5); }
}

.kinny-food-info {
  flex: 1;
  min-width: 0;
}

.kinny-food-title-main {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.kinny-food-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 12px 0;
}

.kinny-food-stock {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.stock-label {
  color: rgba(255, 255, 255, 0.7);
}

.stock-value {
  color: #ff6b6b;
  font-size: 24px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.stock-value.has-stock {
  color: #4caf50;
}

/* 🎯 Single Action Card */
.kinny-action-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feed-kinny-btn-primary {
  width: 100%;
  padding: 24px;
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  border: none;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
  position: relative;
  overflow: hidden;
}

.feed-kinny-btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.6);
}

.feed-kinny-btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.feed-kinny-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.feed-kinny-btn-primary.is-feeding {
  background: linear-gradient(135deg, #ffa726 0%, #ff9800 100%);
}

.feed-kinny-btn-primary.out-of-stock {
  background: linear-gradient(135deg, #757575 0%, #616161 100%);
}

.btn-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.btn-icon-large {
  font-size: 48px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
}

.btn-text-main {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.btn-effect {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

/* Secondary Actions */
.secondary-actions {
  display: flex;
  gap: 8px;
}

.harvest-btn-secondary {
  flex: 1;
  padding: 16px;
  background: linear-gradient(135deg, #ffc107 0%, #ffa000 100%);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.4);
  transition: all 0.3s ease;
}

.harvest-btn-secondary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(255, 193, 7, 0.6);
}

.harvest-btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon-sm {
  font-size: 20px;
}

.btn-text-sm {
  font-size: 16px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 32px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 2px dashed rgba(255, 255, 255, 0.2);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
}

.inventory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

/* 🎯 gamified preview: Kinny loves foods */
.kinny-loves-foods {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.1);
}

.kinny-text {
  font-size: 10px;
  font-weight: 600;
  color: #e0e7ff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  white-space: nowrap;
  animation: kinnyTextGlow 3s ease-in-out infinite;
}

@keyframes kinnyTextGlow {
  0%, 100% { 
    color: #e0e7ff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  }
  50% { 
    color: #fbbf24;
    text-shadow: 0 1px 4px rgba(251, 191, 36, 0.4);
  }
}

.food-emojis-scroll {
  display: flex;
  align-items: center;
  gap: 2px;
  overflow: hidden;
}

.food-emoji-item {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  animation: foodItemFloat 2s ease-in-out infinite;
}

@keyframes foodItemFloat {
  0%, 100% { 
    transform: translateY(0px) scale(1);
  }
  50% { 
    transform: translateY(-2px) scale(1.05);
  }
}

.food-emoji-item:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.2) translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  z-index: 10;
}

.more-foods {
  font-size: 9px;
  font-weight: 600;
  color: #94a3b8;
  padding: 2px 4px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: 4px;
  white-space: nowrap;
}

.food-emoji-mini:before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.food-emoji-mini:hover:before {
  left: 100%;
}

.food-emoji-mini:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.15);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.inventory-title {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0;
  white-space: nowrap; /* 防止标题换行 */
  overflow: hidden;
  text-overflow: ellipsis;
}

.food-count {
  font-size: 12px;
  color: rgba(255,255,255,0.7);
  background: rgba(255,255,255,0.1);
  padding: 4px 8px;
  border-radius: 12px;
}

.header-controls {
  display: flex;
  gap: 8px;
}

.checkin-btn, .comparison-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  color: white;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.checkin-btn:hover, .comparison-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.checkin-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.checkin-btn.checked-in {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
}

.comparison-btn.active {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
}

.food-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

/* 🎯 精准改善：两列布局 */
.food-grid-two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
  padding-right: 4px;
}

/* 滚动条样式 */
.food-grid-two-columns::-webkit-scrollbar {
  width: 4px;
}

.food-grid-two-columns::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.food-grid-two-columns::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.food-grid-two-columns::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

.food-card {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 8px;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 120px;
}

.food-card:hover {
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.2);
  transform: translateY(-2px);
}

.food-card.selected {
  border-color: #4caf50;
  background: rgba(76, 175, 80, 0.1);
}

.food-card.can-harvest {
  border-color: #ffc107;
  background: rgba(255, 193, 7, 0.1);
}

.food-card.out-of-stock {
  opacity: 0.6;
}

.food-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  cursor: pointer;
}

.food-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.1);
  border-radius: 50%;
}

/* 🍽️ 统一的 Kinny Food icon 样式 */
.food-icon.unified-food-icon {
  background: linear-gradient(135deg, #ff6b6b 0%, #feca57 50%, #48dbfb 100%);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
  animation: unifiedFoodPulse 3s ease-in-out infinite;
}

@keyframes unifiedFoodPulse {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
  }
  50% { 
    transform: scale(1.05);
    box-shadow: 0 6px 16px rgba(255, 107, 107, 0.5);
  }
}

.food-emoji {
  font-size: 24px;
}

.food-info {
  flex: 1;
}

.food-name {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 2px;
}

.food-effect {
  font-size: 12px;
  color: rgba(255,255,255,0.7);
}

/* 🎯 Enhanced Food Quantities - 精准改善黑色文字渲染问题 */
.food-quantities {
  margin-bottom: 8px;
}

.food-quantities-enhanced {
  margin-bottom: 12px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.quantity-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  padding: 2px 4px;
  border-radius: 4px;
}

.quantity-row.primary {
  background: rgba(255, 255, 255, 0.15);
  font-weight: 600;
}

.quantity-row.partner {
  color: rgba(173, 216, 230, 0.9);
  background: rgba(173, 216, 230, 0.1);
}

.quantity-row.harvestable {
  color: #ffd700;
  background: rgba(255, 215, 0, 0.1);
  animation: harvestGlow 2s ease-in-out infinite;
}

.qty-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.7);
}

.qty-value {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
  min-width: 24px;
  text-align: center;
}

/* 🎯 不同状态的数量值样式 */
.qty-value.has-stock {
  background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
  color: white;
  box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
}

.qty-value.out-of-stock {
  background: linear-gradient(135deg, #757575 0%, #9e9e9e 100%);
  color: rgba(255, 255, 255, 0.7);
}

.qty-value.partner-qty {
  background: linear-gradient(135deg, #2196f3 0%, #42a5f5 100%);
  color: white;
}

.qty-value.harvest-ready {
  background: linear-gradient(135deg, #ffc107 0%, #ff8f00 100%);
  color: #1a1a1a;
  font-weight: 700;
  animation: harvestPulse 2s ease-in-out infinite;
}

/* 🎯 Enhanced Food Actions - AAA游戏级按钮体验 */
.food-actions,
.food-actions-enhanced {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* Desktop-specific layout for aggregated single-card presentation */
@media (min-width: 769px) {
  .food-grid-single {
    display: flex;
    justify-content: center;
    padding: 8px 12px;
  }

  .food-card.aggregated {
    width: 720px; /* Desktop preferred width for aggregated card */
    max-width: calc(100% - 96px);
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  /* Arrange action buttons horizontally with tight spacing */
  .food-actions-enhanced {
    flex-direction: row;
    gap: 12px;
  }

  .action-btn {
    flex: 0 0 auto; /* prefer intrinsic width */
  }

  .feed-btn-enhanced {
    min-width: 160px;
  }

  .harvest-btn {
    min-width: 140px;
  }
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: none;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
}

.feed-btn {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  color: white;
}

.feed-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(76, 175, 80, 0.3);
}

.feed-btn.selected {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
}

/* 🎯 Enhanced Feed Button - AAA游戏级喂食体验 */
.feed-btn-enhanced {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border: none;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex: 1;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  box-shadow: 0 3px 6px rgba(255, 107, 107, 0.3);
  position: relative;
  overflow: hidden;
}

.feed-btn-enhanced::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.6s ease;
}

.feed-btn-enhanced:hover::before {
  left: 100%;
}

.feed-btn-enhanced:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 12px rgba(255, 107, 107, 0.4);
  background: linear-gradient(135deg, #ff5252 0%, #d32f2f 100%);
}

.feed-btn-enhanced:active {
  transform: translateY(0) scale(0.98);
  box-shadow: 0 2px 4px rgba(255, 107, 107, 0.3);
}

.feed-btn-enhanced:disabled {
  background: linear-gradient(135deg, #757575 0%, #616161 100%);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.feed-btn-enhanced:disabled::before {
  display: none;
}

.harvest-btn {
  background: linear-gradient(135deg, #ffc107 0%, #ff8f00 100%);
  color: white;
}

.harvest-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(255, 193, 7, 0.3);
}

.harvest-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.status-info {
  flex: 1;
  text-align: center;
}

.status-text {
  font-size: 11px;
  color: rgba(255,255,255,0.5);
  font-style: italic;
}

/* 移动端responsive layout */
@media (max-width: 768px) {
  .food-grid {
    grid-template-columns: 1fr;
  }
  
  .food-card {
    padding: 10px;
  }
  
  .inventory-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .header-controls {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .food-inventory-section {
    padding: 14px;
    margin-bottom: 12px;
  }
  
  .food-grid {
    grid-template-columns: 1fr;
  }
  
  .inventory-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .header-controls {
    justify-content: center;
  }
}

/* � AAA食物系统说明 - 超紧凑卡片 */
.food-system-info-bottom {
  margin-top: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
}

.food-system-info-bottom .system-header {
  margin-bottom: 10px;
  text-align: center;
}

.food-system-info-bottom .system-title {
  font-size: 13px;
  font-weight: 600;
  color: #ffd700;
  margin: 0;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}

.system-methods-grid-compact {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 10px;
}

.method-card-small {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 7px;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.method-card-small:hover {
  background: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px) translateZ(0);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.18);
}

.method-card-small .method-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.method-card-small .method-content {
  flex: 1;
  min-width: 0;
}

.method-card-small .method-title {
  font-size: 10px;
  font-weight: 600;
  color: white;
  margin-bottom: 1px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}

.method-card-small .method-desc {
  font-size: 8px;
  color: rgba(255, 255, 255, 0.65);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.extra-hint-compact {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  background: rgba(255, 215, 0, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(255, 215, 0, 0.2);
}

.extra-hint-compact .hint-icon {
  font-size: 14px;
  color: #ffd700;
}

.extra-hint-compact .hint-text {
  font-size: 11px;
  color: #ffd700;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* 动画增强 */
@keyframes harvestGlow {
  0%, 100% { box-shadow: 0 0 8px rgba(255, 215, 0, 0.3); }
  50% { box-shadow: 0 0 16px rgba(255, 215, 0, 0.6); }
}

@keyframes harvestPulse {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 2px 4px rgba(255, 193, 7, 0.3);
  }
  50% { 
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(255, 193, 7, 0.5);
  }
}

/* 响应式tuning */
@media (max-width: 480px) {
  .system-methods-grid-compact {
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }
  
  .method-card-small {
    padding: 6px;
    gap: 6px;
  }
  
  /* 🎯 移动端两列布局tuning */
  .food-grid-two-columns {
    grid-template-columns: 1fr 1fr;
    gap: 4px;
    max-height: 280px;
    padding-right: 2px;
  }
  
  .food-card {
    padding: 4px;
    min-height: 95px;
  }
  
  .food-header {
    gap: 8px;
    margin-bottom: 6px;
  }
  
  .food-icon {
    width: 32px;
    height: 32px;
  }
  
  .food-emoji {
    font-size: 20px;
  }
  
  .food-name {
    font-size: 12px;
  }
  
  .food-effect {
    font-size: 10px;
  }
  
  .food-quantities-enhanced {
    padding: 6px;
    margin-bottom: 8px;
  }
  
  .qty-label,
  .qty-value {
    font-size: 10px;
  }
  
  .qty-value {
    padding: 1px 6px;
    min-width: 20px;
  }
  
  .action-btn {
    padding: 4px 8px;
    font-size: 10px;
  }
  
  .feed-btn-enhanced {
    padding: 6px 8px;
    font-size: 10px;
  }
  
  .btn-icon {
    font-size: 12px;
  }
  
  .btn-text {
    font-size: 9px;
  }
  
  /* Header适配 */
  .inventory-header {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
    gap: 6px;
  }
  
  .harvest-all-btn,
  .checkin-btn.compact,
  .comparison-btn {
    padding: 6px 8px;
    font-size: 10px;
  }
  
  /* Bottom info区域 */
  .food-system-info-bottom {
    padding: 8px;
    margin-top: 12px;
  }
  
  .system-methods-grid-compact {
    margin-bottom: 8px;
  }
  
  .method-card-small .method-icon {
    font-size: 16px;
  }
  
  .method-card-small .method-title {
    font-size: 10px;
  }
  
  .method-card-small .method-desc {
    font-size: 9px;
  }
  
  /* 🎯 精准改善：移动端对话框适配 */
  .checkin-dialog {
    max-width: 95vw;
    margin: 10px;
  }
  
  .dialog-header {
    padding: 16px 20px 12px;
  }
  
  .dialog-title {
    font-size: 16px;
  }
  
  .dialog-content {
    padding: 16px 20px;
  }
  
  .dialog-icon {
    font-size: 40px;
    margin-bottom: 12px;
  }
  
  .dialog-message {
    font-size: 13px;
    margin-bottom: 12px;
  }
  
  .dialog-countdown {
    padding: 10px 12px;
    margin-bottom: 12px;
  }
  
  .countdown-time {
    font-size: 16px;
  }
  
  .dialog-actions {
    padding: 12px 20px 16px;
  }
  
  .dialog-btn {
    height: 40px;
    font-size: 13px;
  }
  
  /* Checkin按钮移动端适配 */
  .checkin-countdown {
    font-size: 7px;
    bottom: -1px;
  }
  
  /* 🎯 精准改善：紧凑布局避免滚动 */
  .food-inventory-section-modern {
    padding: 12px;
    margin-bottom: 12px;
  }
  
  .kinny-food-card-mega {
    padding: 16px;
    margin-bottom: 12px;
  }
  
  .secondary-actions-unified {
    gap: 6px;
    margin-top: 12px;
  }
  
  .action-btn-unified {
    padding: 8px 12px;
    font-size: 11px;
  }
}

/* 🎯 aggressive mobile performance tuning -------------------------------- */
@media (max-width: 768px) {
  /* 减少GPU渲染压力 */
  .kinny-svg-container,
  .emoji-particle,
  .veg-wave,
  .fly-food {
    will-change: auto;
    transform: translateZ(0);
  }
  
  /* 简化动画 */
  @keyframes kinnyFloat {
    0%, 100% { transform: translateY(0px) translateZ(0); }
    50% { transform: translateY(-2px) translateZ(0); }
  }
}

/* 🎯 低性能device-specific tuning */
@media (max-width: 480px) and (-webkit-max-device-pixel-ratio: 2) {
  .emoji-particle,
  .veg-wave {
    opacity: 0.7; /* 减少视觉复杂度 */
    animation-duration: 1s; /* 加快动画完成 */
  }
}

/* 🎯 极低性能设备：禁用特效 */
@media (max-width: 360px) {
  .emoji-particle,
  .veg-wave {
    display: none;
  }
  
  .kinny-svg-container {
    animation: none;
  }
}

/* 🎯 移动端动画performance tuning */
@media (max-width: 768px) {
  /* 减少动画复杂度 */
  .food-emoji-flying {
    animation-duration: 0.5s; /* 延长周期减少计算频率 */
  }
  
  /* 简化动画关键帧 */
  @keyframes foodFloat {
    from { transform: scale(1) translateZ(0); }
    to { transform: scale(1.05) translateZ(0); }
  }
  
  /* tuningemoji粒子动画 */
  .emoji-particle {
    text-shadow: none; /* 移除阴影减少GPU负载 */
  }
  
  .veg-wave {
    text-shadow: 0 2px 6px rgba(0,0,0,0.25); /* 简化阴影 */
  }
  
  /* 禁用过度的视觉效果 */
  .kinny-svg-container.eating .kinny-face-img {
    filter: none; /* 移除复杂滤镜 */
    transform: translateY(1px) scale(1.03) translateZ(0);
  }
}

/* 🎯 低性能设备检测：通过CSS变量暴露 */
@media (max-device-width: 768px) and (-webkit-max-device-pixel-ratio: 2) {
  :root {
    --is-low-performance: 1;
  }
}

/* 🎮 AAA Game Toast Animations */
@keyframes gameToastIn {
  0% {
    opacity: 0;
    transform: translateX(-50%) translateY(-30px) scale(0.8);
  }
  60% {
    transform: translateX(-50%) translateY(5px) scale(1.05);
  }
  100% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
}

@keyframes gameToastOut {
  0% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px) scale(0.9);
  }
}
</style>

<template>
  <v-app class="quest-game-arena">
    <!-- Popup warning dialog -->
    <v-dialog v-model="showWarning" width="400">
      <v-card>
        <v-card-title class="headline">Warning</v-card-title>
        <v-card-text>Message Sent!</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="warning" @click="showWarning = false">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Web端左右分栏布局 -->
    <div class="game-content-zone" :class="{ 'split-layout': isDesktop }">
      <!-- 左侧：菜谱区域 -->
      <RoundlyRecipe 
        :show-instructions="false"
        :show-dice="false"
        :show-tasks="!isDesktop"
        @recipe-rolled="onRecipeRolled"
      />
      
      <!-- 右侧：任务面板（仅web端显示） -->
      <div v-if="isDesktop" class="quest-sidebar">
        <!-- 顶部导航切换 -->
        <div class="sidebar-tabs">
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'tasks' }"
            @click="activeTab = 'tasks'"
          >
            <span class="tab-icon">📸</span>
            <span class="tab-label">Quest</span>
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'market' }"
            @click="activeTab = 'market'"
          >
            <span class="tab-icon">🛒</span>
            <span class="tab-label">Market</span>
          </button>
        </div>
        
        <!-- 任务面板 -->
        <div v-show="activeTab === 'tasks'" class="tab-content">
          <div class="sidebar-header">
            <div class="header-icon">📸</div>
            <div class="header-content">
              <h3>INGREDIENT QUEST</h3>
              <p>Complete your mission to move on to STEP 3</p>
            </div>
          </div>
          
          <!-- <div class="quest-progress">
            <div class="progress-bar-container">
              <div class="progress-bar" :style="{ width: questProgress + '%' }"></div>
            </div>
            <div class="progress-text">{{ questProgress }}% Complete</div>
          </div> -->

          <div class="quest-content">
          <!-- 任务完成状态 -->
          <div v-if="allTasksCompleted" class="quest-complete">
            <div class="complete-icon">🎉</div>
            <h4>Mission Complete!</h4>
            <p>Ready to start cooking</p>
            <button @click="router.push('/diary')" class="action-btn primary">
              <span class="btn-icon">🍳</span>
              <span>START COOKING</span>
            </button>
          </div>

          <!-- 任务进行中 -->
          <div v-else class="quest-active">
            <div class="quest-card" v-for="task in currentTasks" :key="task.id">
              <div class="task-status" :class="{ completed: task.is_verified }">
                <span v-if="task.is_verified" class="status-icon">✓</span>
                <span v-else class="status-icon">○</span>
              </div>
              
              <div class="task-ingredient">
                <div class="ingredient-image">
                  <img
                    v-if="task.ingredient?.default_picture"
                    :src="fixUrl(task.ingredient.default_picture)"
                    :alt="task.ingredient?.name"
                  />
                  <div v-else class="ingredient-placeholder">🥗</div>
                </div>
                <div class="ingredient-info">
                  <div class="ingredient-name">{{ task.ingredient?.name || 'Unknown' }}</div>
                  <div class="ingredient-hint">Take a photo to verify</div>
                </div>
              </div>
              
              <button 
                v-if="!task.is_verified"
                @click="verifyTask(task)"
                class="verify-btn"
              >
                📸 Verify
              </button>
              <div v-else class="completed-badge">
                <span>✓ Verified</span>
              </div>
            </div>

            <div v-if="currentTasks.length === 0" class="no-tasks">
              <div class="empty-icon">🎲</div>
              <p>Roll the dice to get your quest!</p>
            </div>
          </div>
        </div>
        </div>
        
        <!-- 市场面板 -->
        <div v-show="activeTab === 'market'" class="tab-content">
          <div class="market-header">
            <div class="market-icon">🛒</div>
            <div class="market-title-group">
              <h3>MARKET FINDER</h3>
              <p>Find nearby grocery stores</p>
            </div>
          </div>
          
          <div class="quest-progress">
            <button class="market-scout-btn" @click="scanStores" :disabled="marketLoading">
              <span v-if="!marketLoading" class="scout-content">
                <span class="scout-icon">🔍</span>
                <span>SCOUT STORES</span>
              </span>
              <span v-else class="scout-loading">
                <span class="loading-spinner"></span>
                <span>Scanning...</span>
              </span>
            </button>
          </div>

          <div class="market-content">
            <div v-if="marketError" class="error-banner">
              <span class="error-icon">⚠️</span>
              <span class="error-text">{{ marketError }}</span>
            </div>
            
            <div v-if="nearbyStores.length > 0" class="stores-list">
              <div v-for="store in nearbyStores" :key="store.id" 
                   class="store-card" @click="openStoreMap(store)">
                <div class="store-badge">{{ store.distance?.toFixed(1) }}km</div>
                <div class="store-info">
                  <h4 class="store-name">{{ store.name }}</h4>
                  <p class="store-address">{{ store.address }}</p>
                </div>
                <div class="store-action">📍</div>
              </div>
            </div>
            
            <div v-else-if="!marketLoading && marketScanned" class="market-empty">
              <div class="empty-icon">🏪</div>
              <p>No stores found nearby</p>
              <p class="empty-hint">Try again or check location</p>
            </div>
            
            <div v-else-if="!marketScanned" class="market-intro">
              <div class="intro-icon">🗺️</div>
              <p>Tap Scout to find stores</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Ingredient Verification Modal -->
    <IngredientVerifyModal
      v-if="currentVerifyTask"
      :visible="showVerifyModal"
      :task="currentVerifyTask"
      @success="onVerifySuccess"
      @cancel="onVerifyCancel"
      @confirm="router.push('/diary')"
    />
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import RoundlyRecipe from '@/components/RoundlyRecipe.vue'
import IngredientVerifyModal from '@/components/IngredientVerifyModal.vue'
import { useRecipesStore } from '@/stores/recipeStore'
import { useTaskStore } from '@/stores/taskStore'
import { resolveURL } from '@/utils/resolveURL'
import { trackViewRecipePage } from '@/utils/analytics'

const router = useRouter()
const recipesStore = useRecipesStore()
const taskStore = useTaskStore()

const showWarning = ref(false)
const isDesktop = ref(window.innerWidth >= 769)
const activeTab = ref<'tasks' | 'market'>('tasks')

// Verification modal state
const showVerifyModal = ref(false)
const currentVerifyTask = ref<any>(null)

// Market store finder state
const marketLoading = ref(false)
const marketError = ref('')
const marketScanned = ref(false)
const nearbyStores = ref<any[]>([])

// 响应式监听窗口大小
const handleResize = () => {
  isDesktop.value = window.innerWidth >= 769
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  
  // 🎯 Analytics: Track recipe page view (Step 1 & 2)
  const currentBracket = recipesStore.currentBracket
  if (currentBracket?.recipe) {
    trackViewRecipePage(
      currentBracket.recipe.id,
      currentBracket.recipe.name,
      false // hasRolledDice - 可以根据实际情况判断
    )
  }
  
  // 🎯 精准改善：不在此处调用fetchTasks
  // RoundlyRecipe组件内部的watch会自动处理数据加载（带缓存）
  // 这样避免了重复调用API
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// 🎯 watcher removed; RoundlyRecipe owns the loading
// RoundlyQuestView只消费taskStore中的数据，不主动加载

// 当前任务列表
const currentTasks = computed(() => taskStore.tasks || [])

// 任务完成状态
const allTasksCompleted = computed(() => taskStore.allDone)

// 任务进度百分比
const questProgress = computed(() => {
  const total = currentTasks.value.length
  if (total === 0) return 0
  const completed = currentTasks.value.filter((t: any) => t.is_verified).length
  return Math.round((completed / total) * 100)
})

// 修复图片URL
function fixUrl(url: string | null | undefined) {
  return resolveURL(url) || ''
}

// 验证任务
function verifyTask(task: any) {
  currentVerifyTask.value = task
  showVerifyModal.value = true
}

// 处理验证成功
function onVerifySuccess() {
  showVerifyModal.value = false
  currentVerifyTask.value = null
  // 🎯 no manual refresh needed; verifyTask already clears the cache and reloads
  // taskStore.verifyTask() 会自动调用 fetchTasks(recipeId, true)
}

// 处理验证取消
function onVerifyCancel() {
  showVerifyModal.value = false
  currentVerifyTask.value = null
}

function roll() {
  showWarning.value = true
  // Send random SMS to couple here
}

function onRecipeRolled(recipe: any) {
  // 你可以根據需要加分數或提示
}

// Market store finder functions
const toRad = (d: number) => d * Math.PI / 180
const haversine = (lat1: number, lon1: number, lat2: number, lon2: number) => {
  const R = 6371
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

const buildAddress = (tags: Record<string, string>, lat: number, lon: number) => {
  const line1 = [tags['addr:housenumber'], tags['addr:street']].filter(Boolean).join(' ')
  const city = [tags['addr:city'], tags['addr:state']].filter(Boolean).join(' ')
  const line2 = [city, tags['addr:postcode']].filter(Boolean).join(' ')
  return [line1, line2].filter(Boolean).join(', ') || `${lat.toFixed(4)}, ${lon.toFixed(4)}`
}

function openStoreMap(store: any) {
  const query = encodeURIComponent(`${store.name} ${store.address}`)
  window.open(`https://www.google.com/maps/search/?api=1&query=${query}`, '_blank')
}

async function scanStores() {
  marketError.value = ''
  nearbyStores.value = []
  marketLoading.value = true
  marketScanned.value = true
  
  try {
    const position = await new Promise<GeolocationPosition>((resolve, reject) =>
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 8000
      })
    )
    
    const { latitude: lat, longitude: lon } = position.coords
    const query = `[out:json][timeout:15];node["shop"~"supermarket|grocery"](around:5000,${lat},${lon});out;`
    
    const response = await fetch('https://overpass-api.de/api/interpreter', {
      method: 'POST',
      body: query
    })
    
    if (!response.ok) throw new Error('Network error')
    
    const data = await response.json()
    
    nearbyStores.value = data.elements.map((el: any) => {
      const tags = el.tags || {}
      return {
        id: String(el.id),
        name: tags.name || 'Unnamed Store',
        lat: el.lat,
        lon: el.lon,
        address: buildAddress(tags, el.lat, el.lon),
        brand: tags.brand,
        distance: haversine(lat, lon, el.lat, el.lon)
      }
    }).sort((a: any, b: any) => a.distance - b.distance).slice(0, 10)
    
    if (nearbyStores.value.length === 0) {
      marketError.value = 'No stores found within 5km'
    }
  } catch (e: any) {
    if (e.code === 1) {
      marketError.value = 'Location permission denied'
    } else if (e.code === 2) {
      marketError.value = 'Location unavailable'
    } else if (e.code === 3) {
      marketError.value = 'Location request timeout'
    } else {
      marketError.value = 'Failed to fetch stores'
    }
  } finally {
    marketLoading.value = false
  }
}
</script>
<style scoped>
/* ===== 游戏竞技场 ===== */
.quest-game-arena {
  min-height: 100vh;
  background: linear-gradient(135deg, 
    #0f172a 0%, 
    #1e293b 25%, 
    #334155 50%, 
    #1e293b 75%,
    #0f172a 100%);
  background-size: 400% 400%;
  animation: gameArenaFlow 12s ease-in-out infinite;
  display: flex;
  flex-direction: column;
  color: #fff;
  padding: 0;
  position: relative;
}

@keyframes gameArenaFlow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* ===== 游戏内容区域 - 移动端单栏 ===== */
.game-content-zone {
  flex: 1;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  position: relative;
  z-index: 5;
  max-width: 100%;
  width: 100%;
}

.recipe-panel {
  flex: 1;
  width: 100%;
  /* 🎯 the recipe panel scrolls far enough to show everything */
  overflow-y: auto;
  max-height: calc(100vh - 4rem);
  padding-bottom: 2rem; /* 底部留白，确保最后内容可见 */
}

/* Web端左右分栏布局 - 黄金比例tuning */
.game-content-zone.split-layout {
  flex-direction: row;
  gap: 2rem;
  padding: 2rem;
  align-items: flex-start;
  max-width: 100%;
}

.game-content-zone.split-layout .recipe-panel {
  flex: 1.618;  /* 黄金比例 */
  min-width: 0;
  max-width: calc(100% - 440px);
  /* 🎯 精准改善：保持滚动能力，确保Step 2完整显示 */
  overflow-y: auto;
  max-height: calc(100vh - 4rem);
  padding-right: 0.5rem; /* 为滚动条留出空间 */
}

/* 🎯 精准改善：美化recipe-panel滚动条 */
.recipe-panel::-webkit-scrollbar {
  width: 8px;
}

.recipe-panel::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.recipe-panel::-webkit-scrollbar-thumb {
  background: rgba(251, 191, 36, 0.3);
  border-radius: 4px;
  transition: background 0.3s ease;
}

.recipe-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(251, 191, 36, 0.5);
}

/* deep selector giving RoundlyRecipe more width */
.game-content-zone :deep(.card) {
  max-width: 100% !important;
  width: 100% !important;
  margin: 0 !important;
  transform: scale(1);
  transition: all 0.3s ease;
}

.game-content-zone :deep(.card:hover) {
  transform: scale(1.005);
  box-shadow: 0 10px 30px rgba(236, 72, 153, 0.12);
}

/* ===== 右侧任务面板（Web端专属） - 黄金比例 1:1.618 ===== */
.quest-sidebar {
  flex: 1;  /* 黄金比例的对应值 */
  width: 420px;
  min-width: 420px;
  max-width: 420px;
  flex-shrink: 0;
  height: calc(100vh - 4rem);  /* 固定高度 - 确保始终等高 */
  max-height: calc(100vh - 4rem);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.95));
  border-radius: 1rem;
  padding: 0;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(20px);
  border: 2px solid rgba(251, 191, 36, 0.4);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05);
  overflow: hidden;
  position: sticky;
  top: 2rem;
}

/* ===== Tab Navigation System - AAA 游戏级别导航 ===== */
.sidebar-tabs {
  display: flex;
  padding: 1rem;
  gap: 0.5rem;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.3));
  border-bottom: 2px solid rgba(251, 191, 36, 0.4);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  flex-shrink: 0;
  position: relative;
}

.sidebar-tabs::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(251, 191, 36, 0.6), transparent);
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { opacity: 0.3; transform: translateX(-100%); }
  50% { opacity: 1; transform: translateX(100%); }
}

/* Tab Button - AAA 游戏大作级别交互 */
.tab-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.4rem; /* 🎯 减少内部间距 */
  padding: 0.85rem 0.65rem; /* 🎯 tuningpadding，留更多点击区域 */
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.15);
  border-radius: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease; /* 🎯 简化动画，减少延迟 */
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  min-height: 4rem; /* 🎯 确保足够的点击区域（Fitts定律） */
  touch-action: manipulation; /* 🎯 tuning触摸响应 */
}

.tab-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(245, 158, 11, 0.15));
  opacity: 0;
  transition: opacity 0.4s ease;
}

.tab-btn::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(251, 191, 36, 0.6), transparent);
  transform: translate(-50%, -50%);
  transition: width 0.6s ease, height 0.6s ease, opacity 0.6s ease;
  opacity: 0;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(251, 191, 36, 0.5);
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 6px 16px rgba(251, 191, 36, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.tab-btn:hover::after {
  width: 200px;
  height: 200px;
  opacity: 0.3;
}

.tab-btn:hover::before {
  opacity: 1;
}

/* Active Tab - 超强AAA游戏激活状态 */
.tab-btn.active {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.25), rgba(245, 158, 11, 0.2));
  border-color: rgba(251, 191, 36, 0.9);
  box-shadow: 
    0 0 25px rgba(251, 191, 36, 0.6), 
    0 8px 20px rgba(251, 191, 36, 0.4),
    inset 0 0 20px rgba(251, 191, 36, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transform: scale(1.08) translateY(-2px);
  animation: active-glow 2s ease-in-out infinite;
}

@keyframes active-glow {
  0%, 100% { box-shadow: 
    0 0 25px rgba(251, 191, 36, 0.6), 
    0 8px 20px rgba(251, 191, 36, 0.4),
    inset 0 0 20px rgba(251, 191, 36, 0.15); 
  }
  50% { box-shadow: 
    0 0 35px rgba(251, 191, 36, 0.8), 
    0 12px 28px rgba(251, 191, 36, 0.6),
    inset 0 0 25px rgba(251, 191, 36, 0.2); 
  }
}

.tab-btn.active::before {
  opacity: 1;
  animation: pulse-bg 3s ease-in-out infinite;
}

@keyframes pulse-bg {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}

.tab-icon {
  font-size: 2rem;
  filter: drop-shadow(0 2px 8px rgba(251, 191, 36, 0.5));
  transition: all 0.3s ease;
}

.tab-btn:hover .tab-icon,
.tab-btn.active .tab-icon {
  filter: drop-shadow(0 4px 12px rgba(251, 191, 36, 0.8));
  transform: scale(1.1);
}

.tab-label {
  font-size: 0.9rem; /* 🎯 稍微缩小，平衡视觉 */
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.8px; /* 🎯 稍微紧凑 */
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.3s ease;
  user-select: none; /* 🎯 防止文本选中，提升触摸体验 */
}

.tab-btn:hover .tab-label,
.tab-btn.active .tab-label {
  color: #fbbf24;
  text-shadow: 0 2px 8px rgba(251, 191, 36, 0.5);
}

/* ===== Tab Content ===== */
.tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 2rem;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
}

/* Quest content specific height - 固定高度，不会因内容变化而改变 */
.quest-content {
  flex: 1;
  min-height: 0;
  max-height: 100%;  /* 防止超出父容器 */
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid rgba(251, 191, 36, 0.4);
  margin: -0.5rem -0.5rem 0;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  padding-top: 0;
  flex-shrink: 0;
  min-height: 80px;
}

.header-icon {
  font-size: 3rem;
  filter: drop-shadow(0 4px 12px rgba(251, 191, 36, 0.6));
  animation: icon-float 3s ease-in-out infinite;
}

@keyframes icon-float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
}

.header-content h3 {
  font-size: 1.3rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: #fbbf24;
  margin: 0;
  text-shadow: 0 3px 10px rgba(251, 191, 36, 0.7), 0 0 20px rgba(251, 191, 36, 0.3);
  line-height: 1.2;
}

.header-content p {
  font-size: 1.05rem; /* 🎯 从0.8rem → 1.05rem，+31%易读性 */
  color: rgba(255, 255, 255, 0.75);
  margin: 0.4rem 0 0;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* 进度条 */
.quest-progress {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex-shrink: 0;
  min-height: 70px;
}

.progress-bar-container {
  height: 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
  border-radius: 0.75rem;
  transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 0 15px rgba(251, 191, 36, 0.6);
}

.progress-text {
  font-size: 0.95rem; /* 🎯 从0.7rem → 0.95rem，+36%易读性 */
  font-weight: 700;
  color: #fbbf24;
  text-align: center;
  letter-spacing: 0.5px;
}

/* 任务内容区域 */
.quest-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
}

/* 任务完成状态 */
.quest-complete {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem 1rem;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(22, 163, 74, 0.1));
  border-radius: 1rem;
  border: 2px solid rgba(34, 197, 94, 0.3);
  height: 100%;
  justify-content: center;
}

.complete-icon {
  font-size: 4rem;
  animation: bounce 1s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.quest-complete h4 {
  font-size: 1.1rem;
  font-weight: 900;
  color: #22c55e;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.quest-complete p {
  font-size: 1rem; /* 🎯 0.8rem → 1rem，+25% */
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  font-weight: 600;
}

/* 任务进行中 */
.quest-active {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.quest-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 1rem;
  padding: 0.9rem 1rem; /* 🎯 tuningpadding分配 */
  display: flex;
  align-items: center;
  gap: 0.7rem; /* 🎯 减少gap防止拥挤 */
  border: 2px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  min-height: 4.5rem; /* 🎯 最小高度确保不挤压 */
  flex-wrap: nowrap; /* 🎯 强制单行，防止换行 */
}

.quest-card:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(251, 191, 36, 0.6);
  transform: translateX(8px) translateY(-2px);
  box-shadow: 0 6px 16px rgba(251, 191, 36, 0.3);
}

.task-status {
  flex-shrink: 0;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border: 3px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.task-status.completed {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  border-color: #22c55e;
  box-shadow: 0 0 15px rgba(34, 197, 94, 0.5);
  animation: pulse-complete 2s ease-in-out infinite;
}

@keyframes pulse-complete {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.status-icon {
  font-size: 1.1rem;
  font-weight: 900;
  color: white;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.task-ingredient {
  flex: 1 1 auto; /* 🎯 允许弹性伸缩 */
  display: flex;
  align-items: center;
  gap: 0.75rem; /* 🎯 紧凑布局 */
  min-width: 0;
  max-width: none; /* 🎯 移除固定限制，让内容自适应 */
  overflow: hidden; /* 🎯 确保不溢出 */
}

.ingredient-image {
  flex-shrink: 0;
  width: 3rem; /* 🎯 再缩小一点，留更多空间给按钮 */
  height: 3rem;
  border-radius: 0.75rem;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(251, 191, 36, 0.2);
  transition: all 0.3s ease;
}

.quest-card:hover .ingredient-image {
  border-color: rgba(251, 191, 36, 0.5);
  transform: scale(1.05);
}

.ingredient-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ingredient-placeholder {
  font-size: 1.5rem;
}

.ingredient-info {
  flex: 1 1 auto; /* 🎯 弹性伸缩 */
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.2rem; /* 🎯 减少内部间距 */
  overflow: hidden; /* 🎯 确保不溢出父容器 */
}

.ingredient-name {
  font-size: 1rem;
  font-weight: 800;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
  line-height: 1.3;
}

.ingredient-hint {
  font-size: 0.65rem; /* 🎯 进一步缩小，确保完整显示 */
  color: rgba(251, 191, 36, 0.95);
  font-weight: 600;
  letter-spacing: 0.1px; /* 🎯 更紧凑的字间距 */
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  line-height: 1;
  white-space: nowrap;
  overflow: hidden; /* 🎯 防止溢出 */
  text-overflow: ellipsis; /* 🎯 超长时显示省略号 */
}

.verify-btn {
  flex: 0 0 auto; /* 🎯 固定尺寸，不伸缩 */
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  border: none;
  border-radius: 0.5rem; /* 🎯 稍微减小圆角 */
  padding: 0.5rem 0.85rem; /* 🎯 更紧凑的内边距 */
  font-size: 0.75rem; /* 🎯 稍微缩小字体 */
  font-weight: 800;
  color: #1e293b;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 3px 10px rgba(245, 158, 11, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.15px;
  white-space: nowrap;
  min-width: fit-content;
  margin-left: auto; /* 🎯 确保按钮靠右，不会被挤压 */
}

.verify-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.6);
}

.completed-badge {
  flex: 0 0 auto; /* 🎯 固定尺寸 */
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid #22c55e;
  border-radius: 0.6rem;
  padding: 0.6rem 1rem;
  font-size: 0.8rem;
  font-weight: 800;
  color: #22c55e;
  text-transform: uppercase;
  letter-spacing: 0.2px;
  white-space: nowrap;
  min-width: fit-content;
}

/* 无任务状态 */
.no-tasks {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem 1rem;
  opacity: 0.6;
}

.empty-icon {
  font-size: 3rem;
  filter: grayscale(1);
}

.no-tasks p {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
}

/* 行动按钮 */
.action-btn {
  width: 100%;
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  border: none;
  border-radius: 0.75rem;
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.5);
  color: #1e293b;
  font-weight: 900;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 1rem;
}

.action-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(245, 158, 11, 0.7);
}

.btn-icon {
  font-size: 1.3rem;
}

/* 滚动条 */
.tab-content::-webkit-scrollbar {
  width: 6px;
}

.tab-content::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.3);
  border-radius: 3px;
}

.tab-content::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border-radius: 3px;
  box-shadow: 0 0 8px rgba(251, 191, 36, 0.3);
}

.tab-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
}

/* ===== Market Panel Styling ===== */
.market-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid rgba(251, 191, 36, 0.4);
  margin: -0.5rem -0.5rem 0;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  padding-top: 0;
  flex-shrink: 0;
  /* 确保与 sidebar-header 高度一致 */
  min-height: 80px;
}

.market-icon {
  font-size: 3rem;
  filter: drop-shadow(0 4px 12px rgba(251, 191, 36, 0.6));
  animation: icon-float 3s ease-in-out infinite;
}

.market-title-group h3 {
  font-size: 1.3rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: #fbbf24;
  margin: 0;
  text-shadow: 0 3px 10px rgba(251, 191, 36, 0.7), 0 0 20px rgba(251, 191, 36, 0.3);
  line-height: 1.2;
}

.market-title-group p {
  font-size: 1rem; /* 🎯 0.8rem → 1rem，+25% */
  color: rgba(255, 255, 255, 0.85);
  margin: 0.4rem 0 0;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.market-scout-btn {
  width: 100%;
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  border: none;
  border-radius: 0.75rem;
  padding: 1rem;
  min-height: 58px;
  font-size: 1rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.5);
  color: #1e293b;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.market-scout-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(245, 158, 11, 0.7);
}

.market-scout-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Market Content - 与 quest-content 完全一致的固定高度结构 */
.market-content {
  flex: 1;
  min-height: 0;
  max-height: 100%;  /* 防止超出父容器 */
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  justify-items: center;
  align-items: center;
}

.scout-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.scout-icon {
  font-size: 1.3rem;
}

.scout-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.loading-spinner {
  width: 1.2rem;
  height: 1.2rem;
  border: 3px solid rgba(30, 41, 59, 0.3);
  border-top-color: #1e293b;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error Banner - 新结构 */
.error-banner {
  background: rgba(239, 68, 68, 0.15);
  border: 2px solid rgba(239, 68, 68, 0.4);
  border-radius: 0.75rem;
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  flex-shrink: 0;
  animation: attention-pulse 2s ease-in-out infinite;
  width: fit-content;
}

.error-icon {
  font-size: 1.2rem;
  filter: drop-shadow(0 2px 4px rgba(239, 68, 68, 0.5));
}

.error-text {
  color: #fca5a5;
  font-size: 0.95rem; /* 🎯 0.8rem → 0.95rem，+19% */
  font-weight: 700;
  text-align: center;
}

@keyframes attention-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

/* Stores List - now a child of market-content, so it does not scroll itself */
.stores-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  flex-shrink: 0;
}

.store-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 1rem;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border: 2px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  flex-shrink: 0;
}

.store-card:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(251, 191, 36, 0.6);
  transform: translateX(8px) translateY(-2px);
  box-shadow: 0 6px 16px rgba(251, 191, 36, 0.3);
}

.store-badge {
  flex-shrink: 0;
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  color: #1e293b;
  font-size: 0.75rem;
  font-weight: 800;
  padding: 0.4rem 0.75rem;
  border-radius: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.store-info {
  flex: 1;
  min-width: 0;
}

.store-name {
  font-size: 1.05rem; /* 🎯 0.9rem → 1.05rem，+17% */
  font-weight: 800;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin: 0 0 0.3rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
}

.store-address {
  font-size: 0.85rem; /* 🎯 0.7rem → 0.85rem，+21% */
  color: rgba(251, 191, 36, 0.9);
  font-weight: 600;
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.store-action {
  flex-shrink: 0;
  font-size: 1.5rem;
  filter: drop-shadow(0 2px 4px rgba(251, 191, 36, 0.5));
  transition: all 0.3s ease;
}

.store-card:hover .store-action {
  filter: drop-shadow(0 4px 8px rgba(251, 191, 36, 0.8));
  transform: scale(1.2);
}

/* Empty/Intro States - AAA 游戏大作级别的设计 */
.market-empty, .market-intro {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  text-align: center;
  position: relative;
  background: radial-gradient(circle at center, rgba(251, 191, 36, 0.03), transparent 70%);
}

.empty-icon, .intro-icon {
  font-size: 4.5rem;
  filter: drop-shadow(0 8px 24px rgba(251, 191, 36, 0.4));
  animation: float-subtle 4s ease-in-out infinite, glow-pulse 3s ease-in-out infinite;
  position: relative;
}

@keyframes float-subtle {
  0%, 100% { transform: translateY(0px) scale(1); }
  50% { transform: translateY(-12px) scale(1.05); }
}

@keyframes glow-pulse {
  0%, 100% { filter: drop-shadow(0 8px 24px rgba(251, 191, 36, 0.4)); }
  50% { filter: drop-shadow(0 12px 32px rgba(251, 191, 36, 0.7)) brightness(1.1); }
}

.market-empty p, .market-intro p {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}

.empty-hint {
  font-size: 1rem !important; /* 🎯 0.8rem → 1rem，+25% */
  color: rgba(251, 191, 36, 0.9) !important;
  font-style: italic;
  font-weight: 700 !important;
  padding: 0.6rem 1.2rem;
  background: rgba(251, 191, 36, 0.1);
  border-radius: 0.5rem;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

/* ===== MarketFind Integration Styling (Old - Keep for compatibility) ===== */
.tab-content :deep(.market-game-hub) {
  padding: 0 !important;
  background: transparent !important;
  min-height: auto !important;
}

.tab-content :deep(.quest-header) {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(245, 158, 11, 0.1)) !important;
  border-radius: 1rem !important;
  padding: 1.5rem !important;
  margin-bottom: 1.5rem !important;
  border: 2px solid rgba(251, 191, 36, 0.3) !important;
}

.tab-content :deep(.quest-icon) {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem !important;
}

.tab-content :deep(.shopping-mascot) {
  width: 80px !important;
  height: 80px !important;
  filter: drop-shadow(0 4px 12px rgba(251, 191, 36, 0.6)) !important;
  animation: shopping-float 3s ease-in-out infinite !important;
}

@keyframes shopping-float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-8px) rotate(5deg); }
}

.tab-content :deep(.quest-title) {
  font-size: 1.4rem !important;
  font-weight: 900 !important;
  text-transform: uppercase !important;
  letter-spacing: 1.5px !important;
  color: #fbbf24 !important;
  text-align: center !important;
  margin: 0 0 0.5rem !important;
  text-shadow: 0 3px 10px rgba(251, 191, 36, 0.7), 0 0 20px rgba(251, 191, 36, 0.3) !important;
}

.tab-content :deep(.quest-subtitle) {
  font-size: 1rem !important; /* 🎯 0.8rem → 1rem，+25% */
  color: rgba(255, 255, 255, 0.85) !important;
  text-align: center !important;
  margin: 0 !important;
  font-weight: 700 !important;
  letter-spacing: 0.3px !important;
}

.tab-content :deep(.scout-btn) {
  width: 100% !important;
  background: linear-gradient(135deg, #f59e0b, #fbbf24) !important;
  border: none !important;
  border-radius: 0.75rem !important;
  padding: 1rem !important;
  font-size: 1rem !important;
  font-weight: 900 !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
  cursor: pointer !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.5) !important;
  color: #1e293b !important;
  position: relative !important;
  overflow: hidden !important;
  margin-bottom: 1rem !important;
}

.tab-content :deep(.scout-btn:hover:not(:disabled)) {
  transform: translateY(-3px) !important;
  box-shadow: 0 8px 25px rgba(245, 158, 11, 0.7) !important;
}

.tab-content :deep(.scout-btn:disabled) {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}

.tab-content :deep(.btn-icon) {
  font-size: 1.3rem !important;
  margin-right: 0.5rem !important;
}

.tab-content :deep(.error-message) {
  background: rgba(239, 68, 68, 0.15) !important;
  border: 2px solid rgba(239, 68, 68, 0.4) !important;
  border-radius: 0.75rem !important;
  padding: 0.8rem 1.2rem !important;
  color: #fca5a5 !important;
  font-size: 0.95rem !important; /* 🎯 0.8rem → 0.95rem，+19% */
  font-weight: 700 !important;
  text-align: center !important;
  margin-bottom: 1rem !important;
}

/* Modal adjustments for sidebar context */
.tab-content :deep(.treasure-modal) {
  max-width: 90vw !important;
  max-height: 85vh !important;
}

.tab-content :deep(.treasure-list) {
  max-height: 60vh !important;
}

.tab-content :deep(.treasure-card) {
  background: rgba(255, 255, 255, 0.08) !important;
  border: 2px solid rgba(251, 191, 36, 0.2) !important;
  border-radius: 1rem !important;
  padding: 1rem !important;
  margin-bottom: 1rem !important;
  cursor: pointer !important;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
}

.tab-content :deep(.treasure-card:hover) {
  background: rgba(255, 255, 255, 0.15) !important;
  border-color: rgba(251, 191, 36, 0.6) !important;
  transform: translateX(8px) translateY(-2px) !important;
  box-shadow: 0 6px 16px rgba(251, 191, 36, 0.3) !important;
}

/* ===== Web端RoundlyRecipe组件tuning ===== */

/* 头部区域水平布局tuning */
.game-content-zone.split-layout :deep(.head) {
  display: flex;
  flex-direction: row;
  gap: 1rem;
  align-items: flex-start;
}

.game-content-zone.split-layout :deep(.recipe-image-wrapper) {
  flex-shrink: 0;
  width: 180px;
  height: 180px;
}

.game-content-zone.split-layout :deep(.meta) {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.5rem;
}

.game-content-zone.split-layout :deep(.name) {
  font-size: 1.5rem !important;
  margin: 0 !important;
}

.game-content-zone.split-layout :deep(.tags) {
  gap: 0.5rem;
}

.game-content-zone.split-layout :deep(.tags span) {
  font-size: 0.9rem !important; /* 🎯 0.7rem → 0.9rem，+29% */
  padding: 0.35rem 0.85rem !important;
  font-weight: 700 !important;
}

/* 展开提示tuning */
.game-content-zone.split-layout :deep(.expand-hint) {
  padding: 0.6rem 0.9rem;
  margin-top: 0.75rem;
}

.game-content-zone.split-layout :deep(.hint-main) {
  font-size: 1rem !important; /* 🎯 0.85rem → 1rem，+18% */
  font-weight: 700 !important;
}

.game-content-zone.split-layout :deep(.hint-sub) {
  font-size: 0.85rem !important; /* 🎯 0.7rem → 0.85rem，+21% */
}

/* Recipe Details 区域tuning */
.game-content-zone.split-layout :deep(.recipe-details) {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 0.75rem;
}

.game-content-zone.split-layout :deep(.prep) {
  font-size: 1.15rem !important; /* 🎯 1.05rem → 1.15rem，+10% */
  padding: 1.2rem !important;
  line-height: 1.8 !important; /* 🎯 更大行高 */
}

.game-content-zone.split-layout :deep(.prep h3) {
  font-size: 1.8rem !important; /* 🎯 1.6rem → 1.8rem，+13% */
  margin-bottom: 0.8rem !important;
  font-weight: 900 !important; /* 🎯 更粗字重 */
}

.game-content-zone.split-layout :deep(.prep p) {
  line-height: 1.8 !important;
  font-size: 1.15rem !important; /* 🎯 同步尺寸 */
}

/* Ingredients list tuning - Web端增强 */
.game-content-zone.split-layout :deep(.ing-list) {
  padding: 0.75rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.5), rgba(252, 231, 243, 0.3));
  border-radius: 1rem;
  border: 1px solid rgba(236, 72, 153, 0.15);
}

.game-content-zone.split-layout :deep(.ings-title) {
  font-size: 1.7rem !important; /* 🎯 1.5rem → 1.7rem，+13% */
  margin-bottom: 0.8rem !important;
  font-weight: 900 !important; /* 🎯 更粗字重 */
}

.game-content-zone.split-layout :deep(.ing-grid) {
  gap: 1.2rem !important; /* 🎯 增大间距 */
  justify-content: flex-start;
}

/* Web端 chip 尺寸tuning */
.game-content-zone.split-layout :deep(.chip) {
  --sz: 6.5rem !important; /* 🎯 5.5rem → 6.5rem，+18% 更大尺寸 */
  padding: 0.6rem 0.6rem 0.9rem !important; /* 🎯 增大内边距 */
  border-radius: 1rem !important;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08) !important;
  border: 2px solid rgba(236, 72, 153, 0.12) !important;
  background: linear-gradient(135deg, #ffffff 0%, #fdf2f8 100%) !important;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
}

.game-content-zone.split-layout :deep(.chip:hover) {
  transform: translateY(-6px) scale(1.12) !important;
  box-shadow: 0 12px 28px rgba(236, 72, 153, 0.25) !important;
  border-color: rgba(251, 191, 36, 0.5) !important;
}

.game-content-zone.split-layout :deep(.chip .thumb) {
  border-radius: 0.5rem !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1) !important;
}

.game-content-zone.split-layout :deep(.chip:hover .thumb) {
  filter: drop-shadow(0 0 12px rgba(251, 191, 36, 0.7)) !important;
  transform: scale(1.05) !important;
}

.game-content-zone.split-layout :deep(.chip .name) {
  font-size: 1.15rem !important; /* 🎯 1.05rem → 1.15rem，+10% */
  margin-top: 0.6rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.3px !important;
  line-height: 1.4 !important; /* 🎯 增加行高，更好阅读 */
}

.game-content-zone.split-layout :deep(.chip .qty) {
  right: -10px !important;
  bottom: -10px !important;
  min-width: 2.2rem !important; /* 🎯 2rem → 2.2rem */
  height: 2rem !important; /* 🎯 1.8rem → 2rem */
  font-size: 1.2rem !important; /* 🎯 1.1rem → 1.2rem，+9% */
  font-weight: 900 !important;
  box-shadow: 0 0 0 3px #fff, 0 2px 8px rgba(99, 102, 241, 0.5) !important;
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  line-height: 1 !important; /* 🎯 垂直居中 */
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

/* Instructions 区域tuning */
.game-content-zone.split-layout :deep(.inst) {
  font-size: 1.15rem !important; /* 🎯 1.05rem → 1.15rem，+10% */
  line-height: 1.8 !important;
  padding: 1.2rem !important; /* 🎯 增大内边距 */
}

.game-content-zone.split-layout :deep(.inst h4) {
  font-size: 1.7rem !important; /* 🎯 1.5rem → 1.7rem，+13% */
  margin-bottom: 0.8rem !important;
  font-weight: 900 !important; /* 🎯 更粗字重 */
}

.game-content-zone.split-layout :deep(.inst-box-full) {
  line-height: 1.8 !important;
  padding: 1.2rem !important;
  font-size: 1.15rem !important; /* 🎯 同步尺寸 */
}

/* Kitchen header tuning */
.game-content-zone.split-layout :deep(.kitchen-header) {
  padding: 0.5rem !important;
}

.game-content-zone.split-layout :deep(.kitchen-header h2) {
  font-size: 1.6rem !important;
  text-shadow: 0 2px 8px rgba(190, 24, 93, 0.3) !important;
}

/* Panel 整体tuning - 统一 padding */
.game-content-zone.split-layout :deep(.panel) {
  padding: 1.5rem !important;
  gap: 1rem !important;
  border: 2px solid rgba(236, 72, 153, 0.15) !important;
}

/* 任务区域宽度tuning */
.game-content-zone :deep(.daily-quests) {
  width: 100% !important;
  max-width: none !important;
}

.game-content-zone :deep(.quest-items) {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)) !important;
  gap: 1.2rem !important;
}

.game-content-zone :deep(.quest-item) {
  min-height: 140px !important;
  padding: 0.8rem !important;
}

/* 骰子区域tuning */
.game-content-zone :deep(.main-dice) {
  right: 1.2rem !important;
  top: 1.2rem !important;
  transform: scale(1.05) !important;
}

/* ===== 响应式 - 黄金比例保持一致 ===== */
@media (min-width: 1600px) {
  .game-content-zone.split-layout {
    padding: 2.5rem 3.5rem;
    gap: 2.5rem;
  }
  
  .quest-sidebar {
    width: 480px;
    min-width: 480px;
    max-width: 480px;
  }
  
  .game-content-zone.split-layout .recipe-panel {
    max-width: calc(100% - 530px);
  }
  
  .tab-content {
    padding: 2.5rem;
    gap: 1.75rem;
  }
  
  .sidebar-tabs {
    padding: 1.25rem;
    gap: 0.75rem;
  }
  
  .tab-btn {
    padding: 1.25rem 1rem;
  }
  
  .tab-icon {
    font-size: 2.25rem;
  }
  
  .tab-label {
    font-size: 0.85rem;
  }
  
  .sidebar-header, .market-header {
    padding-bottom: 1.75rem;
  }
  
  .header-icon, .market-icon {
    font-size: 3.5rem;
  }
  
  .header-content h3, .market-title-group h3 {
    font-size: 1.4rem;
  }
  
  .store-card {
    padding: 1.25rem;
  }
  
  .store-name {
    font-size: 1rem;
  }
  
  .store-address {
    font-size: 0.75rem;
  }
}

@media (min-width: 1200px) and (max-width: 1599px) {
  .game-content-zone.split-layout {
    padding: 2rem 2.5rem;
    gap: 2rem;
  }
  
  .quest-sidebar {
    width: 440px;
    min-width: 440px;
    max-width: 440px;
  }
  
  .game-content-zone.split-layout .recipe-panel {
    max-width: calc(100% - 480px);
  }
  
  .tab-content {
    padding: 2rem;
    gap: 1.5rem;
  }
  
  .sidebar-header, .market-header {
    padding-bottom: 1.5rem;
  }
}

@media (min-width: 769px) and (max-width: 1199px) {
  .game-content-zone.split-layout {
    gap: 1.5rem;
  }
  
  .quest-sidebar {
    width: 380px;
    min-width: 380px;
    max-width: 380px;
  }
  
  .game-content-zone.split-layout .recipe-panel {
    max-width: calc(100% - 420px);
  }
  
  .tab-content {
    padding: 1.5rem;
    gap: 1.25rem;
  }
  
  .sidebar-tabs {
    padding: 0.75rem;
    gap: 0.5rem;
  }
  
  .tab-btn {
    padding: 0.75rem 0.5rem;
  }
  
  .tab-icon {
    font-size: 1.75rem;
  }
  
  .tab-label {
    font-size: 0.85rem; /* 🎯 0.7rem → 0.85rem，+21% */
    font-weight: 700;
  }
  
  .sidebar-header, .market-header {
    padding-bottom: 1.25rem;
  }
  
  .header-icon, .market-icon {
    font-size: 2.5rem;
  }
  
  .header-content h3, .market-title-group h3 {
    font-size: 1.1rem;
  }
  
  .store-card {
    padding: 0.9rem;
  }
  
  .store-name {
    font-size: 0.85rem;
  }
  
  /* 中等屏幕 chip 尺寸微调 */
  .game-content-zone.split-layout :deep(.chip) {
    --sz: 5rem !important;
  }
}

/* 移动端 - 单栏布局 */
@media (max-width: 768px) {
  .game-content-zone {
    padding: 1rem;
    flex-direction: column !important;
  }
  
  .recipe-panel {
    max-width: 100% !important;
  }
  
  .game-content-zone :deep(.card) {
    max-width: 100% !important;
  }
  
  .game-content-zone :deep(.quest-items) {
    grid-template-columns: 1fr !important;
  }
  
  /* on mobile the separate task panel is hidden in favour of the one inside RoundlyRecipe */
  .quest-sidebar {
    display: none;
  }
}

/* ===== 游戏化滚动条 ===== */
.game-content-zone::-webkit-scrollbar {
  width: 6px;
}

.game-content-zone::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.3);
  border-radius: 3px;
}

.game-content-zone::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border-radius: 3px;
  box-shadow: 0 0 8px rgba(251, 191, 36, 0.3);
}

.game-content-zone::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
}

/* ===== 底部行动栏 ===== */
.action-bar {
  padding: 1rem 2.5rem;
  background: linear-gradient(135deg, 
    rgba(15, 23, 42, 0.95), 
    rgba(30, 41, 59, 0.9));
  border-top: 2px solid #fbbf24;
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: center;
}

.game-action-btn {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  border: none;
  border-radius: 12px;
  padding: 0.75rem 2rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
  color: #1e293b;
  font-weight: 800;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.game-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.6);
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
}

.action-icon {
  font-size: 1.3rem;
}
</style>
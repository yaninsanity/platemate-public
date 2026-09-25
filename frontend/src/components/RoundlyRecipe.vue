<template>
  <div class="card" :class="[loaded ? 'op' : 'hide', isGolden && 'glow', isDiaryPage && 'diary-layout']">
    <!-- ───────── Loading ───────── -->
    <section v-if="!loaded" class="state">
      <div class="spinner">🎲</div><p>Loading…</p>
    </section>

    <!-- ───────── Error ───────── -->
    <section v-else-if="store.error" class="state err">
      {{ store.error }}<br><button @click="reload">Retry</button>
    </section>

    <!-- ───────── Main content ───────── -->
    <section v-else>
      <!-- Single Dice Control -->
      <div
        v-if="showDice"
        class="main-dice"
        :class="{ shake: shaking }"
        title="Roll for new recipe"
      >
        <GameDice
          :balance="store.dice?.balance || 0"
          :disabled="!canReroll"
          size="xs"
          @roll-start="shaking = true"
          @roll-end="shaking = false"
        />
        <span class="dice-count">{{ store.dice?.balance || 0 }}</span>
      </div>

      <!-- Compact Header - 只在非diary页面显示 -->
      <header v-if="!isDiaryPage" class="kitchen-header">
        <TimeProgressBar
          v-if="bracket"
          class="time-progress"
          :round="bracket.round"
          :rerolled="rerolledFlag"
        />
        <h2>🍳 Step 1: What are we cooking?</h2>
      </header>

      <p v-if="isGolden" class="golden-status">✨ Golden Quest - Free Reroll</p>

      <!-- Recipe panel -->
      <article v-if="recipe" class="panel" :class="{ 'diary-mode': isDiaryPage }">
        <!-- Diary模式：极简显示 -->
        <div v-if="isDiaryPage" class="diary-simple-layout">
          <!-- a single compact row of ingredient icons, shown first -->
          <div v-if="recipe?.ingredients_detail?.length" class="diary-ingredients">
            <div class="diary-ingredients-row">
              <div
                v-for="ingredientInRecipe in recipe.ingredients_detail"
                :key="ingredientInRecipe.id"
                class="diary-ingredient-icon"
                @click="showIngredientDetail(ingredientInRecipe)"
              >
                <div class="ingredient-icon-wrapper">
                  <img
                    v-if="ingredientInRecipe.ingredient.default_picture"
                    :src="fix(ingredientInRecipe.ingredient.default_picture)"
                    :alt="ingredientInRecipe.ingredient.name"
                    class="ingredient-icon-img"
                  />
                  <div v-else class="ingredient-icon-emoji">
                    {{ getIngredientEmoji(ingredientInRecipe.ingredient.name) }}
                  </div>
                </div>
                <span class="ingredient-icon-name">{{ ingredientInRecipe.ingredient.name }}</span>
                <span class="ingredient-icon-quantity">{{ ingredientInRecipe.quantity }}</span>
              </div>
            </div>
          </div>

          <!-- Instructions - 无header，完整显示 -->
          <section v-if="recipe?.instructions" class="diary-instructions">
            <div class="diary-inst-content">
              {{ recipe.instructions }}
            </div>
          </section>
        </div>

        <!-- 非Diary模式：完整版本 -->
        <div v-else>
          <!-- Recipe Header - quest模式下不可点击折叠，其他模式可点击 -->
          <div 
            class="recipe-toggle-header" 
            :class="{ 'no-toggle': isQuestMode }"
            @click="!isQuestMode && (recipeExpanded = !recipeExpanded)"
          >
            <div class="head">
              <!-- Thumbnail -->
              <div
                v-if="recipe.default_picture"
                class="recipe-image-wrapper"
                @click.stop="openImageDialog"
              >
                <img
                  :src="fix(recipe.default_picture)"
                  :alt="recipe.name"
                  class="recipe-image"
                />
                <div class="image-overlay-hint">
                  <svg class="zoom-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="M21 21l-4.35-4.35"/>
                    <path d="M11 8v6"/>
                    <path d="M8 11h6"/>
                  </svg>
                </div>
              </div>

              <!-- Metadata -->
              <div class="meta">
                <h3 class="name">{{ recipe.name }}</h3>
                <div class="tags">
                  <span>{{ recipe.cuisine }}</span>
                  <span>{{ recipe.dish_type }}</span>
                </div>
              </div>
            </div>

            <!-- 🎯 the collapse button is hidden in quest mode and shown elsewhere -->
            <div 
              v-if="!isQuestMode"
              class="expand-hint" 
              :class="{ expanded: recipeExpanded }"
            >
              <div class="hint-icon">{{ recipeExpanded ? '📖' : '🎯' }}</div>
              <div class="hint-text">
                <div class="hint-main">{{ recipeExpanded ? 'Recipe Details' : 'Tap to explore' }}</div>
                <div class="hint-sub">{{ recipeExpanded ? 'Cooking guide expanded' : 'View ingredients & steps' }}</div>
              </div>
              <div class="expand-arrow" :class="{ expanded: recipeExpanded }">▼</div>
            </div>
          </div>

          <!-- Recipe Details (quest模式始终显示，其他模式可折叠) -->
          <transition name="recipe-expand">
            <div v-if="isQuestMode || recipeExpanded" class="recipe-details" :class="{ 'always-visible': isQuestMode }">
              <!-- Preparation - 只在非Diary页面显示 -->
              <section v-if="recipe?.preparation && !isDiaryPage" class="prep">
                <h3>📋 Step 2: Ingredients Preparation</h3>
                <h4>Feel free to adjust ingredients based on your preferences</h4>

                <!-- 任务完成状态的成功提示 -->
                <transition name="success-appear">
                  <div v-if="allTasksCompleted" class="mission-success-banner">
                    <div class="success-icon">🎉</div>
                    <div class="success-content">
                      <div class="success-title">Photo Mission Complete!</div>
                      <div class="success-text">Great capture! Ready to cook</div>
                    </div>
                    <div class="success-sparkle">✨</div>
                  </div>
                </transition>
                
                <p>{{ recipe?.preparation }}</p>
              </section>

              <!-- Ingredients - 非Diary页面显示完整成分列表 -->
              <IngredientList
                v-if="!isDiaryPage"
                class="ing-list"
                :items="formattedIngredients"
                :chipSize="'md'"
                :showName="true"
                :hoverGlow="true"
              />

              <!-- Instructions - 只在非Diary模式显示 -->
              <section v-if="showInstructions && recipe?.instructions && !isDiaryPage" class="inst">
                <h4>🍳 Cooking Instructions</h4>
                <div class="inst-box-full">
                  {{ recipe?.instructions }}
                </div>
              </section>
            </div>
          </transition>
        </div>

        <!-- Single Task Mobile-Optimized Layout -->
        <section v-if="showTasks && tasks.length" class="mobile-quest-workflow">
          <!-- Task Complete State: Full-width highlight -->
          <div v-if="taskStore.allDone" class="victory-layout">
            <div class="victory-header">
              <div class="victory-icon">🎉</div>
              <h3>Mission Complete!</h3>
              <p>{{ myTask?.ingredient.name }} verified successfully</p>
            </div>
            
            <div class="victory-ingredient">
              <div class="ingredient-showcase">
                <img
                  v-if="myTask?.ingredient.default_picture"
                  :src="fix(myTask?.ingredient.default_picture)"
                  :alt="myTask?.ingredient.name"
                  class="ingredient-hero"
                />
                <div v-else class="ingredient-hero-placeholder">🥗</div>
                <div class="success-aura">✨</div>
              </div>
            </div>

            <!-- Highlighted Start Cooking Button -->
            <div class="cooking-action">
              <button @click="goToDiary" class="start-cooking-hero">
                <div class="btn-icon">🍳</div>
                <div class="btn-text">
                  <strong>Start Cooking</strong>
                  <span>Let's create magic!</span>
                </div>
                <div class="btn-arrow">→</div>
              </button>
            </div>
          </div>

          <!-- Task Pending State: Compact single row -->
          <div v-else class="pending-layout">
            <div class="task-header">
              <h4>📸 Ingredient Task</h4>
            </div>

            <!-- gamified notice box, moved here between task-header and single-task-row -->
            <transition name="mission-complete">
              <div v-if="!allTasksCompleted" class="photo-reminder-alert">
                <div class="alert-icon">📸</div>
                <div class="alert-content">
                  <div class="alert-title">Photo Mission!</div>
                  <div class="alert-text">Take a photo of {{ myTask?.ingredient.name }} to complete the task</div>
                </div>
                <div class="alert-pulse">✨</div>
              </div>
            </transition>

            <div class="single-task-row">
              <div class="task-ingredient">
                <div class="ingredient-preview-main">
                  <img
                    v-if="myTask?.ingredient.default_picture"
                    :src="fix(myTask?.ingredient.default_picture)"
                    :alt="myTask?.ingredient.name"
                    class="ingredient-img-main"
                  />
                  <div v-else class="img-placeholder-main">🥗</div>
                </div>
                <div class="task-info">
                  <span class="ingredient-name-main">{{ myTask?.ingredient.name }}</span>
                  <span class="task-hint">Tap to verify →</span>
                </div>
              </div>
              
              <button
                @click="openVerifyModal(myTask || tasks[0])"
                class="verify-btn-main"
                title="Take photo together"
              >
                📸 Verify
              </button>
            </div>
            
            <!-- Market Adventure below when pending -->
            <div class="market-section">
              <MarketFind />
            </div>
          </div>
        </section>

        <!-- Ingredient Verification Modal -->
        <IngredientVerifyModal
          v-if="selectedTask"
          :visible="true"
          :task="selectedTask"
          @cancel="closeVerifyModal"
          @confirm="onVerifyConfirm"
        />
      </article>

      <!-- Quest Start -->
      <!-- <div v-else class="quest-start">
        <div class="start-icon">🎲</div>
        <h3>Ready to Cook?</h3>
        <p>Roll the dice to discover your culinary adventure!</p>
        <button :disabled="shaking || !showDice" @click="roll" class="start-quest-btn">
          {{ shaking ? '🎲 Rolling...' : '🍳 Start Quest' }}
        </button>
      </div> -->
    </section>

    <!-- ───────── Image Zoom Overlay ───────── -->
    <Teleport to="body">
      <transition name="zoom-bounce">
        <div
          v-if="imageDlgOpen"
          class="image-overlay"
          role="dialog"
          aria-labelledby="recipe-img-large"
          @click.self="closeImageDialog"
          @keyup.esc="closeImageDialog"
          tabindex="-1"
        >
          <div class="image-container">
            <img
              :id="'recipe-img-large'"
              :src="fix(recipe?.default_picture || '')"
              :alt="recipe?.name || 'Recipe'"
              class="large-image"
              @click.stop
            />

            <!-- Close bubble -->
            <button class="close-btn" @click="closeImageDialog" aria-label="Close">✕</button>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- ───────── Ingredient Detail Tooltip ───────── -->
    <Teleport to="body">
      <transition name="fade-scale">
        <div
          v-if="ingredientTooltipOpen && selectedIngredient"
          class="ingredient-overlay"
          @click.self="closeIngredientDetail"
          @keyup.esc="closeIngredientDetail"
        >
          <div class="ingredient-detail-card">
            <div class="ingredient-detail-header">
              <div class="ingredient-preview">
                <img
                  v-if="selectedIngredient.ingredient.default_picture"
                  :src="fix(selectedIngredient.ingredient.default_picture)"
                  :alt="selectedIngredient.ingredient.name"
                  class="ingredient-detail-img"
                />
                <div v-else class="ingredient-detail-emoji">
                  {{ getIngredientEmoji(selectedIngredient.ingredient.name) }}
                </div>
              </div>
              <div class="ingredient-detail-info">
                <h3>{{ selectedIngredient.ingredient.name }}</h3>
                <div class="ingredient-quantity">
                  <span class="quantity-label">Need Amount:</span>
                  <span class="quantity-value">{{ selectedIngredient.quantity }}</span>
                </div>
              </div>
              <button class="detail-close-btn" @click="closeIngredientDetail">✕</button>
            </div>
            <div v-if="selectedIngredient.ingredient.info" class="ingredient-description">
              {{ selectedIngredient.ingredient.info }}
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import GameDice         from '@/components/GameDice.vue'
import IngredientList   from '@/components/IngredientList.vue'
import TimeProgressBar  from '@/components/TimeProgressBar.vue'
import MarketFind from '@/components/MarketFind.vue'
import { useRecipesStore } from '@/stores/recipeStore'
import { useTaskStore } from '@/stores/taskStore'
import { useUserStore } from '@/stores/userStore'
import type { RoundBracket, Recipe, RecipeIngredientTask } from '@/models/recipes'
import IngredientVerifyModal from '@/components/IngredientVerifyModal.vue' // new import


/* ─── Props ─────────────────────────────────────── */
const props = withDefaults(
  defineProps<{ showDice?: boolean; showInstructions?: boolean; showTasks?: boolean }>(),
  { showDice: true, showInstructions: true, showTasks: true }
)

/* ─── Store & reactive state ───────────────────── */
const store          = useRecipesStore()
const taskStore      = useTaskStore()
const userStore      = useUserStore()
const router         = useRouter()
const route          = useRoute()
const loaded         = ref(false)
const now            = ref(new Date())
const shaking        = ref(false)
const imageDlgOpen   = ref(false)

const instBox  = ref<HTMLDivElement | null>(null)
const showFade = ref(true)
const dlg      = ref<HTMLDialogElement | null>(null)
const selectedTask = ref<RecipeIngredientTask | null>(null)
const selectedRecipe = ref(-1)

// 根据路由设置默认展开状态
const recipeExpanded = ref(false)

// Diary模式cooking steps展开状态
const instructionsExpanded = ref(false)

// Ingredients弹窗状态
const selectedIngredient = ref<any>(null)
const ingredientTooltipOpen = ref(false)

// 判断是否为diary页面
const isDiaryPage = computed(() => {
  return route.path.includes('/diary') || route.path.includes('/memory')
})

// 🎯 in quest mode the recipe details stay expanded
const isQuestMode = computed(() => {
  return route.path.includes('/roundly-quest') || route.path.includes('/quest')
})

/* ─── Lifecycle ─────────────────────────────────── */
let timer: ReturnType<typeof setInterval> | null = null
onMounted(async () => {
  // 🎯 quest mode is always expanded, so recipeExpanded is unnecessary
  // 因为模板中使用 v-if="isQuestMode || recipeExpanded"
  // 非quest模式下默认收起
  if (!isQuestMode.value) {
    recipeExpanded.value = false
  }
  
  await reload()
  // 🎯 do not call fetchTasks in onMounted; the watcher handles it (immediate: true）
  // 这样避免重复调用
  timer = setInterval(() => (now.value = new Date()), 60_000)
  nextTick(onScroll)
})
onUnmounted(() => timer && clearInterval(timer))


function openVerifyModal(task: RecipeIngredientTask) {
  selectedTask.value = task
}

function closeVerifyModal() {
  selectedTask.value = null
  // 🎯 精准改善：不需要手动刷新，使用缓存机制
  // taskStore内部已经处理了更新逻辑
}

async function onVerifyConfirm() {
  // 🎯 no manual refresh; verifyTask already handles it
  router.push('/diary')
  // 添加成功验证的流畅交互体验
  // if (selectedTask.value) {
  //   // 1. 播放成功音效（如果有的话）
  //   console.log('🎉 Ingredient verified successfully!', selectedTask.value.ingredient.name)
    
  //   // 2. 更新任务状态为已验证
  //   selectedTask.value.is_verified = true
    
  //   // 3. 延迟关闭模态框，让用户看到成功状态
  //   setTimeout(() => {
  //     closeVerifyModal()
      
  //     // 4. 刷新数据确保UI同步
  //     reload()
      
  //     // 5. 如果所有任务完成，显示庆祝动画
  //     if (allTasksCompleted.value) {
  //       console.log('🏆 All tasks completed! Mission accomplished!')
  //       // 可以添加全局庆祝效果
  //     }
  //   }, 1500) // 1.5秒延迟让用户享受成功反馈
  // } else {
  //   closeVerifyModal()
  // }
}

/* ─── Computed ──────────────────────────────────── */
const bracket = computed((): RoundBracket | null => {
  return store.currentBracket
})

const recipe = computed((): Recipe | null => {
  return store.currentBracket?.recipe || null
})

const tasks = computed((): RecipeIngredientTask[] => {
  return store.currentBracket?.ingredient_tasks || []
})

const myTask = computed((): RecipeIngredientTask | null => {
  return taskStore.userPendingTasks[0] || null
})

const allTasksCompleted = computed((): boolean => {
  return taskStore.allDone
})

const formattedIngredients = computed(() => {
  const recipe = store.currentBracket?.recipe
  if (!recipe?.ingredients_detail) return []
  
  return recipe.ingredients_detail.map((ing: any) => ({
    id: ing.ingredient.id,
    name: ing.ingredient.name,
    default_picture: ing.ingredient.default_picture,
    info: ing.ingredient.info || '',
    quantity: ing.quantity
  }))
})

const isGolden = computed((): boolean => {
  const b = bracket.value
  return !!b && (b as any).is_golden
})

const rerolledFlag = computed((): boolean => {
  const b = bracket.value
  return !!b && (b as any).rerolled
})

const canReroll = computed((): boolean => {
  const b = bracket.value
  if (!b) return false
  const dice = store.dice
  if (!dice) return false
  if (dice.balance <= 0 && !(b as any).is_golden) return false
  return true
})

watch(
  () => recipe.value?.id,
  (newId) => {
    if (newId && newId !== selectedRecipe.value) {
      selectedRecipe.value = newId
      taskStore.fetchTasks(newId)
    }
  },
  { immediate: true } // This makes it run on component creation
)

// Ingredient emoji mapping function
function getIngredientEmoji(name: string): string {
  const lowerName = name.toLowerCase()
  
  // 蔬菜类
  if (lowerName.includes('tomato')) return '🍅'
  if (lowerName.includes('onion')) return '🧅'
  if (lowerName.includes('carrot')) return '🥕'
  if (lowerName.includes('potato')) return '🥔'
  if (lowerName.includes('pepper') || lowerName.includes('bell')) return '🫑'
  if (lowerName.includes('broccoli')) return '🥦'
  if (lowerName.includes('corn')) return '🌽'
  if (lowerName.includes('eggplant')) return '🍆'
  if (lowerName.includes('lettuce') || lowerName.includes('salad')) return '🥬'
  if (lowerName.includes('cucumber')) return '🥒'
  if (lowerName.includes('avocado')) return '🥑'
  if (lowerName.includes('mushroom')) return '🍄'
  
  // 水果类
  if (lowerName.includes('apple')) return '🍎'
  if (lowerName.includes('banana')) return '🍌'
  if (lowerName.includes('orange')) return '🍊'
  if (lowerName.includes('lemon')) return '🍋'
  if (lowerName.includes('lime')) return '🍋‍🟩'
  if (lowerName.includes('grape')) return '🍇'
  if (lowerName.includes('strawberry')) return '🍓'
  if (lowerName.includes('peach')) return '🍑'
  if (lowerName.includes('pineapple')) return '🍍'
  if (lowerName.includes('mango')) return '🥭'
  
  // 肉类
  if (lowerName.includes('chicken') || lowerName.includes('poultry')) return '🐔'
  if (lowerName.includes('beef') || lowerName.includes('steak')) return '🥩'
  if (lowerName.includes('pork') || lowerName.includes('bacon')) return '🥓'
  if (lowerName.includes('fish') || lowerName.includes('salmon')) return '🐟'
  if (lowerName.includes('shrimp') || lowerName.includes('prawn')) return '🦐'
  if (lowerName.includes('crab')) return '🦀'
  if (lowerName.includes('lobster')) return '🦞'
  
  // 谷物豆类
  if (lowerName.includes('rice')) return '🍚'
  if (lowerName.includes('bread') || lowerName.includes('wheat')) return '🍞'
  if (lowerName.includes('pasta') || lowerName.includes('noodle')) return '🍝'
  if (lowerName.includes('bean') || lowerName.includes('lentil')) return '🫘'
  if (lowerName.includes('corn')) return '🌽'
  
  // 乳制品
  if (lowerName.includes('milk')) return '🥛'
  if (lowerName.includes('cheese')) return '🧀'
  if (lowerName.includes('butter')) return '🧈'
  if (lowerName.includes('egg')) return '🥚'
  if (lowerName.includes('yogurt')) return '🥛'
  
  // 调料香料
  if (lowerName.includes('salt')) return '🧂'
  if (lowerName.includes('pepper')) return '🌶️'
  if (lowerName.includes('garlic')) return '🧄'
  if (lowerName.includes('ginger')) return '🫚'
  if (lowerName.includes('oil') || lowerName.includes('olive')) return '🫒'
  if (lowerName.includes('honey')) return '🍯'
  if (lowerName.includes('sugar')) return '🍬'
  
  // 饮品
  if (lowerName.includes('coffee')) return '☕'
  if (lowerName.includes('tea')) return '🍵'
  if (lowerName.includes('wine')) return '🍷'
  if (lowerName.includes('beer')) return '🍺'
  if (lowerName.includes('water')) return '💧'
  
  // 默认
  return '🥗'
}

/* ─── Methods ───────────────────────────────────── */
async function reload() {
  loaded.value = false
  await store.loadBrackets()
  loaded.value = true
}

async function roll() {
  if (!canReroll.value) return
  await store.reroll()
  await reload()
}

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

function openImageDialog() {
  imageDlgOpen.value = true
}

function closeImageDialog() {
  imageDlgOpen.value = false
}

function goToDiary() {
  // 🎯 no preload needed; the diary page loads what it wants
  router.push('/diary')
}

function showIngredientDetail(ingredientInRecipe: any) {
  selectedIngredient.value = ingredientInRecipe
  ingredientTooltipOpen.value = true
}

function closeIngredientDetail() {
  selectedIngredient.value = null
  ingredientTooltipOpen.value = false
}

function onScroll() {
  // Handle scroll fade
}
</script>

<style scoped>
/* ───── Card container - AAA游戏大作统一设计 ─────────────────────────── */
.card {
  width: 100%;
  max-width: 100%;
  height: calc(100vh - 4rem);  /* 固定高度，和右侧侧边栏完全一致 */
  max-height: calc(100vh - 4rem);
  margin: 0;
  padding: 0;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.95));
  border-radius: 1rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05);
  position: sticky;
  border: 2px solid rgba(251, 191, 36, 0.4);
  backdrop-filter: blur(20px);
  display: flex;
  flex-direction: column;
  overflow-y: scroll;
}

/* ===== 游戏化滚动条 ===== */
.card::-webkit-scrollbar {
  width: 6px;
}

.card::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.3);
  border-radius: 3px;
}

.card::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border-radius: 3px;
  box-shadow: 0 0 8px rgba(251, 191, 36, 0.3);
}

.card::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
}

/* Diary模式下的cardtuning */
.card.diary-layout {
  max-width: 100%;
  width: 100%;
  height: auto;
  max-height: none;
  position: relative;
  padding: 0.2rem;
}
.op{opacity:1;transition:.3s ease}.hide{opacity:0;transform:translateY(1rem);transition:.3s ease}
.glow{box-shadow:0 0 20px rgba(251,191,36,.4), 0 8px 25px rgba(236,72,153,.15)}

/* ───── Kitchen Header - AAA游戏大作级别标题 ──────────────────── */
.kitchen-header {
  text-align: center;
  padding: 1.5rem 1rem 1rem;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.3));
  border-bottom: 2px solid rgba(251, 191, 36, 0.4);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  margin: 0;
  flex-shrink: 0;
  position: relative;
}

.kitchen-header::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(251, 191, 36, 0.6), transparent);
  animation: shimmer 3s ease-in-out infinite;
}

.kitchen-header h2 {
  text-align: center;
  font-size: 1.5rem;
  font-weight: 900;
  color: #fbbf24;
  margin: 0.5rem 0 0.5rem;
  text-shadow: 0 3px 10px rgba(251, 191, 36, 0.7), 0 0 20px rgba(251, 191, 36, 0.3);
  letter-spacing: 0.5px;
  line-height: 1.3;
  text-transform: uppercase;
  position: relative;
  animation: title-glow 3s ease-in-out infinite;
}

@keyframes title-glow {
  0%, 100% { text-shadow: 0 3px 10px rgba(251, 191, 36, 0.7), 0 0 20px rgba(251, 191, 36, 0.3); }
  50% { text-shadow: 0 4px 15px rgba(251, 191, 36, 0.9), 0 0 30px rgba(251, 191, 36, 0.5); }
}

.time-progress {
  margin: 0 auto 0.5rem;
  max-width: 100%; /* 🎯 从16rem改为100%，充分利用空间 */
  width: 100%; /* 🎯 确保占满容器宽度 */
  padding: 0 1rem; /* 🎯 留出左右边距 */
  box-sizing: border-box;
}

.golden-status {
  font-size: 0.8rem;
  font-weight: 700;
  color: #fbbf24;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.15));
  padding: 0.5rem 1rem;
  border-radius: 0.75rem;
  text-align: center;
  margin: 0.5rem 1rem;
  border: 2px solid rgba(251, 191, 36, 0.5);
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.3);
  letter-spacing: 0.5px;
}

/* ───── Main Dice (Top Right) ──────────────────── */
.main-dice{position:absolute;top:-0.2rem;right:-0.2rem;width:70px;height:76px;border:none;display:flex;flex-direction:column;justify-content:center;align-items:center;transition:all .2s ease;z-index:10}
.main-dice:hover:not(:disabled){transform:scale(1.05);}
.dice-count{position:absolute;bottom:10px;right:8px;font-size:.45rem;font-weight:700;background:linear-gradient(135deg, #7c3aed, #a855f7);color:#fff;width:16px;height:16px;border-radius:50%;display:flex;justify-content:center;align-items:center;border:1px solid #fff}
.shake{animation:diceShake .4s ease-in-out infinite}@keyframes diceShake{0%,100%{transform:rotate(0deg)}25%{transform:rotate(-3deg)}75%{transform:rotate(3deg)}}

/* ───── Panel & thumbnail - 可滚动内容区域 ───────────────────────── */
.panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  word-wrap: break-word;
  background: transparent;
  border-radius: 0;
  padding: 2rem;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
}

/* Diary模式下的paneltuning */
.panel.diary-mode {
  width: 100%;
  max-width: none;
  padding: 0.3rem;
  gap: 0.3rem;
  overflow: visible;
  flex: none;
  background: linear-gradient(135deg, rgba(255,255,255,.6) 0%, rgba(252,231,243,.4) 100%);
  border-radius: 0.8rem;
  border: 1px solid rgba(236,72,153,.1);
}

/* ───── Diary模式样式 - tuninglayout空间分配 ───────────────────── */
.diary-simple-layout {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  height: 100%;
}

.diary-instructions {
  flex: 1;
  order: 2;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.diary-inst-content {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%);
  border: 2px solid rgba(139, 92, 246, 0.2);
  border-radius: 0.8rem;
  padding: 0.8rem;
  font-size: 0.8rem;
  line-height: 1.7;
  color: #7c3aed;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1);
  white-space: pre-wrap;
  overflow-y: auto;
  flex: 1;
  min-height: 200px;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* 滚动条样式 */
.diary-inst-content::-webkit-scrollbar {
  width: 6px;
}

.diary-inst-content::-webkit-scrollbar-track {
  background: rgba(139, 92, 246, 0.1);
  border-radius: 2px;
}

.diary-inst-content::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.3);
  border-radius: 2px;
}

.diary-inst-content::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.5);
}

/* ───── Diarycompact ingredient icon row, leaving room for the instructions ─────────────── */
.diary-ingredients {
  order: 1;
  flex-shrink: 0;
  margin-bottom: 0.2rem;
}

.diary-ingredients-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.15rem;
  padding: 0.2rem 0.35rem;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.06) 0%, rgba(124, 58, 237, 0.03) 100%);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 0.5rem;
  margin: 0;
  justify-content: flex-start;
  align-items: center;
  overflow: visible;
  flex-shrink: 0;
  width: 100%;
  min-height: auto;
}

.diary-ingredient-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.03rem;
  padding: 0.08rem;
  min-width: 1.3rem;
  flex-shrink: 0;
  transition: all 0.2s ease;
  cursor: pointer;
  border-radius: 0.2rem;
}

.diary-ingredient-icon:hover {
  transform: translateY(-2px) scale(1.05);
  background: rgba(139, 92, 246, 0.1);
}

.diary-ingredient-icon:active {
  transform: translateY(-1px) scale(1.02);
}

.ingredient-icon-img {
  width: 16px;
  height: 16px;
  border-radius: 0.25rem;
  object-fit: cover;
  border: 1px solid rgba(139, 92, 246, 0.25);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 1px 2px rgba(139, 92, 246, 0.1);
}

.ingredient-icon-emoji {
  font-size: 0.8rem;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(124, 58, 237, 0.08) 100%);
  border-radius: 0.25rem;
  border: 1px solid rgba(139, 92, 246, 0.25);
  box-shadow: 0 1px 2px rgba(139, 92, 246, 0.1);
}

.ingredient-icon-name {
  font-size: 0.32rem;
  color: #7c3aed;
  font-weight: 600;
  text-align: center;
  line-height: 0.85;
  max-width: 1.3rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ───── Recipe Toggle Header ───────────────────── */
.recipe-toggle-header {
  cursor: pointer;
  transition: all 0.25s ease;
  border-radius: 0.6rem;
  padding: 0.2rem;
  margin: -0.2rem;
}

.recipe-toggle-header:hover {
  background: rgba(236, 72, 153, 0.05);
  transform: translateY(-1px);
}

/* 🎯 精准改善：quest模式下禁用折叠功能 */
.recipe-toggle-header.no-toggle {
  cursor: default;
  pointer-events: none;
}

.recipe-toggle-header.no-toggle:hover {
  background: transparent;
  transform: none;
}

/* Recipe Header - 统一配色 */
.head {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 1rem;
  border: 2px solid rgba(251, 191, 36, 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* ───── 游戏化展开提示 ───────────────────── */
.expand-hint {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
  border: 1px solid rgba(124, 58, 237, 0.2);
  border-radius: 0.5rem;
  padding: 0.3rem 0.5rem;
  margin-top: 0.3rem;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

/* Quest页面的特殊样式 */
.expand-hint.quest-mode {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%);
  border-color: rgba(34, 197, 94, 0.2);
}

.recipe-toggle-header:hover .expand-hint {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%);
  border-color: rgba(124, 58, 237, 0.3);
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.1);
  transform: translateY(-1px);
}

/* 展开状态的高亮 */
.expand-hint.expanded {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%);
  border-color: rgba(124, 58, 237, 0.3);
  box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.1);
}

.hint-icon {
  font-size: 1rem;
  animation: icon-pulse 2s ease-in-out infinite;
  transition: all 0.25s ease;
}

/* 根据状态变化图标动画 */
.expand-hint:not(.expanded) .hint-icon {
  animation: attention-pulse 2s ease-in-out infinite;
}

@keyframes icon-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes attention-pulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.15); opacity: 1; }
}

.hint-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.hint-main {
  font-size: 0.7rem;
  font-weight: 700;
  color: #cbb7ed;
  line-height: 1;
}

.hint-sub {
  font-size: 0.6rem;
  color: rgb(254, 136, 183);
  opacity: 0.8;
  font-style: italic;
  line-height: 1;
}

.expand-arrow {
  font-size: 0.8rem;
  color: #7c3aed;
  transition: transform 0.25s ease;
  font-weight: 700;
}

.expand-arrow.expanded {
  transform: rotate(180deg);
}

/* ───── Recipe Details 展开动画 ───────────────── */
.recipe-expand-enter-active,
.recipe-expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.recipe-expand-enter-from,
.recipe-expand-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-10px);
}

.recipe-expand-enter-to,
.recipe-expand-leave-from {
  opacity: 1;
  max-height: 1000px;
  transform: translateY(0);
}

.recipe-details {
  padding-top: 0.3rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

/* 🎯 in quest mode recipe-details stays visible; there is room for it */
.recipe-details.always-visible {
  max-height: none !important;
  opacity: 1 !important;
  transform: translateY(0) !important;
  overflow: visible !important;
  padding-bottom: 1rem;
}

.recipe-image-wrapper{position:relative;width:4rem;height:4rem;border-radius:.6rem;overflow:hidden;cursor:pointer;flex-shrink:0;transition:all .25s ease;border:2px solid rgba(236,72,153,.1)}
.recipe-image-wrapper:hover{transform:translateY(-2px) scale(1.04);box-shadow:0 8px 20px rgba(236,72,153,.2);border-color:rgba(236,72,153,.3)}
.recipe-image{width:100%;height:100%;object-fit:cover}

/* Hover hint */
.image-overlay-hint{position:absolute;inset:0;background:rgba(0,0,0,.35);display:flex;justify-content:center;align-items:center;opacity:0;transition:opacity .25s ease;backdrop-filter:blur(1.2px)}
.recipe-image-wrapper:hover .image-overlay-hint{opacity:1}
.zoom-icon{width:1.6rem;height:1.6rem;color:#fff;stroke-width:2;animation:pulse-light 1.4s infinite}
@keyframes pulse-light{0%,100%{transform:scale(.82);opacity:.8}50%{transform:scale(1);opacity:1}}

/* Recipe Meta - 统一配色 */
.meta {
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 1.3rem;
  font-weight: 800;
  margin: 0 0 0.75rem;
  color: #fbbf24;
  line-height: 1.3;
  text-shadow: 0 2px 8px rgba(251, 191, 36, 0.5);
  letter-spacing: 0.5px;
}

.tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0;
}

.tags span {
  font-size: 0.65rem;
  font-weight: 700;
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  border: 1px solid rgba(251, 191, 36, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ───── Preparation & instructions - AAA游戏大作级别 Step 2 ─────────────── */
.prep {
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(251, 191, 36, 0.3);
  border-radius: 1rem;
  padding: 1.5rem;
  margin: 0 0 1rem 0; /* 🎯 增加底部间距，确保完整显示 */
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  position: relative;
  overflow: visible; /* 🎯 改为visible，确保内容不被截断 */
  min-height: fit-content; /* 🎯 确保高度自适应内容 */
}

.prep::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(251, 191, 36, 0.6) 30%, 
    rgba(251, 191, 36, 0.8) 50%, 
    rgba(251, 191, 36, 0.6) 70%, 
    transparent
  );
  animation: prep-shimmer 3s ease-in-out infinite;
}

@keyframes prep-shimmer {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.prep h4 {
  font-weight: 700;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: rgba(251, 191, 36, 0.9);
  line-height: 1.3;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.prep h3 {
  text-align: center;
  font-size: 1.8rem;
  font-weight: 900;
  margin-bottom: 1.5rem;
  color: #fbbf24;
  line-height: 1.2;
  text-shadow: 0 3px 10px rgba(251, 191, 36, 0.7), 0 0 20px rgba(251, 191, 36, 0.3);
  text-transform: uppercase;
  letter-spacing: 1px;
  position: relative;
  padding-bottom: 1rem;
  animation: step-glow 3s ease-in-out infinite;
}

.prep h3::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(251, 191, 36, 0.6), transparent);
}

@keyframes step-glow {
  0%, 100% { 
    text-shadow: 0 3px 10px rgba(251, 191, 36, 0.7), 0 0 20px rgba(251, 191, 36, 0.3);
  }
  50% { 
    text-shadow: 0 4px 15px rgba(251, 191, 36, 0.9), 0 0 30px rgba(251, 191, 36, 0.5);
  }
}

.prep p {
  margin-top: 0;
  line-height: 1.6;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

/* ───── Ingredients List - 统一配色 ─────────────── */
.ing-list {
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(251, 191, 36, 0.2);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

/* ───── 游戏化重要提醒框 ─────────────── */
.photo-reminder-alert {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
  border: 2px solid rgba(245, 158, 11, 0.4);
  border-radius: 0.8rem;
  padding: 0.5rem 0.6rem;
  margin: 0.4rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
  animation: attention-glow 3s ease-in-out infinite;
}

/* 任务完成成功横幅 */
.mission-success-banner {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: 2px solid rgba(16, 185, 129, 0.4);
  border-radius: 0.8rem;
  padding: 0.5rem 0.6rem;
  margin: 0.4rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  animation: success-celebration 2s ease-in-out;
}

@keyframes attention-glow {
  0%, 100% { 
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    transform: scale(1);
  }
  50% { 
    box-shadow: 0 6px 20px rgba(245, 158, 11, 0.5), 0 0 0 2px rgba(245, 158, 11, 0.2);
    transform: scale(1.02);
  }
}

@keyframes success-celebration {
  0% { 
    transform: scale(0.8);
    opacity: 0;
  }
  30% { 
    transform: scale(1.05);
    opacity: 1;
  }
  50% { 
    transform: scale(0.98);
  }
  100% { 
    transform: scale(1);
    opacity: 1;
  }
}

.alert-icon, .success-icon {
  font-size: 1.4rem;
  z-index: 2;
}

.alert-content, .success-content {
  flex: 1;
  z-index: 2;
}

.alert-title, .success-title {
  font-size: 0.8rem;
  font-weight: 800;
  color: #fff;
  line-height: 1.1;
  margin-bottom: 0.1rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.alert-text, .success-text {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.2;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.alert-pulse, .success-sparkle {
  font-size: 1rem;
  z-index: 2;
}

/* ───── Cooking Instructions - 统一配色 ─────────────── */
.inst {
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(251, 191, 36, 0.2);
  border-radius: 1rem;
  padding: 1.5rem;
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.inst h4 {
  font-size: 1rem;
  font-weight: 800;
  margin-bottom: 1rem;
  color: #fbbf24;
  line-height: 1.3;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 6px rgba(251, 191, 36, 0.5);
}

/* 完整指令显示 */
.inst-box-full {
  padding: 1rem;
  font-size: 0.9rem;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.9);
  white-space: pre-wrap;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.75rem;
  border: 1px solid rgba(251, 191, 36, 0.2);
  font-weight: 500;
}

/* Diary模式下的指令重点显示 */
.inst-box-full.diary-focused {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%);
  border: 2px solid rgba(139, 92, 246, 0.2);
  padding: 0.6rem;
  font-size: 0.8rem;
  line-height: 1.6;
  color: #7c3aed;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1);
}

/* ───── Mobile Optimized Single Task Layout ─────────────────────────────── */
.mobile-quest-workflow{background:linear-gradient(135deg, rgba(255,255,255,.6) 0%, rgba(252,231,243,.4) 100%);border-radius:.8rem;padding:.4rem;margin:.3rem 0;backdrop-filter:blur(10px);border:1px solid rgba(236,72,153,.1)}

/* Victory State: Compact celebration */
.victory-layout{text-align:center;padding:.3rem 0}

.victory-header{margin-bottom:.5rem}
.victory-icon{font-size:1.8rem;margin-bottom:.1rem;animation:victory-bounce 1s ease-in-out infinite alternate}
@keyframes victory-bounce{0%{transform:scale(1) rotate(0deg)}100%{transform:scale(1.1) rotate(5deg)}}

.victory-header h3{font-size:.95rem;font-weight:800;color:#059669;margin:.1rem 0;text-shadow:0 1px 3px rgba(5,150,105,.2)}
.victory-header p{font-size:.7rem;color:#831843;margin:0;font-weight:600}

.victory-ingredient{margin:.5rem 0 .8rem;display:flex;justify-content:center}
.ingredient-showcase{position:relative;width:60px;height:60px;border-radius:.8rem;overflow:hidden;box-shadow:0 6px 20px rgba(34,197,94,.25);border:2px solid rgba(34,197,94,.3)}
.ingredient-hero{width:100%;height:100%;object-fit:cover}
.ingredient-hero-placeholder{width:100%;height:100%;display:flex;justify-content:center;align-items:center;background:linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);font-size:1.5rem}
.success-aura{position:absolute;top:-3px;right:-3px;font-size:1rem;animation:aura-pulse 1.5s ease-in-out infinite}
@keyframes aura-pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.3)}}

/* Compact Hero Start Cooking Button */
.cooking-action{margin-top:.5rem}
.start-cooking-hero{background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%, #15803d 100%);color:#fff;border:none;border-radius:.6rem;padding:.6rem .8rem;width:100%;display:flex;align-items:center;justify-content:space-between;cursor:pointer;transition:all .3s ease;box-shadow:0 3px 12px rgba(34,197,94,.3);position:relative;overflow:hidden}

.start-cooking-hero:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(34,197,94,.4)}
.start-cooking-hero:active{transform:translateY(0)}

.btn-icon{font-size:1.1rem;z-index:2}
.btn-text{flex:1;text-align:center;z-index:2}
.btn-text strong{display:block;font-size:.8rem;font-weight:700;margin-bottom:.05rem}
.btn-text span{font-size:.6rem;opacity:.9;font-weight:500}
.btn-arrow{font-size:1rem;font-weight:700;z-index:2;animation:arrow-flow 2s ease-in-out infinite}
@keyframes arrow-flow{0%,100%{transform:translateX(0)}50%{transform:translateX(3px)}}

/* Pending State: Ultra-compact single row */
.pending-layout{padding:.1rem 0}
.task-header{margin-bottom:.4rem;text-align:center}
.task-header h4{font-size:1.3rem;font-weight:700;color:#be185d;margin:0}

.single-task-row{display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg, rgba(255,255,255,.8) 0%, rgba(252,231,243,.6) 100%);border:1px solid rgba(236,72,153,.15);border-radius:.5rem;padding:.4rem;margin-bottom:.6rem;transition:all .2s ease}
.single-task-row:hover{transform:translateY(-1px);box-shadow:0 3px 10px rgba(236,72,153,.15)}

.task-ingredient{display:flex;align-items:center;gap:.4rem;flex:1;min-width:0}
.ingredient-preview-main{width:32px;height:32px;border-radius:.5rem;overflow:hidden;flex-shrink:0;box-shadow:0 2px 6px rgba(236,72,153,.15)}
.ingredient-img-main{width:100%;height:100%;object-fit:cover}
.img-placeholder-main{width:100%;height:100%;display:flex;justify-content:center;align-items:center;background:rgba(236,72,153,.1);font-size:.8rem}

.task-info{flex:1;min-width:0}
.ingredient-name-main{display:block;font-size:.75rem;font-weight:700;color:#be185d;line-height:1.1;margin-bottom:.05rem}
.task-hint{font-size:.6rem;color:#831843;opacity:.7;font-style:italic}

.verify-btn-main{background:linear-gradient(135deg, #ec4899, #db2777);color:#fff;border:none;border-radius:.4rem;padding:.4rem 1rem;font-size:1rem;font-weight:600;cursor:pointer;transition:all .2s ease;flex-shrink:0;box-shadow:0 2px 6px rgba(249,115,22,.2)}
.verify-btn-main:hover{transform:scale(1.05);box-shadow:0 3px 10px rgba(249,115,22,.3)}

.diary-button {
  display: flex;
  justify-content: center;
  padding: 0.4rem 0;
}

.diary-btn {
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
  color: #fff;
  border: none;
  border-radius: 0.4rem;
  padding: 0.4rem 1.2rem;
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(249, 115, 22, 0.2);
  white-space: nowrap;
  text-align: center;
}

.diary-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 3px 10px rgba(249, 115, 22, 0.3);
}

.diary-btn:active {
  transform: scale(0.98);
}

.market-section{margin-top:.4rem;padding-top:.4rem;border-top:1px solid rgba(236,72,153,.1)}

/* ───── Quest Start ─────────────────────────────── */
.quest-start{display:flex;flex-direction:column;align-items:center;gap:.5rem;padding:1rem;background:linear-gradient(135deg, rgba(255,255,255,.8) 0%, rgba(252,231,243,.6) 100%);border-radius:.8rem;margin:.5rem 0;text-align:center;border:1px solid rgba(236,72,153,.15)}
.start-icon{font-size:2rem;margin-bottom:.2rem;animation:bounce 2s infinite}@keyframes bounce{0%,20%,50%,80%,100%{transform:translateY(0)}40%{transform:translateY(-8px)}60%{transform:translateY(-4px)}}
.quest-start h3{font-size:.85rem;font-weight:700;color:#be185d;margin:0}
.quest-start p{font-size:.65rem;color:#831843;margin:.2rem 0 .5rem 0;line-height:1.3}
.start-quest-btn{background:linear-gradient(135deg, #ec4899 0%, #be185d 100%);color:#fff;padding:.5rem 1rem;border-radius:.6rem;font-weight:700;font-size:.7rem;border:none;transition:all .2s ease;box-shadow:0 3px 8px rgba(236,72,153,.2)}
.start-quest-btn:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 5px 12px rgba(236,72,153,.3)}
.start-quest-btn:disabled{opacity:.6;background:linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%)}

/* ───── Image overlay (glass) ──────────────────── */
.image-overlay{position:fixed;inset:0;display:flex;justify-content:center;align-items:center;background:rgba(255,255,255,.16);backdrop-filter:blur(6px) saturate(140%);z-index:1000}
.image-container{position:relative;display:flex;justify-content:center;align-items:center}
.large-image{max-width:88vw;max-height:88vh;object-fit:contain;border-radius:.9rem;box-shadow:0 20px 45px rgba(0,0,0,.25)}

/* Close bubble */
.close-btn{position:absolute;top:8px;right:8px;width:38px;height:38px;border:none;border-radius:50%;background:linear-gradient(135deg,#a78bfa 0%,#fb7185 100%);color:#fff;font-size:1.25rem;font-weight:700;display:flex;justify-content:center;align-items:center;line-height:1;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,.22);transition:transform .18s ease, box-shadow .18s ease}
.close-btn:hover{transform:scale(1.1);box-shadow:0 6px 16px rgba(0,0,0,.28)}

/* Overlay entry / exit */
.zoom-bounce-enter-active,.zoom-bounce-leave-active{transition:opacity .28s ease, transform .28s cubic-bezier(.34,1.56,.64,1)}
.zoom-bounce-enter-from,.zoom-bounce-leave-to{opacity:0;transform:scale(.7)}

/* ───── Ingredient Detail Overlay ──────────────────── */
.ingredient-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  z-index: 1001;
}

.ingredient-detail-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(252, 231, 243, 0.9) 100%);
  border-radius: 1rem;
  padding: 1rem;
  max-width: 280px;
  width: 90vw;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(139, 92, 246, 0.2);
  backdrop-filter: blur(20px);
}

.ingredient-detail-header {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.8rem;
}

.ingredient-preview {
  flex-shrink: 0;
}

.ingredient-detail-img {
  width: 60px;
  height: 60px;
  border-radius: 0.8rem;
  object-fit: cover;
  border: 2px solid rgba(139, 92, 246, 0.3);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.ingredient-detail-emoji {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(124, 58, 237, 0.1) 100%);
  border-radius: 0.8rem;
  border: 2px solid rgba(139, 92, 246, 0.3);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.ingredient-detail-info {
  flex: 1;
  min-width: 0;
}

.ingredient-detail-info h3 {
  font-size: 1rem;
  font-weight: 700;
  color: #7c3aed;
  margin: 0 0 0.4rem 0;
  line-height: 1.2;
}

.ingredient-quantity {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.quantity-label {
  font-size: 0.7rem;
  color: #6b7280;
  font-weight: 600;
}

.quantity-value {
  font-size: 0.8rem;
  font-weight: 700;
  color: #7c3aed;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%);
  padding: 0.2rem 0.4rem;
  border-radius: 0.4rem;
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.detail-close-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  color: #fff;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
}

.detail-close-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);
}

.ingredient-description {
  font-size: 0.75rem;
  color: #6b7280;
  line-height: 1.5;
  padding: 0.6rem;
  background: rgba(139, 92, 246, 0.05);
  border-radius: 0.6rem;
  border: 1px solid rgba(139, 92, 246, 0.1);
}

/* Fade scale transition */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.3s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* ───── States ─────────────────────────────────── */
.state{display:flex;flex-direction:column;align-items:center;gap:.48rem;padding:1.7rem 0;color:#be185d}
.spinner{font-size:1.4rem;animation:spin 2s linear infinite}@keyframes spin{to{transform:rotate(1turn)}}
.err{background:linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);color:#dc2626;border:1px solid rgba(220,38,38,.2);border-radius:.7rem;padding:.75rem 1rem;text-align:center}
.state button{background:#ef4444;color:#fff;padding:.3rem .75rem;border-radius:.45rem;font-size:.7rem;border:none}

/* 手机tuning */
@media (max-width: 480px) {
  .card.diary-layout {
    padding: 0.1rem;
    margin: 0;
  }
  
  .panel.diary-mode {
    padding: 0.2rem;
  }
  
  .diary-ingredients-row {
    padding: 0.3rem 0.4rem;
    gap: 0.2rem;
    flex-wrap: wrap;
  }
  
  .diary-ingredient-icon {
    min-width: 2.2rem;
    padding: 0.2rem;
    gap: 0.05rem;
  }
  
  .ingredient-icon-img,
  .ingredient-icon-emoji {
    width: 24px;
    height: 24px;
  }
  
  .ingredient-icon-emoji {
    font-size: 1.2rem;
  }
  
  .ingredient-icon-name {
    font-size: 0.5rem;
    max-width: 2.2rem;
    line-height: 1;
  }
}
</style>

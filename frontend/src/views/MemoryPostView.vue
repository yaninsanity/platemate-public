<template>
  <v-app class="memory-game-arena">
    <section class="game-content-zone">
      <!-- Two-Column Layout: Step 3 (Left) | Step 4 (Right) - 黄金比例 -->
      <div class="split-layout-gaming">
        <!-- Left Column: Recipe Reference - Step 3 -->
        <div class="reference-panel">
          <div class="panel-header">
            <div class="header-icon">📋</div>
            <div class="header-content">
              <h3>Step 3: Cooking Reference</h3>
              <p>Review your recipe ingredients & instructions</p>
            </div>
          </div>
          <div class="recipe-container">
            <div class="recipe-head">
              <!-- Metadata -->
              <div class="recipe-meta">
                <h3 class="recipe-name">{{ recipe?.name }}</h3>
                <div class="recipe-tags">
                  <span>{{ recipe?.cuisine }}</span>
                  <span>{{ recipe?.dish_type }}</span>
                </div>
              </div>
            </div>
            <RoundlyRecipe
              :show-dice="false"
              :show-instructions="true"
              :show-tasks="false"
              :compact-mode="true"
              :ingredients-as-icons="true"
            />
          </div>
          
          <!-- 左下角Kinny烹饪技巧区 -->
          <div class="cooking-motivation">
            <div class="motivation-icon">💡</div>
            <div class="motivation-text">
              <strong>Kinny Cooking Tips</strong>
              <p>{{ currentTip }}</p>
            </div>
          </div>
        </div>

        <!-- Right Column: Post Composer - Step 4 -->
        <div class="composer-panel">
          <div class="panel-header priority">
            <div class="header-icon">🍳</div>
            <div class="header-content">
              <h3>Step 4: Share Memory</h3>
              <p>Share your work!</p>
            </div>
          </div>
          
          <!-- 新增：详细用户引导区域 -->
          <div class="composer-guide">
            <div class="guide-item">
              <span class="guide-icon">📸</span>
              <div class="guide-text">
                <strong>Upload 4 Photos</strong>
                <p><b>Tap ⭐ for highlight</b></p>
              </div>
            </div>
            <div class="guide-item">
              <span class="guide-icon">✍️</span>
              <div class="guide-text">
                <strong>Write Your Story</strong>
              </div>
            </div>
            <div class="guide-item">
              <span class="guide-icon">😊</span>
              <div class="guide-text">
                <strong>Select A Mood</strong>
              </div>
            </div>
            <div class="guide-item">
              <span class="guide-icon">🎯</span>
              <div class="guide-text">
                <strong>Feed Kinny!</strong>
              </div>
            </div>
          </div>
          
          <div class="composer-container">
            <NewMemoryComposer />
          </div>
        </div>
      </div>
    </section>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import RoundlyRecipe      from '@/components/RoundlyRecipe.vue'
import NewMemoryComposer from '@/components/NewMemoryComposer.vue'
import { useRecipesStore } from '@/stores/recipeStore'
import { useCoupleMemoryStore } from '@/stores/couplememoryStore'
import { trackViewDiaryPage, trackViewRecipeReference } from '@/utils/analytics'
import type { Recipe } from '@/models/recipes'

// Get stores
const recipesStore = useRecipesStore()
const memoryStore = useCoupleMemoryStore()

// Computed recipe for template
const recipe = computed((): Recipe | null => {
  return recipesStore.currentBracket?.recipe || null
})

// Fetch current memory data
memoryStore.fetchCurrent()

// Kinny's 20 Cooking Tips
const cookingTips = [
  'Season your food in layers - taste as you cook! 🧂',
  'Always heat your pan before adding oil 🔥',
  'Let meat rest 5-10 min after cooking for juicier results 🥩',
  'Add acid (lemon/vinegar) to brighten flavors ✨',
  'Salt your pasta water like the sea 🌊',
  'Toast spices before using to unlock full flavor 🌶️',
  'Don\'t overcrowd the pan - give food space to breathe 🍳',
  'Room temp ingredients mix better & cook evenly 🌡️',
  'Sharp knives are safer than dull ones - keep \'em honed! 🔪',
  'Mise en place: prep everything before you start cooking 📝',
  'Use thermometer for perfect doneness every time 🌡️',
  'Dry protein before searing for golden crust 💎',
  'Add cheese off heat to prevent clumping 🧀',
  'Fresh herbs at end, dried herbs at start ⏰',
  'Don\'t flip meat constantly - let it develop crust 🥓',
  'Deglaze pan with wine/stock to capture all flavor 🍷',
  'Invest in good salt - it makes a HUGE difference 💰',
  'Taste, taste, taste - trust your palate! 👅',
  'Cold butter on hot pan = flavor bomb 💣',
  'Cook with love - food absorbs your energy! ❤️'
]

const currentTip = ref(cookingTips[Math.floor(Math.random() * cookingTips.length)])
let tipInterval: NodeJS.Timeout | null = null

const rotateTip = () => {
  currentTip.value = cookingTips[Math.floor(Math.random() * cookingTips.length)]
}

onMounted(() => {
  // Rotate on component mount
  rotateTip()
  
  // Auto-rotate every 60 seconds
  tipInterval = setInterval(rotateTip, 60000)
  
  // 🎯 Analytics: Track diary page view (Step 3 & 4)
  const currentRecipe = recipesStore.currentBracket?.recipe
  const hasExistingMemories = memoryStore.current !== null
  
  console.log('[MemoryPostView] 📊 Analytics Check:', {
    hasCurrentRecipe: !!currentRecipe,
    recipeId: currentRecipe?.id,
    recipeName: currentRecipe?.name,
    hasExistingMemories
  })
  
  if (currentRecipe) {
    // Track overall diary page view (Step 4 - composer on right)
    console.log('[MemoryPostView] 🎯 Calling trackViewDiaryPage')
    trackViewDiaryPage(
      currentRecipe.id,
      currentRecipe.name,
      hasExistingMemories
    )
    
    // Track recipe reference view (Step 3 - recipe on left)
    console.log('[MemoryPostView] 🎯 Calling trackViewRecipeReference')
    trackViewRecipeReference(
      currentRecipe.id,
      currentRecipe.name,
      'step3_cooking_reference'
    )
  } else {
    // Track diary page visit even without recipe
    console.log('[MemoryPostView] ⚠️ No recipe found, tracking page view anyway')
    trackViewDiaryPage(
      0, // No recipe ID
      'no_recipe',
      hasExistingMemories
    )
  }
})

onUnmounted(() => {
  if (tipInterval) {
    clearInterval(tipInterval)
  }
})
</script>

<style scoped lang="scss">
/* ===== AAAarena styled to match RoundlyQuestView ===== */
.memory-game-arena {
  min-height: 100vh;
  background: linear-gradient(135deg, 
    #1e1b4b 0%, 
    #312e81 25%,
    #1e293b 50%,
    #0f172a 100%);
  background-size: 400% 400%;
  animation: gameArenaFlow 12s ease-in-out infinite;
  display: flex;
  flex-direction: column;
  color: #fff;
  padding: 0;
  position: relative;
  overflow-x: hidden;
}

@keyframes gameArenaFlow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* ===== 游戏内容区域 ===== */
.game-content-zone {
  flex: 1;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  position: relative;
  z-index: 5;
  max-width: 100%;
  width: 100%;
}

/* Two-column layout for web - tuning比例 2:1 (Reference:Composer) */
.split-layout-gaming {
  display: flex;
  gap: 1.25rem;
  width: 100%;
  align-items: flex-start;
  max-width: 100%;
}

.split-layout-gaming .reference-panel {
  flex: 1.4;
  min-width: 0;
  max-width: 58.33%;
}

.split-layout-gaming .composer-panel {
  flex: 1;
  min-width: 0;
  max-width: 41.67%;
}

/* ===== 游戏面板设计 - AAA级暗黑玻璃态射 ===== */
.reference-panel,
.composer-panel {
  background: linear-gradient(135deg, 
    rgba(15, 23, 42, 0.98) 0%, 
    rgba(30, 41, 59, 0.95) 100%);
  border-radius: 0.85rem;
  padding: 0;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(20px);
  border: 2px solid rgba(251, 191, 36, 0.4);
  box-shadow: 
    0 10px 40px rgba(0, 0, 0, 0.5), 
    0 0 0 1px rgba(255, 255, 255, 0.05);
  overflow: hidden;
  position: relative;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  height: calc(100vh - 3rem);
  max-height: calc(100vh - 3rem);
}

.reference-panel:hover,
.composer-panel:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 15px 50px rgba(0, 0, 0, 0.6),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}

/* Reference Panel - 蓝色能量主题 */
.reference-panel {
  border-color: rgba(59, 130, 246, 0.5);
}

.reference-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(59, 130, 246, 0.8), 
    transparent);
  animation: energy-flow 3s ease-in-out infinite;
}

@keyframes energy-flow {
  0%, 100% { 
    opacity: 0.4; 
    transform: translateX(-100%); 
  }
  50% { 
    opacity: 1; 
    transform: translateX(100%); 
  }
}

/* Composer Panel - 绿色能量主题 */
.composer-panel {
  border-color: rgba(34, 197, 94, 0.5);
}

.composer-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(34, 197, 94, 0.8), 
    transparent);
  animation: energy-flow 3s ease-in-out infinite;
}

/* ===== Panel Headers - AAA游戏级标题系统 ===== */
.panel-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1.15rem 0.75rem;
  border-bottom: 2px solid rgba(251, 191, 36, 0.4);
  background: linear-gradient(135deg, 
    rgba(0, 0, 0, 0.5) 0%, 
    rgba(0, 0, 0, 0.3) 100%);
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.3), 
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  flex-shrink: 0;
  position: relative;
}

.panel-header::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(251, 191, 36, 0.6), 
    transparent);
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { 
    opacity: 0.3; 
    transform: translateX(-100%); 
  }
  50% { 
    opacity: 1; 
    transform: translateX(100%); 
  }
}

.header-icon {
  font-size: 2.2rem;
  filter: drop-shadow(0 4px 12px rgba(251, 191, 36, 0.6));
  animation: icon-float 3s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes icon-float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
}

.header-content {
  flex: 1;
  min-width: 0;
}

.header-content h3 {
  font-size: 1.05rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #fbbf24;
  margin: 0;
  text-shadow: 
    0 3px 10px rgba(251, 191, 36, 0.7), 
    0 0 20px rgba(251, 191, 36, 0.3);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-content p {
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.75);
  margin: 0.25rem 0 0;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* Reference Panel特殊颜色 - 蓝色 */
.reference-panel .panel-header::after {
  background: linear-gradient(90deg, 
    transparent, 
    rgba(59, 130, 246, 0.6), 
    transparent);
}

.reference-panel .header-icon {
  filter: drop-shadow(0 4px 12px rgba(59, 130, 246, 0.6));
}

.reference-panel .header-content h3 {
  color: #60a5fa;
  text-shadow: 
    0 3px 10px rgba(59, 130, 246, 0.7), 
    0 0 20px rgba(59, 130, 246, 0.3);
}

/* Composer Panel特殊颜色 - 绿色 */
.composer-panel .panel-header::after {
  background: linear-gradient(90deg, 
    transparent, 
    rgba(34, 197, 94, 0.6), 
    transparent);
}

.composer-panel .header-icon {
  filter: drop-shadow(0 4px 12px rgba(34, 197, 94, 0.6));
}

.composer-panel .header-content h3 {
  color: #4ade80;
  text-shadow: 
    0 3px 10px rgba(34, 197, 94, 0.7), 
    0 0 20px rgba(34, 197, 94, 0.3);
}

/* ===== Alert Banners - AAA游戏级提示系统 ===== */
.ingredient-alert,
.share-alert {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.45rem 0.7rem;
  margin: 0.4rem 1rem;
  background: rgba(251, 191, 36, 0.15);
  border: 2px solid rgba(251, 191, 36, 0.4);
  border-radius: 0.5rem;
  animation: attention-pulse 2s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes attention-pulse {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 4px 15px rgba(251, 191, 36, 0.3);
  }
  50% { 
    transform: scale(1.02);
    box-shadow: 0 6px 20px rgba(251, 191, 36, 0.5);
  }
}

.alert-icon {
  font-size: 1.1rem;
  filter: drop-shadow(0 2px 8px rgba(251, 191, 36, 0.6));
  animation: icon-bounce 2s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes icon-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.alert-text {
  font-size: 0.68rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-align: center;
  letter-spacing: 0.3px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  line-height: 1.25;
}

/* Reference Panel - 蓝色Alert */
.reference-panel .ingredient-alert {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
}

.reference-panel .ingredient-alert .alert-icon {
  filter: drop-shadow(0 2px 8px rgba(59, 130, 246, 0.6));
}

@keyframes attention-pulse-blue {
  0%, 100% { 
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
  }
  50% { 
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
  }
}

.reference-panel .ingredient-alert {
  animation: attention-pulse-blue 2s ease-in-out infinite;
}

/* Composer Panel - 绿色Alert */
.composer-panel .share-alert {
  background: rgba(34, 197, 94, 0.15);
  border-color: rgba(34, 197, 94, 0.4);
}

.composer-panel .share-alert .alert-icon {
  filter: drop-shadow(0 2px 8px rgba(34, 197, 94, 0.6));
}

@keyframes attention-pulse-green {
  0%, 100% { 
    box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);
  }
  50% { 
    box-shadow: 0 6px 20px rgba(34, 197, 94, 0.5);
  }
}

.composer-panel .share-alert {
  animation: attention-pulse-green 2s ease-in-out infinite;
}

/* ===== 用户引导区域 - AAA游戏级教程系统（超紧凑）===== */
.composer-guide {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.5rem 0.75rem;
  margin: 0.45rem 1rem 0.5rem;
  background: linear-gradient(135deg, 
    rgba(34, 197, 94, 0.16) 0%, 
    rgba(16, 185, 129, 0.11) 100%);
  border: 2.5px solid rgba(34, 197, 94, 0.4);
  border-radius: 0.65rem;
  backdrop-filter: blur(15px);
  box-shadow: 
    0 5px 18px rgba(0, 0, 0, 0.4),
    inset 0 2px 0 rgba(255, 255, 255, 0.08),
    0 0 30px rgba(34, 197, 94, 0.15);
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

.composer-guide::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(34, 197, 94, 0.15),
    transparent
  );
  animation: guide-shimmer 3s ease-in-out infinite;
}

@keyframes guide-shimmer {
  0%, 100% { left: -100%; }
  50% { left: 100%; }
}

.guide-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
  transition: all 0.3s ease;
  position: relative;
  z-index: 1;
}

.guide-icon {
  font-size: 1.15rem;
  flex-shrink: 0;
  filter: drop-shadow(0 3px 10px rgba(34, 197, 94, 0.7));
  animation: icon-glow 2.5s ease-in-out infinite;
}

@keyframes icon-glow {
  0%, 100% { 
    transform: scale(1);
    filter: drop-shadow(0 2px 6px rgba(34, 197, 94, 0.5));
  }
  50% { 
    transform: scale(1.05);
    filter: drop-shadow(0 3px 10px rgba(34, 197, 94, 0.7));
  }
}

.guide-text {
  flex: 1;
  min-width: 0;
}

.guide-text strong {
  display: inline;
  font-size: 0.72rem;
  font-weight: 800;
  color: #4ade80;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 3px 10px rgba(34, 197, 94, 0.7);
  margin-right: 0.3rem;
}

.guide-text p {
  display: inline;
  font-size: 0.66rem;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  line-height: 1.35;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

/* ===== Content Containers ===== */
.recipe-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.9rem 1rem;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.composer-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0rem 0.95rem 0.55rem;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

/* Component Integration */
.composer-container :deep(.composer),
.recipe-container :deep(.card) {
  background: transparent;
  box-shadow: none;
  padding: 0;
  margin: 0;
}

/* ===== Composer内部表单元素 - AAA游戏级统一设计（超紧凑）===== */
.composer-container :deep(textarea) {
  max-height: 95px !important;
  min-height: 80px !important;
  font-size: 0.8rem;
  padding: 0.65rem 0.8rem;
  line-height: 1.45;
  background: linear-gradient(135deg, 
    rgba(34, 197, 94, 0.08) 0%, 
    rgba(16, 185, 129, 0.05) 100%);
  border: 2px solid rgba(34, 197, 94, 0.3);
  border-radius: 0.65rem;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 500;
  letter-spacing: 0.2px;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
}

.composer-container :deep(textarea:focus) {
  border-color: rgba(34, 197, 94, 0.6);
  background: linear-gradient(135deg, 
    rgba(34, 197, 94, 0.12) 0%, 
    rgba(16, 185, 129, 0.08) 100%);
  box-shadow: 
    0 6px 20px rgba(34, 197, 94, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 0 30px rgba(34, 197, 94, 0.2);
}

.composer-container :deep(.form-group) {
  margin-bottom: 0.55rem;
}

.composer-container :deep(.form-label) {
  font-size: 0.75rem;
  margin-bottom: 0.4rem;
  font-weight: 700;
  color: #4ade80;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  text-shadow: 0 2px 8px rgba(34, 197, 94, 0.5);
}

/* Badge提示区样式集成（超紧凑）*/
.composer-container :deep(.badge-prompt) {
  margin-bottom: 0.45rem;
}

.composer-container :deep(.badge-section) {
  margin-bottom: 0.5rem;
}

.composer-container :deep(.badge-container),
.composer-container :deep(.tag-container) {
  gap: 0.4rem;
  margin: 0.55rem 0;
  display: flex;
  flex-wrap: wrap;
}

.composer-container :deep(.badge),
.composer-container :deep(.tag) {
  padding: 0.3rem 0.65rem;
  font-size: 0.7rem;
  font-weight: 700;
  background: linear-gradient(135deg, 
    rgba(34, 197, 94, 0.2) 0%, 
    rgba(16, 185, 129, 0.15) 100%);
  border: 2px solid rgba(34, 197, 94, 0.4);
  border-radius: 0.5rem;
  color: #4ade80;
  letter-spacing: 0.3px;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 
    0 3px 10px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  text-shadow: 0 2px 6px rgba(34, 197, 94, 0.4);
}

.composer-container :deep(.badge:hover),
.composer-container :deep(.tag:hover) {
  transform: translateY(-2px) scale(1.05);
  border-color: rgba(34, 197, 94, 0.6);
  background: linear-gradient(135deg, 
    rgba(34, 197, 94, 0.3) 0%, 
    rgba(16, 185, 129, 0.22) 100%);
  box-shadow: 
    0 5px 15px rgba(34, 197, 94, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.composer-container :deep(.badge.selected),
.composer-container :deep(.tag.selected) {
  background: linear-gradient(135deg, 
    rgba(34, 197, 94, 0.35) 0%, 
    rgba(16, 185, 129, 0.25) 100%);
  border-color: rgba(34, 197, 94, 0.7);
  color: #22c55e;
  box-shadow: 
    0 0 20px rgba(34, 197, 94, 0.6),
    0 5px 18px rgba(34, 197, 94, 0.5);
}

/* Emoji 统一游戏风格 */
.composer-container :deep(.emoji) {
  font-size: 1.1rem;
  filter: drop-shadow(0 2px 6px rgba(34, 197, 94, 0.4));
  transition: all 0.3s ease;
}

.composer-container :deep(.badge:hover .emoji),
.composer-container :deep(.tag:hover .emoji) {
  transform: scale(1.1) rotate(5deg);
  filter: drop-shadow(0 3px 10px rgba(34, 197, 94, 0.7));
}

/* ===== Upload Grid - AAA游戏级上传系统 (1x4横向布局超紧凑) ===== */
.composer-container :deep(.upload-grid) {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  flex-shrink: 0;
  padding: 0;
}

.composer-container :deep(.upload-slot) {
  aspect-ratio: 1;
  padding-top: 0;
  height: 90px;
  min-height: 75px;
  max-height: 90px;
  border: 3px solid rgba(34, 197, 94, 0.4);
  background: linear-gradient(135deg, 
    rgba(34, 197, 94, 0.15) 0%, 
    rgba(16, 185, 129, 0.1) 100%);
  border-radius: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 
    0 6px 18px rgba(0, 0, 0, 0.4),
    inset 0 2px 0 rgba(255, 255, 255, 0.08),
    0 0 30px rgba(34, 197, 94, 0.2);
  overflow: hidden;
}

.composer-container :deep(.upload-slot::before) {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    45deg,
    transparent 30%,
    rgba(34, 197, 94, 0.1) 50%,
    transparent 70%
  );
  animation: shine 3s ease-in-out infinite;
}

@keyframes shine {
  0%, 100% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
  50% { transform: translateX(100%) translateY(100%) rotate(45deg); }
}

/* Empty slot显示+号 */
.composer-container :deep(.upload-slot:not(.selected):not(:has(img)))::after {
  content: '+';
  position: absolute;
  font-size: 3rem;
  font-weight: 300;
  color: rgba(34, 197, 94, 0.6);
  line-height: 1;
  pointer-events: none;
  z-index: 2;
  text-shadow: 0 4px 12px rgba(34, 197, 94, 0.5);
}

.composer-container :deep(.upload-slot:hover) {
  border-color: rgba(34, 197, 94, 0.7);
  background: linear-gradient(135deg, 
    rgba(34, 197, 94, 0.22) 0%, 
    rgba(16, 185, 129, 0.15) 100%);
  transform: translateY(-5px) scale(1.03);
  box-shadow: 
    0 10px 30px rgba(34, 197, 94, 0.5),
    inset 0 2px 0 rgba(255, 255, 255, 0.12),
    0 0 40px rgba(34, 197, 94, 0.35);
}

.composer-container :deep(.upload-slot.selected) {
  border-color: rgba(34, 197, 94, 0.8);
  border-width: 3px;
  border-style: solid;
  background: linear-gradient(135deg, 
    rgba(22, 163, 74, 0.3) 0%, 
    rgba(34, 197, 94, 0.22) 100%);
  box-shadow: 
    0 0 35px rgba(22, 163, 74, 0.7),
    0 10px 35px rgba(34, 197, 94, 0.6),
    inset 0 0 30px rgba(34, 197, 94, 0.2);
  animation: selected-pulse 2s ease-in-out infinite;
}

@keyframes selected-pulse {
  0%, 100% { 
    box-shadow: 
      0 0 25px rgba(22, 163, 74, 0.6),
      0 8px 30px rgba(34, 197, 94, 0.5);
  }
  50% { 
    box-shadow: 
      0 0 35px rgba(22, 163, 74, 0.8),
      0 12px 40px rgba(34, 197, 94, 0.7);
  }
}

.composer-container :deep(.slot-icon) {
  color: #4ade80;
  font-size: 1.8rem;
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  filter: drop-shadow(0 4px 12px rgba(34, 197, 94, 0.7));
  position: relative;
  z-index: 1;
}

.composer-container :deep(.upload-slot:hover .slot-icon) {
  transform: scale(1.15) rotate(12deg);
  filter: drop-shadow(0 6px 20px rgba(34, 197, 94, 1));
  color: #22c55e;
}

.composer-container :deep(.upload-slot:hover::after) {
  color: rgba(34, 197, 94, 0.9);
  transform: scale(1.1) rotate(90deg);
}

.composer-container :deep(.slot-img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 0.8rem;
}

/* ===== Compact Reference Recipe - 暗黑主题整合 ===== */
.recipe-container :deep(.panel) {
  gap: 0.5rem;
  padding: 0;
  overflow: hidden;
  background: transparent;
}

/* 隐藏复杂元素，只保留必要内容 */
.recipe-container :deep(.head) {
  display: none;
}

.recipe-container :deep(.recipe-image-wrapper) {
  display: none;
}

.recipe-container :deep(.name) {
  display: none;
}

.recipe-container :deep(.tags) {
  display: none;
}

.recipe-container :deep(.prep) {
  display: none;
}

/* ===== Ingredients - AAA游戏级完整展示（带数量） ===== */
.recipe-container :deep(.diary-ingredients) {
  margin: 0.3rem 0;
  flex-shrink: 0;
}

.recipe-container :deep(.diary-ingredients-row) {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 0.5rem;
  padding: 0;
}

.recipe-container :deep(.diary-ingredient-icon) {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.28rem;
  padding: 0.5rem 0.38rem;
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.16) 0%, 
    rgba(37, 99, 235, 0.11) 100%);
  border-radius: 0.65rem;
  border: 2px solid rgba(59, 130, 246, 0.42);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 
    0 4px 14px rgba(0, 0, 0, 0.32),
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 0 20px rgba(59, 130, 246, 0.12);
  position: relative;
}

.recipe-container :deep(.diary-ingredient-icon:hover) {
  transform: translateY(-4px) scale(1.03);
  border-color: rgba(59, 130, 246, 0.8);
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.25) 0%, 
    rgba(37, 99, 235, 0.15) 100%);
  box-shadow: 
    0 8px 20px rgba(59, 130, 246, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.recipe-container :deep(.ingredient-icon-wrapper) {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.recipe-container :deep(.ingredient-icon-img),
.recipe-container :deep(.ingredient-icon-emoji) {
  width: 2.9rem;
  height: 2.9rem;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 2px solid rgba(59, 130, 246, 0.35);
  box-shadow: 0 3px 10px rgba(59, 130, 246, 0.45);
}

.recipe-container :deep(.ingredient-icon-emoji) {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.45rem;
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.22) 0%, 
    rgba(37, 99, 235, 0.16) 100%);
}

.recipe-container :deep(.ingredient-icon-name) {
  font-size: 0.66rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.96);
  text-align: center;
  line-height: 1.18;
  letter-spacing: 0.3px;
  text-shadow: 0 2px 5px rgba(0, 0, 0, 0.55);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.recipe-container :deep(.ingredient-icon-quantity) {
  font-size: 0.71rem;
  font-weight: 800;
  color: rgba(251, 191, 36, 0.95);
  text-align: center;
  padding: 0.2rem 0.45rem;
  background: linear-gradient(135deg, 
    rgba(251, 191, 36, 0.2) 0%, 
    rgba(245, 158, 11, 0.15) 100%);
  border-radius: 0.4rem;
  border: 2px solid rgba(251, 191, 36, 0.4);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  box-shadow: 
    0 2px 8px rgba(251, 191, 36, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  letter-spacing: 0.4px;
  min-width: 80%;
}

/* ===== Instructions - AAA游戏级完整展示（超大字体易读）===== */
.recipe-container :deep(.diary-instructions) {
  margin: 0.55rem 0 0;
  flex-shrink: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.recipe-container :deep(.diary-inst-content) {
  font-size: 0.88rem;
  padding: 0.85rem 1rem;
  line-height: 1.65;
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.13) 0%, 
    rgba(37, 99, 235, 0.09) 100%);
  border: 2px solid rgba(59, 130, 246, 0.35);
  border-radius: 0.7rem;
  color: rgba(255, 255, 255, 0.98);
  border-left: 5px solid rgba(59, 130, 246, 0.7);
  box-shadow: 
    0 4px 16px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.07),
    0 0 25px rgba(59, 130, 246, 0.18);
  transition: all 0.3s ease;
  white-space: pre-wrap;
  word-break: break-word;
  font-weight: 500;
  letter-spacing: 0.3px;
  flex: 1;
  overflow-y: auto;
}

.recipe-container :deep(.diary-inst-content:hover) {
  border-left-width: 6px;
  box-shadow: 
    0 6px 20px rgba(59, 130, 246, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

/* ===== 左下角Kinny烹饪技巧 - AAA游戏级智能提示系统 ===== */
.cooking-motivation {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.6rem 0.8rem;
  margin: 0.5rem 1rem 0.6rem;
  background: linear-gradient(135deg, 
    rgba(251, 191, 36, 0.18) 0%, 
    rgba(245, 158, 11, 0.12) 100%);
  border: 2.5px solid rgba(251, 191, 36, 0.45);
  border-radius: 0.7rem;
  backdrop-filter: blur(15px);
  box-shadow: 
    0 5px 18px rgba(0, 0, 0, 0.4),
    inset 0 2px 0 rgba(255, 255, 255, 0.08),
    0 0 30px rgba(251, 191, 36, 0.2);
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  animation: motivation-glow 3s ease-in-out infinite;
}

@keyframes motivation-glow {
  0%, 100% { 
    box-shadow: 
      0 5px 18px rgba(0, 0, 0, 0.4),
      inset 0 2px 0 rgba(255, 255, 255, 0.08),
      0 0 30px rgba(251, 191, 36, 0.2);
  }
  50% { 
    box-shadow: 
      0 6px 22px rgba(0, 0, 0, 0.45),
      inset 0 2px 0 rgba(255, 255, 255, 0.1),
      0 0 40px rgba(251, 191, 36, 0.35);
  }
}

.cooking-motivation::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    45deg,
    transparent 30%,
    rgba(251, 191, 36, 0.15) 50%,
    transparent 70%
  );
  animation: motivation-shine 4s ease-in-out infinite;
}

@keyframes motivation-shine {
  0%, 100% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
  50% { transform: translateX(100%) translateY(100%) rotate(45deg); }
}

.motivation-icon {
  font-size: 1.8rem;
  filter: drop-shadow(0 4px 12px rgba(251, 191, 36, 0.7));
  animation: kinny-bounce 2s ease-in-out infinite;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

@keyframes kinny-bounce {
  0%, 100% { 
    transform: translateY(0) scale(1) rotate(-3deg);
  }
  50% { 
    transform: translateY(-4px) scale(1.05) rotate(3deg);
  }
}

.motivation-text {
  flex: 1;
  position: relative;
  z-index: 1;
}

.motivation-text strong {
  display: block;
  font-size: 0.72rem;
  font-weight: 800;
  color: #fbbf24;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 3px 10px rgba(251, 191, 36, 0.7);
  margin-bottom: 0.2rem;
}

.motivation-text p {
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  line-height: 1.35;
  font-weight: 600;
  letter-spacing: 0.25px;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
}

/* ===== Content Containers ===== */

/* ===== 游戏化滚动条 ===== */
.recipe-container::-webkit-scrollbar,
.composer-container::-webkit-scrollbar {
  width: 8px;
}

.recipe-container::-webkit-scrollbar-track,
.composer-container::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 4px;
}

.recipe-container::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  border-radius: 4px;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

.composer-container::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #4ade80, #22c55e);
  border-radius: 4px;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
}

.recipe-container::-webkit-scrollbar-thumb:hover,
.composer-container::-webkit-scrollbar-thumb:hover {
  filter: brightness(1.2);
}

/* ===== Composer内部元素tuning - 紧凑布局 ===== */
.composer-container :deep(.quest-header) {
  display: none; /* 隐藏重复标题 */
}

.composer-container :deep(.recipe-row) {
  margin: 0.5rem 0;
  gap: 0.4rem;
}

.composer-container :deep(.recipe-chip) {
  padding: 0.4rem 0.7rem;
  font-size: 0.7rem;
}

.composer-container :deep(.new-input) {
  padding: 0.7rem 0.85rem;
  font-size: 0.75rem;
  min-height: 60px;
  line-height: 1.4;
}

.composer-container :deep(.emoji-trigger) {
  width: 2rem;
  height: 2rem;
  font-size: 1.2rem;
}

.composer-container :deep(.badge-section) {
  margin: 0.7rem 0;
}

.composer-container :deep(.badge-grid) {
  gap: 0.45rem;
}

.composer-container :deep(.badge-chip) {
  width: 2.5rem;
  height: 2.5rem;
  font-size: 1.3rem;
}

.composer-container :deep(.badge-status) {
  padding: 0.4rem 0.7rem;
  font-size: 0.7rem;
  margin-top: 0.5rem;
}

.composer-container :deep(.submit-section) {
  margin: 0.8rem 0 0.4rem;
}

.composer-container :deep(.btn-post) {
  padding: 0.75rem 1.25rem;
  font-size: 0.8rem;
}

.composer-container :deep(.hint) {
  font-size: 0.68rem;
  margin: 0.5rem 0 0;
  padding: 0.4rem;
}

/* ===== responsive layout ===== */
@media (max-width: 768px) {
  .game-content-zone {
    padding: 1rem;
  }

  /* Mobile: Stack columns vertically */
  .split-layout-gaming {
    flex-direction: column;
    gap: 1rem;
  }

  .split-layout-gaming .reference-panel,
  .split-layout-gaming .composer-panel {
    max-width: 100%;
  }

  .panel-header {
    padding: 1.5rem 1.5rem 1.25rem;
    gap: 1rem;
  }

  .header-icon {
    font-size: 2.5rem;
  }

  .header-content h3 {
    font-size: 1.1rem;
  }

  .header-content p {
    font-size: 0.75rem;
  }

  .ingredient-alert,
  .share-alert {
    padding: 0.75rem 1rem;
    margin: 0.75rem 1.5rem;
  }

  .alert-icon {
    font-size: 1.3rem;
  }

  .alert-text {
    font-size: 0.75rem;
  }

  .recipe-container,
  .composer-container {
    padding: 1.5rem;
  }
}

@media (max-width: 420px) {
  .memory-game-arena {
    padding: 0;
  }

  .game-content-zone {
    padding: 0.5rem;
  }

  .split-layout-gaming {
    gap: 0.75rem;
  }

  .reference-panel,
  .composer-panel {
    border-radius: 0.75rem;
  }

  .panel-header {
    padding: 1rem 1rem 0.75rem;
    gap: 0.75rem;
  }

  .header-icon {
    font-size: 2rem;
  }

  .header-content h3 {
    font-size: 0.95rem;
    letter-spacing: 0.8px;
  }

  .header-content p {
    font-size: 0.65rem;
  }

  .ingredient-alert,
  .share-alert {
    padding: 0.6rem 0.8rem;
    margin: 0.5rem 1rem;
  }

  .alert-icon {
    font-size: 1.1rem;
  }

  .alert-text {
    font-size: 0.65rem;
  }

  .recipe-container,
  .composer-container {
    padding: 1rem;
  }

  .reference-panel,
  .composer-panel {
    height: auto;
    max-height: none;
  }

  .recipe-container {
    padding: 1rem;
  }

  /* Ingredients mobile tuning */
  .recipe-container :deep(.diary-ingredients-row) {
    grid-template-columns: repeat(auto-fill, minmax(95px, 1fr));
    gap: 0.65rem;
  }

  .recipe-container :deep(.diary-ingredient-icon) {
    padding: 0.7rem 0.5rem;
    gap: 0.4rem;
  }

  .recipe-container :deep(.ingredient-icon-img),
  .recipe-container :deep(.ingredient-icon-emoji) {
    width: 3rem;
    height: 3rem;
  }

  .recipe-container :deep(.ingredient-icon-emoji) {
    font-size: 1.5rem;
  }

  .recipe-container :deep(.ingredient-icon-name) {
    font-size: 0.7rem;
  }

  .recipe-container :deep(.ingredient-icon-quantity) {
    font-size: 0.8rem;
    padding: 0.25rem 0.5rem;
  }

  /* Instructions mobile tuning */
  .recipe-container :deep(.diary-inst-content) {
    font-size: 0.8rem;
    padding: 0.9rem 1.1rem;
    line-height: 1.65;
  }

  /* Upload Grid mobile tuning */
  .composer-container :deep(.upload-grid) {
    gap: 0.75rem;
  }

  .composer-container :deep(.upload-slot) {
    height: 70px;
    border-width: 2px;
  }

  .composer-container :deep(.slot-icon) {
    font-size: 1.5rem;
  }
}

/* ===== 超小屏幕tuning ===== */
@media (max-width: 360px) {
  .game-content-zone {
    padding: 0.4rem;
  }

  .split-layout-gaming {
    gap: 0.5rem;
  }

  .panel-header {
    padding: 0.75rem 0.75rem 0.6rem;
    gap: 0.6rem;
  }

  .header-icon {
    font-size: 1.75rem;
  }

  .header-content h3 {
    font-size: 0.85rem;
  }

  .header-content p {
    font-size: 0.6rem;
  }

  .ingredient-alert,
  .share-alert {
    padding: 0.5rem 0.6rem;
    margin: 0.4rem 0.75rem;
  }

  .alert-icon {
    font-size: 1rem;
  }

  .alert-text {
    font-size: 0.6rem;
  }

  .recipe-container,
  .composer-container {
    padding: 0.75rem;
  }

  .recipe-container :deep(.diary-ingredients-row) {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 0.55rem;
  }

  .recipe-container :deep(.diary-ingredient-icon) {
    padding: 0.6rem 0.4rem;
    gap: 0.35rem;
  }

  .recipe-container :deep(.ingredient-icon-img),
  .recipe-container :deep(.ingredient-icon-emoji) {
    width: 2.5rem;
    height: 2.5rem;
  }

  .recipe-container :deep(.ingredient-icon-emoji) {
    font-size: 1.3rem;
  }

  .recipe-container :deep(.ingredient-icon-name) {
    font-size: 0.65rem;
  }

  .recipe-container :deep(.ingredient-icon-quantity) {
    font-size: 0.75rem;
    padding: 0.2rem 0.4rem;
  }

  .recipe-container :deep(.diary-inst-content) {
    font-size: 0.75rem;
    padding: 0.8rem 0.95rem;
    line-height: 1.6;
  }

  .composer-container :deep(.upload-slot) {
    height: 60px;
  }

  .composer-container :deep(.slot-icon) {
    font-size: 1.3rem;
  }
}

.recipe-head {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 1rem;
  border: 2px solid rgba(251, 191, 36, 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.recipe-meta {
  flex: 1;
  min-width: 0;
}

.recipe-name {
  font-size: 1.3rem;
  font-weight: 800;
  margin: 0 0 0.75rem;
  color: #fbbf24;
  line-height: 1.3;
  text-shadow: 0 2px 8px rgba(251, 191, 36, 0.5);
  letter-spacing: 0.5px;
}

.recipe-tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0;
}

.recipe-tags span {
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
</style>

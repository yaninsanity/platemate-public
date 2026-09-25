<!-- File: src/views/RoundlyBattleHistoryView.vue -->
<template>
    <div class="battle-history-container" :style="backgroundStyle">
    <!-- Game-style header with stats -->
    <div class="game-header">
      <div class="header-bg">
        <div class="header-content">
          <!-- 左：标题 -->
          <div class="title-section">
            <div class="trophy-icon">💕</div>
            <div class="title-text">
              <h1 class="main-title">Love Kitchen</h1>
            </div>
          </div>
          
          <!-- 中：统一统计行（记分牌 + 紧凑统计） -->
          <div class="unified-stats-row" v-if="rounds.length > 0">
            <!-- 战斗记分牌 - 增强PK对抗感 + Profile导航 -->
            <div class="battle-scoreboard">
              <div class="score-card you">
                <div class="player-avatar you-avatar clickable-avatar" @click="$router.push('/profile')" title="View Profile">👨‍🍳</div>
                <div class="score-info">
                  <div class="score-value">{{ selfWins }}</div>
                  <div class="score-header">{{ selfName }}</div>
                </div>
              </div>
              
              <div class="score-divider">
                <div class="vs-badge">⚔️ VS</div>
                <div class="triple-progress-bar">
                  <div class="progress-seg you" :style="{ width: selfWinPercent + '%' }"></div>
                  <div class="progress-seg tie" :style="{ width: tiePercent + '%' }"></div>
                  <div class="progress-seg partner" :style="{ width: partnerWinPercent + '%' }"></div>
                </div>
              </div>
              
              <div class="score-card partner">
                <div class="score-info">
                  <div class="score-value">{{ partnerWins }}</div>
                  <div class="score-header">{{ partnerName }}</div>
                </div>
                <div class="player-avatar partner-avatar clickable-avatar" @click="$router.push('/profile')" title="View Profile">👩‍🍳</div>
              </div>
            </div>
            
            <!-- 紧凑统计 - 同一行，清晰标签 + Emoji -->
            <div class="compact-stats-grid">
              <div class="stat-item">
                <span class="stat-emoji">🤝</span>
                <span class="stat-num">{{ tieCount }}</span>
                <span class="stat-txt">Ties</span>
              </div>
              <div class="stat-item">
                <span class="stat-emoji">⚔️</span>
                <span class="stat-num">{{ rounds.length }}</span>
                <span class="stat-txt">Battles</span>
              </div>
              <div class="stat-item">
                <span class="stat-emoji">📸</span>
                <span class="stat-num">{{ totalPhotos }}</span>
                <span class="stat-txt">Photos</span>
              </div>
              <div class="stat-item">
                <span class="stat-emoji">💬</span>
                <span class="stat-num">{{ totalComments }}</span>
                <span class="stat-txt">Comments</span>
              </div>
            </div>
          </div>
          
          <!-- 右：视图切换 - 清晰提示目标模式 -->
          <!-- <button class="view-switcher-btn" v-if="rounds.length > 0" @click="viewMode = viewMode === 'grid' ? 'single' : 'grid'">
            <span class="switch-icon">{{ viewMode === 'grid' ? '◉' : '▦' }}</span>
            <span class="switch-label">Switch to</span>
            <span class="switch-text">{{ viewMode === 'grid' ? 'Focus' : 'Grid' }}</span>
          </button> -->
        </div>
      </div>
    </div>

    <!-- Loading states with game theme -->
    <div v-if="memStore.loading || recipeStore.loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p class="loading-text">Loading sweet memories...</p>
    </div>
    
    <div v-else-if="memStore.error" class="error-state">
      <div class="error-icon">⚠️</div>
      <p class="error-text">{{ memStore.error }}</p>
    </div>
    
    <div v-else-if="!rounds.length" class="empty-state">
      <div class="empty-icon">🍳</div>
      <h3 class="empty-title">No Memories Yet</h3>
      <p class="empty-text">Start cooking together and create sweet memories!</p>
    </div>

    <!-- 🎮 AAA游戏化Battle视图 -->
    <div v-else class="battles-arena">
      <!-- Focus单个浏览模式 - AAA游戏级完整展示 -->
      <div v-if="viewMode === 'single'" class="focus-mode">
        <button 
          class="nav-arrow-btn prev" 
          @click="prevBattle" 
          :disabled="currentIndex === 0"
          v-if="rounds.length > 1">
          <span class="arrow-icon">◀</span>
          <span class="arrow-hint">Previous Battle</span>
        </button>
        
        <div class="focus-content">
          <div class="focus-indicator">
            <span class="current-num">{{ currentIndex + 1 }}</span>
            <span class="divider">/</span>
            <span class="total-num">{{ rounds.length }}</span>
          </div>
          
          <!-- 🎮 Focus模式专用：完整展开的Battle详情 -->
          <BattleDetailExpanded
            :memory="rounds[currentIndex]"
            :self-id="selfId"
            :self-name="selfName"
            :partner-id="partnerId"
            :partner-name="partnerName"
            :battle-number="rounds.length - currentIndex"
            @navigate="handleNavigate"
          />
        </div>
        
        <button 
          class="nav-arrow-btn next" 
          @click="nextBattle" 
          :disabled="currentIndex === rounds.length - 1"
          v-if="rounds.length > 1">
          <span class="arrow-hint">Next Battle</span>
          <span class="arrow-icon">▶</span>
        </button>
      </div>
      
      <!-- Grid平铺模式 - 充分利用空间 -->
      <TransitionGroup
        v-else
        name="battle-slide"
        tag="div"
        class="battles-grid-pro"
      >
        <BattleRow
          v-for="(w, index) in rounds"
          :key="w.id"
          :memory="w"
          :self-id="selfId"
          :self-name="selfName"
          :partner-id="partnerId"
          :partner-name="partnerName"
          :battle-number="rounds.length - index"
        />
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref }   from 'vue'
import { useRouter }             from 'vue-router'
import BattleRow                 from '@/components/RoundlyBattleRow.vue'
import BattleDetailExpanded      from '@/components/BattleDetailExpanded.vue'
import { useCoupleMemoryStore }  from '@/stores/couplememoryStore'
import { useUserStore }          from '@/stores/userStore'
import { useRecipesStore }       from '@/stores/recipeStore'
import { createBackgroundManager } from '@/utils/backgroundManager'
import { trackViewBattleHistory } from '@/utils/analytics'

/* 🎯 路由导航 */
const router = useRouter()

/* 🎮 统一背景管理系统 - 游戏化体验 */
const bgManager = createBackgroundManager()
const backgroundStyle = computed(() => {
  const style = bgManager.getStyle(0.15)  // 轻度紫色渐变叠加
  console.log('🎨 RoundlyBattleHistory backgroundStyle:', style)
  return style
})

/* ── stores ────────────────────────────────────────────── */
const memStore    = useCoupleMemoryStore()
const userStore   = useUserStore()
const recipeStore = useRecipesStore()

/* 🎮 视图模式状态 */
const viewMode = ref<'grid' | 'single'>('grid')  // 默认网格视图（平铺）
const currentIndex = ref(0)  // 单个浏览当前索引

/* 单个浏览导航函数 */
const prevBattle = () => {
  if (currentIndex.value > 0) currentIndex.value--
}
const nextBattle = () => {
  if (currentIndex.value < rounds.value.length - 1) currentIndex.value++
}

/* 🎯 点击进入详情页面 */
const handleNavigate = (memoryId: number) => {
  router.push({ name: 'RoundlyBattle', params: { roundId: memoryId } })
}

/* fetch once on enter */
onMounted(async () => {
  console.debug('[RoundlyBattleHistory] fetchMemories')
  
  try {
    // 确保 recipes 数据已加载，用于显示菜名
    console.log('Current recipes count:', recipeStore.recipes.length)
    
    if (recipeStore.recipes.length === 0) {
      console.debug('[RoundlyBattleHistory] Loading recipes for recipe names')
      await recipeStore.loadBasics()
      console.log('After loading recipes count:', recipeStore.recipes.length)
    }
    
    await memStore.fetchMemories({ page_size: 100, ordering: '-round_start' })
    
    // 🎯 track the battle-history view after the data loads, so the count is real
    trackViewBattleHistory(memStore.memories.length, 'all')
  } catch (error) {
    console.error('Error in RoundlyBattleHistory onMounted:', error)
  }
})

/* reactive shortcuts */
const rounds       = computed(() => memStore.memories)
const selfId      = computed(() => userStore.user?.id ?? 0)          // 0 => “unknown”
const selfName    = computed(() => userStore.user?.username ?? 'You')
const partnerId   = computed(() => userStore.couple?.members?.find((p: { id: any }) => p.id !== selfId.value)?.id ?? 0)  // 🔧 FIX: 添加默认值 0，避免 undefined
const partnerName = computed(() => userStore.couple?.members?.find((p: { id: any }) => p.id !== selfId.value)?.username ?? 'Partner')

const selfWins = computed(() => rounds.value.filter(m => m.winner_entry?.author_username === selfName.value).length)
const partnerWins = computed(() => rounds.value.filter(m => m.winner_entry?.author_username === partnerName.value).length)
const tieCount = computed(() => rounds.value.filter(m => !m.winner_entry || m.winner_entry.author_username === null).length)
const winRate = computed(() => rounds.value.length > 0 ? Math.round((selfWins.value / rounds.value.length) * 100) : 0)
const totalPhotos = computed(() => rounds.value.reduce((sum, m) => sum + m.entries.flatMap(e => e.media).length, 0))
const totalComments = computed(() => rounds.value.reduce((sum, m) => sum + (m.comments_count || 0), 0))
const selfWinPercent = computed(() => {
  const total = selfWins.value + partnerWins.value + tieCount.value
  return total > 0 ? Math.round((selfWins.value / total) * 100) : 33
})
const partnerWinPercent = computed(() => {
  const total = selfWins.value + partnerWins.value + tieCount.value
  return total > 0 ? Math.round((partnerWins.value / total) * 100) : 33
})
const tiePercent = computed(() => {
  const total = selfWins.value + partnerWins.value + tieCount.value
  return total > 0 ? Math.round((tieCount.value / total) * 100) : 34
})
</script>

<style scoped>
/* 🎮 统一系统风格 - 随机背景游戏体验 */
.battle-history-container {
  /* 🎯 精准修复：确保容器和背景图片完全填充视口 */
  min-height: 100vh;
  width: 100%;
  max-width: 100vw;  /* 防止超出视口 */
  /* 🎯 the background is injected inline by backgroundStyle */
  /* background-size: cover 自动缩放填充 */
  /* background-position: center 居中显示 */
  /* background-attachment: fixed/scroll 根据设备自适应 */
  margin: 0;
  padding: 0;
  position: relative;
  display: flex;
  flex-direction: column;
  color: #fff;
  overflow-x: hidden;
  box-sizing: border-box;
  
  /* 柔和光晕叠加效果 */
  &::after {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.08) 0%, transparent 50%),
      radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.06) 0%, transparent 50%);
    pointer-events: none;
    opacity: 0.6;
    z-index: 0;
  }
  
  > * {
    position: relative;
    z-index: 1;
  }
}

/* Game-style header - 确保任何背景下都清晰 */
.game-header {
  position: sticky;
  top: 0;  /* 🎯 sits flush against the padding-top set in App.vue */
  z-index: 100;
  margin-bottom: 0;  /* 🎯 精准修复：移除 gap */
  flex-shrink: 0;
  width: 100%;
}

.header-bg {
  /* 🎯 深色半透明背景确保在任何背景图下都清晰可读 */
  background: linear-gradient(135deg, 
    rgba(25, 25, 40, 0.95) 0%,
    rgba(20, 20, 35, 0.92) 50%,
    rgba(15, 15, 30, 0.95) 100%
  );
  backdrop-filter: blur(30px) saturate(150%);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 2px 8px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(138, 180, 248, 0.2);
  border-radius: 0 0 1.5rem 1.5rem;
  border: 2px solid rgba(138, 180, 248, 0.3);
  border-top: none;
  padding: 1rem 0;  /* 🎯 只控制上下 padding */
  position: relative;
  overflow: hidden;
  
  /* 额外遮罩层增强可读性 */
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at top, 
      rgba(0, 0, 0, 0.3) 0%, 
      transparent 70%
    );
    pointer-events: none;
    z-index: 0;
  }
  
  /* 底部发光边框 */
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, 
      transparent, 
      rgba(138, 180, 248, 0.8) 20%,
      rgba(99, 102, 241, 0.8) 50%,
      rgba(138, 180, 248, 0.8) 80%,
      transparent
    );
    box-shadow: 0 0 20px rgba(138, 180, 248, 0.6);
    z-index: 2;
  }
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  /* 🎯 drop the max-width so the header fills the viewport, as in HomeView */
  width: 100%;
  margin: 0;
  gap: 1rem;
  flex-wrap: nowrap;
  padding: 0 1.5rem;
  position: relative;
  z-index: 1;
  box-sizing: border-box;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 0;
  flex: 0 0 auto;
  background: transparent;
  padding: 0;
  border-radius: 0;
  border: none;
  position: relative;
}

.trophy-icon {
  font-size: 1.4rem;
  filter: drop-shadow(0 0 8px rgba(168, 230, 207, 1))
          drop-shadow(0 0 15px rgba(168, 230, 207, 0.6))
          drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
  animation: trophy-glow 2s ease-in-out infinite alternate;
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

@keyframes trophy-glow {
  0% { 
    transform: scale(1) rotate(-2deg);
    filter: drop-shadow(0 0 8px rgba(168, 230, 207, 1))
            drop-shadow(0 0 15px rgba(168, 230, 207, 0.6))
            drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
  }
  100% { 
    transform: scale(1.08) rotate(2deg);
    filter: drop-shadow(0 0 15px rgba(168, 230, 207, 1))
            drop-shadow(0 0 25px rgba(168, 230, 207, 0.8))
            drop-shadow(0 2px 6px rgba(0, 0, 0, 0.6));
  }
}

.title-text {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.main-title {
  font-size: 1.1rem;
  font-weight: 900;
  margin: 0;
  /* 🎯 增强蓝色发光阴影确保任何背景下都清晰 */
  text-shadow: 
    0 0 30px rgba(138, 180, 248, 1),
    0 0 20px rgba(99, 102, 241, 0.8),
    0 3px 10px rgba(0, 0, 0, 1),
    0 6px 20px rgba(0, 0, 0, 0.8);
  letter-spacing: 0.8px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
  /* 亮白渐变文字 */
  background: linear-gradient(135deg,
    #ffffff 0%,
    #c7d2fe 25%,
    #ffffff 50%,
    #a5b4fc 75%,
    #ffffff 100%
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.8));
  white-space: nowrap;
  min-width: fit-content;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@keyframes title-shine {
  0% { background-position: 0% center; }
  100% { background-position: 200% center; }
}

.sub-title {
  font-size: 0.55rem;
  opacity: 0.95;
  margin: 0;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.5),
               0 0 10px rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.95);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-transform: uppercase;
}

.stats-badge {
  background: linear-gradient(135deg,
    rgba(255, 255, 255, 0.25),
    rgba(255, 255, 255, 0.12)
  );
  border-radius: 0.75rem;
  padding: 0.3rem 0.5rem;
  backdrop-filter: blur(15px) saturate(180%);
  border: 1.5px solid rgba(255, 255, 255, 0.35);
  text-align: center;
  min-width: 2.8rem;
  flex-shrink: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25),
              0 0 20px rgba(255, 255, 255, 0.15) inset;
  position: relative;
  overflow: hidden;
  order: 3;
}

.stats-badge::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 200%;
  background: linear-gradient(45deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transform: rotate(45deg);
  animation: badge-shine 3s ease-in-out infinite;
}

@keyframes badge-shine {
  0%, 100% { transform: translateX(-100%) rotate(45deg); }
  50% { transform: translateX(100%) rotate(45deg); }
}

.battles-count {
  display: block;
  font-size: 0.95rem;
  font-weight: 900;
  color: white;
  line-height: 1.2;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
  position: relative;
  z-index: 1;
}

.battles-label {
  display: block;
  font-size: 0.55rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  position: relative;
  z-index: 1;
}

/* 视图切换按钮 - AAA游戏化，清晰提示 */
.view-switcher-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.1rem;
  padding: 0.5rem 0.8rem;
  background: linear-gradient(135deg, 
    rgba(168, 230, 207, 0.12), 
    rgba(168, 230, 207, 0.08)
  );
  border: 1.5px solid rgba(168, 230, 207, 0.3);
  border-radius: 0.7rem;
  backdrop-filter: blur(12px);
  cursor: pointer;
  transition: all 0.25s ease;
  flex-shrink: 0;
  min-width: 5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3),
              0 0 20px rgba(168, 230, 207, 0.1) inset;
}

.view-switcher-btn:hover {
  background: linear-gradient(135deg, 
    rgba(168, 230, 207, 0.22), 
    rgba(168, 230, 207, 0.15)
  );
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4),
              0 0 30px rgba(168, 230, 207, 0.25) inset;
  border-color: rgba(168, 230, 207, 0.5);
}

.view-switcher-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.switch-icon {
  font-size: 1.3rem;
  line-height: 1;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
}

.switch-label {
  font-size: 0.45rem;
  font-weight: 600;
  letter-spacing: 0.3px;
  color: rgba(255, 255, 255, 0.7);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
  white-space: nowrap;
  text-transform: uppercase;
}

.switch-text {
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6),
               0 0 10px currentColor;
  white-space: nowrap;
}

.view-btn-pro {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.35rem 0.6rem;
  background: rgba(0, 0, 0, 0.2);
  border: 1.5px solid rgba(255, 255, 255, 0.25);
  border-radius: 0.5rem;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.7rem;
  font-weight: 700;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
  letter-spacing: 0.3px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  backdrop-filter: blur(10px);
  position: relative;
  overflow: hidden;
}

.view-btn-pro::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.view-btn-pro:hover::before {
  left: 100%;
}

.view-btn-pro:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.view-btn-pro.active {
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.95) 0%, 
    rgba(118, 75, 162, 0.95) 100%
  );
  color: white;
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 3px 15px rgba(102, 126, 234, 0.6),
              0 0 25px rgba(102, 126, 234, 0.4) inset;
  transform: scale(1.05);
}

.view-btn-pro .btn-icon {
  font-size: 0.9rem;
  line-height: 1;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.4));
}

.view-btn-pro .btn-text {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.3px;
}

/* 统一统计行 - 记分牌+紧凑统计同一行 */
.unified-stats-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.8rem;
  flex: 1;
  min-width: 0;
}

/* 战斗记分牌 - 暗黑游戏风格 */
.battle-scoreboard {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  background: linear-gradient(135deg, 
    rgba(20, 20, 30, 0.6), 
    rgba(15, 15, 25, 0.7)
  );
  border-radius: 0.8rem;
  padding: 0.5rem 1.2rem;
  backdrop-filter: blur(15px);
  border: 1.5px solid rgba(168, 230, 207, 0.25);
  flex-shrink: 0;
  min-width: fit-content;
  box-shadow: 0 3px 15px rgba(0, 0, 0, 0.5),
              0 0 30px rgba(168, 230, 207, 0.1) inset;
}

.score-card {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-card.you {
  flex-direction: row;
}

.score-card.partner {
  flex-direction: row-reverse;
}

/* 玩家头像 - 暗黑游戏风格 + 可点击导航 */
.player-avatar {
  font-size: 2rem;
  line-height: 1;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, 
    rgba(20, 20, 30, 0.8), 
    rgba(15, 15, 25, 0.9)
  );
  border: 2px solid rgba(168, 230, 207, 0.3);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.5);
  flex-shrink: 0;
  transition: all 0.3s ease;
}

/* 🎮 可点击头像交互效果 */
.clickable-avatar {
  cursor: pointer;
}

.clickable-avatar:hover {
  transform: scale(1.15);
}

.clickable-avatar:active {
  transform: scale(1.05);
}

.you-avatar {
  border-color: rgba(168, 230, 207, 0.6);
  box-shadow: 0 3px 10px rgba(168, 230, 207, 0.4),
              0 0 20px rgba(168, 230, 207, 0.2) inset;
}

.you-avatar.clickable-avatar:hover {
  border-color: rgba(168, 230, 207, 0.9);
  box-shadow: 
    0 5px 15px rgba(168, 230, 207, 0.6),
    0 0 30px rgba(168, 230, 207, 0.4) inset;
}

.partner-avatar {
  border-color: rgba(255, 107, 157, 0.6);
  box-shadow: 0 3px 10px rgba(255, 107, 157, 0.4),
              0 0 20px rgba(255, 107, 157, 0.2) inset;
}

.partner-avatar.clickable-avatar:hover {
  border-color: rgba(255, 107, 157, 0.9);
  box-shadow: 
    0 5px 15px rgba(255, 107, 157, 0.6),
    0 0 30px rgba(255, 107, 157, 0.4) inset;
}

.score-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.1rem;
}

.score-card.you .score-value {
  color: #a8e6cf;
}

.score-card.partner .score-value {
  color: #ff6b9d;
}

.score-value {
  font-size: 1.3rem;
  font-weight: 900;
  line-height: 1;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6),
               0 0 15px currentColor;
}

.score-header {
  font-size: 0.6rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.9;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
  white-space: nowrap;
}

.score-divider {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  align-items: center;
  flex: 1;
  min-width: 10rem;
  max-width: 18rem;
}

.vs-badge {
  background: linear-gradient(135deg, #a8e6cf, #6ee7b7);
  color: #0f172a;
  font-size: 0.7rem;
  font-weight: 900;
  padding: 0.2rem 0.6rem;
  border-radius: 0.5rem;
  letter-spacing: 0.5px;
  box-shadow: 0 3px 10px rgba(168, 230, 207, 0.6),
              0 0 20px rgba(168, 230, 207, 0.3) inset;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.triple-progress-bar {
  width: 100%;
  height: 0.6rem;
  display: flex;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.6),
              0 1px 0 rgba(255, 255, 255, 0.1);
}

.progress-seg {
  height: 100%;
  transition: width 0.5s ease;
}

.progress-seg.you {
  background: #a8e6cf;
}

.progress-seg.tie {
  background: #fbbf24;
}

.progress-seg.partner {
  background: #ff6b9d;
}

@keyframes shimmer {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* 紧凑统计网格 - 暗黑游戏风格 */
.compact-stats-grid {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.7rem;
  background: linear-gradient(135deg, 
    rgba(20, 20, 30, 0.6), 
    rgba(15, 15, 25, 0.7)
  );
  border-radius: 0.6rem;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(168, 230, 207, 0.2);
  transition: all 0.2s ease;
  min-width: fit-content;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.stat-item:hover {
  background: linear-gradient(135deg, 
    rgba(20, 20, 30, 0.75), 
    rgba(15, 15, 25, 0.85)
  );
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5),
              0 0 20px rgba(168, 230, 207, 0.15) inset;
  border-color: rgba(168, 230, 207, 0.4);
}

.stat-emoji {
  font-size: 1rem;
  line-height: 1;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
  flex-shrink: 0;
}

.stat-num {
  font-size: 1rem;
  font-weight: 900;
  color: white;
  line-height: 1;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
  flex-shrink: 0;
}

.stat-txt {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
  text-transform: capitalize;
}

/* 活动统计卡片行 */
.activity-stats-row {
  display: flex;
  gap: 0.5rem;
  justify-content: space-between;
}

.stat-card-mini {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 0.75rem;
  padding: 0.5rem 0.65rem;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.stat-card-mini::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(255, 255, 255, 0.15),
    transparent
  );
  transition: left 0.5s ease;
}

.stat-card-mini:hover {
  background: rgba(255, 255, 255, 0.18);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-card-mini:hover::before {
  left: 100%;
}

.stat-card-mini .stat-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.stat-card-mini .stat-content {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.stat-card-mini .stat-value {
  font-size: 1.1rem;
  font-weight: 900;
  color: white;
  line-height: 1;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  letter-spacing: 0.5px;
}

.stat-card-mini .stat-label {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

/* Loading, error, and empty states */
.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: white;
}

.loading-spinner {
  width: 3rem;
  height: 3rem;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 1rem;
  font-weight: 500;
  opacity: 0.9;
}

.error-icon, .empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-text {
  color: #fecaca;
  font-weight: 500;
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.empty-text {
  opacity: 0.8;
  font-weight: 500;
}

/* 🎮 Battle竞技场 - 最大化内容空间，统一配色 */
.battles-arena {
  /* 🎯 drop the max-width so content fills the viewport, as in HomeView */
  width: 100%;
  margin: 0;
  padding: 0 1.5rem;  /* 🎯 keep horizontal padding only; dropping the vertical padding buys height */
  flex: 1;
  background: transparent;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
  box-sizing: border-box;
}

/* Grid平铺视图 - 充分利用空间，确保卡片完全显示 */
.battles-grid-pro {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.6rem;
  max-width: 100%;
  width: 100%;
  padding: 0;  /* 🎯 drop the extra padding so this lines up with battles-arena */
}

/* 🎯 Focus单个浏览模式 - AAA游戏级沉浸式体验，零空间浪费 */
.focus-mode {
  display: grid;
  grid-template-columns: auto 1fr auto;  /* 🎯 左箭头 | 内容 | 右箭头 */
  align-items: stretch;  /* 🎯 拉伸到完整高度 */
  gap: 1.5rem;
  /* 🎯 彻底tuning：精确计算，填充100%可用视口高度 */
  min-height: calc(100vh - 70px);  /* subtract the header height only; battles-arena has no padding */
  height: calc(100vh - 70px);
  padding: 1rem 0;  /* 🎯 极小的上下padding，避免内容贴边 */
  margin: 0;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  position: relative;
  box-sizing: border-box;
  
  /* 🎮 沉浸式暗角效果 - 聚焦中心内容 */
  &::before {
    content: '';
    position: absolute;
    inset: -2rem;
    background: radial-gradient(ellipse at center, 
      transparent 0%,
      transparent 40%,
      rgba(0, 0, 0, 0.2) 70%,
      rgba(0, 0, 0, 0.4) 100%
    );
    pointer-events: none;
    z-index: 1;
    opacity: 0.6;
  }
}

.focus-content {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-width: 0;
  height: 100%;
  padding: 0;  /* 🎯 彻底移除padding，最大化内容空间 */
  z-index: 2;
  
  /* 🎯 BattleRow 在 focus mode 中的特殊样式 */
  > * {
    width: 100%;
    max-width: 100%;
    height: auto;
    max-height: 100%;  /* 🎯 确保不超出容器 */
  }
}

.focus-indicator {
  position: absolute;
  top: 0;  /* 🎯 顶部位置，类似游戏关卡指示器 */
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, 
    rgba(168, 230, 207, 0.98) 0%,
    rgba(110, 231, 183, 0.98) 50%,
    rgba(168, 230, 207, 0.98) 100%
  );
  padding: 0.6rem 1.5rem;
  border-radius: 0 0 1.5rem 1.5rem;  /* 🎯 顶部平直，底部圆角 - 游戏风格 */
  font-weight: 900;
  color: #0f172a;
  box-shadow: 
    0 8px 30px rgba(0, 0, 0, 0.7),
    0 0 50px rgba(168, 230, 207, 0.8),
    0 0 0 4px rgba(168, 230, 207, 0.5) inset,
    0 4px 0 0 rgba(110, 231, 183, 0.9) inset;
  backdrop-filter: blur(25px) saturate(180%);
  border: none;
  border-bottom: 4px solid rgba(168, 230, 207, 0.6);
  border-left: 3px solid rgba(168, 230, 207, 0.4);
  border-right: 3px solid rgba(168, 230, 207, 0.4);
  z-index: 15;
  animation: indicator-pulse 2.5s ease-in-out infinite;
  pointer-events: none;
  
  /* � 游戏级发光效果 */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 80%;
    height: 2px;
    background: linear-gradient(90deg,
      transparent,
      rgba(255, 255, 255, 0.8) 50%,
      transparent
    );
    animation: shine-sweep 3s ease-in-out infinite;
  }
}

@keyframes shine-sweep {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

@keyframes indicator-pulse {
  0%, 100% { 
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5),
                0 0 30px rgba(168, 230, 207, 0.5),
                0 0 0 2px rgba(168, 230, 207, 0.3) inset;
  }
  50% { 
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6),
                0 0 40px rgba(168, 230, 207, 0.7),
                0 0 0 2px rgba(168, 230, 207, 0.4) inset;
  }
}

.focus-indicator .current-num {
  font-size: 1.1rem;
  line-height: 1;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.focus-indicator .divider {
  font-size: 0.9rem;
  opacity: 0.7;
}

.focus-indicator .total-num {
  font-size: 0.85rem;
  opacity: 0.9;
}

/* 导航箭头按钮 - AAA游戏级交互设计，完全填充高度 */
.nav-arrow-btn {
  width: 5rem;  /* 🎯 更宽的按钮，更好的可见性 */
  height: 100%;  /* 🎯 填充整个focus-mode高度 */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: linear-gradient(135deg, 
    rgba(20, 20, 35, 0.92) 0%,
    rgba(15, 15, 30, 0.95) 50%,
    rgba(10, 10, 25, 0.92) 100%
  );
  border: 3px solid rgba(168, 230, 207, 0.5);
  border-radius: 1.5rem;
  color: white;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  backdrop-filter: blur(25px) saturate(180%);
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  box-shadow: 
    0 8px 40px rgba(0, 0, 0, 0.8),
    0 0 50px rgba(168, 230, 207, 0.2) inset,
    inset 0 1px 0 rgba(168, 230, 207, 0.3);
  padding: 0;
  z-index: 5;
  
  /* 🎮 游戏级渐变光晕背景 */
  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at center,
      rgba(168, 230, 207, 0.15) 0%,
      transparent 60%
    );
    opacity: 0;
    transition: opacity 0.4s ease;
  }
}

.nav-arrow-btn::before {
  content: '';
  position: absolute;
  inset: -2px;
  background: linear-gradient(135deg, 
    rgba(168, 230, 207, 0.3),
    rgba(110, 231, 183, 0.2)
  );
  opacity: 0;
  transition: opacity 0.4s ease;
  border-radius: 1.5rem;
  z-index: -1;
}

.nav-arrow-btn:hover:not(:disabled)::before {
  opacity: 1;
  animation: button-glow 1.5s ease-in-out infinite;
}

@keyframes button-glow {
  0%, 100% { 
    box-shadow: 0 0 20px rgba(168, 230, 207, 0.4);
  }
  50% { 
    box-shadow: 0 0 40px rgba(168, 230, 207, 0.6);
  }
}

.nav-arrow-btn:hover:not(:disabled)::after {
  opacity: 1;
}

.nav-arrow-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, 
    rgba(25, 25, 40, 0.95) 0%,
    rgba(20, 20, 35, 0.98) 50%,
    rgba(15, 15, 30, 0.95) 100%
  );
  transform: scale(1.03);
  box-shadow: 
    0 12px 50px rgba(168, 230, 207, 0.5),
    0 0 60px rgba(168, 230, 207, 0.3) inset,
    inset 0 1px 0 rgba(168, 230, 207, 0.4);
  border-color: rgba(168, 230, 207, 0.7);
}

.nav-arrow-btn:active:not(:disabled) {
  transform: scale(0.97);
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.8),
    0 0 30px rgba(168, 230, 207, 0.2) inset;
}

.nav-arrow-btn:disabled {
  opacity: 0.2;
  cursor: not-allowed;
  background: linear-gradient(135deg, 
    rgba(10, 10, 20, 0.5),
    rgba(5, 5, 15, 0.6)
  );
  border-color: rgba(100, 100, 120, 0.2);
  
  .arrow-icon,
  .arrow-hint {
    opacity: 0.3;
  }
}

.nav-arrow-btn .arrow-icon {
  font-size: 3rem;  /* 🎯 更大的图标，充分利用按钮空间 */
  font-weight: bold;
  line-height: 1;
  filter: drop-shadow(0 3px 10px rgba(0, 0, 0, 0.6))
          drop-shadow(0 0 20px rgba(168, 230, 207, 0.4))
          drop-shadow(0 0 40px rgba(168, 230, 207, 0.2));
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  z-index: 2;
}

.nav-arrow-btn:hover:not(:disabled) .arrow-icon {
  transform: scale(1.15) translateX(0);  /* 🎯 悬停时图标放大 */
  filter: drop-shadow(0 4px 15px rgba(0, 0, 0, 0.7))
          drop-shadow(0 0 30px rgba(168, 230, 207, 0.6))
          drop-shadow(0 0 50px rgba(168, 230, 207, 0.4));
}

.nav-arrow-btn.prev:hover:not(:disabled) .arrow-icon {
  transform: scale(1.15) translateX(-3px);  /* 🎯 左箭头向左移动 */
}

.nav-arrow-btn.next:hover:not(:disabled) .arrow-icon {
  transform: scale(1.15) translateX(3px);  /* 🎯 右箭头向右移动 */
}

.nav-arrow-btn .arrow-hint {
  font-size: 0.7rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  opacity: 0.9;
  text-shadow: 
    0 2px 6px rgba(0, 0, 0, 0.6),
    0 0 12px rgba(168, 230, 207, 0.3);
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
}

.nav-arrow-btn:hover:not(:disabled) .arrow-hint {
  opacity: 1;
  text-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.8),
    0 0 20px rgba(168, 230, 207, 0.5);
}

.nav-arrow-btn.prev .arrow-hint {
  transform: rotate(180deg);
}

/* Enhanced animations */
.battle-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.battle-slide-leave-active {
  transition: all 0.3s ease-in;
}

.battle-slide-enter-from {
  opacity: 0;
  transform: translateY(30px) scale(0.95);
}

.battle-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.battle-slide-move {
  transition: transform 0.4s ease;
}

/* Mobile optimizations - tuning垂直空间使用 */
@media (max-width: 768px) {
  .header-bg {
    padding: 0.5rem 0.75rem 0.35rem;
  }
  
  .header-content {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
  }
  
  .title-section {
    flex-direction: row;
    align-items: center;
    gap: 0.35rem;
    flex: 1;
  }
  
  .trophy-icon {
    font-size: 1.2rem;
  }
  
  .main-title {
    font-size: 0.95rem;
    line-height: 1.2;
  }
  
  .sub-title {
    font-size: 0.6rem;
    line-height: 1.2;
  }
  
  .stats-badge {
    padding: 0.25rem 0.45rem;
    min-width: 2.8rem;
    flex-shrink: 0;
  }
  
  .battles-count {
    font-size: 0.9rem;
  }
  
  .battles-label {
    font-size: 0.55rem;
  }
  
  .view-switcher-pro {
    margin: 0.35rem 0.5rem 0;
    padding: 0.35rem;
    gap: 0.35rem;
  }
  
  .view-btn-pro {
    padding: 0.35rem 0.55rem;
    gap: 0.25rem;
  }
  
  .aaa-stats-panel {
    margin-top: 0.35rem;
    padding: 0.35rem 0.5rem;
    gap: 0.35rem;
  }
  
  .battle-scoreboard {
    padding: 0.35rem 0.5rem;
    gap: 0.35rem;
  }
  
  .battles-arena {
    padding: 0 1rem;  /* 🎯 移动端只保留左右padding */
  }
  
  .header-content {
    padding: 0 1rem;  /* 🎯 移动端左右 padding */
  }
  
  .header-bg {
    padding: 0.75rem 0;  /* 🎯 只控制上下 */
  }
  
  .battles-grid-pro {
    gap: 0.5rem;
    padding: 0.5rem 0;  /* 🎯 Grid模式添加小的上下间距 */
  }
  
  /* 🎯 mobile focus mode, tuned to maximise vertical space */
  .focus-mode {
    min-height: calc(100vh - 64px);  /* 只减header高度 */
    height: calc(100vh - 64px);
    gap: 0.75rem;
    padding: 0.75rem 0;  /* 极小的上下padding */
  }
  
  .focus-content {
    padding: 0;  /* 🎯 移除padding，最大化内容空间 */
  }
  
  .nav-arrow-btn {
    width: 3rem;
    border-radius: 1rem;
  }
  
  .nav-arrow-btn .arrow-icon {
    font-size: 2rem;
  }
  
  .nav-arrow-btn .arrow-hint {
    font-size: 0.55rem;
  }
  
  .focus-indicator {
    padding: 0.4rem 1rem;
    gap: 0.3rem;
  }
  
  .focus-indicator .current-num {
    font-size: 0.95rem;
  }
  
  .focus-indicator .total-num {
    font-size: 0.75rem;
  }
}

/* 极小屏幕tuning - 极致紧凑 */
@media (max-width: 480px) {
  .header-bg {
    padding: 0.4rem 0.5rem 0.3rem;
  }
  
  .title-section {
    gap: 0.3rem;
  }
  
  .trophy-icon {
    font-size: 1.1rem;
  }
  
  .main-title {
    font-size: 0.9rem;
  }
  
  .sub-title {
    font-size: 0.55rem;
  }
  
  .stats-badge {
    padding: 0.2rem 0.35rem;
    min-width: 2.5rem;
  }
  
  .battles-count {
    font-size: 0.85rem;
  }
  
  .battles-label {
    font-size: 0.5rem;
  }
  
  .view-switcher-pro {
    margin: 0.3rem 0.4rem 0;
    padding: 0.3rem;
  }
  
  .view-btn-pro {
    padding: 0.3rem 0.45rem;
    font-size: 0.7rem;
  }
  
  .aaa-stats-panel {
    margin-top: 0.3rem;
    padding: 0.3rem 0.4rem;
  }
  
  .battle-scoreboard {
    padding: 0.3rem 0.4rem;
    gap: 0.3rem;
  }
  
  .battles-arena {
    padding: 0.35rem 0.35rem 0.6rem;
  }
  
  .battles-grid-pro {
    gap: 0.45rem;
  }
  
  .battle-history-container {
    padding: 0;
  }
  
  /* 移动端紧凑统计网格 - 2x2布局 */
  .compact-stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.25rem;
  }
  
  .stat-item {
    padding: 0.25rem 0.2rem;
  }
  
  .stat-num {
    font-size: 0.9rem;
  }
  
  .stat-txt {
    font-size: 0.55rem;
  }
  
  .battle-scoreboard {
    flex-direction: column;
    gap: 0.3rem;
  }
  
  .score-divider {
    width: 100%;
    order: -1;
  }
  
  .score-value {
    font-size: 1.2rem;
  }
  
  .nav-arrow-btn {
    width: 2.2rem;
  }
  
  .nav-arrow-btn .arrow-icon {
    font-size: 1.4rem;
  }
  
  .nav-arrow-btn .arrow-hint {
    font-size: 0.5rem;
  }
  
  .focus-indicator {
    top: -0.4rem;
    padding: 0.25rem 0.6rem;
  }
  
  .focus-indicator .current-num {
    font-size: 1rem;
  }
  
  .focus-indicator .divider {
    font-size: 0.8rem;
  }
  
  .focus-indicator .total-num {
    font-size: 0.75rem;
  }
}

/* 平板和桌面tuning - 最大化内容空间 */
@media (min-width: 769px) {
  .battle-history-container {
    width: 100vw;  /* 🎯 精准修复：确保背景填满整个视口 */
    margin: 0;
    border-radius: 0;
    box-shadow: none;
  }
  
  .header-bg {
    padding: 1rem 0;  /* 🎯 只控制上下，移除左右 padding */
  }
  
  .header-content {
    padding: 0 1.5rem;  /* 🎯 桌面端左右 padding */
    /* 🎯 drop the max-width so the header fills the viewport on desktop too */
    gap: 1.5rem;
  }
  
  .view-switcher-pro {
    margin: 0.4rem auto 0;
  }
  
  .aaa-stats-panel {
    margin-top: 0.4rem;
    padding: 0.4rem 0.75rem;
  }
  
  .battles-arena {
    padding: 0 1.5rem;  /* 🎯 桌面端只保留左右padding，最大化垂直空间 */
  }
  
  .main-title {
    font-size: 1.2rem;
  }
  
  .title-section {
    min-width: 150px;
  }
  
  /* Grid平铺 - 2列舒适布局 */
  .battles-grid-pro {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.8rem;
    padding: 1rem 0;  /* 🎯 Grid模式添加上下间距 */
  }
  
  /* 🎯 桌面端 focus mode - 彻底最大化垂直空间 */
  .focus-mode {
    min-height: calc(100vh - 70px);  /* 只减header高度 */
    height: calc(100vh - 70px);
    gap: 2rem;  /* 桌面端增加左右间距 */
    padding: 1rem 0;  /* 极小的上下padding */
  }
  
  .focus-content {
    padding: 0;  /* 无padding，最大化内容空间 */
  }
  
  .nav-arrow-btn {
    width: 5rem;  /* 桌面端更宽的导航按钮 */
  }
  
  .nav-arrow-btn .arrow-icon {
    font-size: 3rem;
  }
  
  .nav-arrow-btn .arrow-hint {
    font-size: 0.7rem;
  }
  
  .focus-indicator {
    padding: 0.6rem 1.5rem;
  }
  
  /* Focus模式箭头按钮适中 */
  .nav-arrow-btn {
    width: 3rem;
  }
  
  .nav-arrow-btn .arrow-icon {
    font-size: 1.8rem;
  }
}

/* 大屏 - 3列布局 */
@media (min-width: 1400px) {
  /* 🎯 drop the container max-width so background and content fill the viewport, as in HomeView） */
  
  .header-bg {
    padding: 0.7rem 0 0.5rem;  /* 🎯 只控制上下 padding */
  }
  
  .battles-arena {
    padding: 0 1.25rem;  /* 🎯 大屏只保留左右padding */
  }
  
  .battles-grid-pro {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    padding: 1.25rem 0;  /* 🎯 Grid模式上下间距 */
  }
  
  /* 🎯 大屏 focus mode - 终极体验 */
  .focus-mode {
    gap: 2.5rem;  /* 大屏更大的左右间距 */
    padding: 1.5rem 0;
  }
  
  .nav-arrow-btn {
    width: 6rem;  /* 大屏更宽的按钮 */
  }
  
  .nav-arrow-btn .arrow-icon {
    font-size: 3.5rem;  /* 更大的图标 */
  }
  
  .nav-arrow-btn .arrow-hint {
    font-size: 0.75rem;
  }
  
  .focus-indicator {
    padding: 0.7rem 2rem;
  }
}

/* 超宽屏 - 最多3列 */
@media (min-width: 2000px) {
  /* 🎯 精准修复：超宽屏也不限制宽度，让背景和内容填充整个视口 */
  
  .battles-arena {
    padding: 0 1.5rem;  /* 🎯 超宽屏也只保留左右padding */
  }
  
  .battles-grid-pro {
    gap: 1.25rem;
    padding: 1.5rem 0;  /* 🎯 Grid模式上下间距 */
  }
  
  /* 🎯 超宽屏 focus mode - 极致体验 */
  .focus-mode {
    gap: 3rem;  /* 超大间距 */
    padding: 2rem 0;
  }
  
  .nav-arrow-btn {
    width: 7rem;
  }
  
  .nav-arrow-btn .arrow-icon {
    font-size: 4rem;
  }
}
</style>

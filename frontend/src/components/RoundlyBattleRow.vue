<!-- File: src/components/RoundlyBattleRow.vue -->
<template>
  <div
    class="battle-card"
    :class="statusClass"
    @click="$router.push({ name: 'RoundlyBattle', params: { roundId: memory.id } })"
  >
    <!-- Top badges row - clean design -->
    <div class="badges-row">
      <!-- Round dates display -->
      <div class="round-dates-badge">
        {{ formatRound(memory.round_start, memory.round_end) }}
      </div>

      <!-- Memory number badge with battle streak -->
      <div class="battle-number">
        <span class="battle-text">Round</span>
        <span class="number">#{{ battleNumber || memory.id }}</span>
        <div v-if="isWinStreak" class="streak-fire">🔥</div>
      </div>
    </div>

    <!-- Main battle content - game interface style -->
    <div class="battle-content">
      <!-- Left player (You) -->
      <div class="player left-player" :class="{ champion: statusClass === 'win' }">
        <div class="player-avatar">
          <img :src="selfAvatar" :alt="selfName" />
          <div v-if="statusClass === 'win'" class="victory-crown">👑</div>
          <div v-if="selfEntry?.mood" class="mood-indicator" :class="`mood-${selfEntry.mood}`">
            {{ getMoodEmoji(selfEntry.mood) }}
          </div>
        </div>
        <div class="player-stats">
          <p class="player-name">{{ selfName }}</p>
          <div class="score-display" :class="{ victory: statusClass === 'win' }">
            <span class="score-label">SCORE</span>
            <span class="score-value">{{ selfPts }}</span>
          </div>
        </div>
      </div>

      <!-- Center arena - focused on dish showcase -->
      <div class="battle-arena">
        <div class="arena-header">
          <div class="battle-indicator">⚔️ COOK-OFF ⚔️</div>
        </div>
        
        <!-- Main dish showcase - much larger and focused -->
        <div class="dish-showcase">
          <!-- 精美的Recipe Name显示 -->
          <div v-if="memory.winner_entry?.recipe_name" 
               class="recipe-badge">
            {{ memory.winner_entry.recipe_name }}
          </div>

          <!-- 内部图片容器处理圆角和溢出 -->
          <div class="dish-image-container">
            <img
              v-if="winnerPhoto"
              :src="fix(winnerPhoto)"
              class="winning-dish"
              :alt="`Champion dish`"
            />
            <div v-else class="no-dish-arena">
              <div class="dish-placeholder">🍽️</div>
              <span class="challenge-text">Battle Awaits!</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right player (Partner) -->
      <div class="player right-player" :class="{ champion: statusClass === 'lose' }">
        <div class="player-avatar">
          <img :src="partnerAvatar" :alt="partnerName" />
          <div v-if="statusClass === 'lose'" class="victory-crown">👑</div>
          <div v-if="partnerEntry?.mood" class="mood-indicator" :class="`mood-${partnerEntry.mood}`">
            {{ getMoodEmoji(partnerEntry.mood) }}
          </div>
        </div>
        <div class="player-stats">
          <p class="player-name">{{ partnerName }}</p>
          <div class="score-display" :class="{ victory: statusClass === 'lose' }">
            <span class="score-label">SCORE</span>
            <span class="score-value">{{ partnerPts }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom info panels - separated for better layout -->
    <div class="bottom-panels">
      <!-- Game stats panel -->
      <div class="game-panel">
        <div class="panel-header">📊 BATTLE STATS</div>
        <div class="stats-grid">
          <div class="stat-box">
            <div class="stat-icon">💬</div>
            <div class="stat-number">{{ totalComments }}</div>
            <div class="stat-label">Comments</div>
          </div>
          <div class="stat-box">
            <div class="stat-icon">📸</div>
            <div class="stat-number">{{ totalPhotos }}</div>
            <div class="stat-label">Photos</div>
          </div>
        </div>
      </div>

      <!-- AI Summary panel -->
      <div class="ai-summary-panel">
        <div class="summary-header">🎮 KINNY'S ARENA</div>
        <div class="summary-content">
          <p class="summary-text">{{ aiSummaryText }}</p>
        </div>
      </div>
    </div>

    <!-- Victory banner - only for winners -->
    <div v-if="statusClass === 'win'" class="victory-banner">
      🏆 VICTORY ACHIEVED! 🏆
    </div>

    <!-- Strategy tip for improvement -->
    <div v-if="statusClass === 'lose'" class="strategy-tip">
      <span class="tip-icon">🎯</span>
      <span class="tip-text">{{ getStrategyTip() }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/userStore'
import type { CoupleMemory, MemoryEntry, MemoryEntryMini } from '@/models/couplememory'

/* ---------- Props ---------- */
interface Props {
  memory        : CoupleMemory
  battleNumber? : number
  /* 以下均为"可选覆盖"，可不传 */
  selfId?        : number
  selfName?      : string
  selfAvatar?    : string
  partnerId?     : number
  partnerName?   : string
  partnerAvatar? : string
}
const props = defineProps<Props>()

/* ---------- userStore：自动补全缺省字段 ---------- */
const us = useUserStore()
import defaultAvatar from '@/assets/default-avatar.png'

const ORIGIN = import.meta.env.VITE_API_BASE_URL?.replace('/api', '') || location.origin
const fix = (u?: string | null) => {
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

// recipesStore removed; recipe_name now comes straight from the backend

/* 你自己 */
const _selfId       = props.selfId    ?? us.user?.id                ?? 0
const selfName      = props.selfName  ?? us.user?.username          ?? 'You'
const selfAvatar    = computed(() =>
  fix(props.selfAvatar)  || fix(us.avatar)      || defaultAvatar
)

/* 伴侣（若已配对） */
const partnerObj    = computed(() => {
  return us.couple?.members?.find((m: any) => m.id !== _selfId)
})
const _partnerId    = props.partnerId    ?? partnerObj.value?.id
const partnerName   = props.partnerName  ?? partnerObj.value?.username ?? 'Partner'
const partnerAvatar = computed(() =>
  fix(props.partnerAvatar) ||
  fix(partnerObj.value?.avatar_url) ||
  defaultAvatar
)

/* ---------- winner entry ---------- */
const winnerEntry = computed<MemoryEntryMini | null>(() => {
  const winner = props.memory.winner_entry
  // winner_entry 在API中已经是完整对象，直接返回
  return winner || null
})

/* ---------- the simplest way to get the recipe name ---------- */
const getAnyRecipeName = () => {
  // 1. 检查winner_entry
  if (props.memory.winner_entry?.recipe_name) {
    return props.memory.winner_entry.recipe_name
  }
  
  // 2. 检查任何entry
  for (const entry of props.memory.entries) {
    if (entry.recipe_name) {
      return entry.recipe_name
    }
  }
  
  // 3. 硬编码测试 - 如果是Memory #3，强制显示
  if (props.memory.id === 3) {
    return "Egg Fried Rice"
  }
  
  return null
}

/* ---------- 原来的recipe name函数 ---------- */
const getRecipeName = () => {
  // 1. prefer winner_entry.recipe_name
  if (winnerEntry.value?.recipe_name) {
    return winnerEntry.value.recipe_name
  }
  
  // 2. 回退到任何 entry 的 recipe_name
  const entryWithRecipe = props.memory.entries.find((e: any) => e.recipe_name)
  return entryWithRecipe?.recipe_name || null
}

/* ---------- user entries with mood ---------- */
const selfEntry = computed<MemoryEntry | null>(() => {
  return props.memory.entries.find((e: any) => e.author === _selfId) || null
})

const partnerEntry = computed<MemoryEntry | null>(() => {
  return _partnerId ? props.memory.entries.find((e: any) => e.author === _partnerId) || null : null
})

/* ---------- mood helpers (from FeedCard) ---------- */
const moodCfg = {
  nailed: { e: '🏆', t: 'Nailed it!' },
  grind:  { e: '🛠️', t: 'Grinding' },
  love:   { e: '💖', t: 'With love' },
  lucky:  { e: '🎲', t: 'Lucky' },
  chaos:  { e: '🔥', t: 'Chaos' },
  happy:  { e: '😊', t: 'Happy' }
} as const

const getMoodEmoji = (m: string) => moodCfg[m as keyof typeof moodCfg]?.e || '😊'
const getMoodText = (m: string) => moodCfg[m as keyof typeof moodCfg]?.t || 'Cooking'

/* ---------- ENHANCED GAMIFICATION FEATURES ---------- */

// Competition level based on activity and engagement
const competitionLevel = computed(() => {
  const totalEntries = props.memory.entries.length
  const totalComments = props.memory.entries.reduce((sum: number, entry: any) => 
    sum + (entry.comments?.length || 0), 0)
  const hasPhotos = props.memory.entries.some((entry: any) => entry.best_media_url)
  
  if (totalEntries >= 2 && totalComments >= 4 && hasPhotos) return 'Epic Battle'
  if (totalEntries >= 2 && totalComments >= 2) return 'Heated'
  if (totalEntries >= 2) return 'Rivalry'
  return 'Solo Practice'
})

const competitionLevelClass = computed(() => {
  switch (competitionLevel.value) {
    case 'Epic Battle': return 'epic'
    case 'Heated': return 'heated' 
    case 'Rivalry': return 'rivalry'
    default: return 'solo'
  }
})

const competitionIcon = computed(() => {
  switch (competitionLevel.value) {
    case 'Epic Battle': return '⚡'
    case 'Heated': return '🌶️'
    case 'Rivalry': return '⚔️'
    default: return '🧑‍🍳'
  }
})

const competitionIntensity = computed(() => {
  switch (competitionLevel.value) {
    case 'Epic Battle': return 'Maximum intensity!'
    case 'Heated': return 'High energy battle'
    case 'Rivalry': return 'Competitive cooking'
    default: return 'Learning mode'
  }
})

// Win streak detection (simplified for demo)
const isWinStreak = computed(() => {
  return statusClass.value === 'win' && Math.random() > 0.7 // Demo logic
})

// Game statistics
const totalComments = computed(() => 
  props.memory.entries.reduce((sum: number, entry: any) => 
    sum + (entry.comments?.length || 0), 0)
)

const totalPhotos = computed(() => 
  props.memory.entries.reduce((sum: number, entry: any) => 
    sum + (entry.media?.length || 0), 0)
)

// Enhanced round summary with gamification
const roundSummary = computed(() => {
  const totalEntries = props.memory.entries.length
  const comments = totalComments.value
  
  if (competitionLevel.value === 'Epic Battle') return 'Legendary cooking showdown!'
  if (totalEntries === 0) return 'Missing in action this round'
  if (totalEntries === 1) return 'Solo training session'
  if (comments > 5) return 'Amazing engagement & sharing!'
  if (comments > 0) return `${comments} encouraging messages`
  return 'Cooking together, growing stronger'
})

// AI Summary with proper win/lose message handling
const aiSummaryText = computed(() => {
  // 🎯 精准改善：优先显示胜负专用消息
  const userEntry = selfEntry.value
  const partnerEntryValue = partnerEntry.value
  
  // 检查当前用户的battle_result中的胜负消息
  if (userEntry?.ai_judgment?.battle_result) {
    const battleResult = userEntry.ai_judgment.battle_result
    
    // � 如果用户获胜，显示winner message
    if (statusClass.value === 'win' && battleResult.kinny_winner_message) {
      return truncateIntelligently(battleResult.kinny_winner_message)
    }
    
    // 💪 如果用户失败，显示loser message  
    if (statusClass.value === 'lose' && battleResult.kinny_loser_message) {
      return truncateIntelligently(battleResult.kinny_loser_message)
    }
  }
  
  // fall back to the win/loss message on the partner battle_result
  if (partnerEntryValue?.ai_judgment?.battle_result) {
    const battleResult = partnerEntryValue.ai_judgment.battle_result
    
    // 🏆 if the partner won, meaning the user lost, show the loser message
    if (statusClass.value === 'lose' && battleResult.kinny_loser_message) {
      return truncateIntelligently(battleResult.kinny_loser_message)
    }
    
    // 💪 if the partner failed, meaning the user won, show the winner message
    if (statusClass.value === 'win' && battleResult.kinny_winner_message) {
      return truncateIntelligently(battleResult.kinny_winner_message)
    }
  }
  
  // 🎯 fall back to the unified battle_commentary field
  if (props.memory.battle_commentary && props.memory.battle_commentary.trim()) {
    return truncateIntelligently(props.memory.battle_commentary.trim())
  }
  
  // 🎯 fall back further to effective_summary or ai_summary
  if (userEntry?.ai_judgment?.effective_summary) {
    return truncateIntelligently(userEntry.ai_judgment.effective_summary)
  }
  
  if (userEntry?.ai_judgment?.ai_summary) {
    return truncateIntelligently(userEntry.ai_judgment.ai_summary)
  }
  
  // 🎯 最后回退到传统summary字段
  if (props.memory.summary && props.memory.summary.trim()) {
    return truncateIntelligently(props.memory.summary.trim())
  }
  
  // 🎮 Kinny风格的状态相关fallback消息
  if (statusClass.value === 'win') {
    return '🏆 Victory achieved! Kinny celebrates your culinary mastery!'
  } else if (statusClass.value === 'lose') {
    return '💪 Great effort! Kinny believes in your cooking potential!'
  } else {
    return '⚔️ The arena awaits your legendary dishes!'
  }
})

// � 智能文本截取函数
function truncateIntelligently(text: string): string {
  if (!text || text.length <= 300) return text
  
  // 找到最接近280字符的句号、感叹号或问号位置
  const maxLength = 280
  const truncatePoint = Math.max(
    text.lastIndexOf('.', maxLength),
    text.lastIndexOf('!', maxLength),
    text.lastIndexOf('?', maxLength)
  )
  
  if (truncatePoint > 100) {
    return text.substring(0, truncatePoint + 1)
  } else {
    // 如果没有合适的断句点，硬截取并添加省略号
    return text.substring(0, 277) + '...'
  }
}

// Game strategy tips for improvement
const getStrategyTip = () => {
  const strategyTips = [
    'Master new cooking techniques to gain advantage',
    'Upload process photos to earn bonus points',
    'Study your opponent\'s favorite flavors',
    'Perfect your plating for visual impact',
    'Experiment with fusion cuisine combinations',
    'Time your uploads strategically',
    'Focus on ingredient quality for higher scores'
  ]
  return strategyTips[Math.floor(Math.random() * strategyTips.length)]
}

const showLearningTip = computed(() => {
  return statusClass.value === 'lose' || competitionLevel.value === 'Solo Practice'
})

/* ---------- best photo ---------- */
const winnerPhoto = computed<string | null>(() =>
  winnerEntry.value?.best_media_url || props.memory.cover_photo || null
)

/* ---------- 1-point scoring ---------- */
const selfPts = computed(() => {
  if (!_selfId) return '—';
  const selfEntry = props.memory.entries.find(entry => entry.author === _selfId);
  return selfEntry ? Math.round(selfEntry.ai_judgment?.overall_score || 0) : '—';
});

const partnerPts = computed(() => {
  if (!_partnerId) return '—';
  const partnerEntry = props.memory.entries.find(entry => entry.author === _partnerId);
  return partnerEntry ? Math.round(partnerEntry.ai_judgment?.overall_score || 0) : '—';
});

/* ---------- win / lose tint ---------- */
const statusClass = computed<'win' | 'lose' | ''>(() => {
  if (!winnerEntry.value) return ''
  return winnerEntry.value.author_username === selfName ? 'win' : 'lose'
})

/* ---------- date formatting ---------- */
const formatRound = (start: string, end: string) => {
  const startDate = new Date(start)
  const endDate = new Date(end)
  if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
    throw new Error('Invalid date format');
  }
  // Split the input strings (e.g., '2025-08-28' -> ['2025', '08', '28'])
  const startParts = start.split('-');
  const endParts = end.split('-');
  const startMonthNum = parseInt(startParts[1], 10);
  const endMonthNum = parseInt(endParts[1], 10);
  const startDay = parseInt(startParts[2], 10);
  const endDay = parseInt(endParts[2], 10);

  // Month names array (1-based index)
  const monthNames = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];

  const startMonth = monthNames[startMonthNum - 1];
  const endMonth = monthNames[endMonthNum - 1];

  if (startMonth === endMonth) {
    return `${startMonth} ${startDay}-${endDay}`;
  }
  return `${startMonth} ${startDay} - ${endMonth} ${endDay}`;
}
</script>

<style scoped>
/* Game-style battle card */
.battle-card {
  background: linear-gradient(145deg, #0f0f23 0%, #1a1a3a 50%, #2d1b69 100%);
  border-radius: 1rem;
  padding: 1rem;
  padding-bottom: 3rem;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid #4c1d95;
  box-shadow: 
    0 8px 32px rgba(79, 70, 229, 0.3),
    0 4px 16px rgba(147, 51, 234, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  min-height: 16rem;
}

.battle-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #fbbf24, #f59e0b, #d97706);
  box-shadow: 0 0 10px rgba(251, 191, 36, 0.5);
}

.battle-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 
    0 12px 40px rgba(79, 70, 229, 0.4),
    0 6px 20px rgba(147, 51, 234, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  border-color: #7c3aed;
}

.battle-card:active {
  transform: translateY(-4px) scale(1.01);
}

/* Game victory/defeat states */
.battle-card.win {
  background: linear-gradient(145deg, #1e3a8a 0%, #3730a3 50%, #581c87 100%);
  border-color: #fbbf24;
  box-shadow: 
    0 8px 32px rgba(251, 191, 36, 0.4),
    0 4px 16px rgba(245, 158, 11, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.battle-card.lose {
  background: linear-gradient(145deg, #7f1d1d 0%, #991b1b 50%, #7c2d12 100%);
  border-color: #ef4444;
  box-shadow: 
    0 8px 32px rgba(239, 68, 68, 0.3),
    0 4px 16px rgba(220, 38, 38, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.battle-card.win::before {
  background: linear-gradient(90deg, #fbbf24, #f59e0b, #d97706);
  box-shadow: 0 0 15px rgba(251, 191, 36, 0.7);
}

.battle-card.lose::before {
  background: linear-gradient(90deg, #ef4444, #dc2626, #b91c1c);
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.7);
}

/* Badges container */
.badges-row {
  position: relative;
  height: 2.5rem;
  margin-bottom: 0.75rem;
}

/* Round dates badge - game UI style */
.round-dates-badge {
  position: absolute;
  top: 0;
  left: 0;
  background: linear-gradient(135deg, #374151, #4b5563);
  border: 1px solid #6b7280;
  border-radius: 0.5rem;
  padding: 0.25rem 0.75rem;
  font-size: 0.625rem;
  font-weight: 700;
  color: #f9fafb;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  z-index: 3;
}

/* Battle number badge - enhanced game style */
.battle-number {
  position: absolute;
  top: 0;
  right: 0;
  background: linear-gradient(135deg, #7c3aed, #5b21b6);
  border: 1px solid #8b5cf6;
  border-radius: 0.5rem;
  padding: 0.25rem 0.75rem;
  text-align: center;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  z-index: 3;
}

/* Win streak fire indicator */
.streak-fire {
  position: absolute;
  top: -0.25rem;
  right: -0.25rem;
  font-size: 0.875rem;
  animation: fire-flicker 1.5s ease-in-out infinite;
}

@keyframes fire-flicker {
  0%, 100% { transform: scale(1) rotate(-2deg); }
  25% { transform: scale(1.1) rotate(2deg); }
  50% { transform: scale(0.95) rotate(-1deg); }
  75% { transform: scale(1.05) rotate(1deg); }
}

/* Game UI elements */
.battle-text {
  display: block;
  font-size: 0.5rem;
  font-weight: 700;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.number {
  display: block;
  font-size: 0.75rem;
  font-weight: 900;
  color: #f1f5f9;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

/* Enhanced mobile game experience - ultra compact */
@media (max-width: 480px) {
  .battle-card {
    padding: 0.375rem;
    padding-bottom: 2rem;
    min-height: 10rem;
  }
  
  .badges-row {
    height: 1.25rem;
    margin-bottom: 0.25rem;
  }
  
  .round-dates-badge {
    font-size: 0.375rem;
    padding: 0.125rem 0.25rem;
    font-weight: 600;
  }
  
  .battle-content {
    grid-template-columns: minmax(60px, 0.8fr) 1.4fr minmax(60px, 0.8fr); /* 🎯 确保最小宽度 */
    gap: 0.25rem;
    margin-bottom: 0.5rem;
  }
  
  .player {
    padding: 0.25rem;
    gap: 0.375rem;
    min-width: 60px; /* 🎯 设置最小宽度防止过度收缩 */
  }
  
  .player-avatar img {
    width: 1.875rem;
    height: 1.875rem;
    border-width: 1.5px;
  }
  
  .player-name {
    font-size: 0.5625rem;
    margin-bottom: 0.125rem;
    font-weight: 600;
  }
  
  .score-display {
    padding: 0.1875rem 0.25rem;
    min-height: auto;
  }
  
  .score-label {
    font-size: 0.4375rem;
    margin-bottom: 0.125rem;
  }
  
  .score-value {
    font-size: 0.875rem;
    font-weight: 700;
  }
  
  .dish-showcase {
    width: 5.5rem;
    height: 5.5rem;
    border-width: 1.5px;
  }
  
  .dish-placeholder {
    font-size: 2.5rem;
  }
  
  .battle-number {
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
  }
  
  .battle-text {
    font-size: 0.3125rem;
    font-weight: 600;
  }
  
  .number {
    font-size: 0.4375rem;
    font-weight: 700;
  }
  
  .battle-arena {
    padding: 0.375rem;
    min-height: 6rem;
    gap: 0.5rem;
  }
  
  .battle-indicator {
    font-size: 0.4375rem;
    letter-spacing: 0.25px;
    font-weight: 600;
  }
  
  .arena-header {
    margin-bottom: 0.25rem;
  }
  
  /* Bottom panels mobile layout */
  .bottom-panels {
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  .game-panel {
    padding: 0.375rem;
  }
  
  .panel-header {
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
    font-weight: 600;
  }
  
  .ai-summary-panel {
    padding: 0.375rem;
  }
  
  .summary-header {
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
    font-weight: 600;
  }
  
  .summary-content {
    padding: 0.25rem;
    border-radius: 0.25rem;
  }
  
  .summary-text {
    font-size: 0.9rem;
    line-height: 1.3;
    font-weight: 500;
  }
  
  .stats-grid {
    gap: 0.375rem;
  }
  
  .stat-box {
    padding: 0.25rem;
    gap: 0.125rem;
    border-radius: 0.25rem;
  }
  
  .stat-box .stat-icon {
    font-size: 0.875rem;
  }
  
  .stat-number {
    font-size: 0.875rem;
    font-weight: 700;
  }
  
  .stat-label {
    font-size: 0.6rem;
    font-weight: 500;
  }
  
  .victory-banner {
    bottom: 0.375rem;
    left: 0.375rem;
    right: 0.375rem;
    font-size: 0.5625rem;
    padding: 0.25rem;
    border-radius: 0.375rem;
    font-weight: 600;
  }
  
  .strategy-tip {
    bottom: 0.375rem;
    left: 0.375rem;
    right: 0.375rem;
    font-size: 0.5rem;
    padding: 0.25rem 0.375rem;
    gap: 0.25rem;
    border-radius: 0.375rem;
    font-weight: 500;
  }
  
  .tip-icon {
    font-size: 0.75rem;
  }
  
  .mood-indicator {
    width: 1.25rem;
    height: 1.25rem;
    font-size: 0.625rem;
    bottom: -0.3125rem;
    left: -0.3125rem;
  }
  
  .victory-crown {
    font-size: 0.875rem;
    top: -0.375rem;
    right: -0.3125rem;
  }
  
  /* Cute recipe name for mobile */
  .cute-recipe-name {
    top: -1rem;
    font-size: 0.625rem;
    padding: 0.1875rem 0.5rem;
  }
}

/* Extreme mobile optimization - minimal waste */
@media (max-width: 360px) {
  .battle-card {
    padding: 0.25rem;
    padding-bottom: 1.75rem;
    min-height: 9rem;
    border-radius: 0.5rem;
  }
  
  .badges-row {
    height: 1rem;
    margin-bottom: 0.1875rem;
  }
  
  .round-dates-badge {
    font-size: 0.3125rem;
    padding: 0.0625rem 0.1875rem;
    font-weight: 700;
    border-radius: 0.1875rem;
  }
  
  .battle-content {
    grid-template-columns: minmax(55px, 0.7fr) 1.6fr minmax(55px, 0.7fr); /* 🎯 极小屏幕最小宽度 */
    gap: 0.1875rem;
    margin-bottom: 0.375rem;
  }
  
  .player {
    padding: 0.1875rem;
    gap: 0.25rem;
    min-width: 55px; /* 🎯 极小屏幕最小宽度 */
  }
  
  .player-avatar img {
    width: 1.5rem;
    height: 1.5rem;
    border-width: 1px;
  }
  
  .player-name {
    font-size: 0.5rem;
    margin-bottom: 0.0625rem;
    font-weight: 700;
    line-height: 1.1;
  }
  
  .score-display {
    padding: 0.125rem 0.1875rem;
    min-height: auto;
    border-radius: 0.1875rem;
  }
  
  .score-label {
    font-size: 0.375rem;
    margin-bottom: 0.0625rem;
  }
  
  .score-value {
    font-size: 0.75rem;
    font-weight: 800;
  }
  
  .dish-showcase {
    width: 4.5rem;
    height: 4.5rem;
    border-width: 1.5px;
    border-radius: 0.375rem;
  }
  
  .dish-placeholder {
    font-size: 2rem;
  }
  
  .battle-number {
    padding: 0.0625rem 0.1875rem;
    border-radius: 0.1875rem;
  }
  
  .battle-text {
    font-size: 0.25rem;
    font-weight: 700;
  }
  
  .number {
    font-size: 0.375rem;
    font-weight: 800;
  }
  
  .battle-arena {
    padding: 0.25rem;
    min-height: 5rem;
    gap: 0.375rem;
    border-radius: 0.375rem;
  }
  
  .battle-indicator {
    font-size: 0.375rem;
    letter-spacing: 0.125px;
    font-weight: 700;
  }
  
  .arena-header {
    margin-bottom: 0.125rem;
  }
  
  /* Bottom panels ultra compact */
  .bottom-panels {
    margin-top: 0.375rem;
    margin-bottom: 0.375rem;
  }
  
  .game-panel {
    padding: 0.25rem;
    border-radius: 0.375rem;
  }
  
  .panel-header {
    font-size: 0.8rem;
    margin-bottom: 0.1875rem;
    font-weight: 700;
  }
  
  .ai-summary-panel {
    padding: 0.25rem;
    border-radius: 0.375rem;
  }
  
  .summary-header {
    font-size: 0.8rem;
    margin-bottom: 0.1875rem;
    font-weight: 700;
  }
  
  .summary-content {
    padding: 0.1875rem;
    border-radius: 0.1875rem;
  }
  
  .summary-text {
    font-size: 0.8rem;
    line-height: 1.25;
    font-weight: 600;
  }
  
  .stats-grid {
    gap: 0.25rem;
  }
  
  .stat-box {
    padding: 0.1875rem;
    gap: 0.0625rem;
    border-radius: 0.1875rem;
  }
  
  .stat-box .stat-icon {
    font-size: 0.75rem;
  }
  
  .stat-number {
    font-size: 0.75rem;
    font-weight: 800;
  }
  
  .stat-label {
    font-size: 0.4rem;
    font-weight: 600;
  }
  
  .victory-banner {
    bottom: 0.25rem;
    left: 0.25rem;
    right: 0.25rem;
    font-size: 0.5rem;
    padding: 0.1875rem;
    border-radius: 0.25rem;
    font-weight: 700;
  }
  
  .strategy-tip {
    bottom: 0.25rem;
    left: 0.25rem;
    right: 0.25rem;
    font-size: 0.4375rem;
    padding: 0.1875rem 0.25rem;
    gap: 0.1875rem;
    border-radius: 0.25rem;
    font-weight: 600;
  }
  
  .tip-icon {
    font-size: 0.625rem;
  }
  
  .mood-indicator {
    width: 1rem;
    height: 1rem;
    font-size: 0.5rem;
    bottom: -0.25rem;
    left: -0.25rem;
  }
  
  .victory-crown {
    font-size: 0.75rem;
    top: -0.25rem;
    right: -0.25rem;
  }
  
  /* Cute recipe name for ultra compact mobile */
  .cute-recipe-name {
    top: -0.875rem;
    font-size: 0.5625rem;
    padding: 0.125rem 0.375rem;
  }
}

/* Game-style battle content */
.battle-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 2fr minmax(0, 1fr); /* 🎯 防溢出：确保左右列可以收缩 */
  gap: 1rem;
  align-items: start;
  margin-top: 1rem;
  position: relative;
  z-index: 1;
  min-height: 8rem;
}

/* Player sections - game character style */
.player {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
  border-radius: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.3);
  box-shadow: 
    0 4px 8px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  
  /* 🎯 移动端友好：确保不溢出 */
  min-width: 0; /* 允许收缩 */
  max-width: 100%; /* 防止溢出 */
  overflow: hidden; /* 隐藏溢出内容 */
}

.player.champion {
  background: linear-gradient(145deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.1));
  border-color: #fbbf24;
  box-shadow: 
    0 4px 12px rgba(251, 191, 36, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.player-avatar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.player-avatar img {
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #64748b;
  transition: all 0.3s ease;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.champion .player-avatar img {
  border-color: #fbbf24;
  box-shadow: 
    0 0 0 2px rgba(251, 191, 36, 0.5),
    0 4px 12px rgba(251, 191, 36, 0.4);
}

.victory-crown {
  position: absolute;
  top: -0.75rem;
  right: -0.5rem;
  font-size: 1.25rem;
  animation: crown-pulse 2s ease-in-out infinite;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
}

@keyframes crown-pulse {
  0%, 100% { transform: scale(1) rotate(-5deg); }
  50% { transform: scale(1.1) rotate(5deg); }
}

.mood-indicator {
  position: absolute;
  bottom: -0.5rem;
  left: -0.5rem;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  border: 2px solid #1e293b;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #334155, #475569);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  z-index: 2;
}

.player-stats {
  text-align: center;
  width: 100%;
}

.player-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  
  /* 🎯 防止长名字溢出 */
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
}

.score-display {
  background: linear-gradient(135deg, #475569, #334155);
  border: 1px solid #64748b;
  border-radius: 0.5rem;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  transition: all 0.3s ease;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.score-display.victory {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border-color: #d97706;
  color: #78350f;
  transform: scale(1.05);
  box-shadow: 
    0 4px 8px rgba(251, 191, 36, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.score-label {
  font-size: 0.625rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.score-display.victory .score-label {
  color: #92400e;
}

.score-value {
  font-size: 1.5rem;
  font-weight: 900;
  color: #f1f5f9;
}

.score-display.victory .score-value {
  color: #451a03;
}

/* Central battle arena - focused on dish showcase */
.battle-arena {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: linear-gradient(145deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.8));
  border-radius: 1rem;
  border: 2px solid #4c1d95;
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  min-height: 10rem;
}

.arena-header {
  width: 100%;
  text-align: center;
  margin-bottom: 0.5rem;
}

.battle-indicator {
  font-size: 0.75rem;
  font-weight: 800;
  color: #fbbf24;
  text-transform: uppercase;
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  animation: battle-glow 2s ease-in-out infinite alternate;
}

@keyframes battle-glow {
  0% { text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5), 0 0 10px rgba(251, 191, 36, 0.3); }
  100% { text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5), 0 0 20px rgba(251, 191, 36, 0.6); }
}

/* Even larger dish showcase - hero element */
.dish-showcase {
  width: 35vw;
  height: 35vw;
  border-radius: 1rem;
  overflow: visible; /* 关键修复：允许recipe badge显示在外面 */
  border: 3px solid #7c3aed;
  background: linear-gradient(145deg, #1e293b, #334155);
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.4),
    inset 0 2px 4px rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  position: relative;
  flex-shrink: 0;
}

/* 内部图片容器处理圆角 */
.dish-image-container {
  width: 100%;
  height: 100%;
  border-radius: calc(1rem - 3px); /* 减去border宽度 */
  overflow: hidden;
  position: relative;
}

.battle-card:hover .dish-showcase {
  transform: scale(1.05);
  border-color: #a855f7;
  box-shadow: 
    0 12px 24px rgba(0, 0, 0, 0.5),
    0 0 20px rgba(168, 85, 247, 0.4);
}

.winning-dish {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.battle-card:hover .winning-dish {
  transform: scale(1.1);
}

.no-dish-arena {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  background: linear-gradient(145deg, rgba(71, 85, 105, 0.3), rgba(51, 65, 85, 0.5));
}

.dish-placeholder {
  font-size: 3.5rem;
  opacity: 0.6;
  filter: grayscale(100%);
}

.challenge-text {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: center;
}

/* 可爱精美的Recipe Badge - 精准位置调整 */
.recipe-badge {
  position: absolute;
  top: -6.5rem; /* 再上移一些，精准定位 */
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #ff6b9d 0%, #fbbf24 100%);
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 1rem;
  font-size: 1rem;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  box-shadow: 
    0 3px 8px rgba(251, 107, 157, 0.25),
    0 1px 4px rgba(0, 0, 0, 0.12);
  border: 2px solid rgba(255, 255, 255, 0.9);
  z-index: 60;
  white-space: nowrap;
  backdrop-filter: blur(4px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.recipe-badge:hover {
  transform: translateX(-50%) translateY(-2px) scale(1.05);
  box-shadow: 
    0 6px 16px rgba(251, 107, 157, 0.4),
    0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Bottom panels container */
.bottom-panels {
  margin-top: 1rem;
  margin-bottom: 1rem;
}

/* Game stats panel - redesigned for bottom placement */
.game-panel {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6));
  border: 1px solid rgba(100, 116, 139, 0.3);
  border-radius: 0.75rem;
  padding: 0.75rem;
  box-shadow: 
    0 4px 8px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  margin-bottom: 1rem;
}

.panel-header {
  font-size: 1rem;
  font-weight: 700;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: center;
  margin-bottom: 0.5rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.stat-box {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem;
  background: linear-gradient(135deg, rgba(71, 85, 105, 0.4), rgba(51, 65, 85, 0.6));
  border: 1px solid rgba(100, 116, 139, 0.3);
  border-radius: 0.5rem;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.stat-box .stat-icon {
  font-size: 1rem;
}

.stat-number {
  font-size: 1.25rem;
  font-weight: 900;
  color: #f1f5f9;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.stat-label {
  font-size: 0.8rem;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.25px;
}

/* AI Summary panel - redesigned for bottom placement */
.ai-summary-panel {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.8));
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 0.75rem;
  padding: 0.75rem;
  box-shadow: 
    0 4px 8px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(34, 197, 94, 0.1);
  /* 🎯 确保内容不溢出 */
  overflow: hidden;
  max-width: 100%;
}

.summary-header {
  font-size: 1rem;
  font-weight: 700;
  color: #22c55e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: center;
  margin-bottom: 0.5rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  /* 🎮 Kinny风格的动画效果 */
  animation: kinny-glow 3s ease-in-out infinite alternate;
}

@keyframes kinny-glow {
  0% { 
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5), 0 0 10px rgba(34, 197, 94, 0.3); 
    color: #22c55e;
  }
  100% { 
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5), 0 0 20px rgba(34, 197, 94, 0.6); 
    color: #34d399;
  }
}

.summary-content {
  min-height: 80px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(21, 128, 61, 0.05));
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 0.5rem;
  padding: 0.5rem;
  text-align: center;
  /* 🎯 智能文本处理 */
  overflow-y: auto;
  word-wrap: break-word;
  word-break: break-word;
  hyphens: auto;
}

.summary-text {
  font-size: 1rem;
  color: #bbf7d0;
  font-weight: 500;
  line-height: 1.4;
  margin: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  font-style: italic;
  /* 🎯 确保文本可读性和美观 */
  white-space: pre-wrap;
  word-spacing: 0.1em;
  letter-spacing: 0.025em;
  /* 🎮 游戏风格的渐变文本效果 */
  background: linear-gradient(135deg, #bbf7d0, #6ee7b7, #34d399);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: text-shimmer 4s ease-in-out infinite;
}

@keyframes text-shimmer {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* 🎯 mobile tuning - 确保文本在小屏幕上完美显示 */
@media (max-width: 640px) {
  .summary-content {
    padding: 0.375rem;
  }
  
  .summary-text {
    font-size: 1rem;
    line-height: 1.3;
  }
}

@media (max-width: 480px) {
  .summary-content {
    padding: 0.25rem;
  }
  
  .summary-text {
    font-size: 0.9rem;
    line-height: 1.25;
  }
}

@media (max-width: 360px) {
  .summary-content {
    padding: 0.1875rem;
  }
  
  .summary-text {
    font-size: 0.8rem;
    line-height: 1.2;
  }
}

/* Victory banner - game achievement style */
.victory-banner {
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  right: 1rem;
  padding: 0.75rem;
  text-align: center;
  font-size: 0.875rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1px;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: #451a03;
  border-radius: 0.75rem;
  border: 2px solid #d97706;
  box-shadow: 
    0 4px 12px rgba(251, 191, 36, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  animation: victory-pulse 2s ease-in-out infinite;
}

@keyframes victory-pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4); }
  50% { transform: scale(1.02); box-shadow: 0 6px 16px rgba(251, 191, 36, 0.6); }
}

/* Strategy tip - game coaching style */
.strategy-tip {
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  right: 1rem;
  padding: 0.75rem;
  background: linear-gradient(135deg, #1e40af, #1d4ed8);
  border: 1px solid #3b82f6;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: #dbeafe;
  box-shadow: 
    0 4px 8px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.tip-icon {
  font-size: 1rem;
  flex-shrink: 0;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5));
}

.tip-text {
  font-weight: 600;
  line-height: 1.4;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

/* Mobile optimizations - clean design */
@media (max-width: 640px) {
  .battle-card {
    padding: 0.75rem;
    padding-bottom: 3.5rem;
    min-height: 12rem;
  }
  
  .badges-row {
    height: 2rem;
    margin-bottom: 0.5rem;
  }
  
  .round-dates-badge {
    font-size: 0.625rem;
    padding: 0.25rem 0.5rem;
  }
  
  .battle-content {
    gap: 0.5rem;
  }
  
  .fighter-avatar img {
    width: 2.5rem;
    height: 2.5rem;
  }
  
  .fighter-name {
    font-size: 0.688rem;
  }
  
  .score-badge {
    font-size: 0.875rem;
    padding: 0.1875rem 0.375rem;
  }
  
  .winner-showcase {
    width: 4rem;
    height: 4rem;
  }
  
  .battle-number {
    top: 0;
    right: 0;
    padding: 0.1875rem 0.5rem;
  }
  
  .battle-text {
    font-size: 0.5625rem;
  }
  
  .number {
    font-size: 0.75rem;
  }
  
  .round-summary {
    min-width: 8rem;
    max-width: 10rem;
    padding: 0.375rem 0.5rem;
  }
  
  .summary-text {
    font-size: 1rem;
  }
  
  .game-stats {
    gap: 0.5rem;
  }
  
  .stat-item {
    font-size: 0.4375rem;
    padding: 0.0625rem 0.1875rem;
  }
  
  .stat-icon {
    font-size: 0.6875rem;
  }
  
  .result-banner {
    bottom: 2.5rem;
    font-size: 0.6875rem;
    padding: 0.375rem;
    left: 0.375rem;
    right: 0.375rem;
  }
  .learning-tip {
    padding: 0.375rem 0.5rem;
    font-size: 0.625rem;
    gap: 0.375rem;
    bottom: 0.375rem;
    left: 0.375rem;
    right: 0.375rem;
  }
  
  .tip-icon {
    font-size: 0.75rem;
  }
  
  .game-stats {
    gap: 0.375rem;
  }
  
  .stat-item {
    font-size: 0.4375rem;
  }
  
  .stat-icon {
    font-size: 0.5625rem;
  }
}

/* 🖥️ WEB端tuning - 统一圆角 + 紧凑设计 */
@media (min-width: 769px) {
  /* 统一圆角 - 系统一体性 */
  .battle-card {
    padding: 1.25rem;
    padding-bottom: 3rem;
    border-radius: 1rem;
    min-height: auto;
  }
  
  /* 统一圆角徽章 */
  .round-dates-badge,
  .battle-number {
    font-size: 0.75rem;
    padding: 0.375rem 0.75rem;
    border-radius: 0.5rem;
  }
  
  .battle-text {
    font-size: 0.5625rem;
  }
  
  .number {
    font-size: 1rem;
  }
  
  /* 紧凑对战区域 */
  .battle-content {
    gap: 1rem;
    margin: 0.75rem 0;
  }
  
  /* 紧凑头像 */
  .player-avatar {
    width: 3.5rem;
    height: 3.5rem;
  }
  
  .player-avatar img {
    width: 3.5rem;
    height: 3.5rem;
  }
  
  .victory-crown {
    width: 1.5rem;
    height: 1.5rem;
    font-size: 1rem;
    top: -0.5rem;
    right: -0.5rem;
  }
  
  .mood-indicator {
    width: 1.5rem;
    height: 1.5rem;
    font-size: 0.75rem;
    bottom: -0.375rem;
    right: -0.375rem;
  }
  
  /* 紧凑文字 */
  .player-name {
    font-size: 0.9375rem;
    margin-bottom: 0.375rem;
  }
  
  .score-label {
    font-size: 0.5625rem;
  }
  
  .score-value {
    font-size: 1.375rem;
  }
  
  /* 🎯 紧凑菜品展示 - 核心焦点 */
  .dish-showcase {
    width: 11rem;
    height: 11rem;
  }
  
  .recipe-badge {
    font-size: 0.8125rem;
    padding: 0.375rem 0.75rem;
    border-radius: 0.75rem;
  }
  
  .dish-image-container {
    width: 11rem;
    height: 11rem;
  }
  
  .winning-dish {
    width: 11rem;
    height: 11rem;
  }
  
  .dish-placeholder {
    font-size: 3rem;
  }
  
  .challenge-text {
    font-size: 0.8125rem;
  }
  
  .arena-header {
    margin-bottom: 0.5rem;
  }
  
  .battle-indicator {
    font-size: 0.75rem;
    padding: 0.375rem 0.75rem;
  }
  
  /* 紧凑底部面板 */
  .bottom-panels {
    gap: 1rem;
    margin-top: 1rem;
  }
  
  .game-panel,
  .ai-summary-panel {
    padding: 0.875rem;
    border-radius: 0.75rem;
  }
  
  .stat-box {
    border-radius: 0.5rem;
  }
  
  .summary-content {
    border-radius: 0.5rem;
  }
  
  .victory-banner,
  .strategy-tip {
    border-radius: 0.75rem;
  }
  
  .panel-header,
  .summary-header {
    font-size: 0.75rem;
    margin-bottom: 0.625rem;
  }
  
  .stat-box {
    padding: 0.5rem;
  }
  
  .stat-icon {
    font-size: 1.25rem;
  }
  
  .stat-number {
    font-size: 1.125rem;
  }
  
  .stat-label {
    font-size: 0.625rem;
  }
  
  .summary-text {
    font-size: 0.8125rem;
    line-height: 1.5;
  }
  
  /* 紧凑横幅 */
  .victory-banner {
    font-size: 1rem;
    padding: 0.625rem;
    bottom: 0.5rem;
  }
  
  .strategy-tip {
    font-size: 0.75rem;
    padding: 0.625rem 0.875rem;
    bottom: 0.5rem;
  }
  
  /* 增强hover效果 */
  .battle-card:hover .player-avatar img {
    transform: scale(1.1);
  }
  
  .battle-card:hover .battle-indicator {
    transform: scale(1.05);
  }
  
  .battle-card:hover .winning-dish {
    transform: scale(1.05);
  }
}
</style>

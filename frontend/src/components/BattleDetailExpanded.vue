<!-- 
🎮 Battle Detail Expanded Component - COMPLETE AI DATA VERSION
================================================================
Focus Mode 专用：完整展开的 Battle 详情组件
包含所有 AI 判断数据的游戏化展示
-->

<template>
  <div 
    class="battle-arena-game" 
    :class="statusClass"
    @click="goToDetail"
  >
    <!-- 🎮 格斗游戏式顶部 HUD - 完整AI数据 -->
    <div class="game-hud-top">
      <!-- 左玩家 HUD -->
      <div class="player-hud left" :class="{ winner: statusClass === 'win' }">
        <div class="hud-avatar">
          <img :src="selfAvatar" :alt="selfName" />
          <div v-if="statusClass === 'win'" class="crown-badge">👑</div>
        </div>
        <div class="hud-details">
          <div class="hud-name">{{ selfName }}</div>
          <!-- AI Overall Score -->
          <div class="score-display" :class="{ winner: statusClass === 'win' }">
            <span class="score-num">{{ selfEntry?.ai_judgment?.overall_score?.toFixed(1) || selfEntry?.effective_ai_score?.toFixed(1) || '-' }}</span>
            <span class="score-label">AI SCORE</span>
          </div>
          <!-- 三维指标 Mini -->
          <div v-if="selfEntry?.ai_metrics" class="metrics-mini">
            <div class="m-item">
              <span class="m-icon">👁️</span>
              <div class="m-bar"><div class="m-fill" :style="{ width: selfEntry.ai_metrics.visual_appeal + '%' }"></div></div>
              <span class="m-val">{{ selfEntry.ai_metrics.visual_appeal?.toFixed(0) }}</span>
            </div>
            <div class="m-item">
              <span class="m-icon">🔥</span>
              <div class="m-bar"><div class="m-fill" :style="{ width: selfEntry.ai_metrics.cooking_technique + '%' }"></div></div>
              <span class="m-val">{{ selfEntry.ai_metrics.cooking_technique?.toFixed(0) }}</span>
            </div>
            <div class="m-item">
              <span class="m-icon">🥬</span>
              <div class="m-bar"><div class="m-fill" :style="{ width: selfEntry.ai_metrics.ingredient_freshness + '%' }"></div></div>
              <span class="m-val">{{ selfEntry.ai_metrics.ingredient_freshness?.toFixed(0) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 中央 VS + Recipe -->
      <div class="center-battle-info">
        <div class="recipe-badge">{{ battleResult?.recipe_name || 'Unknown Dish' }}</div>
        <div class="vs-section">
          <div class="vs-ring"></div>
          <span class="vs-text">VS</span>
          <div class="vs-ring"></div>
        </div>
        <div class="battle-meta">
          <span class="meta-chip">Round #{{ battleNumber || memory.id }}</span>
          <span class="meta-chip" v-if="selfEntry?.ai_judgment?.confidence">
            AI: {{ (selfEntry.ai_judgment.confidence * 100).toFixed(0) }}%
          </span>
        </div>
        <div class="result-badge" :class="statusClass">
          <span class="result-icon">{{ statusClass === 'win' ? '🏆' : statusClass === 'lose' ? '💪' : '🤝' }}</span>
          <span class="result-text">{{ statusClass === 'win' ? 'VICTORY' : statusClass === 'lose' ? 'BRAVE' : 'TIE' }}</span>
        </div>
      </div>

      <!-- 右玩家 HUD -->
      <div class="player-hud right" :class="{ winner: statusClass === 'lose' }">
        <div class="hud-details">
          <div class="hud-name">{{ partnerName }}</div>
          <!-- AI Overall Score -->
          <div class="score-display" :class="{ winner: statusClass === 'lose' }">
            <span class="score-num">{{ partnerEntry?.ai_judgment?.overall_score?.toFixed(1) || partnerEntry?.effective_ai_score?.toFixed(1) || '-' }}</span>
            <span class="score-label">AI SCORE</span>
          </div>
          <!-- 三维指标 Mini -->
          <div v-if="partnerEntry?.ai_metrics" class="metrics-mini">
            <div class="m-item reverse">
              <span class="m-val">{{ partnerEntry.ai_metrics.visual_appeal?.toFixed(0) }}</span>
              <div class="m-bar"><div class="m-fill" :style="{ width: partnerEntry.ai_metrics.visual_appeal + '%' }"></div></div>
              <span class="m-icon">👁️</span>
            </div>
            <div class="m-item reverse">
              <span class="m-val">{{ partnerEntry.ai_metrics.cooking_technique?.toFixed(0) }}</span>
              <div class="m-bar"><div class="m-fill" :style="{ width: partnerEntry.ai_metrics.cooking_technique + '%' }"></div></div>
              <span class="m-icon">🔥</span>
            </div>
            <div class="m-item reverse">
              <span class="m-val">{{ partnerEntry.ai_metrics.ingredient_freshness?.toFixed(0) }}</span>
              <div class="m-bar"><div class="m-fill" :style="{ width: partnerEntry.ai_metrics.ingredient_freshness + '%' }"></div></div>
              <span class="m-icon">🥬</span>
            </div>
          </div>
        </div>
        <div class="hud-avatar">
          <img :src="partnerAvatar" :alt="partnerName" />
          <div v-if="statusClass === 'lose'" class="crown-badge">👑</div>
        </div>
      </div>
    </div>

    <!-- 🎮 主战场 - 双菜品 + AI评论 -->
    <div class="battle-arena-main">
      <!-- 左战士区 -->
      <div class="fighter-zone left" :class="{ winner: statusClass === 'win' }">
        <div v-if="selfEntry?.media?.[0]" class="dish-fighter">
          <img :src="fix(selfEntry.media[0].url)" :alt="selfName + ' dish'" />
          <div class="fighter-label">{{ selfName }}'s Dish</div>
          <div v-if="statusClass === 'win'" class="winner-glow"></div>
        </div>
        <div v-else class="dish-placeholder">
          <div class="placeholder-icon">🍽️</div>
          <p>No Image</p>
        </div>
        
        <!-- AI Summary (Priority #1) - show individual_summary, falling back to ai_summary -->
        <div v-if="selfEntry?.ai_judgment?.individual_summary || selfEntry?.ai_judgment?.ai_summary" class="ai-summary-box">
          <div class="summary-header"><span class="s-icon">🎯</span><span class="s-label">AI Summary</span></div>
          <p class="summary-text">{{ selfEntry.ai_judgment.individual_summary || selfEntry.ai_judgment.ai_summary }}</p>
        </div>
        
        <!-- AI Individual Comment - show individual_comment, falling back to ai_comment -->
        <div v-if="selfEntry?.ai_judgment?.individual_comment || selfEntry?.ai_judgment?.ai_comment" class="ai-comment-box">
          <div class="comment-header"><span class="c-icon">💬</span><span class="c-label">AI Comment</span></div>
          <p class="comment-text">{{ selfEntry.ai_judgment.individual_comment || selfEntry.ai_judgment.ai_comment }}</p>
        </div>
        
        <div v-if="selfEntry" class="dish-meta">
          <p v-if="selfEntry.recipe_name" class="recipe-title">{{ selfEntry.recipe_name }}</p>
          <p v-if="selfEntry.content" class="recipe-desc">{{ selfEntry.content }}</p>
        </div>
      </div>

      <!-- 中央裁判区 - Battle Result -->
      <div class="judge-zone">
        <!-- Battle Summary (AI Overall) - prefer either battle_summary, falling back to battle_comment -->
        <div v-if="selfEntry?.ai_judgment?.battle_summary || partnerEntry?.ai_judgment?.battle_summary || selfEntry?.ai_judgment?.battle_comment || partnerEntry?.ai_judgment?.battle_comment" class="battle-summary">
          <div class="battle-summary-header">
            <span class="bs-icon">🤖</span>
            <span class="bs-label">{{ (selfEntry?.ai_judgment?.battle_summary || partnerEntry?.ai_judgment?.battle_summary) ? 'Battle Summary' : 'Battle Comment' }}</span>
          </div>
          <p class="battle-summary-text">{{ 
            selfEntry?.ai_judgment?.battle_summary || 
            partnerEntry?.ai_judgment?.battle_summary || 
            selfEntry?.ai_judgment?.battle_comment || 
            partnerEntry?.ai_judgment?.battle_comment 
          }}</p>
        </div>
        
        <div v-if="battleResult" class="battle-verdict">
          <div class="verdict-header">
            <span class="v-icon">⚔️</span>
            <span class="v-title">Battle Result</span>
          </div>
          <div class="verdict-reason">
            <p class="reason-text">{{ battleResult.reason }}</p>
          </div>
        </div>
        
        <!-- Kinny Winner/Loser Messages -->
        <div v-if="battleResult" class="kinny-messages">
          <div v-if="statusClass === 'win' && battleResult.kinny_winner_message" class="kinny-msg winner">
            <span class="msg-icon">🎉</span>
            <p class="msg-text">{{ battleResult.kinny_winner_message }}</p>
          </div>
          <div v-else-if="statusClass === 'lose' && battleResult.kinny_loser_message" class="kinny-msg loser">
            <span class="msg-icon">💪</span>
            <p class="msg-text">{{ battleResult.kinny_loser_message }}</p>
          </div>
        </div>
        
        <div class="date-info">{{ formatRound(memory.round_start, memory.round_end) }}</div>
      </div>

      <!-- 右战士区 -->
      <div class="fighter-zone right" :class="{ winner: statusClass === 'lose' }">
        <div v-if="partnerEntry?.media?.[0]" class="dish-fighter">
          <img :src="fix(partnerEntry.media[0].url)" :alt="partnerName + ' dish'" />
          <div class="fighter-label">{{ partnerName }}'s Dish</div>
          <div v-if="statusClass === 'lose'" class="winner-glow"></div>
        </div>
        <div v-else class="dish-placeholder">
          <div class="placeholder-icon">🍽️</div>
          <p>No Image</p>
        </div>
        
        <!-- AI Summary (Priority #1) - show individual_summary, falling back to ai_summary -->
        <div v-if="partnerEntry?.ai_judgment?.individual_summary || partnerEntry?.ai_judgment?.ai_summary" class="ai-summary-box">
          <div class="summary-header"><span class="s-icon">🎯</span><span class="s-label">AI Summary</span></div>
          <p class="summary-text">{{ partnerEntry.ai_judgment.individual_summary || partnerEntry.ai_judgment.ai_summary }}</p>
        </div>
        
        <!-- AI Individual Comment - show individual_comment, falling back to ai_comment -->
        <div v-if="partnerEntry?.ai_judgment?.individual_comment || partnerEntry?.ai_judgment?.ai_comment" class="ai-comment-box">
          <div class="comment-header"><span class="c-icon">💬</span><span class="c-label">AI Comment</span></div>
          <p class="comment-text">{{ partnerEntry.ai_judgment.individual_comment || partnerEntry.ai_judgment.ai_comment }}</p>
        </div>
        
        <div v-if="partnerEntry" class="dish-meta">
          <p v-if="partnerEntry.recipe_name" class="recipe-title">{{ partnerEntry.recipe_name }}</p>
          <p v-if="partnerEntry.content" class="recipe-desc">{{ partnerEntry.content }}</p>
        </div>
      </div>
    </div>

    <!-- 🎮 底部：Kinny评论 + 建议 -->
    <div v-if="battleResult" class="game-footer">
      <!-- Kinny Couple Story -->
      <div v-if="battleResult.kinny_couple_story" class="kinny-story">
        <span class="story-icon">💕</span>
        <p class="story-text">{{ battleResult.kinny_couple_story }}</p>
      </div>
      
      <!-- Future Suggestions -->
      <div v-if="battleResult.future_cooking_suggestions?.length" class="future-tips">
        <span class="tips-icon">💡</span>
        <div class="tips-list">
          <span v-for="(tip, i) in battleResult.future_cooking_suggestions" :key="i" class="tip-tag">{{ tip }}</span>
        </div>
      </div>
    </div>
    
    <!-- 🐛 调试面板 - 显示 AI 数据状态 (开发用) -->
    <div v-if="false" class="debug-panel">
      <div class="debug-title">🐛 AI Data Debug Panel</div>
      <div class="debug-row">
        <span class="debug-label">Individual Summary (Self):</span>
        <span class="debug-value" :class="{ missing: !selfEntry?.ai_judgment?.individual_summary }">
          {{ selfEntry?.ai_judgment?.individual_summary ? '✅ EXISTS' : '❌ MISSING' }}
        </span>
      </div>
      <div class="debug-row">
        <span class="debug-label">Individual Comment (Self):</span>
        <span class="debug-value" :class="{ missing: !selfEntry?.ai_judgment?.individual_comment }">
          {{ selfEntry?.ai_judgment?.individual_comment ? '✅ EXISTS' : '❌ MISSING' }}
        </span>
      </div>
      <div class="debug-row">
        <span class="debug-label">Battle Summary:</span>
        <span class="debug-value" :class="{ missing: !(selfEntry?.ai_judgment?.battle_summary || partnerEntry?.ai_judgment?.battle_summary) }">
          {{ (selfEntry?.ai_judgment?.battle_summary || partnerEntry?.ai_judgment?.battle_summary) ? '✅ EXISTS' : '❌ MISSING' }}
        </span>
      </div>
      <div class="debug-row">
        <span class="debug-label">Battle Comment:</span>
        <span class="debug-value" :class="{ missing: !(selfEntry?.ai_judgment?.battle_comment || partnerEntry?.ai_judgment?.battle_comment) }">
          {{ (selfEntry?.ai_judgment?.battle_comment || partnerEntry?.ai_judgment?.battle_comment) ? '✅ EXISTS' : '❌ MISSING' }}
        </span>
      </div>
      <div class="debug-row">
        <span class="debug-label">Legacy ai_summary (Self):</span>
        <span class="debug-value" :class="{ missing: !selfEntry?.ai_judgment?.ai_summary }">
          {{ selfEntry?.ai_judgment?.ai_summary ? '✅ EXISTS' : '❌ MISSING' }}
        </span>
      </div>
      <div class="debug-row">
        <span class="debug-label">Legacy ai_comment (Self):</span>
        <span class="debug-value" :class="{ missing: !selfEntry?.ai_judgment?.ai_comment }">
          {{ selfEntry?.ai_judgment?.ai_comment ? '✅ EXISTS' : '❌ MISSING' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CoupleMemory } from '@/models/couplememory'

interface Props {
  memory: CoupleMemory
  selfId: number
  selfName: string
  partnerId: number
  partnerName: string
  battleNumber?: number
}

const props = defineProps<Props>()

const emit = defineEmits(['navigate'])

// 🎯 核心数据提取
const battleResult = computed(() => (props.memory as any).battle_result)
const selfEntry = computed(() => props.memory.entries?.find(e => e.author === props.selfId))
const partnerEntry = computed(() => props.memory.entries?.find(e => e.author === props.partnerId))

// 🐛 调试：打印 AI 数据结构
console.log('🐛 BattleDetailExpanded Debug:', {
  memoryId: props.memory.id,
  selfEntry_ai_judgment: selfEntry.value?.ai_judgment,
  partnerEntry_ai_judgment: partnerEntry.value?.ai_judgment,
  has_individual_summary_self: !!selfEntry.value?.ai_judgment?.individual_summary,
  has_individual_summary_partner: !!partnerEntry.value?.ai_judgment?.individual_summary,
  has_battle_summary_self: !!selfEntry.value?.ai_judgment?.battle_summary,
  has_battle_summary_partner: !!partnerEntry.value?.ai_judgment?.battle_summary,
  has_battle_comment_self: !!selfEntry.value?.ai_judgment?.battle_comment,
  has_individual_comment_self: !!selfEntry.value?.ai_judgment?.individual_comment,
})

const selfPts = computed(() => props.memory.entries?.find(e => e.author === props.selfId)?.ai_score || 0)
const partnerPts = computed(() => props.memory.entries?.find(e => e.author === props.partnerId)?.ai_score || 0)

const selfAvatar = computed(() => `/api/placeholder/80/80?text=${props.selfName}`)
const partnerAvatar = computed(() => `/api/placeholder/80/80?text=${props.partnerName}`)

const statusClass = computed(() => {
  if (!props.memory.winner_entry) return 'tie'
  return props.memory.winner_entry.author_username === props.selfName ? 'win' : 'lose'
})

const formatRound = (start: string, end: string) => {
  const s = new Date(start)
  const e = new Date(end)
  return `${s.getMonth()+1}/${s.getDate()} - ${e.getMonth()+1}/${e.getDate()}`
}

const fix = (url: string | undefined) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  if (url.startsWith('/media')) return `${import.meta.env.VITE_API_BASE_URL || ''}${url}`
  return url
}

const goToDetail = () => {
  emit('navigate', props.memory.id)
}
</script>

<style scoped>
/* 🎮 主容器 */
.battle-arena-game {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: 
    radial-gradient(ellipse at center, rgba(20, 20, 40, 0.9), rgba(10, 10, 20, 0.95)),
    linear-gradient(180deg, rgba(168, 230, 207, 0.05), transparent 50%, rgba(236, 72, 153, 0.05));
  border: 4px solid;
  border-image: linear-gradient(135deg, rgba(168, 230, 207, 0.6), rgba(102, 126, 234, 0.4), rgba(236, 72, 153, 0.6)) 1;
  border-radius: 1rem;
  padding: 0.75rem;
  box-shadow: 
    0 15px 60px rgba(0, 0, 0, 0.9),
    0 0 80px rgba(168, 230, 207, 0.1) inset;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.battle-arena-game:hover {
  transform: scale(1.01);
  box-shadow: 
    0 20px 80px rgba(0, 0, 0, 0.95),
    0 0 120px rgba(168, 230, 207, 0.2) inset;
}

.battle-arena-game.win {
  border-image: linear-gradient(135deg, rgba(251, 191, 36, 0.8), rgba(168, 230, 207, 0.6)) 1;
}

.battle-arena-game.lose {
  border-image: linear-gradient(135deg, rgba(236, 72, 153, 0.8), rgba(219, 39, 119, 0.6)) 1;
}

/* 🎮 顶部 HUD */
.game-hud-top {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: start;
  gap: 1rem;
  padding: 0.5rem;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.6), transparent);
  border-bottom: 2px solid rgba(168, 230, 207, 0.3);
}

.player-hud {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 0.5rem;
  border: 2px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.player-hud.winner {
  border-color: rgba(251, 191, 36, 0.8);
  background: rgba(251, 191, 36, 0.15);
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.4);
}

.player-hud.left {
  flex-direction: row;
}

.player-hud.right {
  flex-direction: row-reverse;
}

.hud-avatar {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid rgba(168, 230, 207, 0.5);
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
}

.hud-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.crown-badge {
  position: absolute;
  top: -10px;
  right: -10px;
  font-size: 1.5rem;
  filter: drop-shadow(0 2px 8px rgba(255, 217, 61, 0.9));
  animation: crown-float 2s ease-in-out infinite;
}

@keyframes crown-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.hud-details {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  flex: 1;
  min-width: 0;
}

.hud-name {
  font-size: 0.9rem;
  font-weight: 900;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.score-display {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
}

.score-num {
  font-size: 1.5rem;
  font-weight: 900;
  color: #A8E6CF;
  text-shadow: 0 0 10px rgba(168, 230, 207, 0.8);
  line-height: 1;
}

.score-display.winner .score-num {
  color: #FFD93D;
  text-shadow: 0 0 12px rgba(255, 217, 61, 0.9);
}

.score-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
}

.metrics-mini {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.m-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.7rem;
}

.m-item.reverse {
  flex-direction: row-reverse;
}

.m-icon {
  font-size: 0.9rem;
  flex-shrink: 0;
}

.m-bar {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
  min-width: 40px;
}

.m-fill {
  height: 100%;
  background: linear-gradient(90deg, #A8E6CF, #6EE7B7);
  border-radius: 2px;
  transition: width 0.5s ease;
}

.m-val {
  font-size: 0.7rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
  min-width: 20px;
  text-align: center;
}

/* 中央信息 */
.center-battle-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem;
  background: radial-gradient(circle, rgba(168, 230, 207, 0.15), transparent);
  border: 2px solid rgba(168, 230, 207, 0.4);
  border-radius: 0.75rem;
  min-width: 180px;
}

.recipe-badge {
  font-size: 0.85rem;
  font-weight: 900;
  color: white;
  text-transform: uppercase;
  text-align: center;
  padding: 0.3rem 0.6rem;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 0.5rem;
  border: 1px solid rgba(168, 230, 207, 0.4);
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
}

.vs-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.vs-ring {
  width: 30px;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(168, 230, 207, 0.8), transparent);
}

.vs-text {
  font-size: 1.1rem;
  font-weight: 900;
  color: white;
  text-shadow: 0 0 10px rgba(168, 230, 207, 0.8), 0 2px 8px rgba(0, 0, 0, 0.9);
  letter-spacing: 2px;
}

.battle-meta {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
  justify-content: center;
}

.meta-chip {
  font-size: 0.6rem;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(0, 0, 0, 0.5);
  padding: 0.2rem 0.5rem;
  border-radius: 0.5rem;
  text-transform: uppercase;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.result-badge {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 0.5rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.result-badge.win {
  border-color: rgba(251, 191, 36, 0.8);
  background: rgba(251, 191, 36, 0.2);
}

.result-badge.lose {
  border-color: rgba(236, 72, 153, 0.8);
  background: rgba(236, 72, 153, 0.2);
}

.result-icon {
  font-size: 1.2rem;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.8));
}

.result-text {
  font-size: 0.75rem;
  font-weight: 900;
  color: white;
  text-transform: uppercase;
  letter-spacing: 1px;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
}

/* 主战场 */
.battle-arena-main {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 0.75rem;
  min-height: 0;
  padding: 0.5rem;
  background: radial-gradient(ellipse at 50% 50%, rgba(168, 230, 207, 0.05), transparent 70%);
}

.fighter-zone {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  padding: 0.6rem;
  transition: all 0.3s ease;
}

.fighter-zone.winner {
  border-color: rgba(251, 191, 36, 0.6);
  background: rgba(251, 191, 36, 0.1);
  box-shadow: 0 0 30px rgba(251, 191, 36, 0.3) inset;
}

.dish-fighter {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 3px solid rgba(168, 230, 207, 0.3);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
}

.dish-fighter img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.fighter-zone:hover .dish-fighter img {
  transform: scale(1.05);
}

.fighter-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0.4rem;
  background: linear-gradient(0deg, rgba(0, 0, 0, 0.9), transparent);
  font-size: 0.65rem;
  font-weight: 800;
  color: white;
  text-align: center;
  text-transform: uppercase;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
}

.winner-glow {
  position: absolute;
  inset: -3px;
  border-radius: 0.5rem;
  background: linear-gradient(45deg, rgba(251, 191, 36, 0.4), rgba(255, 217, 61, 0.4));
  filter: blur(8px);
  animation: winner-shine 2s ease-in-out infinite;
}

@keyframes winner-shine {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.dish-placeholder {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 0.5rem;
}

.placeholder-icon {
  font-size: 3rem;
  opacity: 0.3;
}

.dish-placeholder p {
  margin: 0.5rem 0 0 0;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 700;
}

/* AI Summary Box - 最高优先级展示 */
.ai-summary-box {
  padding: 0.6rem;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(255, 217, 61, 0.15));
  border: 2px solid rgba(251, 191, 36, 0.5);
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.3);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-bottom: 0.4rem;
}

.s-icon {
  font-size: 1.1rem;
}

.s-label {
  font-size: 0.7rem;
  font-weight: 900;
  color: #FCD34D;
  text-transform: uppercase;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
}

.summary-text {
  margin: 0;
  font-size: 0.75rem;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 600;
}

/* AI Comment Box */
.ai-comment-box {
  padding: 0.5rem;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 0.5rem;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-bottom: 0.3rem;
}

.c-icon {
  font-size: 1rem;
}

.c-label {
  font-size: 0.65rem;
  font-weight: 800;
  color: #c7d2fe;
  text-transform: uppercase;
}

.comment-text {
  margin: 0;
  font-size: 0.7rem;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.9);
  font-style: italic;
}

.dish-meta {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.recipe-title {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 800;
  color: #A8E6CF;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recipe-desc {
  margin: 0;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 裁判区 */
.judge-zone {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  justify-content: center;
  width: 160px;
  padding: 0.6rem;
  background: rgba(0, 0, 0, 0.5);
  border-left: 2px solid rgba(168, 230, 207, 0.3);
  border-right: 2px solid rgba(236, 72, 153, 0.3);
  border-radius: 0.5rem;
}

/* Battle Summary - 中央AI总结 */
.battle-summary {
  padding: 0.6rem;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  border: 2px solid rgba(139, 92, 246, 0.6);
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
}

.battle-summary-header {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-bottom: 0.4rem;
}

.bs-icon {
  font-size: 1rem;
}

.bs-label {
  font-size: 0.7rem;
  font-weight: 900;
  color: #C7D2FE;
  text-transform: uppercase;
}

.battle-summary-text {
  margin: 0;
  font-size: 0.7rem;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.battle-verdict {
  padding: 0.5rem;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 0.5rem;
}

.verdict-header {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-bottom: 0.3rem;
}

.v-icon {
  font-size: 1rem;
}

.v-title {
  font-size: 0.7rem;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
}

.verdict-reason {
  margin-top: 0.3rem;
}

.reason-text {
  margin: 0;
  font-size: 0.65rem;
  line-height: 1.3;
  color: rgba(255, 255, 255, 0.8);
}

/* Kinny Winner/Loser Messages */
.kinny-messages {
  padding: 0.5rem;
  border-radius: 0.5rem;
}

.kinny-msg {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.kinny-msg.winner {
  padding: 0.5rem;
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.4);
  border-radius: 0.5rem;
}

.kinny-msg.loser {
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.4);
  border-radius: 0.5rem;
}

.msg-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.msg-text {
  margin: 0;
  font-size: 0.7rem;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.date-info {
  font-size: 0.6rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  padding: 0.3rem;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 0.5rem;
}

/* 底部 */
.game-footer {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-top: 2px solid rgba(168, 230, 207, 0.2);
  border-radius: 0 0 0.5rem 0.5rem;
}

.kinny-story {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(236, 72, 153, 0.1);
  border-left: 3px solid rgba(236, 72, 153, 0.5);
  border-radius: 0.5rem;
}

.story-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.story-text {
  margin: 0;
  font-size: 0.7rem;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.85);
  font-style: italic;
}

.future-tips {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(34, 197, 94, 0.1);
  border-left: 3px solid rgba(34, 197, 94, 0.5);
  border-radius: 0.5rem;
}

.tips-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
  line-height: 1;
}

.tips-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  flex: 1;
}

.tip-tag {
  font-size: 0.6rem;
  font-weight: 700;
  padding: 0.25rem 0.5rem;
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.4);
  border-radius: 1rem;
  color: #dcfce7;
  white-space: nowrap;
}

/* 🐛 调试面板样式 */
.debug-panel {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  background: rgba(0, 0, 0, 0.95);
  border: 2px solid #fbbf24;
  border-radius: 0.5rem;
  padding: 1rem;
  max-width: 400px;
  z-index: 9999;
  font-family: 'Courier New', monospace;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
}

.debug-title {
  font-size: 0.9rem;
  font-weight: 900;
  color: #fbbf24;
  margin-bottom: 0.5rem;
  text-align: center;
  border-bottom: 1px solid #fbbf24;
  padding-bottom: 0.5rem;
}

.debug-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.debug-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
}

.debug-value {
  font-size: 0.7rem;
  font-weight: 700;
  color: #10b981;
}

.debug-value.missing {
  color: #ef4444;
}

/* 响应式 */
@media (max-width: 1200px) {
  .battle-arena-main {
    grid-template-columns: 1fr;
  }
  
  .judge-zone {
    width: 100%;
    border-left: none;
    border-right: none;
    border-top: 2px solid rgba(168, 230, 207, 0.3);
    border-bottom: 2px solid rgba(236, 72, 153, 0.3);
  }
}

@media (max-width: 768px) {
  .game-hud-top {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .center-battle-info {
    order: -1;
  }
  
  .battle-arena-game {
    padding: 0.5rem;
    gap: 0.4rem;
  }
}
</style>

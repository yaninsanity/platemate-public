<!-- 厨神1v1 PK竞技场 - AAA游戏体验 -->
<template>
  <div class="chef-arena">
    <!-- 竞技场头部 -->
    <div class="arena-header">
      <div class="battle-title">
        <h2>🔥 Chef Battle Arena 🔥</h2>
        <div class="battle-subtitle">
          <span class="subtitle-text">AI Judge • Couple Comments • Ultimate Showdown</span>
          <div v-if="currentRecipe" class="current-recipe">
            <span class="recipe-icon">📋</span>
            <span class="recipe-name">{{ currentRecipe }}</span>
          </div>
        </div>
      </div>
      <div class="battle-status" :class="battlePhase">
        <div class="status-icon">{{ getPhaseIcon() }}</div>
        <span>{{ getPhaseText() }}</span>
      </div>
    </div>

    <!-- 主PK战场 -->
    <div class="pk-battlefield">
      <!-- 选手A区域 -->
      <div class="chef-zone chef-a" :class="getChefStatus('A')">
        <div class="chef-profile">
          <ChefAvatar 
            :avatar="userA.avatar" 
            :name="userA.name" 
            :is-winner="isWinner('A')"
          />
          <div class="chef-info">
            <h3>{{ userA.name }}</h3>
            <div v-if="userA.recipeName" class="chef-recipe">
              <span class="recipe-icon">🍽️</span>
              <span class="recipe-text">{{ userA.recipeName }}</span>
            </div>
            <div class="chef-score" v-if="userA.aiScore">
              <span class="score-number">{{ Math.round(userA.aiScore) }}</span>
              <span class="score-label">pts</span>
            </div>
          </div>
        </div>

        <!-- 单张PK图片 -->
        <div class="dish-spotlight">
          <div v-if="getHighlightPhoto(userA)" class="spotlight-frame" @click="toggleUserAGallery">
            <img :src="getHighlightPhoto(userA)?.url" alt="Chef's Masterpiece">
            <div class="spotlight-overlay">
              <div class="dish-label">Masterpiece</div>
              <div v-if="isAnalyzing" class="analyzing-pulse">🤖 AI Analyzing...</div>
              <div class="view-all-btn">👁️ View All</div>
            </div>
          </div>
          <div v-else class="empty-spotlight">
            <EmptyChefSlot 
              :chef-name="userA.name" 
              @remind="remindPartner"
            />
          </div>
        </div>

        <!-- 展开的图片库 -->
        <div v-if="showUserAGallery && userA.photos.length > 1" class="inline-gallery">
          <div class="gallery-header">
            <span>{{ userA.name }}'s Dishes ({{ userA.photos.length }})</span>
            <button @click="showUserAGallery = false" class="close-gallery">×</button>
          </div>
          <div class="photos-row">
            <div v-for="(photo, index) in userA.photos" :key="`a-${index}`" 
                 class="photo-thumb" :class="{ highlight: photo.isHighlight }">
              <img :src="photo.url" :alt="`Dish ${index + 1}`">
              <div v-if="photo.isHighlight" class="star">⭐</div>
            </div>
          </div>
        </div>

        <!-- Enhanced AI评分展示区域 -->
        <div class="enhanced-ai-section" v-if="getHighlightPhoto(userA)">
          <EnhancedAIScoreDisplay 
            :ai-judgment="userA.ai_judgment"
            :ai-score="userA.aiScore"
            :is-analyzing="isAnalyzing"
          />
        </div>

        <!-- 情侣评论区 -->
        <div class="couple-comments" v-if="getHighlightPhoto(userA)">
          <div class="comment-header">💕 Your Partner's Love Note</div>
          <div class="comment-input">
            <input 
              v-model="partnerComments.toA" 
              placeholder="Leave a sweet comment for your chef..." 
              @keyup.enter="submitComment('A')"
            >
            <button @click="submitComment('A')" class="comment-btn">💌</button>
          </div>
          <div v-if="partnerComments.fromB" class="love-comment">
            "{{ partnerComments.fromB }}" ❤️
          </div>
        </div>
      </div>

      <!-- VS核心战斗区 -->
      <div class="vs-core-battle">
        <div class="energy-field" :class="{ active: isAnalyzing, winner: hasWinner }">
          <div class="vs-symbol">VS</div>
          <div class="energy-waves" v-if="isAnalyzing">
            <div class="wave" v-for="n in 3" :key="n"></div>
          </div>
        </div>
        <div class="battle-progress" v-if="isAnalyzing">
          <div class="progress-text">AI Judging...</div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${analysisProgress}%` }"></div>
          </div>
        </div>
        <div class="final-verdict" v-else-if="hasWinner">
          <div class="winner-text">{{ getWinnerName() }} Wins!</div>
          <div class="score-diff">+{{ getScoreDifference() }} points</div>
        </div>
      </div>

      <!-- 选手B区域 -->
      <div class="chef-zone chef-b" :class="getChefStatus('B')">
        <div class="chef-profile">
          <div class="chef-info">
            <h3>{{ userB.name }}</h3>
            <div v-if="userB.recipeName" class="chef-recipe">
              <span class="recipe-icon">🍽️</span>
              <span class="recipe-text">{{ userB.recipeName }}</span>
            </div>
            <div class="chef-score" v-if="userB.aiScore">
              <span class="score-number">{{ Math.round(userB.aiScore) }}</span>
              <span class="score-label">pts</span>
            </div>
          </div>
          <ChefAvatar 
            :avatar="userB.avatar" 
            :name="userB.name" 
            :is-winner="isWinner('B')"
          />
        </div>

        <!-- 单张PK图片 -->
        <div class="dish-spotlight">
          <div v-if="getHighlightPhoto(userB)" class="spotlight-frame" @click="toggleUserBGallery">
            <img :src="getHighlightPhoto(userB)?.url" alt="Chef's Masterpiece">
            <div class="spotlight-overlay">
              <div class="dish-label">Masterpiece</div>
              <div v-if="isAnalyzing" class="analyzing-pulse">🤖 AI Analyzing...</div>
              <div class="view-all-btn">👁️ View All</div>
            </div>
          </div>
          <div v-else class="empty-spotlight">
            <EmptyChefSlot 
              :chef-name="userB.name" 
              @remind="remindPartner"
            />
          </div>
        </div>

        <!-- 展开的图片库 -->
        <div v-if="showUserBGallery && userB.photos.length > 1" class="inline-gallery">
          <div class="gallery-header">
            <span>{{ userB.name }}'s Dishes ({{ userB.photos.length }})</span>
            <button @click="showUserBGallery = false" class="close-gallery">×</button>
          </div>
          <div class="photos-row">
            <div v-for="(photo, index) in userB.photos" :key="`b-${index}`" 
                 class="photo-thumb" :class="{ highlight: photo.isHighlight }">
              <img :src="photo.url" :alt="`Dish ${index + 1}`">
              <div v-if="photo.isHighlight" class="star">⭐</div>
            </div>
          </div>
        </div>

        <!-- Enhanced AI评分展示区域 -->
        <div class="enhanced-ai-section" v-if="getHighlightPhoto(userB)">
          <EnhancedAIScoreDisplay 
            :ai-judgment="userB.ai_judgment"
            :ai-score="userB.aiScore"
            :is-analyzing="isAnalyzing"
          />
        </div>

        <!-- 情侣评论区 -->
        <div class="couple-comments" v-if="getHighlightPhoto(userB)">
          <div class="comment-header">💕 Your Partner's Love Note</div>
          <div class="comment-input">
            <input 
              v-model="partnerComments.toB" 
              placeholder="Leave a sweet comment for your chef..." 
              @keyup.enter="submitComment('B')"
            >
            <button @click="submitComment('B')" class="comment-btn">💌</button>
          </div>
          <div v-if="partnerComments.fromA" class="love-comment">
            "{{ partnerComments.fromA }}" ❤️
          </div>
        </div>
      </div>

      <!-- VS核心战斗区 -->
      <div class="vs-core-battle">
        <div class="energy-field" :class="{ active: isAnalyzing, winner: hasWinner }">
          <div class="vs-symbol">VS</div>
          <div class="energy-waves" v-if="isAnalyzing">
            <div class="wave"></div>
            <div class="wave"></div>
            <div class="wave"></div>
          </div>
          <div v-if="hasWinner" class="victory-crown">👑</div>
        </div>
        
        <!-- 战斗进度显示 -->
        <div v-if="isAnalyzing" class="battle-progress">
          <div class="progress-text">🤖 AI Judge is analyzing...</div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${analysisProgress}%` }"></div>
          </div>
        </div>
      </div>

      <!-- 选手B区域 -->
      <div class="chef-zone chef-b" :class="getChefStatus('B')">
        <div class="chef-profile">
          <ChefAvatar 
            :avatar="userB.avatar" 
            :name="userB.name" 
            :is-winner="isWinner('B')"
          />
        </div>

        <!-- 单张PK图片 -->
        <div class="dish-spotlight">
          <div v-if="getHighlightPhoto(userB)" class="spotlight-frame" @click="toggleUserBGallery">
            <img :src="getHighlightPhoto(userB)?.url" alt="Chef's Masterpiece">
            <div class="spotlight-overlay">
              <div class="dish-label">Masterpiece</div>
              <div v-if="isAnalyzing" class="analyzing-pulse">🤖 AI Analyzing...</div>
              <div class="view-all-btn">👁️ View All</div>
            </div>
          </div>
          <div v-else class="empty-spotlight">
            <EmptyChefSlot 
              :chef-name="userB.name" 
              @remind="remindPartner"
            />
          </div>
        </div>

        <!-- 展开的图片库 -->
        <div v-if="showUserBGallery && userB.photos.length > 1" class="inline-gallery">
          <div class="gallery-header">
            <span>{{ userB.name }}'s Dishes ({{ userB.photos.length }})</span>
            <button @click="showUserBGallery = false" class="close-gallery">×</button>
          </div>
          <div class="photos-row">
            <div v-for="(photo, index) in userB.photos" :key="`b-${index}`" 
                 class="photo-thumb" :class="{ highlight: photo.isHighlight }">
              <img :src="photo.url" :alt="`Dish ${index + 1}`">
              <div v-if="photo.isHighlight" class="star">⭐</div>
            </div>
          </div>
        </div>

        <!-- Enhanced AI评分展示区域 -->
        <div class="enhanced-ai-section" v-if="getHighlightPhoto(userB)">
          <EnhancedAIScoreDisplay 
            :ai-judgment="userB.ai_judgment"
            :ai-score="userB.aiScore"
            :is-analyzing="isAnalyzing"
          />
        </div>

        <!-- 情侣评论区 -->
        <div class="couple-comments" v-if="getHighlightPhoto(userB)">
          <div class="comment-header">💕 Your Partner's Love Note</div>
          <div class="comment-input">
            <input 
              v-model="partnerComments.toB" 
              placeholder="Leave a sweet comment for your chef..." 
              @keyup.enter="submitComment('B')"
            >
            <button @click="submitComment('B')" class="comment-btn">💌</button>
          </div>
          <div v-if="partnerComments.fromA" class="love-comment">
            "{{ partnerComments.fromA }}" ❤️
          </div>
        </div>
      </div>
    </div>

    <!-- 互动游戏区 -->
    <div class="interactive-zone" v-if="hasWinner">
      <div class="celebration">
        <div class="confetti">🎉 🎊 ✨ 🌟 🎉 🎊 ✨ 🌟</div>
        <div class="victory-message">{{ getVictoryMessage() }}</div>
      </div>
      <div class="next-battle">
        <button @click="startNewBattle" class="next-btn">🔥 Next Battle Round 🔥</button>
      </div>
    </div>

    <!-- 简化后的快速战斗总结（移除复杂模态框） -->
    <div v-if="showQuickSummary" class="quick-battle-summary">
      <div class="summary-header">
        <h3>⚡ Quick Battle Summary</h3>
        <button @click="showQuickSummary = false" class="close-btn">×</button>
      </div>
      <div class="battle-stats-simple">
        <div class="stat">{{ userA.name }}: {{ userA.photos.length }} dishes</div>
        <div class="stat">{{ userB.name }}: {{ userB.photos.length }} dishes</div>
        <div class="stat" v-if="hasWinner">Winner: {{ getWinnerName() }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import defaultAvatar from '@/assets/default-avatar.png'
import ChefAvatar from './battle/ChefAvatar.vue'
import EmptyChefSlot from './battle/EmptyChefSlot.vue'
import EnhancedAIScoreDisplay from './EnhancedAIScoreDisplay.vue'
import type { BattlePhoto, ChefBattleUser, AICommentData } from '@/models/couplememory'

// helper that repairs avatar URLs, as in ProfileView
const ORIGIN = location.origin
const fixAvatarUrl = (url?: string) => {
  if (!url) return defaultAvatar
  if (url.startsWith('http')) {
    return url.replace(/^https?:\/\/web:\d+/i, ORIGIN)
  }
  return url.startsWith('/') ? ORIGIN + url : url
}

const props = withDefaults(
  defineProps<{
    userA: ChefBattleUser
    userB: ChefBattleUser
    isAnalyzing?: boolean
    currentRecipe?: string
    aiComments?: AICommentData[]
  }>(),
  {
    isAnalyzing: false,
    currentRecipe: '',
    aiComments: () => []
  }
)

const emit = defineEmits<{
  newBattle: []
  commentSubmitted: [chef: string, comment: string]
}>()

// reactive state
const analysisProgress = ref(0)
const partnerComments = ref({
  toA: '',
  toB: '',
  fromA: '',
  fromB: ''
})

// 头像错误状态追踪
const avatarError = ref({
  userA: false,
  userB: false
})

// Inline gallery 展示状态
const showUserAGallery = ref(false)
const showUserBGallery = ref(false)
const showQuickSummary = ref(false)

// computed
const battlePhase = computed(() => {
  if (props.isAnalyzing) return 'judging'
  if (hasWinner.value) return 'decided'
  if (bothHaveDishes.value) return 'battle'
  return 'waiting'
})

const bothHaveDishes = computed(() => 
  getHighlightPhoto(props.userA) && getHighlightPhoto(props.userB)
)

const hasWinner = computed(() => {
  return props.userA.aiScore && props.userB.aiScore && 
         props.userA.aiScore !== props.userB.aiScore
})

// 方法函数
const getHighlightPhoto = (user: ChefBattleUser): BattlePhoto | null => {
  return user.photos.find((p: BattlePhoto) => p.isHighlight) || user.photos[0] || null
}

const isWinner = (fighter: 'A' | 'B'): boolean => {
  const scoreA = props.userA.aiScore || 0
  const scoreB = props.userB.aiScore || 0
  
  if (scoreA === scoreB) return false
  return fighter === 'A' ? scoreA > scoreB : scoreB > scoreA
}

const getChefStatus = (chef: 'A' | 'B') => {
  const user = chef === 'A' ? props.userA : props.userB
  return {
    'has-dish': !!getHighlightPhoto(user),
    'winner': isWinner(chef),
    'analyzing': props.isAnalyzing
  }
}

const getPhaseIcon = (): string => {
  if (props.isAnalyzing) return '⚖️'
  if (hasWinner.value) return '🏆'
  if (bothHaveDishes.value) return '⚔️'
  return '⏳'
}

const getPhaseText = (): string => {
  if (props.isAnalyzing) return 'AI Judge Analyzing...'
  if (hasWinner.value) return 'Battle Complete!'
  if (bothHaveDishes.value) return 'Epic Battle in Progress!'
  return 'Waiting for Chefs...'
}

const getAIJudgment = (user: ChefBattleUser): string => {
  if (!user.aiScore) return ''
  
  const score = user.aiScore
  if (score >= 95) return "🌟 Absolutely phenomenal! This is restaurant-quality perfection. Every detail shows mastery and passion!"
  if (score >= 90) return "👨‍🍳 Outstanding technique! Your culinary skills are truly impressive. Professional level execution!"
  if (score >= 85) return "🔥 Excellent work! This dish showcases great skill and creativity. You're becoming a master chef!"
  if (score >= 80) return "😋 Really good effort! The presentation and technique show real talent. Keep pushing forward!"
  if (score >= 75) return "👍 Good job! You're developing solid cooking fundamentals. Practice makes perfect!"
  if (score >= 70) return "💪 Nice try! There's clear potential here. Focus on technique refinement for even better results!"
  return "🍳 Keep experimenting! Every chef starts somewhere. The journey to mastery is about constant learning!"
}

const getRecipeMatch = (user: ChefBattleUser): string => {
  if (!user.aiScore) return 'Analyzing...'
  
  const score = user.aiScore
  if (score >= 90) return 'Perfect Match! 100%'
  if (score >= 80) return 'Great Match! 90%'
  if (score >= 70) return 'Good Match! 80%'
  if (score >= 60) return 'Fair Match 70%'
  return 'Creative Interpretation 60%'
}

const getWinnerName = (): string => {
  return isWinner('A') ? props.userA.name : props.userB.name
}

const getScoreDifference = (): number => {
  const scoreA = props.userA.aiScore || 0
  const scoreB = props.userB.aiScore || 0
  return Math.abs(scoreA - scoreB)
}

const getVictoryMessage = (): string => {
  const winner = getWinnerName()
  const messages = [
    `🎉 ${winner} claims victory in this epic culinary battle!`,
    `🏆 ${winner} emerges as the ultimate kitchen champion!`,
    `👑 Bow down to ${winner}, the master of flavors!`,
    `⭐ ${winner} has achieved culinary greatness!`
  ]
  return messages[Math.floor(Math.random() * messages.length)]
}

const submitComment = (chef: 'A' | 'B') => {
  const comment = chef === 'A' ? partnerComments.value.toA : partnerComments.value.toB
  if (comment.trim()) {
    emit('commentSubmitted', chef, comment)
    // Clear input
    if (chef === 'A') partnerComments.value.toA = ''
    else partnerComments.value.toB = ''
  }
}

const startNewBattle = () => {
  emit('newBattle')
}

// 获取用户相关的AI评论
const getUserAIComments = (user: ChefBattleUser): AICommentData[] => {
  if (!props.aiComments || props.aiComments.length === 0) return []
  
  return props.aiComments.filter(comment => {
    // 如果评论提到了用户名
    if (comment.text.toLowerCase().includes(user.name.toLowerCase())) {
      return true
    }
    // 如果评论提到了用户的食谱
    if (user.recipeName && comment.text.toLowerCase().includes(user.recipeName.toLowerCase())) {
      return true
    }
    // 如果评论分数接近用户分数（±10分以内）
    if (comment.rawScore && user.aiScore && Math.abs(comment.rawScore - user.aiScore) <= 10) {
      return true
    }
    return false
  }).slice(0, 2) // 最多显示2条相关评论
}

// 获取评论类型图标
const getCommentTypeIcon = (type: string) => {
  const iconMap = {
    positive: '👍',
    neutral: '🤔',
    suggestion: '💡',
    comparison: '⚖️',
    technical: '🔧'
  }
  return iconMap[type as keyof typeof iconMap] || '💬'
}

const getVisualScore = (chef: ChefBattleUser | null): number => {
  return chef?.aiScore ? Math.round((chef.aiScore / 100) * 10) : 0
}

const getTechniqueScore = (chef: ChefBattleUser | null): number => {
  return chef?.aiScore ? Math.round(((chef.aiScore + 5) / 100) * 10) : 0
}

const getRecipeMatchScore = (chef: ChefBattleUser | null): number => {
  return chef?.aiScore ? Math.round(((chef.aiScore - 5) / 100) * 10) : 0
}

// 新增：提醒伙伴做饭
const remindPartner = (partnerName: string) => {
  // TODO: Connect to backend API to send reminder notification
  alert(`Reminder sent to ${partnerName}! 🍳`)
}

// 新增：切换gallery显示
const toggleUserAGallery = () => {
  showUserAGallery.value = !showUserAGallery.value
  // 关闭另一个
  if (showUserAGallery.value) showUserBGallery.value = false
}

const toggleUserBGallery = () => {
  showUserBGallery.value = !showUserBGallery.value
  // 关闭另一个
  if (showUserBGallery.value) showUserAGallery.value = false
}

// 监听分析进度
watch(() => props.isAnalyzing, (newValue) => {
  if (newValue) {
    simulateAnalysis()
  }
})

const simulateAnalysis = () => {
  analysisProgress.value = 0
  const interval = setInterval(() => {
    analysisProgress.value += Math.random() * 15 + 5
    if (analysisProgress.value >= 100) {
      analysisProgress.value = 100
      clearInterval(interval)
    }
  }, 500)
}
</script>

<style scoped>
/* AAA游戏级主容器 */
.chef-arena {
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #2d1b69 100%);
  border-radius: 24px;
  padding: 24px;
  color: white;
  position: relative;
  overflow: hidden;
  min-height: 80vh;
}

.chef-arena::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(255, 107, 107, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(78, 205, 196, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 50% 50%, rgba(255, 215, 0, 0.05) 0%, transparent 50%);
  pointer-events: none;
  animation: ambientGlow 8s ease-in-out infinite;
}

/* 竞技场头部 */
.arena-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.battle-title h2 {
  margin: 0;
  font-size: 2rem;
  font-weight: bold;
  background: linear-gradient(45deg, #ff6b6b, #ffd700, #4ecdc4);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-align: center;
}

.battle-subtitle {
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 8px;
}

.subtitle-text {
  font-size: 1rem;
  display: block;
  margin-bottom: 6px;
}

.current-recipe {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(255, 215, 0, 0.2);
  border: 1px solid rgba(255, 215, 0, 0.4);
  border-radius: 20px;
  padding: 6px 16px;
  margin-top: 8px;
  backdrop-filter: blur(10px);
}

.recipe-icon {
  font-size: 1rem;
}

.recipe-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #ffd700;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
}

.battle-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border-radius: 25px;
  font-weight: bold;
  transition: all 0.3s ease;
}

.battle-status.waiting {
  background: rgba(255, 193, 7, 0.2);
  border: 2px solid rgba(255, 193, 7, 0.4);
}

.battle-status.battle {
  background: rgba(255, 107, 107, 0.2);
  border: 2px solid rgba(255, 107, 107, 0.4);
  animation: battlePulse 2s ease-in-out infinite;
}

.battle-status.judging {
  background: rgba(78, 205, 196, 0.2);
  border: 2px solid rgba(78, 205, 196, 0.4);
  animation: judgingPulse 1.5s ease-in-out infinite;
}

.battle-status.decided {
  background: rgba(255, 215, 0, 0.2);
  border: 2px solid rgba(255, 215, 0, 0.4);
  animation: victoryGlow 2s ease-in-out infinite;
}

.status-icon {
  font-size: 1.5rem;
}

/* PK战场布局 */
.pk-battlefield {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 24px;
  align-items: start;
  margin-bottom: 24px;
}

/* 选手区域 */
.chef-zone {
  background: rgba(255, 255, 255, 0.06);
  border-radius: 20px;
  padding: 20px;
  backdrop-filter: blur(15px);
  border: 2px solid transparent;
  transition: all 0.4s ease;
  position: relative;
}

.chef-zone.has-dish {
  border-color: rgba(78, 205, 196, 0.5);
  box-shadow: 0 0 30px rgba(78, 205, 196, 0.2);
}

.chef-zone.winner {
  border-color: #ffd700;
  box-shadow: 0 0 40px rgba(255, 215, 0, 0.4);
  animation: winnerGlow 2s ease-in-out infinite;
}

.chef-zone.analyzing {
  border-color: #00ff88;
  animation: analyzingPulse 1.5s ease-in-out infinite;
}

/* 选手资料 */
.chef-profile {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.chef-a .chef-profile {
  flex-direction: row;
}

.chef-b .chef-profile {
  flex-direction: row-reverse;
}

.chef-avatar {
  position: relative;
  width: 70px;
  height: 70px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  font-weight: bold;
  color: white;
  border: 3px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.chef-avatar:hover {
  transform: scale(1.05);
  border-color: rgba(255, 255, 255, 0.6);
}

.chef-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.chef-avatar .avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
}

.chef-crown {
  position: absolute;
  top: -5px;
  right: -5px;
  font-size: 1.2rem;
  background: rgba(255, 215, 0, 0.9);
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
  animation: crownShine 2s ease-in-out infinite;
}

.chef-info h3 {
  margin: 0 0 8px 0;
  font-size: 1.3rem;
  font-weight: bold;
}

.chef-recipe {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 6px 0;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 12px;
  border-radius: 12px;
  backdrop-filter: blur(5px);
}

.chef-b .chef-recipe {
  justify-content: flex-end;
}

.recipe-icon {
  font-size: 0.9rem;
}

.recipe-text {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.chef-a .chef-info {
  text-align: left;
}

.chef-b .chef-info {
  text-align: right;
}

.chef-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.chef-b .chef-score {
  justify-content: flex-end;
}

.score-number {
  font-size: 1.5rem;
  font-weight: bold;
  color: #ffd700;
}

.score-label {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

/* 料理聚光灯 */
.dish-spotlight {
  margin-bottom: 20px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spotlight-frame {
  position: relative;
  width: 100%;
  height: 200px;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 3px solid transparent;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
}

.spotlight-frame:hover {
  transform: scale(1.02);
  border-color: rgba(255, 255, 255, 0.4);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.spotlight-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.spotlight-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  padding: 16px;
  color: white;
}

.dish-label {
  font-size: 1.1rem;
  font-weight: bold;
  color: #ffd700;
}

.analyzing-pulse {
  margin-top: 8px;
  font-size: 0.9rem;
  animation: textPulse 1s ease-in-out infinite;
}

.empty-spotlight {
  width: 100%;
  height: auto; /* 让子组件自己控制高度 */
  display: flex;
  align-items: center;
  justify-content: center;
}

/* AI裁判区 */
.ai-judge-section {
  margin-bottom: 20px;
}

.judge-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: bold;
  color: #00ff88;
}

.judge-icon {
  font-size: 1.2rem;
}

.judgment-card {
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.3);
  border-radius: 12px;
  padding: 12px;
}

/* AI专业点评区域 - 游戏化手机tuning */
.ai-judge-section {
  background: linear-gradient(135deg, rgba(78, 205, 196, 0.15), rgba(17, 153, 142, 0.15));
  border-radius: 16px;
  padding: 12px;
  margin: 8px 0;
  border: 2px solid rgba(78, 205, 196, 0.3);
  box-shadow: 0 4px 20px rgba(78, 205, 196, 0.1);
  animation: ai-glow 3s ease-in-out infinite;
}

@keyframes ai-glow {
  0%, 100% { box-shadow: 0 4px 20px rgba(78, 205, 196, 0.1); }
  50% { box-shadow: 0 6px 25px rgba(78, 205, 196, 0.2); }
}

.judge-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(78, 205, 196, 0.2);
}

.judge-icon {
  font-size: 1.2rem;
  animation: pulse 2s infinite;
}

.judge-title {
  color: #4ecdc4;
  font-weight: 600;
  font-size: 0.9rem;
}

/* 真实AI评论气泡 - 手机游戏tuning */
.real-ai-comments {
  margin-bottom: 10px;
}

.ai-comment-bubble {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 10px;
  margin-bottom: 6px;
  border-left: 3px solid;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.ai-comment-bubble::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.05), transparent);
  transform: translateX(-100%);
  transition: transform 0.8s;
}

.ai-comment-bubble:hover::before {
  transform: translateX(100%);
}

.ai-comment-bubble:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.ai-comment-bubble.positive { 
  border-left-color: #4caf50; 
  background: rgba(76, 175, 80, 0.1);
}
.ai-comment-bubble.neutral { 
  border-left-color: #2196f3; 
  background: rgba(33, 150, 243, 0.1);
}
.ai-comment-bubble.suggestion { 
  border-left-color: #ff9800; 
  background: rgba(255, 152, 0, 0.1);
}
.ai-comment-bubble.comparison { 
  border-left-color: #9c27b0; 
  background: rgba(156, 39, 176, 0.1);
}
.ai-comment-bubble.technical { 
  border-left-color: #607d8b; 
  background: rgba(96, 125, 139, 0.1);
}

.ai-comment-bubble .comment-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 0.8rem;
}

.comment-type {
  font-size: 1.1rem;
  filter: drop-shadow(0 0 3px rgba(255, 255, 255, 0.5));
}

.comment-category {
  color: rgba(255, 255, 255, 0.9);
  flex: 1;
  font-weight: 500;
}

.score-badge {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.3), rgba(255, 193, 7, 0.3));
  color: #ffd700;
  padding: 3px 8px;
  border-radius: 10px;
  font-weight: bold;
  font-size: 0.75rem;
  border: 1px solid rgba(255, 215, 0, 0.4);
  box-shadow: 0 2px 4px rgba(255, 215, 0, 0.2);
}

.ai-comment-bubble .comment-text {
  color: rgba(255, 255, 255, 0.95);
  font-size: 0.85rem;
  line-height: 1.5;
  margin-bottom: 8px;
  font-weight: 400;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.confidence-bar {
  position: relative;
  height: 4px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 4px;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #4ecdc4, #44a08d);
  border-radius: 2px;
  transition: width 0.8s ease;
  position: relative;
}

.confidence-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: shimmer 2s infinite;
}

.confidence-text {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 2px;
}

/* 🎯 AI Metrics详细评分样式 */
.ai-metrics-breakdown {
  margin-top: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(78, 205, 196, 0.3);
}

.metrics-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #4ecdc4;
  margin-bottom: 8px;
  text-align: center;
}

.metric-item {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  gap: 8px;
}

.metric-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.9);
  min-width: 70px;
  text-align: left;
}

.metric-bar {
  flex: 1;
  position: relative;
  height: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.metric-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1);
  border-radius: 8px;
  transition: width 0.8s ease;
  position: relative;
}

.metric-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: metric-shimmer 2s infinite;
}

.metric-value {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.7rem;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
  z-index: 1;
}

@keyframes metric-shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff9800, #4caf50);
  border-radius: 2px;
  transition: width 0.8s ease;
}

.confidence-text {
  position: absolute;
  top: -18px;
  right: 0;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
}

.quality-score {
  margin-bottom: 12px;
}

.score-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b, #ffd700, #4ecdc4);
  border-radius: 4px;
  transition: width 1s ease;
}

.score-text {
  font-size: 0.9rem;
  font-weight: bold;
  color: #ffd700;
}

.ai-comment {
  margin: 12px 0;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
}

.recipe-match {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.match-icon {
  font-size: 1rem;
}

/* 情侣评论区 */
.couple-comments {
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 12px;
  padding: 16px;
}

.comment-header {
  font-weight: bold;
  color: #ff6b6b;
  margin-bottom: 12px;
  font-size: 0.95rem;
}

.comment-input {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.comment-input input {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  padding: 8px 12px;
  color: white;
  font-size: 0.9rem;
}

.comment-input input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.comment-btn {
  background: #ff6b6b;
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.comment-btn:hover {
  background: #ff5252;
  transform: scale(1.05);
}

.love-comment {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 8px 12px;
  font-style: italic;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
}

/* VS核心战斗区 */
.vs-core-battle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 140px;
  min-height: 300px;
  position: relative;
}

.energy-field {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  transition: all 0.3s ease;
  border: 3px solid rgba(255, 255, 255, 0.3);
}

.energy-field.active {
  animation: energyPulse 2s ease-in-out infinite;
  box-shadow: 0 0 40px rgba(78, 205, 196, 0.6);
}

.energy-field.winner {
  background: linear-gradient(135deg, #ffd700, #ff8c00);
  box-shadow: 0 0 50px rgba(255, 215, 0, 0.8);
  animation: victoryRotate 3s ease-in-out infinite;
}

.vs-symbol {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  z-index: 2;
}

.energy-waves {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.wave {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 20px;
  height: 20px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: waveExpand 2s ease-out infinite;
}

.wave:nth-child(2) { animation-delay: 0.7s; }
.wave:nth-child(3) { animation-delay: 1.4s; }

.battle-progress {
  text-align: center;
  width: 100%;
}

.progress-text {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 8px;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00ff88, #4ecdc4);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.final-verdict {
  text-align: center;
}

.winner-text {
  font-size: 1.1rem;
  font-weight: bold;
  color: #ffd700;
  margin-bottom: 4px;
}

.score-diff {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

/* 互动游戏区 */
.interactive-zone {
  margin-top: 32px;
  text-align: center;
}

.celebration {
  margin-bottom: 20px;
}

.confetti {
  font-size: 1.5rem;
  margin-bottom: 16px;
  animation: confettiDance 3s ease-in-out infinite;
}

.victory-message {
  font-size: 1.2rem;
  font-weight: bold;
  color: #ffd700;
  margin-bottom: 20px;
}

.next-btn {
  background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
  border: none;
  border-radius: 25px;
  padding: 16px 32px;
  color: white;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.next-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 25px rgba(78, 205, 196, 0.4);
  border-color: rgba(255, 255, 255, 0.3);
}

/* 料理详情模态框 */
.dish-detail-card {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  color: white;
}

.detail-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-content {
  padding: 24px;
}

.detail-image {
  margin-bottom: 20px;
  border-radius: 12px;
  overflow: hidden;
}

.detail-image img {
  width: 100%;
  height: 300px;
  object-fit: cover;
}

.detail-analysis h4 {
  color: #00ff88;
  margin-bottom: 16px;
}

.analysis-points {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.point {
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border-left: 3px solid #4ecdc4;
}

/* 动画定义 */
@keyframes ambientGlow {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

@keyframes battlePulse {
  0%, 100% { box-shadow: 0 0 15px rgba(255, 107, 107, 0.4); }
  50% { box-shadow: 0 0 25px rgba(255, 107, 107, 0.8); }
}

@keyframes judgingPulse {
  0%, 100% { box-shadow: 0 0 15px rgba(78, 205, 196, 0.4); }
  50% { box-shadow: 0 0 25px rgba(78, 205, 196, 0.8); }
}

@keyframes victoryGlow {
  0%, 100% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.4); }
  50% { box-shadow: 0 0 35px rgba(255, 215, 0, 0.8); }
}

@keyframes winnerGlow {
  0%, 100% { box-shadow: 0 0 40px rgba(255, 215, 0, 0.4); }
  50% { box-shadow: 0 0 60px rgba(255, 215, 0, 0.7); }
}

@keyframes analyzingPulse {
  0%, 100% { border-color: #00ff88; box-shadow: 0 0 20px rgba(0, 255, 136, 0.3); }
  50% { border-color: #4ecdc4; box-shadow: 0 0 35px rgba(78, 205, 196, 0.6); }
}

@keyframes crownShine {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); box-shadow: 0 0 15px rgba(255, 215, 0, 0.8); }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes textPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes energyPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes victoryRotate {
  0% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(180deg) scale(1.1); }
  100% { transform: rotate(360deg) scale(1); }
}

@keyframes waveExpand {
  0% { opacity: 1; transform: translate(-50%, -50%) scale(0); }
  100% { opacity: 0; transform: translate(-50%, -50%) scale(4); }
}

@keyframes confettiDance {
  0%, 100% { transform: translateY(0); }
  25% { transform: translateY(-5px); }
  75% { transform: translateY(5px); }
}

/* responsive layout */
@media (max-width: 1024px) {
  .pk-battlefield {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .vs-core-battle {
    order: 2;
    width: 100%;
    min-height: 120px;
  }
  
  .chef-profile {
    justify-content: center;
  }
  
  .chef-b .chef-profile {
    flex-direction: row;
  }
  
  .chef-info {
    text-align: center !important;
  }
  
  .chef-score {
    justify-content: center !important;
  }
}

@media (max-width: 768px) {
  .chef-arena {
    padding: 16px;
  }
  
  .arena-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .battle-title h2 {
    font-size: 1.5rem;
  }
  
  .chef-zone {
    padding: 16px;
  }
  
  .dish-spotlight {
    min-height: 150px;
  }
  
  .spotlight-frame {
    height: 150px;
  }
}

/* Inline Gallery样式 */
.inline-gallery {
  margin-top: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  font-weight: 600;
}

.close-gallery {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.close-gallery:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.photos-row {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 4px 0;
}

.photo-thumb {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  border: 2px solid transparent;
  transition: all 0.3s ease;
  cursor: pointer;
}

.photo-thumb:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.4);
}

.photo-thumb.highlight {
  border-color: #ffd700;
  box-shadow: 0 0 12px rgba(255, 215, 0, 0.4);
}

.photo-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-thumb .star {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 0.7rem;
  background: rgba(255, 215, 0, 0.9);
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.view-all-btn {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.spotlight-frame:hover .view-all-btn {
  opacity: 1;
}

.quick-battle-summary {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 255, 255, 0.95);
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  min-width: 300px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.summary-header h3 {
  margin: 0;
  color: #333;
}

.summary-header .close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.battle-stats-simple {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.battle-stats-simple .stat {
  padding: 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  color: #333;
}
.battle-compare-card {
  border-radius: 20px;
  overflow: hidden;
}

.compare-header {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.compare-header span {
  font-size: 1.3rem;
  font-weight: bold;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.compare-content {
  padding: 24px;
  background: #f8f9fa;
}

.side-by-side {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.chef-side {
  flex: 1;
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.chef-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.chef-avatar-small, .chef-avatar-text-small {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-weight: bold;
  font-size: 1.2rem;
}

.chef-header h3 {
  margin: 0;
  flex: 1;
  font-size: 1.1rem;
  color: #333;
}

.score-display {
  background: linear-gradient(135deg, #ff6b6b, #ffa726);
  color: white;
  padding: 8px 12px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 0.9rem;
}

.dishes-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  min-height: 200px;
}

.dish-item {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  aspect-ratio: 1;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.dish-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.dish-item.highlight {
  border-color: #ffd700;
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
}

.dish-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.star-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  background: rgba(255, 215, 0, 0.9);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
}

.vs-separator {
  display: flex;
  align-items: center;
  padding: 0 10px;
}

.vs-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b6b, #ffa726);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
}

.vs-text {
  color: white;
  font-weight: bold;
  font-size: 1.2rem;
}

.no-dishes {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #999;
}

.empty-placeholder {
  font-size: 2rem;
  margin-bottom: 8px;
  opacity: 0.5;
}

.empty-text {
  font-size: 0.9rem;
}

.quick-stats {
  display: flex;
  justify-content: space-around;
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-top: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}

.stat {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 4px;
}

.stat-number {
  font-size: 1.2rem;
  font-weight: bold;
  color: #333;
}

.winner-stat .stat-number.winner {
  color: #ff6b6b;
  background: linear-gradient(135deg, #ff6b6b, #ffa726);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

@media (max-width: 768px) {
  .side-by-side {
    flex-direction: column;
  }
  
  .vs-separator {
    padding: 12px 0;
    justify-content: center;
  }
  
  .dishes-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .quick-stats {
    flex-direction: column;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .chef-arena {
    padding: 12px;
  }
  
  .battle-title h2 {
    font-size: 1.2rem;
  }
  
  .chef-avatar {
    width: 50px;
    height: 50px;
    font-size: 1.3rem;
  }
  
  .dish-spotlight {
    min-height: 120px;
  }
  
  .spotlight-frame {
    height: 120px;
  }
  
  .comment-input {
    flex-direction: column;
  }
}
</style>

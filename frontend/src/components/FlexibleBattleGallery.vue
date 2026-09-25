<!-- 智能情侣料理PK系统 - 根据实际数据动态渲染 -->
<template>
  <div class="flexible-battle-gallery">
    <!-- 双人PK模式 -->
    <div v-if="hasValidUsers" class="couple-pk-mode">
      <!-- Recipe信息头部 -->
      <div v-if="recipeInfo?.winnerRecipe" class="recipe-header">
        <div class="recipe-crown">👑</div>
        <div class="recipe-info">
          <h2 class="recipe-title">{{ recipeInfo.winnerRecipe }}</h2>
          <div class="recipe-stats">
            <span class="stat">{{ recipeInfo.totalPoints }} pts</span>
            <span class="stat">{{ recipeInfo.entriesCount }} entries</span>
            <span class="stat">{{ roundSummary?.commentsCount || 0 }} comments</span>
          </div>
        </div>
        <div class="round-period" v-if="roundSummary">
          {{ formatDateRange(roundSummary.roundStart, roundSummary.roundEnd) }}
        </div>
      </div>

      <ChefArena1v1 
        :user-a="userA!"
        :user-b="userB!" 
        :is-analyzing="isAnalyzing"
        :current-recipe="recipeInfo?.winnerRecipe || currentRecipe"
        :ai-comments="hideAiSection ? [] : aiComments"
        @new-battle="$emit('newBattle')"
        @comment-submitted="$emit('commentSubmitted', $event)"
        @remind-partner="$emit('remindPartner', $event)"
      />
      
      <!-- 弹幕留言墙 - 真实数据驱动 -->
      <DanmakuCommentWall 
        :comments="commentWallData"
        :is-active="hasValidUsers && !isAnalyzing"
        @add-comment="handleNewComment"
      />
    </div>

    <!-- 单人等待模式 - 紧凑手机tuning -->
    <div v-else-if="singleUserData" class="waiting-for-partner mobile-optimized">
      <!-- 紧凑的厨师卡片 -->
      <div class="compact-chef-card">
        <div class="chef-avatar-section">
          <ChefAvatar 
            :avatar="singleUserData.avatar" 
            :name="singleUserData.name"
            :is-winner="false"
          />
          <div class="chef-info">
            <h3>{{ singleUserData.name }}</h3>
            <div class="chef-stats">
              <span class="stat-chip">{{ singleUserData.photos.length }} dishes</span>
              <span class="stat-chip">{{ singleUserData.aiScore || 'N/A' }} AI</span>
            </div>
          </div>
        </div>
        
        <!-- 照片预览网格 -->
        <div class="photos-grid-compact">
          <div v-for="(photo, index) in singleUserData.photos.slice(0, 4)" 
               :key="index" class="photo-thumbnail">
            <img :src="photo.url" :alt="`Dish ${index + 1}`">
          </div>
          <div v-if="singleUserData.photos.length > 4" class="more-photos-indicator">
            +{{ singleUserData.photos.length - 4 }}
          </div>
        </div>
        
        <!-- 等待消息 -->
        <div class="waiting-message-compact">
          <span class="status-text">🍽️ Ready to battle!</span>
          <button @click="remindPartner" class="remind-btn-compact">
            <span class="btn-icon">🔔</span>
            <span>Remind Partner</span>
          </button>
        </div>
      </div>

      <!-- 简化弹幕留言 - 真实数据驱动 -->
      <DanmakuCommentWall 
        :comments="commentWallData"
        :is-active="true"
        :solo-mode="true"
        @add-comment="handleSoloComment"
      />
    </div>

    <!-- 完全空状态 -->
    <div v-else class="empty-battle-state">
      <div class="empty-illustration">
        <div class="kitchen-icon">🍳</div>
        <h2>No Cooking Battle Yet</h2>
        <p>Start cooking to begin the roundly battle!</p>
      </div>
      
      <button @click="$emit('startCooking')" class="start-cooking-btn">
        <span class="btn-icon">👨‍🍳</span>
        <span>Start Cooking</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import ChefArena1v1 from './ChefArena1v1.vue'
import ChefAvatar from './battle/ChefAvatar.vue'
import DanmakuCommentWall from './DanmakuCommentWall.vue'
import type { 
  BattlePhoto, 
  FlexibleBattleUser, 
  CommentData, 
  AICommentData, 
  RecipeInfo, 
  RoundSummary 
} from '@/models/couplememory'

const props = withDefaults(
  defineProps<{
    userA: FlexibleBattleUser | null
    userB: FlexibleBattleUser | null
    aiComments?: AICommentData[]
    realComments?: CommentData[]
    isAnalyzing?: boolean
    currentRecipe?: string
    recipeInfo?: RecipeInfo | null
    roundSummary?: RoundSummary | null
    hideAiSection?: boolean
  }>(),
  {
    aiComments: () => [],
    realComments: () => [],
    isAnalyzing: false,
    currentRecipe: '',
    recipeInfo: null,
    roundSummary: null,
    hideAiSection: false
  }
)

const emit = defineEmits<{
  newBattle: []
  commentSubmitted: [data: any]
  remindPartner: [username: string]
  startCooking: []
}>()

// computed
const hasValidUsers = computed(() => {
  return (props.userA?.photos?.length ?? 0) > 0 && (props.userB?.photos?.length ?? 0) > 0
})

const singleUserData = computed(() => {
  if ((props.userA?.photos?.length ?? 0) > 0 && !(props.userB?.photos?.length ?? 0)) {
    return props.userA
  }
  if ((props.userB?.photos?.length ?? 0) > 0 && !(props.userA?.photos?.length ?? 0)) {
    return props.userB
  }
  return null
})

// 使用真实评论数据作为弹幕墙数据源
const commentWallData = computed(() => props.realComments || [])

// 方法
const remindPartner = () => {
  const partnerName = singleUserData.value ? 
    (singleUserData.value.name === props.userA?.name ? (props.userB?.name ?? 'Partner') : (props.userA?.name ?? 'Partner')) :
    'Partner'
  
  emit('remindPartner', partnerName)
}

const formatDateRange = (start?: string, end?: string) => {
  if (!start || !end) return ''
  const startDate = new Date(start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const endDate = new Date(end).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  return `${startDate} - ${endDate}`
}

const getCommentTypeIcon = (type: string) => {
  const iconMap = {
    positive: '👏',
    neutral: '💭',
    suggestion: '💡',
    comparison: '⚖️',
    technical: '🔧'
  }
  return iconMap[type as keyof typeof iconMap] || '💬'
}

const formatTimestamp = (timestamp?: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const handleNewComment = (commentText: string) => {
  const newComment: CommentData = {
    id: Date.now().toString(),
    username: 'You',
    text: commentText,
    timestamp: Date.now(),
    type: 'cheer'
  }
  
  // hand it to the parent, which owns the update
  emit('commentSubmitted', newComment)
}

const handleSoloComment = (commentText: string) => {
  const newComment: CommentData = {
    id: Date.now().toString(),
    username: 'You',
    text: commentText,
    timestamp: Date.now(),
    type: 'cheer'
  }
  
  // hand it to the parent, which owns the update
  emit('commentSubmitted', newComment)
}
</script>

<style scoped>
.flexible-battle-gallery {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

/* Recipe信息头部 */
.recipe-header {
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.recipe-crown {
  font-size: 2rem;
  animation: crown-float 2s ease-in-out infinite;
}

@keyframes crown-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

@keyframes ai-feature-glow {
  0%, 100% { 
    box-shadow: 0 12px 40px rgba(78, 205, 196, 0.3);
    border-color: rgba(78, 205, 196, 0.6);
  }
  50% { 
    box-shadow: 0 16px 50px rgba(78, 205, 196, 0.5);
    border-color: rgba(78, 205, 196, 0.8);
  }
}

.recipe-info {
  flex: 1;
}

.recipe-title {
  color: white;
  font-size: 1.8rem;
  font-weight: bold;
  margin: 0 0 8px 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.recipe-stats {
  display: flex;
  gap: 16px;
}

.recipe-stats .stat {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 12px;
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
}

.round-period {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.95rem;
  font-weight: 500;
}

/* AI评论专区 */
.ai-comments-section {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  border: 2px solid rgba(78, 205, 196, 0.3);
  box-shadow: 0 8px 32px rgba(78, 205, 196, 0.1);
}

/* 核心卖点突出显示 */
.ai-comments-section.featured {
  background: linear-gradient(135deg, #2d1b69 0%, #11998e 100%);
  border: 3px solid rgba(78, 205, 196, 0.6);
  box-shadow: 0 12px 40px rgba(78, 205, 196, 0.3);
  animation: ai-feature-glow 3s ease-in-out infinite;
}

.ai-section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.ai-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.ai-section-header h3 {
  color: #4ecdc4;
  margin: 0;
  font-size: 1.3rem;
  flex: 1;
}

.analysis-count {
  background: rgba(78, 205, 196, 0.2);
  color: #4ecdc4;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.ai-comments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

/* Mobiletuning网格 */
.ai-comments-grid.mobile-optimized {
  grid-template-columns: 1fr;
  gap: 8px;
}

.ai-comment-card {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px;
  border-left: 4px solid;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

/* Mobiletuning卡片 */
.ai-comment-card.mobile-card {
  padding: 10px;
  border-radius: 8px;
  font-size: 0.9rem;
}

.ai-comment-card:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-2px);
}

.ai-comment-card.positive {
  border-left-color: #4caf50;
}

.ai-comment-card.neutral {
  border-left-color: #2196f3;
}

.ai-comment-card.suggestion {
  border-left-color: #ff9800;
}

.ai-comment-card.comparison {
  border-left-color: #9c27b0;
}

.ai-comment-card.technical {
  border-left-color: #607d8b;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.comment-type-badge {
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.comment-type-badge.positive {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.comment-type-badge.suggestion {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.confidence-score {
  background: linear-gradient(135deg, #ffd700, #ffb300);
  color: #2d3748;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: bold;
}

.comment-text {
  color: white;
  line-height: 1.5;
  margin-bottom: 12px;
  font-size: 0.95rem;
}

.comment-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
}

.confidence {
  color: rgba(255, 255, 255, 0.6);
}

.timestamp {
  color: rgba(255, 255, 255, 0.5);
}

/* 单人等待模式 - 重新设计为紧凑布局 */
.waiting-for-partner {
  padding: 16px;
  margin: 0 auto;
  max-width: 400px;
}

.waiting-for-partner.mobile-optimized {
  padding: 12px;
  margin-bottom: 12px;
  max-width: 100%;
}

/* 紧凑厨师卡片 */
.compact-chef-card {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px;
  backdrop-filter: blur(10px);
  margin-bottom: 12px;
}

.chef-avatar-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.chef-info h3 {
  margin: 0 0 4px 0;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
}

.chef-stats {
  display: flex;
  gap: 6px;
}

.stat-chip {
  background: rgba(78, 205, 196, 0.2);
  color: #4ecdc4;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* 照片网格 */
.photos-grid-compact {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-bottom: 12px;
}

.photo-thumbnail {
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
}

.photo-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.more-photos-indicator {
  aspect-ratio: 1;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
}

/* 等待消息 */
.waiting-message-compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.status-text {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  font-weight: 500;
}

.remind-btn-compact {
  background: linear-gradient(135deg, #ff6b6b, #ff8e53);
  border: none;
  color: white;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
}

.remind-btn-compact:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
}

.remind-btn-compact .btn-icon {
  font-size: 0.9rem;
}

.chef-section {
  text-align: center;
  flex: 1;
}

.chef-section h3 {
  color: white;
  margin: 15px 0;
  font-size: 1.5rem;
}

.photos-preview {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 15px;
}

.preview-photo {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.preview-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.more-photos {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 0.9rem;
}

.waiting-section {
  flex: 1;
  text-align: center;
}

.waiting-message h2 {
  color: white;
  margin-bottom: 10px;
  font-size: 1.8rem;
}

.waiting-message p {
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 25px;
  font-size: 1.1rem;
}

.remind-partner-btn {
  background: linear-gradient(135deg, #ff6b6b, #ff8e53);
  border: none;
  color: white;
  padding: 15px 30px;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 auto 25px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
}

.remind-partner-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(255, 107, 107, 0.5);
}

.btn-pulse {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}

.waiting-stats {
  display: flex;
  gap: 30px;
  justify-content: center;
}

.stat {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 1.8rem;
  font-weight: bold;
  color: #ffd700;
}

.stat-label {
  display: block;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 4px;
}

/* 完全空状态 */
.empty-battle-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 40px;
}

.empty-illustration {
  margin-bottom: 30px;
}

.kitchen-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.empty-illustration h2 {
  color: white;
  font-size: 2rem;
  margin-bottom: 10px;
}

.empty-illustration p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.2rem;
}

.start-cooking-btn {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  border: none;
  color: white;
  padding: 18px 40px;
  border-radius: 50px;
  font-size: 1.2rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s ease;
  box-shadow: 0 8px 25px rgba(78, 205, 196, 0.4);
}

.start-cooking-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(78, 205, 196, 0.5);
}

/* responsive layout */
@media (max-width: 768px) {
  .solo-chef-display {
    flex-direction: column;
    gap: 25px;
    padding: 20px;
  }
  
  .waiting-stats {
    gap: 20px;
  }
  
  .remind-partner-btn {
    padding: 12px 25px;
    font-size: 1rem;
  }
}
</style>

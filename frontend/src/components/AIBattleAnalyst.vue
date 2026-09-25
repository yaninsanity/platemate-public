<!-- AIbattle analyst component comparing the dishes of user A and user B -->
<template>
  <div class="ai-battle-analyst">
    <!-- AI分析师头像和状态 -->
    <div class="analyst-header">
      <div class="ai-avatar" :class="{ 'thinking': isAnalyzing }">
        <v-icon size="24" :color="isAnalyzing ? '#ffd700' : '#4ecdc4'">
          {{ isAnalyzing ? 'mdi-brain' : 'mdi-robot' }}
        </v-icon>
      </div>
      <div class="analyst-info">
        <div class="analyst-name">
          Kinny AI Chef Analyst
        </div>
        <div class="analyst-status" :class="{ 'analyzing': isAnalyzing }">
          {{ isAnalyzing ? 'Analyzing battle data...' : 'Analysis complete' }}
        </div>
      </div>
      <div class="confidence-meter" v-if="!isAnalyzing && overallConfidence > 0">
        <div class="meter-label">Accuracy</div>
        <div class="meter-bar">
          <div 
            class="meter-fill" 
            :style="{ width: `${overallConfidence * 100}%` }"
          ></div>
        </div>
        <div class="meter-value">{{ Math.round(overallConfidence * 100) }}%</div>
      </div>
    </div>

    <!-- 分析结果展示 -->
    <div class="analysis-results" v-if="!isAnalyzing">
      <!-- 主要结论 -->
      <div class="main-conclusion" v-if="mainConclusion">
        <div class="conclusion-icon">🏆</div>
        <div class="conclusion-text">{{ mainConclusion }}</div>
      </div>

      <!-- 详细评论列表 -->
      <div class="detailed-comments">
        <div 
          v-for="comment in sortedComments" 
          :key="comment.id"
          class="comment-card"
          :class="comment.type"
        >
          <div class="comment-header">
            <div class="comment-icon">
              <v-icon size="16" :color="getCommentColor(comment.type)">
                {{ getCommentIcon(comment.type) }}
              </v-icon>
            </div>
            <div class="comment-category">{{ comment.category }}</div>
            <div class="comment-confidence">
              <div class="confidence-badge" :class="getConfidenceLevel(comment.confidence)">
                {{ Math.round(comment.confidence * 100) }}%
              </div>
            </div>
          </div>
          <div class="comment-body">
            {{ comment.text }}
          </div>
          <div class="comment-insights" v-if="comment.insights?.length">
            <div class="insights-list">
              <div 
                v-for="insight in comment.insights" 
                :key="insight"
                class="insight-tag"
              >
                {{ insight }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 战斗统计 -->
      <div class="battle-stats" v-if="battleStats">
        <div class="stats-header">
          <v-icon size="18" color="#9c27b0">mdi-chart-line</v-icon>
          <span>Battle Statistics</span>
        </div>
        <div class="stats-grid">
          <div class="stat-item" v-for="stat in battleStats" :key="stat.label">
            <div class="stat-icon">{{ stat.icon }}</div>
            <div class="stat-content">
              <div class="stat-label">{{ stat.label }}</div>
              <div class="stat-value">{{ stat.value }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 改进建议 -->
      <div class="improvement-suggestions" v-if="suggestions.length > 0">
        <div class="suggestions-header">
          <v-icon size="18" color="#ff9800">mdi-lightbulb-outline</v-icon>
          <span>Kinny's Suggestions</span>
        </div>
        <div class="suggestions-list">
          <div 
            v-for="suggestion in suggestions" 
            :key="suggestion.id"
            class="suggestion-card"
            @click="highlightSuggestion(suggestion.id)"
          >
            <div class="suggestion-avatar">{{ suggestion.emoji }}</div>
            <div class="suggestion-content">
              <div class="suggestion-title">{{ suggestion.title }}</div>
              <div class="suggestion-text">{{ suggestion.text }}</div>
            </div>
            <div class="suggestion-priority" :class="suggestion.priority">
              <div class="priority-dot"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载动画 -->
    <div class="analyzing-animation" v-if="isAnalyzing">
      <div class="analysis-steps">
        <div 
          v-for="step in analysisSteps" 
          :key="step.id"
          class="analysis-step"
          :class="{ 
            'active': step.id <= currentStep,
            'completed': step.id < currentStep
          }"
        >
          <div class="step-icon">
            <v-icon size="16">{{ step.icon }}</v-icon>
          </div>
          <div class="step-text">{{ step.text }}</div>
          <div class="step-progress" v-if="step.id === currentStep">
            <div class="progress-dots">
              <div class="dot"></div>
              <div class="dot"></div>
              <div class="dot"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { BattleUser, AICommentData } from '@/models/couplememory'

// Props接口定义  
interface Suggestion {
  id: string
  title: string
  text: string
  emoji: string
  priority: 'high' | 'medium' | 'low'
}

interface AnalystAIComment extends AICommentData {
  insights?: string[]
}

const props = withDefaults(
  defineProps<{
    userA: BattleUser | null
    userB: BattleUser | null
    comments: AnalystAIComment[]
    isAnalyzing?: boolean
  }>(),
  {
    isAnalyzing: false,
    comments: () => []
  }
)

// reactive state
const currentStep = ref(1)
const highlightedSuggestion = ref<string | null>(null)

// 分析步骤
const analysisSteps = [
  { id: 1, icon: 'mdi-camera', text: 'Analyzing photos...' },
  { id: 2, icon: 'mdi-food', text: 'Evaluating technique...' },
  { id: 3, icon: 'mdi-chart-line', text: 'Comparing results...' },
  { id: 4, icon: 'mdi-check', text: 'Generating insights...' }
]

// computed
const overallConfidence = computed(() => {
  if (props.comments.length === 0) return 0
  const total = props.comments.reduce((sum, comment) => sum + comment.confidence, 0)
  return total / props.comments.length
})

const sortedComments = computed(() => {
  return [...props.comments].sort((a, b) => b.confidence - a.confidence)
})

const mainConclusion = computed(() => {
  if (!props.userA || !props.userB) return ''
  
  const scoreA = props.userA.aiScore || 0
  const scoreB = props.userB.aiScore || 0
  const photosA = props.userA.photos.length
  const photosB = props.userB.photos.length
  
  if (Math.abs(scoreA - scoreB) < 5) {
    return `🤝 Extremely close battle! Both ${props.userA.name} and ${props.userB.name} show exceptional culinary skills.`
  } else if (scoreA > scoreB) {
    return `🏆 ${props.userA.name} takes the lead with superior technique and presentation!`
  } else {
    return `🏆 ${props.userB.name} dominates with outstanding culinary execution!`
  }
})

const battleStats = computed(() => {
  if (!props.userA || !props.userB) return []
  
  return [
    {
      icon: '📸',
      label: 'Photo Battle',
      value: `${props.userA.photos.length} vs ${props.userB.photos.length}`
    },
    {
      icon: '⭐',
      label: 'Highlights',
      value: `${props.userA.photos.filter(p => p.isHighlight).length} vs ${props.userB.photos.filter(p => p.isHighlight).length}`
    },
    {
      icon: '🎯',
      label: 'AI Scores',
      value: `${Math.round(props.userA.aiScore || 0)} vs ${Math.round(props.userB.aiScore || 0)}`
    }
  ]
})

const suggestions = computed(() => {
  const result: Suggestion[] = []
  
  if (!props.userA || !props.userB) return result
  
  // 根据数据生成建议
  if (props.userA.photos.length < 3) {
    result.push({
      id: 'photos-a',
      title: `More photos for ${props.userA.name}`,
      text: 'Document more cooking steps to improve AI analysis accuracy.',
      emoji: '📸',
      priority: 'medium'
    })
  }
  
  if (props.userB.photos.length < 3) {
    result.push({
      id: 'photos-b',
      title: `More photos for ${props.userB.name}`,
      text: 'Capture different angles and cooking stages for better evaluation.',
      emoji: '📸',
      priority: 'medium'
    })
  }
  
  // 根据AI评分差异给建议
  const scoreDiff = Math.abs((props.userA.aiScore || 0) - (props.userB.aiScore || 0))
  if (scoreDiff > 20) {
    const lowerScorer = (props.userA.aiScore || 0) < (props.userB.aiScore || 0) ? props.userA.name : props.userB.name
    result.push({
      id: 'technique-improvement',
      title: `Technique boost for ${lowerScorer}`,
      text: 'Focus on plating presentation and ingredient preparation for higher scores.',
      emoji: '👨‍🍳',
      priority: 'high'
    })
  }
  
  return result
})

// 方法
const getCommentIcon = (type: string) => {
  const iconMap = {
    positive: 'mdi-thumb-up',
    neutral: 'mdi-information',
    suggestion: 'mdi-lightbulb-outline',
    comparison: 'mdi-compare',
    technical: 'mdi-cog'
  }
  return iconMap[type as keyof typeof iconMap] || 'mdi-comment'
}

const getCommentColor = (type: string) => {
  const colorMap = {
    positive: '#4caf50',
    neutral: '#2196f3',
    suggestion: '#ff9800',
    comparison: '#9c27b0',
    technical: '#607d8b'
  }
  return colorMap[type as keyof typeof colorMap] || '#9e9e9e'
}

const getConfidenceLevel = (confidence: number) => {
  if (confidence >= 0.8) return 'high'
  if (confidence >= 0.6) return 'medium'
  return 'low'
}

const highlightSuggestion = (id: string) => {
  highlightedSuggestion.value = id
  setTimeout(() => {
    highlightedSuggestion.value = null
  }, 2000)
}

// 模拟分析过程
watch(() => props.isAnalyzing, (analyzing) => {
  if (analyzing) {
    currentStep.value = 1
    const interval = setInterval(() => {
      currentStep.value++
      if (currentStep.value > analysisSteps.length) {
        clearInterval(interval)
      }
    }, 800)
  }
})
</script>

<style scoped>
.ai-battle-analyst {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9));
  border-radius: 16px;
  padding: 20px;
  color: white;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(78, 205, 196, 0.2);
}

/* AI分析师头部 */
.analyst-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.ai-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.ai-avatar.thinking {
  animation: thinking 2s ease-in-out infinite;
  background: linear-gradient(135deg, #ffd700, #ffb300);
}

@keyframes thinking {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1) rotate(5deg); }
}

.analyst-info {
  flex: 1;
}

.analyst-name {
  font-weight: bold;
  font-size: 1.1rem;
  color: #4ecdc4;
}

.analyst-status {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 2px;
}

.analyst-status.analyzing {
  color: #ffd700;
  animation: statusBlink 1.5s ease-in-out infinite;
}

@keyframes statusBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.confidence-meter {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 80px;
}

.meter-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
}

.meter-bar {
  width: 60px;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b, #ffa500, #4caf50);
  border-radius: 2px;
  transition: width 0.8s ease;
}

.meter-value {
  font-size: 0.75rem;
  font-weight: bold;
  color: #4caf50;
}

/* 主要结论 */
.main-conclusion {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 215, 0, 0.1);
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.conclusion-icon {
  font-size: 1.5rem;
}

.conclusion-text {
  font-size: 0.95rem;
  line-height: 1.4;
  color: #ffd700;
  font-weight: 500;
}

/* 详细评论 */
.detailed-comments {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.comment-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 12px;
  border-left: 3px solid;
  transition: all 0.3s ease;
}

.comment-card.positive {
  border-left-color: #4caf50;
}

.comment-card.neutral {
  border-left-color: #2196f3;
}

.comment-card.suggestion {
  border-left-color: #ff9800;
}

.comment-card.comparison {
  border-left-color: #9c27b0;
}

.comment-card.technical {
  border-left-color: #607d8b;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.comment-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.comment-category {
  font-size: 0.8rem;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.8);
  flex: 1;
}

.confidence-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: bold;
}

.confidence-badge.high {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.confidence-badge.medium {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.confidence-badge.low {
  background: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.comment-body {
  font-size: 0.9rem;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.9);
}

.insights-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.insight-tag {
  background: rgba(78, 205, 196, 0.2);
  color: #4ecdc4;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 500;
}

/* 战斗统计 */
.battle-stats {
  background: rgba(156, 39, 176, 0.1);
  border: 1px solid rgba(156, 39, 176, 0.2);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 20px;
}

.stats-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: bold;
  color: #9c27b0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  padding: 8px;
  border-radius: 8px;
}

.stat-icon {
  font-size: 1.2rem;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
}

.stat-value {
  font-size: 0.85rem;
  font-weight: bold;
  color: white;
}

/* 改进建议 */
.improvement-suggestions {
  background: rgba(255, 152, 0, 0.1);
  border: 1px solid rgba(255, 152, 0, 0.2);
  border-radius: 10px;
  padding: 12px;
}

.suggestions-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: bold;
  color: #ff9800;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.05);
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.suggestion-card:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.suggestion-avatar {
  font-size: 1.2rem;
  width: 32px;
  text-align: center;
}

.suggestion-content {
  flex: 1;
}

.suggestion-title {
  font-size: 0.85rem;
  font-weight: bold;
  color: white;
  margin-bottom: 2px;
}

.suggestion-text {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.3;
}

.suggestion-priority {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.suggestion-priority.high .priority-dot {
  background: #f44336;
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.suggestion-priority.medium .priority-dot {
  background: #ff9800;
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.suggestion-priority.low .priority-dot {
  background: #4caf50;
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

/* 分析动画 */
.analyzing-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 20px 0;
}

.analysis-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  max-width: 300px;
}

.analysis-step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
  opacity: 0.4;
}

.analysis-step.active {
  opacity: 1;
  background: rgba(255, 215, 0, 0.1);
}

.analysis-step.completed {
  opacity: 0.7;
  background: rgba(76, 175, 80, 0.1);
}

.step-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-text {
  flex: 1;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.progress-dots {
  display: flex;
  gap: 4px;
}

.progress-dots .dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #ffd700;
  animation: dotPulse 1.5s ease-in-out infinite;
}

.progress-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.progress-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dotPulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* responsive layout */
@media (max-width: 768px) {
  .analyst-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .main-conclusion {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
}

@media (max-width: 480px) {
  .ai-battle-analyst {
    padding: 12px;
  }
  
  .confidence-meter {
    min-width: 60px;
  }
  
  .meter-bar {
    width: 40px;
  }
}
</style>

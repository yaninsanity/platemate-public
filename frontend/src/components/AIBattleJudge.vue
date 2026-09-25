<!-- AI裁判系统 - 专业的战斗分析和评价 -->
<template>
  <div class="ai-battle-judge">
    <!-- 裁判头部 -->
    <div class="judge-header">
      <div class="judge-avatar">
        <div class="ai-brain" :class="{ 'thinking': isAnalyzing }">
          <v-icon size="24" color="white">mdi-brain</v-icon>
        </div>
      </div>
      <div class="judge-info">
        <h3 class="judge-name">AI Battle Judge</h3>
        <p class="judge-status">{{ judgeStatusText }}</p>
      </div>
      <div class="battle-stats" v-if="!isAnalyzing && battleWinner">
        <div class="stat-item">
          <span class="stat-label">Winner</span>
          <span class="stat-value winner-name">{{ battleWinner.name }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Score Gap</span>
          <span class="stat-value">{{ scoreGap }}pts</span>
        </div>
      </div>
    </div>

    <!-- 分析进度 -->
    <div class="analysis-progress" v-if="isAnalyzing">
      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${analysisProgress}%` }"></div>
        </div>
        <span class="progress-text">{{ Math.round(analysisProgress) }}%</span>
      </div>
      <div class="current-analysis">
        <v-icon size="16" color="#00ff88">mdi-magnify-scan</v-icon>
        <span>{{ currentAnalysisStep }}</span>
      </div>
    </div>

    <!-- AI评论和分析 -->
    <div class="analysis-results" v-if="!isAnalyzing && comments.length > 0">
      <!-- 综合评分对比 -->
      <div class="score-comparison">
        <div class="score-card score-a">
          <div class="fighter-mini">
            <img v-if="userA.avatar" :src="userA.avatar" :alt="userA.name" />
            <span v-else>{{ userA.name[0] }}</span>
          </div>
          <div class="score-details">
            <span class="fighter-name">{{ userA.name }}</span>
            <div class="score-bar">
              <div class="score-fill" :style="{ width: `${(userA.aiScore || 0)}%` }"></div>
            </div>
            <span class="score-number">{{ Math.round(userA.aiScore || 0) }}pts</span>
          </div>
        </div>

        <div class="vs-divider">
          <span class="vs-text">VS</span>
        </div>

        <div class="score-card score-b">
          <div class="score-details">
            <span class="fighter-name">{{ userB.name }}</span>
            <div class="score-bar">
              <div class="score-fill" :style="{ width: `${(userB.aiScore || 0)}%` }"></div>
            </div>
            <span class="score-number">{{ Math.round(userB.aiScore || 0) }}pts</span>
          </div>
          <div class="fighter-mini">
            <img v-if="userB.avatar" :src="userB.avatar" :alt="userB.name" />
            <span v-else>{{ userB.name[0] }}</span>
          </div>
        </div>
      </div>

      <!-- AI评论列表 -->
      <div class="ai-comments">
        <h4 class="comments-title">
          <v-icon size="20" color="#4ecdc4">mdi-comment-text</v-icon>
          AI Analysis Report
        </h4>
        
        <div class="comments-grid">
          <div 
            v-for="comment in comments" 
            :key="comment.id"
            class="comment-card"
            :class="`comment-${comment.type}`"
          >
            <div class="comment-header">
              <v-icon size="18" :color="getCommentColor(comment.type)">
                {{ getCommentIcon(comment.type) }}
              </v-icon>
              <span class="comment-category">{{ comment.category }}</span>
              <div class="confidence-badge">
                <span>{{ Math.round(comment.confidence * 100) }}%</span>
              </div>
            </div>
            <p class="comment-text">{{ comment.text }}</p>
            
            <!-- 洞察点 -->
            <div class="comment-insights" v-if="comment.insights && comment.insights.length > 0">
              <div class="insights-title">Key Insights:</div>
              <ul class="insights-list">
                <li v-for="insight in comment.insights" :key="insight">{{ insight }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 改进建议 -->
      <div class="improvement-suggestions" v-if="suggestions.length > 0">
        <h4 class="suggestions-title">
          <v-icon size="20" color="#ffd700">mdi-lightbulb</v-icon>
          Battle Improvement Tips
        </h4>
        
        <div class="suggestions-list">
          <div 
            v-for="suggestion in suggestions" 
            :key="suggestion.id"
            class="suggestion-item"
          >
            <div class="suggestion-icon">
              <v-icon size="16" color="#ffd700">mdi-arrow-up</v-icon>
            </div>
            <div class="suggestion-content">
              <span class="suggestion-target">{{ suggestion.target }}</span>
              <p class="suggestion-text">{{ suggestion.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 战斗统计 -->
    <div class="battle-statistics" v-if="!isAnalyzing">
      <h4 class="stats-title">Battle Statistics</h4>
      
      <div class="stats-grid">
        <div class="stat-box">
          <v-icon size="20" color="#ff6b6b">mdi-camera</v-icon>
          <span class="stat-label">Total Photos</span>
          <span class="stat-value">{{ totalPhotos }}</span>
        </div>
        
        <div class="stat-box">
          <v-icon size="20" color="#4ecdc4">mdi-star</v-icon>
          <span class="stat-label">Avg Quality</span>
          <span class="stat-value">{{ averageScore }}pts</span>
        </div>
        
        <div class="stat-box">
          <v-icon size="20" color="#ffd700">mdi-trophy</v-icon>
          <span class="stat-label">Winner</span>
          <span class="stat-value">{{ battleWinner?.name || 'TBD' }}</span>
        </div>
        
        <div class="stat-box">
          <v-icon size="20" color="#9c27b0">mdi-clock</v-icon>
          <span class="stat-label">Analysis Time</span>
          <span class="stat-value">{{ analysisTime }}s</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { BattleUser, AICommentData } from '@/models/couplememory'

// Props和类型定义
interface Suggestion {
  id: string
  target: string
  text: string
}

interface AIComment extends AICommentData {
  insights?: string[]
}

const props = withDefaults(
  defineProps<{
    userA: BattleUser
    userB: BattleUser
    comments?: AIComment[]
    isAnalyzing?: boolean
    battleWinner?: BattleUser | null
  }>(),
  {
    comments: () => [],
    isAnalyzing: false,
    battleWinner: null
  }
)

const emit = defineEmits<{
  analysisComplete: [result: any]
}>()

// reactive state
const analysisProgress = ref(0)
const currentAnalysisStep = ref('Initializing analysis...')
const analysisTime = ref(0)

// computed
const judgeStatusText = computed(() => {
  if (props.isAnalyzing) return 'Analyzing battle data...'
  if (props.battleWinner) return `Analysis complete - ${props.battleWinner.name} declared winner!`
  return 'Ready to analyze'
})

const scoreGap = computed(() => {
  if (!props.userA.aiScore || !props.userB.aiScore) return 0
  return Math.abs(props.userA.aiScore - props.userB.aiScore).toFixed(1)
})

const totalPhotos = computed(() => props.userA.photos.length + props.userB.photos.length)

const averageScore = computed(() => {
  const scores = [props.userA.aiScore, props.userB.aiScore].filter(s => s !== null && s !== undefined) as number[]
  if (scores.length === 0) return 0
  return Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
})

const suggestions = computed(() => {
  // 基于评论生成改进建议
  const suggestionList: Suggestion[] = []
  
  if (props.userA.photos.length < props.userB.photos.length) {
    suggestionList.push({
      id: 'more-photos-a',
      target: props.userA.name,
      text: 'Try capturing more angles and cooking steps to showcase your technique better.'
    })
  } else if (props.userB.photos.length < props.userA.photos.length) {
    suggestionList.push({
      id: 'more-photos-b',
      target: props.userB.name,
      text: 'Consider documenting more stages of your cooking process for better scoring.'
    })
  }
  
  if (props.userA.aiScore && props.userA.aiScore < 70) {
    suggestionList.push({
      id: 'improve-presentation-a',
      target: props.userA.name,
      text: 'Focus on plating and presentation - good visuals can significantly boost your score!'
    })
  }
  
  if (props.userB.aiScore && props.userB.aiScore < 70) {
    suggestionList.push({
      id: 'improve-presentation-b',
      target: props.userB.name,
      text: 'Work on lighting and composition when photographing your dishes.'
    })
  }
  
  return suggestionList
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
  return colorMap[type as keyof typeof colorMap] || '#666'
}

// 模拟分析进度
const simulateAnalysis = () => {
  if (!props.isAnalyzing) return
  
  const steps = [
    'Scanning photo composition...',
    'Evaluating cooking technique...',
    'Analyzing ingredient quality...',
    'Assessing presentation style...',
    'Comparing battle entries...',
    'Calculating final scores...',
    'Generating insights...',
    'Finalizing analysis report...'
  ]
  
  let stepIndex = 0
  let progress = 0
  const startTime = Date.now()
  
  const interval = setInterval(() => {
    if (!props.isAnalyzing) {
      clearInterval(interval)
      analysisTime.value = Math.round((Date.now() - startTime) / 1000)
      emit('analysisComplete', { winner: props.battleWinner })
      return
    }
    
    progress += Math.random() * 12 + 3
    analysisProgress.value = Math.min(progress, 98)
    
    if (progress > stepIndex * 12) {
      currentAnalysisStep.value = steps[stepIndex] || 'Completing analysis...'
      stepIndex++
    }
  }, 600)
}

// 监听分析状态变化
watch(() => props.isAnalyzing, (newValue) => {
  if (newValue) {
    analysisProgress.value = 0
    analysisTime.value = 0
    simulateAnalysis()
  } else {
    analysisProgress.value = 100
  }
})

onMounted(() => {
  if (props.isAnalyzing) {
    simulateAnalysis()
  }
})
</script>

<style scoped>
.ai-battle-judge {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  border: 2px solid rgba(78, 205, 196, 0.3);
}

/* 裁判头部 */
.judge-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.judge-avatar {
  position: relative;
}

.ai-brain {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 32px rgba(78, 205, 196, 0.3);
  transition: all 0.3s ease;
}

.ai-brain.thinking {
  animation: thinkingPulse 2s ease-in-out infinite;
}

.judge-info {
  flex: 1;
}

.judge-name {
  font-size: 1.3rem;
  font-weight: bold;
  margin: 0 0 8px 0;
  color: #4ecdc4;
}

.judge-status {
  margin: 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.95rem;
}

.battle-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 1.1rem;
  font-weight: bold;
}

.winner-name {
  color: #ffd700;
}

/* 分析进度 */
.analysis-progress {
  margin-bottom: 24px;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4ecdc4, #44a08d);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-weight: bold;
  color: #4ecdc4;
  min-width: 45px;
}

.current-analysis {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

/* 分析结果 */
.analysis-results {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 评分对比 */
.score-comparison {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.score-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-a {
  flex-direction: row;
}

.score-b {
  flex-direction: row-reverse;
}

.fighter-mini {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
}

.fighter-mini img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.score-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.score-a .score-details {
  align-items: flex-start;
}

.score-b .score-details {
  align-items: flex-end;
}

.fighter-name {
  font-weight: bold;
  font-size: 0.95rem;
}

.score-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b, #ffd700, #4ecdc4);
  border-radius: 3px;
  transition: width 0.8s ease;
}

.score-number {
  font-size: 1.1rem;
  font-weight: bold;
  color: #ffd700;
}

.vs-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
  font-weight: bold;
  font-size: 0.9rem;
}

/* AI评论 */
.ai-comments {
  margin-bottom: 32px;
}

.comments-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 1.1rem;
  color: #4ecdc4;
}

.comments-grid {
  display: grid;
  gap: 16px;
}

.comment-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid;
  transition: all 0.3s ease;
}

.comment-card:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-2px);
}

.comment-positive { border-left-color: #4caf50; }
.comment-neutral { border-left-color: #2196f3; }
.comment-suggestion { border-left-color: #ff9800; }
.comment-comparison { border-left-color: #9c27b0; }
.comment-technical { border-left-color: #607d8b; }

.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.comment-category {
  flex: 1;
  font-weight: bold;
  font-size: 0.9rem;
}

.confidence-badge {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
}

.comment-text {
  margin: 0 0 12px 0;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.9);
}

.comment-insights {
  margin-top: 12px;
}

.insights-title {
  font-size: 0.85rem;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 6px;
}

.insights-list {
  margin: 0;
  padding-left: 16px;
  color: rgba(255, 255, 255, 0.8);
}

.insights-list li {
  font-size: 0.85rem;
  line-height: 1.4;
  margin-bottom: 4px;
}

/* 改进建议 */
.improvement-suggestions {
  margin-bottom: 32px;
}

.suggestions-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 1.1rem;
  color: #ffd700;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 215, 0, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(255, 215, 0, 0.2);
}

.suggestion-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ffd700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.suggestion-content {
  flex: 1;
}

.suggestion-target {
  font-weight: bold;
  color: #ffd700;
  font-size: 0.9rem;
}

.suggestion-text {
  margin: 4px 0 0 0;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.4;
}

/* 战斗统计 */
.battle-statistics {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.stats-title {
  font-size: 1.1rem;
  color: #4ecdc4;
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  text-align: center;
}

.stat-box .stat-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

.stat-box .stat-value {
  font-size: 1rem;
  font-weight: bold;
  color: white;
}

/* 动画 */
@keyframes thinkingPulse {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 8px 32px rgba(78, 205, 196, 0.3);
  }
  50% { 
    transform: scale(1.05);
    box-shadow: 0 12px 40px rgba(78, 205, 196, 0.5);
  }
}

/* responsive layout */
@media (max-width: 768px) {
  .judge-header {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .battle-stats {
    justify-content: center;
  }
  
  .score-comparison {
    flex-direction: column;
    gap: 12px;
  }
  
  .score-card {
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .ai-battle-judge {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>

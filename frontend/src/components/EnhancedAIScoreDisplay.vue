<!-- AAAAI score display, tuned for a gamified mobile feel -->
<template>
  <div class="enhanced-ai-score-display" :class="{ 'is-analyzing': isAnalyzing, 'is-mobile': isMobile }">
    <!-- 主评分卡片 -->
    <div class="main-score-card" v-if="aiJudgment || aiScore" @click="onMainCardClick">
      <!-- 总分和等级展示 -->
      <div class="score-header" :class="{ 'compact': !isExpanded }">
        <div class="score-circle" :class="getScoreClass(effectiveScore)">
          <div class="score-number">{{ effectiveScore?.toFixed(0) || '?' }}</div>
          <div class="score-label">Score</div>
          <!-- 移动端展开指示器 -->
          <div class="expand-hint" v-if="isMobile && !isExpanded">
            <div class="pulse-ring"></div>
            <span class="hint-text">👆 Tap to expand</span>
          </div>
        </div>
        
        <div class="score-info">
          <div class="chef-level" :class="getLevelClass(effectiveScore)">
            {{ getChefLevel(effectiveScore) }}
          </div>
          <div class="confidence-indicator" v-if="aiJudgment" :class="{ 'hidden-mobile': isMobile && !isExpanded }">
            <span class="confidence-text">Confidence</span>
            <div class="confidence-bars">
              <div 
                v-for="i in 5" 
                :key="i" 
                class="confidence-bar" 
                :class="{ active: i <= Math.round(aiJudgment.confidence * 5) }"
              ></div>
            </div>
            <span class="confidence-percentage">{{ Math.round(aiJudgment.confidence * 100) }}%</span>
          </div>
        </div>
        
        <!-- 移动端快速预览 -->
        <div class="mobile-preview" v-if="isMobile && !isExpanded && aiJudgment">
          <div class="preview-metrics">
            <div class="preview-metric">
              <span class="preview-icon">🌟</span>
              <span class="preview-score">{{ aiJudgment.visual_appeal.toFixed(0) }}</span>
            </div>
            <div class="preview-metric">
              <span class="preview-icon">🔥</span>
              <span class="preview-score">{{ aiJudgment.cooking_technique.toFixed(0) }}</span>
            </div>
            <div class="preview-metric">
              <span class="preview-icon">🌱</span>
              <span class="preview-score">{{ aiJudgment.ingredient_freshness.toFixed(0) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 详细metrics展示 -->
      <div class="metrics-section" v-if="aiJudgment" v-show="!isMobile || isExpanded">
        <h4 class="metrics-title">🎯 Detailed Analysis</h4>
        <div class="metrics-grid" :class="{ 'mobile-expanded': isMobile && isExpanded }">
          <div class="metric-item">
            <div class="metric-icon">🌟</div>
            <div class="metric-content">
              <div class="metric-name">Visual Appeal</div>
              <div class="metric-score-bar">
                <div 
                  class="metric-fill visual" 
                  :style="{ width: `${aiJudgment.visual_appeal}%` }"
                ></div>
                <span class="metric-value">{{ aiJudgment.visual_appeal.toFixed(0) }}</span>
              </div>
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-icon">🔥</div>
            <div class="metric-content">
              <div class="metric-name">Cooking Technique</div>
              <div class="metric-score-bar">
                <div 
                  class="metric-fill technique" 
                  :style="{ width: `${aiJudgment.cooking_technique}%` }"
                ></div>
                <span class="metric-value">{{ aiJudgment.cooking_technique.toFixed(0) }}</span>
              </div>
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-icon">🌱</div>
            <div class="metric-content">
              <div class="metric-name">Ingredient Freshness</div>
              <div class="metric-score-bar">
                <div 
                  class="metric-fill freshness" 
                  :style="{ width: `${aiJudgment.ingredient_freshness}%` }"
                ></div>
                <span class="metric-value">{{ aiJudgment.ingredient_freshness.toFixed(0) }}</span>
              </div>
            </div>
          </div>

          <div class="metric-item" v-if="aiJudgment.creativity_innovation !== undefined">
            <div class="metric-icon">💡</div>
            <div class="metric-content">
              <div class="metric-name">Creativity & Innovation</div>
              <div class="metric-score-bar">
                <div 
                  class="metric-fill creativity" 
                  :style="{ width: `${aiJudgment.creativity_innovation}%` }"
                ></div>
                <span class="metric-value">{{ aiJudgment.creativity_innovation.toFixed(0) }}</span>
              </div>
            </div>
          </div>

          <div class="metric-item" v-if="aiJudgment.nutrition_balance !== undefined">
            <div class="metric-icon">⚖️</div>
            <div class="metric-content">
              <div class="metric-name">Nutrition Balance</div>
              <div class="metric-score-bar">
                <div 
                  class="metric-fill nutrition" 
                  :style="{ width: `${aiJudgment.nutrition_balance}%` }"
                ></div>
                <span class="metric-value">{{ aiJudgment.nutrition_balance.toFixed(0) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI评语展示 -->
      <div class="ai-comment-section" v-if="aiJudgment">
        <div class="platemate-avatar">🤖</div>
        <div class="comment-bubble">
          <div class="comment-header">
            <span class="platemate-name">Kinny • Virtual Pet Chef</span>
            <span class="comment-time">{{ formatTime(aiJudgment.created_at) }}</span>
          </div>
          <div class="comment-text">{{ getEffectiveComment(aiJudgment) }}</div>
          <div class="comment-summary" v-if="getEffectiveSummary(aiJudgment)">
            <span class="summary-label">💭 Summary:</span>
            {{ getEffectiveSummary(aiJudgment) }}
          </div>
          
          <!-- Battle Info Display -->
          <div class="battle-info" v-if="aiJudgment.has_battle_data || aiJudgment.battle_comment">
            <div class="battle-header">🥊 Couple Battle</div>
            <div class="battle-content" v-if="aiJudgment.battle_comment">
              {{ aiJudgment.battle_comment }}
            </div>
            <div class="battle-summary" v-if="aiJudgment.battle_summary">
              <span class="battle-label">⚔️ Result:</span>
              {{ aiJudgment.battle_summary }}
            </div>
          </div>
          
          <!-- Mastery Level Display -->
          <div class="mastery-level" v-if="aiJudgment.mastery_level">
            <span class="mastery-label">🏆 Level:</span>
            <span class="mastery-value">{{ aiJudgment.mastery_level }}</span>
          </div>
          
          <!-- Improvement Tips -->
          <div class="improvement-tips" v-if="aiJudgment.improvement_tips && aiJudgment.improvement_tips.length > 0">
            <div class="tips-header">💡 Pro Tips:</div>
            <ul class="tips-list">
              <li v-for="(tip, index) in aiJudgment.improvement_tips" :key="index" class="tip-item">
                {{ tip }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- 分析中状态 -->
    <div class="analyzing-state" v-else-if="isAnalyzing">
      <div class="analyzing-animation">
        <div class="platemate-thinking">🤖</div>
        <div class="analyzing-text">
          <h3>Kinny is analyzing...</h3>
          <div class="analyzing-steps">
            <div class="step" :class="{ active: analyzeStep >= 1 }">📸 Image Parsing</div>
            <div class="step" :class="{ active: analyzeStep >= 2 }">🔍 Detail Recognition</div>
            <div class="step" :class="{ active: analyzeStep >= 3 }">⚖️ Scoring</div>
            <div class="step" :class="{ active: analyzeStep >= 4 }">✨ Generating Review</div>
          </div>
        </div>
      </div>
      <div class="analyzing-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${Math.min(100, analyzeStep * 25)}%` }"></div>
        </div>
      </div>
    </div>

    <!-- 等待评分状态 -->
  <div class="waiting-score" v-else>
      <div class="waiting-icon">⏳</div>
      <div class="waiting-text">
    <h4>Waiting for score...</h4>
    <p>Upload a photo and Kinny will score it.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import type { AIJudgment } from '@/models/couplememory'

interface Props {
  aiJudgment?: AIJudgment | null
  aiScore?: number | null
  isAnalyzing?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isAnalyzing: false
})

// Analysis step animation
const analyzeStep = ref(0)

// Mobile gaming expansion state
const isExpanded = ref(false)
const isMobile = ref(false)

// Check if running on mobile device
onMounted(() => {
  const checkMobile = () => {
    isMobile.value = window.innerWidth <= 768
  }
  checkMobile()
  window.addEventListener('resize', checkMobile)
  
  // Cleanup
  return () => window.removeEventListener('resize', checkMobile)
})

// Handle main card click for mobile expansion
const onMainCardClick = () => {
  if (isMobile.value) {
    isExpanded.value = !isExpanded.value
    
    // Add haptic feedback if available
    if (navigator.vibrate) {
      navigator.vibrate(50)
    }
    
    // Add visual feedback
    const card = document.querySelector('.main-score-card')
    if (card) {
      card.classList.add('tap-feedback')
      setTimeout(() => card.classList.remove('tap-feedback'), 200)
    }
  }
}

// Effective score (prefer detailed score)
const effectiveScore = computed(() => {
  return props.aiJudgment?.overall_score ?? props.aiScore
})

// Map score to chef level label
const getChefLevel = (score?: number | null): string => {
  if (!score) return 'Pending'

  if (score >= 90) return '🏆 Legendary Master'
  if (score >= 80) return '⭐ Culinary Expert'
  if (score >= 70) return '🔥 Skilled Cook'
  if (score >= 60) return '👍 Rising Chef'
  return '💪 Great Potential'
}

// Style class by score band
const getScoreClass = (score?: number | null): string => {
  if (!score) return 'no-score'
  
  if (score >= 90) return 'legendary'
  if (score >= 80) return 'expert'
  if (score >= 70) return 'skilled'
  if (score >= 60) return 'rising'
  return 'potential'
}

// Level uses the same class mapping
const getLevelClass = (score?: number | null): string => {
  return getScoreClass(score)
}

// Format relative time (en)
const formatTime = (timeStr?: string): string => {
  if (!timeStr) return ''
  
  try {
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
  if (diff < 60000) return 'just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} h ago`
  return `${Math.floor(diff / 86400000)} d ago`
  } catch {
  return 'unknown'
  }
}

// Helper functions for effective comments
const getEffectiveComment = (judgment: AIJudgment): string => {
  return judgment.effective_comment || judgment.individual_comment || judgment.ai_comment || ''
}

const getEffectiveSummary = (judgment: AIJudgment): string => {
  return judgment.effective_summary || judgment.individual_summary || judgment.ai_summary || ''
}

// 分析动画
watch(() => props.isAnalyzing, (newVal) => {
  if (newVal) {
    analyzeStep.value = 0
    const timer = setInterval(() => {
      if (analyzeStep.value < 4) {
        analyzeStep.value++
      } else {
        clearInterval(timer)
      }
    }, 800)
  }
})
</script>

<style scoped>
.enhanced-ai-score-display {
  width: 100%;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 主评分卡片 */
.main-score-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 24px;
  color: white;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.main-score-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

/* Mobile tap feedback */
.main-score-card.tap-feedback {
  transform: scale(0.98);
  transition: transform 0.1s ease;
}

/* Mobile specific styles */
.is-mobile .main-score-card {
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.is-mobile .score-header.compact {
  margin-bottom: 16px;
}

/* 评分头部 */
.score-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.score-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  background: rgba(255, 255, 255, 0.1);
  border: 3px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.score-circle.legendary { border-color: #ffd700; background: rgba(255, 215, 0, 0.2); }
.score-circle.expert { border-color: #ff6b6b; background: rgba(255, 107, 107, 0.2); }
.score-circle.skilled { border-color: #4ecdc4; background: rgba(78, 205, 196, 0.2); }
.score-circle.rising { border-color: #45b7d1; background: rgba(69, 183, 209, 0.2); }
.score-circle.potential { border-color: #96ceb4; background: rgba(150, 206, 180, 0.2); }

.score-number {
  font-size: 1.8rem;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 0.75rem;
  opacity: 0.8;
  margin-top: 2px;
}

/* 展开提示动画 */
.expand-hint {
  position: absolute;
  bottom: -25px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  animation: float 2s ease-in-out infinite;
}

.pulse-ring {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  animation: pulse-ring 1.5s ease-in-out infinite;
}

.hint-text {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  white-space: nowrap;
}

/* Mobile preview metrics */
.mobile-preview {
  margin-top: 16px;
}

.preview-metrics {
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px 8px;
  backdrop-filter: blur(5px);
}

.preview-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.preview-icon {
  font-size: 1.2rem;
}

.preview-score {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

/* Hidden mobile elements */
.hidden-mobile {
  opacity: 0;
  transform: translateY(-10px);
  transition: all 0.3s ease;
}

.is-mobile .hidden-mobile {
  display: none;
}

.score-info {
  flex: 1;
}

.chef-level {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.chef-level.legendary { color: #ffd700; }
.chef-level.expert { color: #ff6b6b; }
.chef-level.skilled { color: #4ecdc4; }
.chef-level.rising { color: #45b7d1; }
.chef-level.potential { color: #96ceb4; }

.confidence-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.confidence-bars {
  display: flex;
  gap: 2px;
}

.confidence-bar {
  width: 4px;
  height: 12px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  transition: all 0.3s ease;
}

.confidence-bar.active {
  background: #4ecdc4;
  transform: scaleY(1.2);
}

.confidence-percentage {
  font-weight: 600;
  color: #4ecdc4;
}

/* 详细metrics */
.metrics-section {
  margin-bottom: 20px;
}

.metrics-title {
  font-size: 1rem;
  margin-bottom: 16px;
  color: rgba(255, 255, 255, 0.9);
}

.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.metric-item:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateX(4px);
}

.metric-icon {
  font-size: 1.2rem;
  width: 24px;
  text-align: center;
}

.metric-content {
  flex: 1;
}

.metric-name {
  font-size: 0.85rem;
  opacity: 0.8;
  margin-bottom: 4px;
}

.metric-score-bar {
  position: relative;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.metric-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.8s ease;
  position: relative;
}

.metric-fill.visual { background: linear-gradient(90deg, #ffd700, #ffed4e); }
.metric-fill.technique { background: linear-gradient(90deg, #ff6b6b, #ff8e53); }
.metric-fill.freshness { background: linear-gradient(90deg, #4ecdc4, #44a08d); }
.metric-fill.creativity { background: linear-gradient(90deg, #9b59b6, #8e44ad); }
.metric-fill.nutrition { background: linear-gradient(90deg, #27ae60, #2ecc71); }

.metric-value {
  position: absolute;
  right: 8px;
  top: -20px;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
}

/* AI评语部分 */
.ai-comment-section {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.platemate-avatar {
  font-size: 2rem;
  animation: float 2s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.comment-bubble {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px 16px 16px 4px;
  padding: 16px;
  position: relative;
}

.comment-bubble::before {
  content: '';
  position: absolute;
  left: -8px;
  top: 16px;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 8px 8px 8px 0;
  border-color: transparent rgba(255, 255, 255, 0.1) transparent transparent;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.platemate-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.comment-time {
  font-size: 0.75rem;
  opacity: 0.7;
}

.comment-text {
  font-size: 0.9rem;
  line-height: 1.4;
  margin-bottom: 8px;
}

.comment-summary {
  font-size: 0.8rem;
  opacity: 0.8;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-label {
  font-weight: 600;
  color: #4ecdc4;
}

/* 对战信息显示 */
.battle-info {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  border-left: 4px solid #ff6b6b;
}

.battle-header {
  font-weight: 600;
  color: #ff6b6b;
  font-size: 0.85rem;
  margin-bottom: 6px;
}

.battle-content {
  font-size: 0.85rem;
  margin-bottom: 6px;
}

.battle-summary {
  font-size: 0.8rem;
  opacity: 0.9;
}

.battle-label {
  font-weight: 600;
  color: #ffd700;
}

/* 分析中状态 */
.analyzing-state {
  text-align: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  color: white;
}

.analyzing-animation {
  margin-bottom: 24px;
}

.platemate-thinking {
  font-size: 3rem;
  animation: think 1.5s ease-in-out infinite;
  margin-bottom: 16px;
}

@keyframes think {
  0%, 100% { transform: scale(1) rotate(0deg); }
  50% { transform: scale(1.1) rotate(5deg); }
}

.analyzing-text h3 {
  margin-bottom: 16px;
  font-size: 1.2rem;
}

.analyzing-steps {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  max-width: 300px;
  margin: 0 auto;
}

.step {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  font-size: 0.8rem;
  transition: all 0.3s ease;
  opacity: 0.5;
}

.step.active {
  background: rgba(255, 255, 255, 0.2);
  opacity: 1;
  transform: scale(1.05);
}

.analyzing-progress {
  width: 100%;
  max-width: 300px;
  margin: 0 auto;
}

.progress-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4ecdc4, #44a08d);
  border-radius: 2px;
  transition: width 0.8s ease;
}

/* 等待状态 */
.waiting-score {
  text-align: center;
  padding: 40px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  color: rgba(255, 255, 255, 0.7);
}

.waiting-icon {
  font-size: 2.5rem;
  margin-bottom: 16px;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.waiting-text h4 {
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.9);
}

.waiting-text p {
  font-size: 0.9rem;
  opacity: 0.8;
}

/* responsive layout */
@media (max-width: 768px) {
  .main-score-card {
    padding: 20px;
  }
  
  .score-header {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .metrics-grid {
    gap: 10px;
  }
  
  .analyzing-steps {
    grid-template-columns: 1fr;
    gap: 6px;
  }
  
  .step {
    font-size: 0.75rem;
    padding: 6px 10px;
  }
}

/* Mastery Level Styling */
.mastery-level {
  margin-top: 12px;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 179, 0, 0.15));
  border-radius: 8px;
  border-left: 3px solid #ffd700;
}

.mastery-label {
  font-weight: 600;
  color: #ffd700;
  margin-right: 8px;
}

.mastery-value {
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Improvement Tips Styling */
.improvement-tips {
  margin-top: 12px;
  padding: 12px;
  background: linear-gradient(135deg, rgba(78, 205, 196, 0.1), rgba(68, 160, 141, 0.1));
  border-radius: 8px;
  border-left: 3px solid #4ecdc4;
}

.tips-header {
  font-weight: 600;
  color: #4ecdc4;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.tips-list {
  margin: 0;
  padding-left: 16px;
  color: rgba(255, 255, 255, 0.9);
}

.tip-item {
  margin-bottom: 4px;
  font-size: 0.85rem;
  line-height: 1.4;
}

.tip-item:last-child {
  margin-bottom: 0;
}

@media (max-width: 480px) {
  .score-circle {
    width: 70px;
    height: 70px;
  }
  
  .score-number {
    font-size: 1.5rem;
  }
  
  .chef-level {
    font-size: 1rem;
  }
  
  .comment-bubble {
    padding: 12px;
  }
  
  .analyzing-state,
  .waiting-score {
    padding: 30px 16px;
  }
  
  /* Mobile specific enhancements */
  .mobile-preview {
    margin-top: 12px;
  }
  
  .preview-metrics {
    padding: 10px 6px;
  }
  
  .preview-icon {
    font-size: 1rem;
  }
  
  .preview-score {
    font-size: 0.75rem;
  }
  
  .expand-hint {
    bottom: -20px;
  }
  
  .hint-text {
    font-size: 0.6rem;
  }
}

/* Mobile gaming animations */
@keyframes float {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(-5px); }
}

@keyframes pulse-ring {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Enhanced metrics grid for mobile expansion */
.metrics-grid.mobile-expanded {
  animation: expand-in 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes expand-in {
  0% {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Touch-friendly metric items on mobile */
@media (max-width: 768px) {
  .metric-item {
    padding: 16px 12px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.05);
    margin-bottom: 12px;
    transition: all 0.2s ease;
  }
  
  .metric-item:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-1px);
  }
  
  .metrics-grid {
    gap: 8px;
  }
}
</style>

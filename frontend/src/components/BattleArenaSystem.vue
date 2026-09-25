<!-- gamified arena: the full AI-judged head-to-head -->
<template>
  <div class="battle-arena-system">
    <!-- 战斗状态栏 -->
    <div class="battle-status-bar">
      <div class="status-left">
        <v-icon color="#ff6b6b" size="20">mdi-sword-cross</v-icon>
        <span class="status-text">Cooking Battle</span>
      </div>
      <div class="battle-timer" :class="{ 'analyzing': isAnalyzing }">
        <v-icon size="16" :color="isAnalyzing ? '#ffd700' : '#4ecdc4'">
          {{ isAnalyzing ? 'mdi-brain' : 'mdi-check-circle' }}
        </v-icon>
        <span>{{ battleStatusText }}</span>
      </div>
      <div class="round-indicator">
        <span>Round {{ currentRound }}</span>
      </div>
    </div>

    <!-- 主战斗竞技场 -->
    <div class="main-arena" :class="battleLayoutClass">
      <!-- 选手A战斗卡 -->
      <div class="fighter-card fighter-a" :class="fighterAClass">
        <div class="fighter-header">
          <div class="fighter-portrait">
            <img v-if="userA.avatar" :src="userA.avatar" :alt="userA.name" />
            <div v-else class="avatar-placeholder">{{ userA.name[0] }}</div>
            <div class="fighter-status" :class="userA.battleStatus">
              <v-icon size="12">{{ getFighterStatusIcon(userA.battleStatus) }}</v-icon>
            </div>
          </div>
          <div class="fighter-info">
            <h3 class="fighter-name">{{ userA.name }}</h3>
            <div class="fighter-stats">
              <span class="stat-item">
                <v-icon size="14">mdi-camera</v-icon>
                {{ userA.photos.length }} photos
              </span>
              <span class="stat-item" v-if="userA.aiScore !== null">
                <v-icon size="14" color="#ffd700">mdi-star</v-icon>
                {{ Math.round(userA.aiScore || 0) }}pts
              </span>
            </div>
          </div>
          <div class="power-level">
            <div class="power-bar">
              <div 
                class="power-fill"
                :style="{ width: `${Math.min((userA.aiScore || 0), 100)}%` }"
              ></div>
            </div>
            <span class="power-text">{{ Math.round(userA.aiScore || 0) }}</span>
          </div>
        </div>

        <!-- 弹性照片展示区 -->
        <div class="photos-arena" :class="`photos-${userA.photos.length}`">
          <div 
            v-for="(photo, index) in userA.photos" 
            :key="`a-${index}`"
            class="photo-battle-card"
            :class="{ 
              'highlight': photo.isHighlight,
              'analyzing': isAnalyzing && currentAnalyzingPhoto === `a-${index}`
            }"
            @click="openBattleGallery('A', index)"
          >
            <img :src="photo.url" :alt="`${userA.name} photo ${index + 1}`" />
            <div v-if="photo.isHighlight" class="highlight-crown">👑</div>
            <div v-if="isAnalyzing && currentAnalyzingPhoto === `a-${index}`" class="analyze-pulse">
              <v-icon color="white">mdi-brain</v-icon>
            </div>
          </div>
          
          <!-- 空位显示 -->
          <div 
            v-for="n in (maxPhotos - userA.photos.length)" 
            :key="`a-empty-${n}`"
            class="photo-empty-slot"
          >
            <v-icon size="32" color="rgba(255,255,255,0.3)">mdi-plus</v-icon>
            <span class="empty-text">Waiting...</span>
          </div>
        </div>
      </div>

      <!-- VS对战核心 -->
      <div class="vs-battle-core">
        <div class="energy-field" :class="{ 'active': isAnalyzing }">
          <div class="energy-ring"></div>
          <div class="vs-symbol">
            <span class="vs-text">VS</span>
            <div class="battle-sparks" v-if="isAnalyzing">
              <div class="spark" v-for="i in 6" :key="i"></div>
            </div>
          </div>
          <div class="energy-beam" :class="{ 'pulsing': isAnalyzing }"></div>
        </div>
        
        <!-- 实时战斗状态 -->
        <div class="battle-progress" v-if="isAnalyzing">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${battleProgress}%` }"></div>
          </div>
          <p class="battle-action">{{ currentBattleAction }}</p>
        </div>

        <!-- 战斗结果预览 -->
        <div class="battle-result-preview" v-if="battleWinner && !isAnalyzing">
          <div class="winner-badge">
            <v-icon color="#ffd700">mdi-crown</v-icon>
            <span>{{ battleWinner.name }} Wins!</span>
          </div>
          <div class="score-difference">
            +{{ Math.abs((userA.aiScore || 0) - (userB.aiScore || 0)).toFixed(1) }} points
          </div>
        </div>
      </div>

      <!-- 选手B战斗卡 -->
      <div class="fighter-card fighter-b" :class="fighterBClass">
        <div class="fighter-header">
          <div class="power-level">
            <div class="power-bar">
              <div 
                class="power-fill"
                :style="{ width: `${Math.min((userB.aiScore || 0), 100)}%` }"
              ></div>
            </div>
            <span class="power-text">{{ Math.round(userB.aiScore || 0) }}</span>
          </div>
          <div class="fighter-info">
            <h3 class="fighter-name">{{ userB.name }}</h3>
            <div class="fighter-stats">
              <span class="stat-item">
                <v-icon size="14">mdi-camera</v-icon>
                {{ userB.photos.length }} photos
              </span>
              <span class="stat-item" v-if="userB.aiScore !== null">
                <v-icon size="14" color="#ffd700">mdi-star</v-icon>
                {{ Math.round(userB.aiScore || 0) }}pts
              </span>
            </div>
          </div>
          <div class="fighter-portrait">
            <img v-if="userB.avatar" :src="userB.avatar" :alt="userB.name" />
            <div v-else class="avatar-placeholder">{{ userB.name[0] }}</div>
            <div class="fighter-status" :class="userB.battleStatus">
              <v-icon size="12">{{ getFighterStatusIcon(userB.battleStatus) }}</v-icon>
            </div>
          </div>
        </div>

        <!-- 弹性照片展示区 -->
        <div class="photos-arena" :class="`photos-${userB.photos.length}`">
          <div 
            v-for="(photo, index) in userB.photos" 
            :key="`b-${index}`"
            class="photo-battle-card"
            :class="{ 
              'highlight': photo.isHighlight,
              'analyzing': isAnalyzing && currentAnalyzingPhoto === `b-${index}`
            }"
            @click="openBattleGallery('B', index)"
          >
            <img :src="photo.url" :alt="`${userB.name} photo ${index + 1}`" />
            <div v-if="photo.isHighlight" class="highlight-crown">👑</div>
            <div v-if="isAnalyzing && currentAnalyzingPhoto === `b-${index}`" class="analyze-pulse">
              <v-icon color="white">mdi-brain</v-icon>
            </div>
          </div>
          
          <!-- 空位显示 -->
          <div 
            v-for="n in (maxPhotos - userB.photos.length)" 
            :key="`b-empty-${n}`"
            class="photo-empty-slot"
          >
            <v-icon size="32" color="rgba(255,255,255,0.3)">mdi-plus</v-icon>
            <span class="empty-text">Waiting...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- AI裁判系统 -->
    <AIBattleJudge
      v-if="aiComments.length > 0 || isAnalyzing"
      :user-a="userA"
      :user-b="userB"
      :comments="aiComments"
      :is-analyzing="isAnalyzing"
      :battle-winner="battleWinner"
      @analysis-complete="onAnalysisComplete"
      class="ai-judge-section"
    />

    <!-- 战斗历史记录 -->
    <div class="battle-history" v-if="battleHistory.length > 0">
      <h3>Previous Battles</h3>
      <div class="history-timeline">
        <div 
          v-for="battle in battleHistory" 
          :key="battle.id"
          class="history-item"
        >
          <div class="history-date">{{ formatBattleDate(battle.date) }}</div>
          <div class="history-result">
            <span class="winner">{{ battle.winner }}</span>
            <span class="score">{{ battle.scoreA }} - {{ battle.scoreB }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 照片战斗画廊模态框 -->
    <v-dialog v-model="battleGallery.show" max-width="1200px">
      <v-card class="battle-gallery-modal">
        <v-card-title class="gallery-header">
          <div class="gallery-title">
            <v-icon color="#ff6b6b">mdi-sword-cross</v-icon>
            <span>{{ battleGallery.fighter }} Battle Gallery</span>
          </div>
          <v-btn icon @click="battleGallery.show = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        
        <v-card-text class="gallery-content">
          <v-carousel
            v-if="battleGallery.photos.length"
            v-model="battleGallery.currentIndex"
            height="500"
            hide-delimiter-background
            show-arrows="hover"
            cycle
          >
            <v-carousel-item
              v-for="(photo, index) in battleGallery.photos"
              :key="index"
            >
              <div class="gallery-photo-container">
                <img 
                  :src="photo.url" 
                  :alt="`Battle photo ${index + 1}`"
                  class="gallery-photo"
                />
                <div v-if="photo.isHighlight" class="gallery-highlight-badge">
                  <v-icon color="yellow">mdi-crown</v-icon>
                  <span>Signature Dish</span>
                </div>
                <div class="photo-analysis-overlay" v-if="photo.aiAnalysis">
                  <div class="analysis-score">
                    <span class="score-value">{{ photo.aiAnalysis.score }}</span>
                    <span class="score-label">AI Score</span>
                  </div>
                  <div class="analysis-insights">
                    <p>{{ photo.aiAnalysis.reason }}</p>
                  </div>
                </div>
              </div>
            </v-carousel-item>
          </v-carousel>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import AIBattleJudge from './AIBattleJudge.vue'
import type { 
  BattlePhoto, 
  BattleUser, 
  BattleAIComment, 
  BattleHistoryItem,
  BattleGalleryState
} from '@/models/couplememory'

const props = withDefaults(
  defineProps<{
    userA: BattleUser
    userB: BattleUser
    aiComments?: BattleAIComment[]
    isAnalyzing?: boolean
    battleHistory?: BattleHistoryItem[]
  }>(),
  {
    aiComments: () => [],
    isAnalyzing: false,
    battleHistory: () => []
  }
)

// reactive state
const currentRound = ref(1)
const battleProgress = ref(0)
const currentBattleAction = ref('Analyzing dishes...')
const currentAnalyzingPhoto = ref<string | null>(null)
const battleGallery = ref<BattleGalleryState>({
  show: false,
  fighter: '',
  photos: [],
  currentIndex: 0
})

// computed
const maxPhotos = computed(() => Math.max(props.userA.photos.length, props.userB.photos.length, 4))

const battleLayoutClass = computed(() => {
  const totalPhotos = props.userA.photos.length + props.userB.photos.length
  if (totalPhotos <= 4) return 'layout-compact'
  if (totalPhotos <= 6) return 'layout-balanced'
  return 'layout-expanded'
})

const battleStatusText = computed(() => {
  if (props.isAnalyzing) return 'AI Battle Analysis in Progress...'
  if (battleWinner.value) return `Battle Complete - ${battleWinner.value.name} Wins!`
  return 'Battle Ready'
})

const battleWinner = computed(() => {
  if (!props.userA.aiScore || !props.userB.aiScore) return null
  return props.userA.aiScore > props.userB.aiScore ? props.userA : props.userB
})

const fighterAClass = computed(() => ({
  'is-winner': battleWinner.value?.name === props.userA.name,
  'is-defeated': battleWinner.value?.name === props.userB.name,
  'is-analyzing': props.isAnalyzing
}))

const fighterBClass = computed(() => ({
  'is-winner': battleWinner.value?.name === props.userB.name,
  'is-defeated': battleWinner.value?.name === props.userA.name,
  'is-analyzing': props.isAnalyzing
}))

// 方法
const getFighterStatusIcon = (status?: string) => {
  const iconMap = {
    ready: 'mdi-shield-check',
    fighting: 'mdi-sword',
    winner: 'mdi-crown',
    defeated: 'mdi-skull'
  }
  return iconMap[status as keyof typeof iconMap] || 'mdi-help'
}

const openBattleGallery = (fighter: 'A' | 'B', photoIndex: number) => {
  const user = fighter === 'A' ? props.userA : props.userB
  battleGallery.value = {
    show: true,
    fighter: `${user.name}'s`,
    photos: user.photos,
    currentIndex: photoIndex
  }
}

const formatBattleDate = (date: string) => {
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const onAnalysisComplete = (result: any) => {
  battleProgress.value = 100
  currentBattleAction.value = 'Battle Analysis Complete!'
}

// 模拟战斗分析进度
const simulateBattleProgress = () => {
  if (!props.isAnalyzing) return
  
  const actions = [
    'Scanning dish composition...',
    'Analyzing cooking technique...',
    'Evaluating presentation quality...',
    'Comparing ingredient usage...',
    'Calculating final scores...'
  ]
  
  let actionIndex = 0
  let progress = 0
  
  const interval = setInterval(() => {
    if (!props.isAnalyzing) {
      clearInterval(interval)
      return
    }
    
    progress += Math.random() * 15
    battleProgress.value = Math.min(progress, 95)
    
    if (progress > actionIndex * 20) {
      currentBattleAction.value = actions[actionIndex] || 'Finalizing analysis...'
      actionIndex++
    }
    
    // 模拟当前分析的照片
    const allPhotos = [
      ...props.userA.photos.map((_, i) => `a-${i}`),
      ...props.userB.photos.map((_, i) => `b-${i}`)
    ]
    
    if (allPhotos.length > 0) {
      currentAnalyzingPhoto.value = allPhotos[Math.floor(Math.random() * allPhotos.length)]
    }
  }, 800)
}

// 监听分析状态变化
watch(() => props.isAnalyzing, (newValue) => {
  if (newValue) {
    battleProgress.value = 0
    simulateBattleProgress()
  } else {
    battleProgress.value = 100
    currentAnalyzingPhoto.value = null
  }
})

onMounted(() => {
  if (props.isAnalyzing) {
    simulateBattleProgress()
  }
})
</script>

<style scoped>
.battle-arena-system {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 20px;
  padding: 24px;
  color: white;
  position: relative;
  overflow: hidden;
}

.battle-arena-system::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(255, 107, 107, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(78, 205, 196, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

/* 战斗状态栏 */
.battle-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.status-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-text {
  font-weight: bold;
  font-size: 1.1rem;
}

.battle-timer {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  transition: all 0.3s ease;
}

.battle-timer.analyzing {
  background: rgba(255, 215, 0, 0.2);
  animation: timerPulse 2s ease-in-out infinite;
}

.round-indicator {
  padding: 6px 12px;
  background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
  border-radius: 20px;
  font-weight: bold;
  font-size: 0.9rem;
}

/* 主竞技场 */
.main-arena {
  display: grid;
  gap: 20px;
  align-items: stretch;
  position: relative;
  z-index: 1;
}

.layout-compact {
  grid-template-columns: 1fr auto 1fr;
}

.layout-balanced {
  grid-template-columns: 1fr auto 1fr;
  gap: 16px;
}

.layout-expanded {
  grid-template-columns: 1fr auto 1fr;
  gap: 12px;
}

/* 选手卡片 */
.fighter-card {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(10px);
  border: 2px solid transparent;
  transition: all 0.4s ease;
  position: relative;
}

.fighter-card.is-winner {
  border-color: #ffd700;
  box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
  animation: winnerGlow 2s ease-in-out infinite;
}

.fighter-card.is-defeated {
  border-color: #666;
  opacity: 0.7;
}

.fighter-card.is-analyzing {
  border-color: #00ff88;
  animation: analyzingPulse 1.5s ease-in-out infinite;
}

.fighter-a {
  border-left: 4px solid #ff6b6b;
}

.fighter-b {
  border-right: 4px solid #4ecdc4;
}

/* 选手头部 */
.fighter-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.fighter-portrait {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  position: relative;
  border: 3px solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.fighter-portrait img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
}

.fighter-status {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
}

.fighter-status.ready { background: #4ecdc4; }
.fighter-status.fighting { background: #ff6b6b; animation: fightingPulse 1s infinite; }
.fighter-status.winner { background: #ffd700; }
.fighter-status.defeated { background: #666; }

.fighter-info {
  flex: 1;
}

.fighter-name {
  font-size: 1.2rem;
  font-weight: bold;
  margin: 0 0 8px 0;
}

.fighter-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
}

/* 力量条 */
.power-level {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.power-bar {
  width: 80px;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.power-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b, #ffd700, #4ecdc4);
  border-radius: 3px;
  transition: width 0.8s ease;
}

.power-text {
  font-size: 1.1rem;
  font-weight: bold;
  color: #ffd700;
}

/* 照片竞技场 */
.photos-arena {
  display: grid;
  gap: 8px;
  min-height: 200px;
}

.photos-1 { grid-template-columns: 1fr; }
.photos-2 { grid-template-columns: 1fr 1fr; }
.photos-3 { 
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
}
.photos-3 .photo-battle-card:first-child { grid-row: 1 / 3; }
.photos-4 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }

.photo-battle-card {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid transparent;
}

.photo-battle-card:hover {
  transform: scale(1.03);
  border-color: rgba(255, 255, 255, 0.3);
}

.photo-battle-card.highlight {
  border-color: #ffd700;
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
}

.photo-battle-card.analyzing {
  border-color: #00ff88;
  animation: photoAnalyzing 1s ease-in-out infinite;
}

.photo-battle-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.highlight-crown {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 1.2rem;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.analyze-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  background: rgba(0, 255, 136, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: analyzePulse 1s ease-in-out infinite;
}

.photo-empty-slot {
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
}

.empty-text {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

/* VS战斗核心 */
.vs-battle-core {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 120px;
  min-height: 300px;
  position: relative;
}

.energy-field {
  position: relative;
  width: 80px;
  height: 80px;
  margin-bottom: 20px;
}

.energy-field.active .energy-ring {
  animation: energyRing 2s ease-in-out infinite;
}

.energy-ring {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 3px solid transparent;
  border-radius: 50%;
  background: linear-gradient(45deg, #ff6b6b, #4ecdc4) border-box;
  mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
}

.vs-symbol {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1rem;
  z-index: 2;
}

.battle-sparks {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.spark {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #ffd700;
  border-radius: 50%;
  animation: sparkFly 1.5s ease-out infinite;
}

.spark:nth-child(1) { top: 10%; left: 50%; animation-delay: 0s; }
.spark:nth-child(2) { top: 30%; right: 15%; animation-delay: 0.3s; }
.spark:nth-child(3) { bottom: 30%; left: 15%; animation-delay: 0.6s; }
.spark:nth-child(4) { bottom: 10%; right: 50%; animation-delay: 0.9s; }
.spark:nth-child(5) { top: 50%; left: 10%; animation-delay: 1.2s; }
.spark:nth-child(6) { top: 50%; right: 10%; animation-delay: 1.5s; }

.energy-beam {
  position: absolute;
  top: 90px;
  bottom: 0;
  left: 50%;
  width: 4px;
  background: linear-gradient(to bottom, #ff6b6b, transparent, #4ecdc4);
  transform: translateX(-50%);
}

.energy-beam.pulsing {
  animation: beamPulse 1.5s ease-in-out infinite;
}

/* 战斗进度 */
.battle-progress {
  width: 100%;
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b, #ffd700, #4ecdc4);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.battle-action {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

/* 战斗结果预览 */
.battle-result-preview {
  text-align: center;
}

.winner-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
  margin-bottom: 8px;
  font-weight: bold;
  color: #ffd700;
}

.score-difference {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

/* AI裁判区域 */
.ai-judge-section {
  margin-top: 24px;
}

/* 战斗历史 */
.battle-history {
  margin-top: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.battle-history h3 {
  margin: 0 0 16px 0;
  color: rgba(255, 255, 255, 0.9);
}

.history-timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.history-date {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

.history-result .winner {
  font-weight: bold;
  color: #ffd700;
  margin-right: 8px;
}

.history-result .score {
  color: rgba(255, 255, 255, 0.8);
}

/* 照片画廊模态框 */
.battle-gallery-modal {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  color: white;
}

.gallery-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.gallery-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.gallery-photo-container {
  position: relative;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gallery-photo {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 12px;
}

.gallery-highlight-badge {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255, 215, 0, 0.9);
  color: #333;
  padding: 8px 16px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: bold;
}

.photo-analysis-overlay {
  position: absolute;
  bottom: 20px;
  left: 20px;
  right: 20px;
  background: rgba(0, 0, 0, 0.8);
  padding: 16px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.analysis-score {
  text-align: center;
  margin-bottom: 12px;
}

.score-value {
  display: block;
  font-size: 2rem;
  font-weight: bold;
  color: #ffd700;
}

.score-label {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

.analysis-insights p {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.9);
}

/* 动画定义 */
@keyframes timerPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@keyframes winnerGlow {
  0%, 100% { box-shadow: 0 0 30px rgba(255, 215, 0, 0.3); }
  50% { box-shadow: 0 0 50px rgba(255, 215, 0, 0.6); }
}

@keyframes analyzingPulse {
  0%, 100% { border-color: #00ff88; }
  50% { border-color: #4ecdc4; }
}

@keyframes fightingPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes photoAnalyzing {
  0%, 100% { border-color: #00ff88; box-shadow: 0 0 15px rgba(0, 255, 136, 0.3); }
  50% { border-color: #4ecdc4; box-shadow: 0 0 25px rgba(78, 205, 196, 0.5); }
}

@keyframes analyzePulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
  50% { transform: translate(-50%, -50%) scale(1.2); opacity: 1; }
}

@keyframes energyRing {
  0% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(180deg) scale(1.1); }
  100% { transform: rotate(360deg) scale(1); }
}

@keyframes sparkFly {
  0% { opacity: 1; transform: scale(1) translate(0, 0); }
  100% { opacity: 0; transform: scale(0.5) translate(var(--random-x, 20px), var(--random-y, -30px)); }
}

@keyframes beamPulse {
  0%, 100% { opacity: 0.6; filter: blur(2px); }
  50% { opacity: 1; filter: blur(0px); }
}

/* responsive layout */
@media (max-width: 968px) {
  .main-arena {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .vs-battle-core {
    order: 2;
    width: 100%;
    min-height: 100px;
    flex-direction: row;
    justify-content: center;
  }
  
  .energy-field {
    margin-bottom: 0;
    margin-right: 20px;
  }
  
  .energy-beam {
    top: 50%;
    bottom: auto;
    left: 90px;
    right: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(to right, #ff6b6b, transparent, #4ecdc4);
    transform: translateY(-50%);
  }
  
  .fighter-card {
    padding: 16px;
  }
  
  .photos-arena {
    min-height: 160px;
  }
}

@media (max-width: 600px) {
  .battle-arena-system {
    padding: 16px;
  }
  
  .battle-status-bar {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .fighter-header {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .photos-arena {
    min-height: 120px;
    gap: 6px;
  }
}
</style>

<template>
  <v-dialog 
    v-model="isVisible" 
    max-width="500" 
    persistent
    class="ai-judgment-modal"
  >
    <v-card class="judgment-card">
      <!-- waiting on scoring, with taste.gif rendered -->
      <div v-if="isLoading" class="loading-stage">
        <!-- 🍽️ 背景氛围 -->
        <div class="ambient-glow"></div>
        
        <!-- 🎮 菜品扫描区域 -->
        <div class="dish-scan-container">
          <!-- 用户highlight的菜品图片 -->
          <div class="dish-image-container" v-if="dishImageUrl && !dishImageError">
            <img 
              :src="dishImageUrl" 
              alt="Your highlighted dish" 
              class="dish-image"
              loading="eager"
              @error="onDishImageError"
            />
            <!-- 扫描效果覆盖层 -->
            <div class="scan-overlay">
              <div class="scan-line"></div>
            </div>
          </div>
          
          <!-- 图片加载失败或无图片时的占位符 -->
          <div class="dish-placeholder-container" v-else>
            <div class="dish-placeholder">
              <v-icon size="48" color="grey-lighten-1">mdi-silverware-fork-knife</v-icon>
              <p class="text-grey-lighten-1 mt-2 text-sm">
                {{ dishImageError ? 'Image temporarily unavailable' : 'Loading your delicious dish...' }}
              </p>
            </div>
            <div class="scan-overlay">
              <div class="scan-line"></div>
            </div>
          </div>
          
          <!-- Kinny 分析动画 -->
          <div class="kinny-analysis-container">
            <img 
              src="/assets/taste.gif" 
              alt="Kinny analyzing" 
              class="kinny-gif"
              loading="eager"
            />
            <!-- 装饰光效 -->
            <div class="sparkle-effects">
              <div class="sparkle sparkle-1">✨</div>
              <div class="sparkle sparkle-2">⭐</div>
              <div class="sparkle sparkle-3">💫</div>
              <div class="sparkle sparkle-4">🌟</div>
            </div>
          </div>
        </div>
        
        <!-- 动态分析进度 -->
        <div class="analysis-progress">
          <h3 class="analysis-title">🍳 Kinny is analyzing your masterpiece!</h3>
          
          <!-- 分析步骤列表 -->
          <div class="analysis-steps-list">
            <div 
              v-for="(step, index) in analysisSteps" 
              :key="index"
              class="analysis-step-item"
              :class="{
                'step-active': index === currentAnalysisStep,
                'step-completed': index < currentAnalysisStep,
                'step-pending': index > currentAnalysisStep
              }"
            >
              <div class="step-icon">{{ step.icon }}</div>
              <div class="step-text">{{ step.text }}</div>
              <div class="step-status">
                <div v-if="index < currentAnalysisStep" class="status-completed">✅</div>
                <div v-else-if="index === currentAnalysisStep" class="status-loading">
                  <div class="loading-spinner"></div>
                </div>
                <div v-else class="status-pending">⏳</div>
              </div>
            </div>
          </div>
          
          <!-- 当前分析提示 -->
          <div class="current-analysis-hint" v-if="currentAnalysisStep < analysisSteps.length">
            <p class="hint-text">
              {{ currentAnalysisStep === analysisSteps.length - 1 ? 
                  '🎯 Almost done! Kinny is finalizing the judgment...' : 
                  '🔄 Analysis in progress... Please wait.' 
              }}
            </p>
            <p class="patience-hint" v-if="isLongWait">
              ✨ Kinny is being extra thorough - your dish must be exceptional!
            </p>
          </div>
        </div>
      </div>

      <!-- AI评分结果阶段 -->
      <div v-else-if="judgment && judgment.overall_score > 0" class="result-stage">
        <!-- 🎮 Kinny taste.gif 在结果顶部 -->
        <div class="result-taste-animation">
          <img 
            src="/assets/taste.gif" 
            alt="Kinny finished analyzing" 
            class="result-taste-gif"
            loading="eager"
            @error="onImageError"
          />
          <!-- 备用显示，如果gif加载失败 -->
          <div class="taste-fallback" v-if="imageError">🍽️✨</div>
        </div>
        
        <!-- 头部标题 -->
        <div class="result-header">
          <div class="score-badge">
            <span class="score-number">{{ judgment.overall_score }}</span>
            <span class="score-label">pts</span>
          </div>
          <h3 class="judgment-title">🏆 Kinny's Verdict</h3>
        </div>

        <!-- 评分详情 -->
        <div class="score-details">
          <div class="score-item">
            <div class="score-item-top">
              <span class="score-icon">👁️</span>
              <span class="score-name">Visual Appeal</span>
              <span class="score-value">{{ judgment.visual_appeal }}</span>
            </div>
            <div class="score-bar">
              <div class="score-fill" :style="{ width: `${judgment.visual_appeal}%` }"></div>
            </div>
          </div>
          
          <div class="score-item">
            <div class="score-item-top">
              <span class="score-icon">🔥</span>
              <span class="score-name">Cooking Technique</span>
              <span class="score-value">{{ judgment.cooking_technique }}</span>
            </div>
            <div class="score-bar">
              <div class="score-fill" :style="{ width: `${judgment.cooking_technique}%` }"></div>
            </div>
          </div>
          
          <div class="score-item">
            <div class="score-item-top">
              <span class="score-icon">🥬</span>
              <span class="score-name">Ingredient Freshness</span>
              <span class="score-value">{{ judgment.ingredient_freshness }}</span>
            </div>
            <div class="score-bar">
              <div class="score-fill" :style="{ width: `${judgment.ingredient_freshness}%` }"></div>
            </div>
          </div>
        </div>

        <!-- AI评论 -->
        <div class="ai-comment">
          <div class="comment-bubble">
            <p class="comment-text">{{ effectiveComment }}</p>
          </div>
          <div class="kinny-avatar">🤖💕</div>
        </div>

        <!-- 信心度指示器 -->
        <div class="confidence-indicator">
          <div class="confidence-indicator-top">
            <span class="confidence-label">Kinny's Confidence:</span>
            <span class="confidence-value">{{ Math.round((judgment.confidence || 0.8) * 100) }}%</span>
          </div>
          <div class="confidence-bar">
            <div class="confidence-fill" :style="{ width: `${(judgment.confidence || 0.8) * 100}%` }"></div>
          </div>
        </div>
      </div>

      <!-- 错误状态 - 只有真正的服务器错误才显示 -->
      <div v-else-if="error && !isAIAnalysisPending" class="error-stage">
        <!-- 系统离线特殊处理 -->
        <div v-if="isSystemOffline" class="system-offline-container">
          <div class="offline-icon">🔌❌</div>
          <h3 class="offline-title">System Temporarily Offline</h3>
          <p class="offline-message">{{ error }}</p>
          
          <div class="offline-actions">
            <p class="offline-hint">Please report this issue to our team:</p>
            <v-btn 
              color="#5865F2" 
              variant="elevated"
              @click="reportToDiscord"
              class="discord-btn"
              prepend-icon="mdi-discord"
            >
              🔧 Report on Discord
            </v-btn>
            <p class="offline-note">We'll get this fixed ASAP!</p>
          </div>
        </div>
        
        <!-- 普通错误状态 -->
        <div v-else class="general-error-container">
          <div class="error-icon">😵</div>
          <h3 class="error-title">Kinny encountered an issue...</h3>
          <p class="error-message">{{ error }}</p>
          
          <!-- 🔄 重试按钮 -->
          <v-btn 
            color="primary" 
            variant="outlined"
            @click="retryAIJudgment"
            class="retry-btn"
            :disabled="isLoading"
          >
            🔄 Try Again
          </v-btn>
        </div>
      </div>

      <!-- AI分析进行中 - 当没有结果但也不是真正的错误时 -->
      <div v-else-if="!judgment || judgment.overall_score <= 0" class="loading-stage">
        <!-- 🍽️ 背景氛围 -->
        <div class="ambient-glow"></div>
        
        <!-- 🎮 Kinny吃东西gif动画 - 精准渲染 -->
        <div class="taste-animation-container">
          <img 
            src="/assets/taste.gif" 
            alt="Kinny is analyzing your dish" 
            class="taste-gif"
            loading="eager"
          />
          
          <!-- 装饰光效 -->
          <div class="sparkle-effects">
            <div class="sparkle sparkle-1">✨</div>
            <div class="sparkle sparkle-2">⭐</div>
            <div class="sparkle sparkle-3">💫</div>
            <div class="sparkle sparkle-4">🌟</div>
          </div>
        </div>
        
        <!-- 文字内容 -->
        <div class="loading-content">
          <h3 class="loading-title">🍳 Kinny is analyzing your masterpiece!</h3>
          
          <div class="loading-dots">
            <span>.</span><span>.</span><span>.</span>
          </div>
          <p class="loading-text">This usually takes 30-60 seconds...</p>
          
          <!-- 简化的等待提示 -->
          <div class="simple-hint">
            <p class="hint-text">🤖 Kinny is working hard behind the scenes</p>
            <p class="hint-text">You can close this modal and check back later!</p>
            <p class="hint-text" v-if="isLongWait">Taking longer than usual? Kinny is being extra thorough! ✨</p>
          </div>
          
        </div>
      </div>

      <!-- action button: shows the action that fits the current state -->
      <v-card-actions class="action-buttons">
        <!-- 🎯 加载状态：提供离开选项但保持简洁 -->
        <template v-if="isLoading || isAIAnalysisPending">
          <v-btn 
            color="secondary"
            variant="outlined"
            @click="goToBattleHistory"
            class="nav-btn secondary-action"
          >
            <v-icon left>⚔️</v-icon>
            Battle History
          </v-btn>
          
          <v-btn 
            color="primary"
            variant="outlined"
            @click="goToHome"
            class="nav-btn primary-action"
          >
            <v-icon left>🏠</v-icon>
            Back to Kitchen
          </v-btn>
        </template>
        
        <!-- 🏆 结果状态：完整的导航选项 -->
        <template v-else-if="judgment && judgment.overall_score > 0">
          <v-btn 
            color="primary" 
            variant="elevated"
            @click="goToHome"
            class="nav-btn primary-action"
          >
            <v-icon left>🏠</v-icon>
            Back to Kitchen
          </v-btn>
          
          <v-btn 
            color="secondary" 
            variant="outlined"
            @click="goToBattleHistory"
            class="nav-btn secondary-action"
          >
            <v-icon left>⚔️</v-icon>
            View Battle History
          </v-btn>
        </template>
        
        <!-- 🚨 错误状态：重试和导航选项 -->
        <template v-else-if="error && !isAIAnalysisPending">
          <v-btn 
            color="primary" 
            variant="outlined"
            @click="retryAIJudgment"
            class="retry-btn primary-action"
            :disabled="isLoading"
          >
            🔄 Try Again
          </v-btn>
          
          <v-btn 
            color="secondary" 
            variant="outlined"
            @click="goToHome"
            class="nav-btn secondary-action"
          >
            <v-icon left>🏠</v-icon>
            Back to Kitchen
          </v-btn>
        </template>
        
        <!-- 🎮 默认状态：基础导航 -->
        <template v-else>
          <v-btn 
            color="secondary" 
            variant="outlined"
            @click="goToHome"
            class="nav-btn secondary-action"
          >
            <v-icon left>🏠</v-icon>
            Back to Kitchen
          </v-btn>
        </template>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/plugins/axios'
import { soundManager, GameSounds } from '@/utils/soundManager'

/* ──────────── Props & Emits ──────────── */
interface Props {
  modelValue: boolean
  entryId?: number | null
  highlightedImageUrl?: string | null // 🎯 新增：显示用户highlight的菜品图片
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

/* ──────────── Router ──────────── */
const router = useRouter()

/* ──────────── reactive state ──────────── */
const isLoading = ref(false)
const judgment = ref<any>(null)
const error = ref<string | null>(null)
const imageError = ref(false)
const dishImageError = ref(false) // 🎯 菜品图片加载错误状态
const isLongWait = ref(false)
const longWaitTimer = ref<NodeJS.Timeout | null>(null)
const isAIAnalysisPending = ref(false) // 🎯 跟踪AI分析状态

// 🎵 分析过程音效状态
const biteAudioRef = ref<HTMLAudioElement | null>(null)
const isBitePlaying = ref(false)

// 🎯 Entry数据获取 - 用于显示菜品图片
const entryData = ref<any>(null)
const isLoadingEntry = ref(false)

// 🎮 动态分析进度状态
const currentAnalysisStep = ref(0)
const analysisSteps = ref([
  { icon: '📸', text: 'Scanning your dish...', status: 'pending' },
  { icon: '🔍', text: 'Examining visual presentation', status: 'pending' },
  { icon: '🎨', text: 'Evaluating color harmony', status: 'pending' },
  { icon: '🔥', text: 'Assessing cooking techniques', status: 'pending' },
  { icon: '🥬', text: 'Analyzing ingredient quality', status: 'pending' },
  { icon: '🤖', text: 'Finalizing AI judgment...', status: 'pending' }
])
const stepTimer = ref<NodeJS.Timeout | null>(null)

// 🚫 防止无效API调用
const isComponentActive = ref(true)
const pollingController = ref<AbortController | null>(null)

/* ──────────── computed ──────────── */
const isVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const effectiveComment = computed(() => {
  if (!judgment.value) return ''
  return judgment.value.individual_comment || judgment.value.ai_comment || 'This dish looks amazing!'
})

// 🔌 检测系统离线状态
const isSystemOffline = computed(() => {
  return error.value && (
    error.value.includes('System offline') ||
    error.value.includes('Image preprocessing failed') ||
    error.value.includes('http://localhost:911') ||
    judgment.value?.ai_summary === 'System offline' ||
    judgment.value?.individual_summary === 'System offline'
  )
})

const ORIGIN = import.meta.env.VITE_API_BASE_URL?.replace('/api', '') || location.origin
const fix = (u?: string) => {
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

// 🎯 精准获取菜品图片URL - 优先从entry数据获取
const dishImageUrl = computed(() => {
  // prefer the highlightedImageUrl that was passed in, the preview
  if (props.highlightedImageUrl) {
    return props.highlightedImageUrl
  }

  // entrybest_media_url, the full path after the POST
  if (entryData.value?.best_media_url) {
    return fix(entryData.value.best_media_url)
  }
  
  return null
})

/* ──────────── Entry数据获取 ──────────── */
const fetchEntryData = async () => {
  if (!props.entryId || isLoadingEntry.value) return
  
  isLoadingEntry.value = true
  try {
    console.log('🎯 Fetching entry data for ID:', props.entryId)
    const response = await api.get(`/couplememory/entries/${props.entryId}/`)
    entryData.value = response.data
    console.log('✅ Entry data loaded:', entryData.value)
  } catch (err) {
    console.error('❌ Failed to fetch entry data:', err)
    entryData.value = null
  } finally {
    isLoadingEntry.value = false
  }
}

/* ──────────── AI判断获取 ──────────── */
const fetchAIJudgment = async () => {
  if (!props.entryId) {
    console.warn('🚨 No entryId provided to AIJudgmentModal')
    error.value = 'Invalid entry ID. Please try again.'
    return
  }
  
  if (!isComponentActive.value) {
    console.log('🚫 Component inactive, aborting AI judgment fetch')
    return
  }
  
  console.log('🎯 Starting AI judgment fetch for entry:', props.entryId)
  console.log('🔄 Ensuring fresh AI judgment - no cached results')
  
  isLoading.value = true
  isAIAnalysisPending.value = true
  currentAnalysisStep.value = 0
  
  // � 启动分析步骤动画
  startAnalysisStepAnimation()
  
  // 45秒后显示长时间等待提示
  longWaitTimer.value = setTimeout(() => {
    if (isLoading.value && isComponentActive.value) {
      isLongWait.value = true
      console.log('⏰ Long wait detected, showing patience hints')
    }
  }, 45000)
  
  error.value = null
  judgment.value = null
  
  try {
    // 🎯 先触发AI分析，确保后台开始处理
    console.log('🚀 Triggering backend AI analysis...')
    try {
      if (pollingController.value) {
        pollingController.value.abort()
      }
      pollingController.value = new AbortController()
      
      // await api.post(`/couplememory/entries/${props.entryId}/trigger_ai_scoring/`, {}, {
      //   signal: pollingController.value.signal
      // })
      // console.log('✅ AI analysis triggered successfully')
    } catch (triggerError: any) {
      if (triggerError.name === 'AbortError') {
        console.log('🚫 AI trigger aborted')
        return
      }
      console.warn('⚠️ AI trigger failed (may already be processing):', triggerError)
      // 继续等待，可能已经在处理中
    }
    
    // 🔄 持续轮询直到获得结果
    const maxAttempts = 30
    let attempts = 0
    
    while (attempts < maxAttempts && isComponentActive.value) {
      try {
        // 检查组件是否仍然活跃
        if (!isComponentActive.value) {
          console.log('🚫 Component became inactive, stopping polling')
          break
        }
        
        // 精准API调用 - 确保正确的端点格式
        console.log(`🔄 Attempt ${attempts + 1}/${maxAttempts} - Fetching AI judgment for entry ${props.entryId}`)
        
        if (pollingController.value) {
          pollingController.value.abort()
        }
        pollingController.value = new AbortController()
        
        // 🎯 加入时间戳避免缓存旧的AI判断结果
        const timestamp = Date.now()
        const response = await api.get(`/couplememory/entries/${props.entryId}/ai_judgment/?t=${timestamp}`, {
          signal: pollingController.value.signal
        })
        
        console.log('📦 API Response:', response.data)
        
        if (response.data && response.data.overall_score !== null && response.data.overall_score !== undefined) {
          console.log('✅ AI judgment received successfully:', response.data)
          judgment.value = response.data
          // 🎉 完成所有分析步骤
          currentAnalysisStep.value = analysisSteps.value.length
          break
        }
        
        // 🎯 提供更详细的等待反馈
        const waitTime = attempts * 2
        console.log(`⏳ AI judgment not ready yet (${waitTime.toFixed(1)}s elapsed), retrying...`)
        
        // 🎮 动态调整等待时间
        const waitInterval = attempts < 10 ? 2000 : attempts < 20 ? 3000 : 4000
        await new Promise(resolve => setTimeout(resolve, waitInterval))
        attempts++
      } catch (err: any) {
        if (err.name === 'AbortError') {
          console.log('🚫 API call aborted')
          return
        }
        
        console.warn(`❌ API Error (attempt ${attempts + 1}):`, err.response?.data || err.message)
        
        // 🎯 a 404 means Kinny is still analysing, not that something failed
        if (err.response?.status === 404) {
          if (attempts < maxAttempts - 1 && isComponentActive.value) {
            // AI判断还未生成，继续等待，这不是错误
            console.log('🔄 404 error - Kinny still analyzing, continuing to wait...')
            isAIAnalysisPending.value = true
            await new Promise(resolve => setTimeout(resolve, 2000))
            attempts++
            continue
          } else {
            // 超时但仍然是分析中，不是真正的错误
            console.log('⏰ Maximum attempts reached but Kinny is still analyzing')
            isAIAnalysisPending.value = true
            // 不抛出错误，保持等待状态
            break
          }
        }
        
        // "MemoryEntry has no ai_judgment" 错误也说明还在分析中
        if (err.response?.data?.detail?.includes('has no ai_judgment') || 
            err.message?.includes('has no ai_judgment')) {
          if (attempts < maxAttempts - 1 && isComponentActive.value) {
            console.log('🔄 No ai_judgment yet - Kinny still analyzing, continuing to wait...')
            isAIAnalysisPending.value = true
            await new Promise(resolve => setTimeout(resolve, 2000))
            attempts++
            continue
          } else {
            console.log('⏰ Still no ai_judgment - Kinny needs more time')
            isAIAnalysisPending.value = true
            break
          }
        }
        
        // 其他HTTP错误才是真正的错误
        if (err.response?.status >= 400) {
          isAIAnalysisPending.value = false
          throw err
        }
        
        throw err
      }
    }
    
    // 🎉 成功获得结果时清理状态
    if (judgment.value && isComponentActive.value) {
      console.log('✅ Kinny analysis completed successfully')
      isAIAnalysisPending.value = false
      clearLongWaitState()
      stopAnalysisStepAnimation()
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      console.log('🚫 Fetch aborted')
      return
    }
    
    console.error('💥 Failed to fetch AI judgment:', err)
    
    // 🎯 精准错误判断 - AI分析相关的"错误"实际上是分析进行中
    if (err.response?.status === 404 || 
        err.response?.data?.detail?.includes('has no ai_judgment') || 
        err.message?.includes('has no ai_judgment')) {
      console.log('⏰ Kinny is still analyzing - keeping analysis pending state')
      isAIAnalysisPending.value = true
      // 不设置error，继续显示分析中状态
      return
    }
    
    // 精准错误处理 - 避免显示原始API错误和技术细节
    let errorMessage = 'Kinny encountered an unexpected issue. Please try again later.'
    
    if (err.response?.status === 400) {
      errorMessage = 'Invalid request. Please try submitting your dish again.'
    } else if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please log in again.'
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server is having issues. Please try again in a few minutes.'
    } else if (err.message && err.message.length < 100 && !err.message.includes('400') && !err.message.includes('error code')) {
      // 只显示简洁清晰的错误消息，过滤掉技术错误码
      errorMessage = err.message
    }
    
    isAIAnalysisPending.value = false
    error.value = errorMessage
    stopAnalysisStepAnimation()
  } finally {
    if (isComponentActive.value) {
      isLoading.value = false
    }
  }
}

/* ──────────── 分析步骤动画控制 ──────────── */
const startAnalysisStepAnimation = () => {
  console.log('🎮 Starting analysis step animation')
  currentAnalysisStep.value = 0
  
  // 清理之前的计时器
  if (stepTimer.value) {
    clearInterval(stepTimer.value)
  }
  
  // 🎵 开始播放bite.mp3循环音效
  startBiteLoop()
  
  // 每3秒推进一个步骤
  stepTimer.value = setInterval(() => {
    if (!isComponentActive.value) {
      stopAnalysisStepAnimation()
      return
    }
    
    if (currentAnalysisStep.value < analysisSteps.value.length - 1) {
      currentAnalysisStep.value++
      console.log(`🔄 Analysis step ${currentAnalysisStep.value}: ${analysisSteps.value[currentAnalysisStep.value]?.text}`)
    } else {
      // 最后一步 - 等待AI结果
      console.log('⏳ Reached final step, waiting for AI judgment...')
    }
  }, 3000)
}

const stopAnalysisStepAnimation = () => {
  console.log('🛑 Stopping analysis step animation')
  if (stepTimer.value) {
    clearInterval(stepTimer.value)
    stepTimer.value = null
  }
  
  // 🎵 停止bite音效循环
  stopBiteLoop()
}

/* ──────────── Bite音效循环控制 ──────────── */
const startBiteLoop = () => {
  try {
    console.log('🎵 Starting bite.mp3 loop during AI analysis')
    
    // 🎯 mobile tuning：使用更低的音量和更短的淡入时间
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
    const volumeConfig = isMobile ? 0.3 : 0.4
    const fadeInTime = isMobile ? 200 : 300
    
    // 使用soundManager播放循环音效
    soundManager.playSound(GameSounds.BITE, { 
      volume: volumeConfig, 
      loop: true,
      fadeIn: fadeInTime 
    })
    
    isBitePlaying.value = true
  } catch (error) {
    console.warn('🔇 Failed to start bite audio loop:', error)
  }
}

const stopBiteLoop = () => {
  try {
    console.log('🎵 Stopping bite.mp3 loop')
    
    // 停止bite音效
    soundManager.stopSound(GameSounds.BITE)
    
    isBitePlaying.value = false
  } catch (error) {
    console.warn('🔇 Failed to stop bite audio loop:', error)
  }
}

/* ──────────── 清理长时间等待状态 ──────────── */
const clearLongWaitState = () => {
  if (longWaitTimer.value) {
    clearTimeout(longWaitTimer.value)
    longWaitTimer.value = null
  }
  isLongWait.value = false
  stopAnalysisStepAnimation()
}

/* ──────────── 导航功能 ──────────── */
const goToHome = () => {
  closeModal()
  router.push('/')
}

const goToBattleHistory = () => {
  closeModal()
  router.push('/battle_history')
}

const closeModal = () => {
  console.log('🚪 Closing AI judgment modal')
  isComponentActive.value = false
  
  // 🚫 停止所有正在进行的操作
  if (pollingController.value) {
    pollingController.value.abort()
    pollingController.value = null
  }
  
  stopAnalysisStepAnimation()
  clearLongWaitState()
  
  isVisible.value = false
  // 延迟重置状态，避免闪烁
  setTimeout(() => {
    resetModalState()
    isComponentActive.value = true // 重新激活，准备下次使用
    console.log('✅ AI judgment modal state reset completed')
  }, 300)
}

/* ──────────── 重试AI判断 ──────────── */
const retryAIJudgment = () => {
  console.log('🔄 Retrying AI judgment for entry:', props.entryId)
  if (props.entryId) {
    resetModalState()
    fetchAIJudgment()
  }
}

/* ──────────── 图片错误处理 ──────────── */
const onImageError = () => {
  console.warn('🖼️ taste.gif failed to load')
  imageError.value = true
}

const onDishImageError = () => {
  console.warn('🍽️ Dish image failed to load, URL:', dishImageUrl.value)
  dishImageError.value = true
}

/* ──────────── Discord报告功能 ──────────── */
const reportToDiscord = () => {
  console.log('🔧 Opening Discord to report system offline issue')
  window.open('https://discord.gg/PgnxX24T', '_blank')
}

/* ──────────── 监听器 ──────────── */
watch(() => props.modelValue, async (newValue) => {
  if (newValue && props.entryId) {
    console.log('🎯 AI Judgment Modal opened for entry:', props.entryId)
    // 🚀 每次打开都完全重置状态，确保全新体验
    isComponentActive.value = true
    resetModalState()
    // 🎯 fetch the entry first, then its AI judgment
    await fetchEntryData()
    fetchAIJudgment()
  } else if (!newValue) {
    // 🚫 Modal关闭时确保清理
    isComponentActive.value = false
    if (pollingController.value) {
      pollingController.value.abort()
      pollingController.value = null
    }
    stopAnalysisStepAnimation()
  }
})

// 当entryId改变时，也要重新获取判断
watch(() => props.entryId, async (newEntryId, oldEntryId) => {
  if (newEntryId && newEntryId !== oldEntryId && props.modelValue) {
    console.log('🔄 Entry ID changed, fetching new AI judgment:', { old: oldEntryId, new: newEntryId })
    isComponentActive.value = true
    resetModalState()
    // 🎯 fetch the entry first, then its AI judgment
    await fetchEntryData()
    fetchAIJudgment()
  }
})

// 🎯 当图片URL变化时，重置错误状态
watch(() => dishImageUrl.value, () => {
  dishImageError.value = false
})

/* ──────────── 状态重置函数 ──────────── */
function resetModalState() {
  console.log('🧹 Resetting AI judgment modal state for fresh experience')
  isLoading.value = false
  judgment.value = null
  error.value = null
  imageError.value = false
  dishImageError.value = false // 🎯 重置菜品图片错误状态
  isAIAnalysisPending.value = false
  currentAnalysisStep.value = 0
  
  // 🎯 重置entry数据
  entryData.value = null
  isLoadingEntry.value = false
  
  // 重置分析步骤状态
  analysisSteps.value.forEach(step => {
    step.status = 'pending'
  })
  
  clearLongWaitState()
  
  // 停止API调用
  if (pollingController.value) {
    pollingController.value.abort()
    pollingController.value = null
  }
}
</script>

<style scoped>
.ai-judgment-modal {
  z-index: 9999;
}

.judgment-card {
  background: linear-gradient(145deg, #1e293b, #334155);
  border: 2px solid #fbbf24;
  border-radius: 20px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.6),
    0 0 30px rgba(251, 191, 36, 0.3);
  overflow: hidden;
}

/* ──────────── 加载阶段 ──────────── */
.loading-stage {
  padding: 2rem 1.5rem;
  text-align: center;
  background: linear-gradient(135deg, #1e293b, #334155);
  position: relative;
}

/* 🎮 菜品扫描区域 */
.dish-scan-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.dish-image-container {
  position: relative;
  flex: 1;
  max-width: 200px;
}

.dish-image {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 12px;
  border: 2px solid #fbbf24;
  box-shadow: 0 8px 25px rgba(251, 191, 36, 0.3);
}

.scan-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 12px;
  overflow: hidden;
  pointer-events: none;
}

.scan-line {
  position: absolute;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, transparent, #00ff41, transparent);
  animation: scanMove 2s linear infinite;
  box-shadow: 0 0 10px #00ff41;
}

@keyframes scanMove {
  0% { top: 0; opacity: 1; }
  50% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

.dish-placeholder-container {
  position: relative;
  flex: 1;
  max-width: 200px;
}

.dish-placeholder {
  width: 100%;
  height: 150px;
  border: 2px dashed #9ca3af;
  border-radius: 12px;
  background: rgba(156, 163, 175, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.debug-text {
  font-size: 0.6rem !important;
  color: #6b7280 !important;
  opacity: 0.7;
  font-family: monospace;
  max-width: 180px;
  word-break: break-all;
  text-align: center;
  margin-top: 0.25rem !important;
}

.kinny-analysis-container {
  position: relative;
  flex: 1;
  max-width: 120px;
}

.kinny-gif {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  box-shadow: 
    0 10px 30px rgba(251, 191, 36, 0.4),
    0 0 50px rgba(251, 191, 36, 0.2);
  animation: tastePulse 3s ease-in-out infinite;
  object-fit: cover;
}

/* ──────────── 动态分析进度 ──────────── */
.analysis-progress {
  margin-top: 1.5rem;
}

.analysis-title {
  color: #fbbf24;
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.analysis-steps-list {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.analysis-step-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.analysis-step-item:last-child {
  margin-bottom: 0;
}

.step-active {
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.4);
  animation: stepPulse 1.5s ease-in-out infinite;
}

.step-completed {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.step-pending {
  background: rgba(71, 85, 105, 0.3);
  opacity: 0.6;
}

@keyframes stepPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

.step-icon {
  font-size: 1.2rem;
  min-width: 24px;
  text-align: center;
}

.step-text {
  flex: 1;
  color: #cbd5e1;
  font-size: 0.9rem;
  font-weight: 500;
}

.step-active .step-text {
  color: #3b82f6;
  font-weight: 600;
}

.step-completed .step-text {
  color: #10b981;
}

.step-status {
  min-width: 24px;
  text-align: center;
}

.status-completed {
  color: #10b981;
  font-size: 1rem;
}

.status-loading {
  display: flex;
  justify-content: center;
  align-items: center;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(59, 130, 246, 0.3);
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.status-pending {
  color: #94a3b8;
  font-size: 0.9rem;
}

.current-analysis-hint {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
}

.hint-text {
  color: #3b82f6;
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.patience-hint {
  color: #10b981;
  font-size: 0.85rem;
  font-weight: 500;
  margin: 0;
  font-style: italic;
}

@keyframes tastePulse {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 
      0 10px 30px rgba(251, 191, 36, 0.4),
      0 0 50px rgba(251, 191, 36, 0.2);
  }
  50% { 
    transform: scale(1.05);
    box-shadow: 
      0 15px 40px rgba(251, 191, 36, 0.6),
      0 0 70px rgba(251, 191, 36, 0.4);
  }
}

/* 装饰光效 */
.sparkle-effects {
  position: absolute;
  width: 200px;
  height: 200px;
  pointer-events: none;
}

.sparkle {
  position: absolute;
  font-size: 1.2rem;
  animation: sparkleFloat 4s ease-in-out infinite;
}

.sparkle-1 {
  top: 10%;
  left: 20%;
  animation-delay: 0s;
}

.sparkle-2 {
  top: 20%;
  right: 10%;
  animation-delay: 1s;
}

.sparkle-3 {
  bottom: 20%;
  left: 10%;
  animation-delay: 2s;
}

.sparkle-4 {
  bottom: 10%;
  right: 20%;
  animation-delay: 3s;
}

@keyframes sparkleFloat {
  0%, 100% {
    opacity: 0.4;
    transform: translateY(0px) scale(0.8);
  }
  50% {
    opacity: 1;
    transform: translateY(-10px) scale(1.2);
  }
}

/* 背景氛围光晕 */
.ambient-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(
    circle at center,
    rgba(251, 191, 36, 0.1) 0%,
    rgba(251, 191, 36, 0.05) 40%,
    transparent 70%
  );
  animation: ambientPulse 6s ease-in-out infinite;
  pointer-events: none;
}

@keyframes ambientPulse {
  0%, 100% {
    opacity: 0.6;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
  }
}

.ai-avatar {
  margin-bottom: 1.5rem;
}

.kinny-thinking {
  font-size: 4rem;
  animation: thinking 2s ease-in-out infinite;
}

@keyframes thinking {
  0%, 100% { transform: scale(1) rotate(0deg); }
  25% { transform: scale(1.1) rotate(-5deg); }
  75% { transform: scale(1.1) rotate(5deg); }
}

.loading-title {
  color: #fbbf24;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.loading-dots {
  font-size: 2rem;
  color: #fbbf24;
  margin-bottom: 1rem;
}

.loading-dots span {
  animation: dot-bounce 1.4s ease-in-out infinite both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.loading-text {
  color: #cbd5e1;
  font-size: 1rem;
  opacity: 0.9;
  margin-bottom: 1rem;
}

/* ──────────── 沉浸式等待提示 ──────────── */
.immersive-hint {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(16, 185, 129, 0.1));
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 16px;
  text-align: center;
  backdrop-filter: blur(10px);
}

.primary-hint {
  color: #3b82f6;
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.secondary-hint {
  color: #94a3b8;
  font-size: 0.9rem;
  margin: 0 0 1rem 0;
  opacity: 0.9;
}

.patience-hint {
  color: #10b981;
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0 0 1.5rem 0;
  padding: 0.5rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.waiting-options {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(30, 41, 59, 0.3);
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.option-text {
  color: #cbd5e1;
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  opacity: 0.9;
}

.analysis-steps {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.analysis-step {
  color: #94a3b8;
  font-size: 0.8rem;
  margin: 0;
  padding: 0.25rem 0;
  opacity: 0.8;
  animation: stepGlow 3s ease-in-out infinite;
}

.analysis-step:nth-child(1) { animation-delay: 0s; }
.analysis-step:nth-child(2) { animation-delay: 0.5s; }
.analysis-step:nth-child(3) { animation-delay: 1s; }
.analysis-step:nth-child(4) { animation-delay: 1.5s; }

@keyframes stepGlow {
  0%, 100% { opacity: 0.6; }
  50% { 
    opacity: 1; 
    color: #3b82f6;
    text-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
  }
}

.return-hint {
  color: #94a3b8;
  font-size: 0.75rem;
  margin: 0;
  opacity: 0.8;
  font-style: italic;
}

/* ──────────── 结果阶段 ──────────── */
.result-stage {
  padding: 2rem;
}

/* 🎮 结果阶段的taste.gif */
.result-taste-animation {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
  /* 调试用 - 确保容器可见 */
  min-height: 120px;
  align-items: center;
}

.result-taste-gif {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  box-shadow: 
    0 8px 25px rgba(251, 191, 36, 0.3),
    0 0 40px rgba(251, 191, 36, 0.15);
  animation: resultTastePulse 4s ease-in-out infinite;
  object-fit: cover;
}

.taste-fallback {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  box-shadow: 
    0 8px 25px rgba(251, 191, 36, 0.3),
    0 0 40px rgba(251, 191, 36, 0.15);
  animation: resultTastePulse 4s ease-in-out infinite;
}

@keyframes resultTastePulse {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 
      0 8px 25px rgba(251, 191, 36, 0.3),
      0 0 40px rgba(251, 191, 36, 0.15);
  }
  50% { 
    transform: scale(1.03);
    box-shadow: 
      0 10px 30px rgba(251, 191, 36, 0.4),
      0 0 50px rgba(251, 191, 36, 0.2);
  }
}

.result-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  text-align: left;
}

.score-badge {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border-radius: 50%;
  width: 80px;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(251, 191, 36, 0.4);
}

.score-number {
  font-size: 2rem;
  font-weight: 900;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.score-label {
  font-size: 0.8rem;
  color: white;
  font-weight: 600;
}

.judgment-title {
  color: #f1f5f9;
  font-size: 1.5rem;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

/* ──────────── 评分详情 ──────────── */
.score-details {
  margin-bottom: 2rem;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: rgba(51, 65, 85, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  margin-bottom: 0.75rem;
  transition: all 0.3s ease;
}

.score-item:hover {
  background: rgba(51, 65, 85, 0.8);
  border-color: rgba(251, 191, 36, 0.5);
}

.score-item-top {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.score-icon {
  font-size: 1.2rem;
  width: 24px;
  text-align: center;
}

.score-name {
  color: #cbd5e1;
  font-weight: 600;
  min-width: 120px;
  flex: 1;
}

.score-bar {
  flex: 2;
  height: 8px;
  background: rgba(71, 85, 105, 0.8);
  border-radius: 4px;
  overflow: hidden;
  margin: 0 1rem;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, 
    #f59e0b 0%, 
    #fbbf24 25%, 
    #facc15 50%, 
    #16a34a 75%, 
    #10b981 100%
  );
  border-radius: 4px;
  transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.score-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.4), 
    transparent
  );
  animation: scoreShimmer 2s ease-in-out;
}

@keyframes scoreShimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

.score-value {
  color: #10b981;
  font-weight: 700;
  min-width: 30px;
  text-align: right;
}

/* ──────────── AI评论 ──────────── */
.ai-comment {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 2rem;
}

.comment-bubble {
  flex: 1;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  padding: 1.25rem;
  border-radius: 20px 20px 20px 5px;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.comment-text {
  margin: 0;
  font-size: 1rem;
  line-height: 1.6;
  font-weight: 500;
}

.kinny-avatar {
  font-size: 2rem;
  margin-top: 0.5rem;
}

/* ──────────── 信心度 ──────────── */
.confidence-indicator {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(30, 41, 59, 0.8);
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  margin-bottom: 1rem;
  transition: all 0.3s ease;
}

.confidence-indicator:hover {
  background: rgba(30, 41, 59, 1);
  border-color: rgba(139, 92, 246, 0.5);
}

.confidence-indicator-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
}

.confidence-label {
  color: #94a3b8;
  font-size: 0.9rem;
  font-weight: 600;
  min-width: 120px;
}

.confidence-bar {
  flex: 2;
  height: 6px;
  background: rgba(71, 85, 105, 0.8);
  border-radius: 3px;
  overflow: hidden;
  margin: 0 1rem;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6, #7c3aed);
  border-radius: 3px;
  transition: width 1s ease-out;
}

.confidence-value {
  color: #8b5cf6;
  font-weight: 700;
  min-width: 40px;
  text-align: right;
}

/* ──────────── 错误阶段 ──────────── */
.error-stage {
  padding: 3rem 2rem;
  text-align: center;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.error-title {
  color: #ef4444;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.error-message {
  color: #cbd5e1;
  font-size: 1rem;
}

/* ──────────── 操作按钮 ──────────── */
.action-buttons {
  padding: 1.5rem 2rem;
  gap: 1rem;
  background: rgba(15, 23, 42, 0.8);
  border-top: 1px solid rgba(148, 163, 184, 0.2);
}

.nav-btn {
  font-weight: 600;
  text-transform: none;
  border-radius: 12px;
  padding: 0.5rem 1.5rem;
}

.close-btn {
  color: #94a3b8;
  font-weight: 500;
}

/* ──────────── 响应式 ──────────── */
@media (max-width: 600px) {
  .judgment-card {
    margin: 0.5rem;
    border-radius: 12px;
    max-width: calc(100vw - 1rem);
  }
  
  .loading-stage {
    padding: 1.5rem 1rem;
  }
  
  /* 移动端菜品扫描区域tuning */
  .dish-scan-container {
    flex-direction: column;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }
  
  .dish-image-container {
    max-width: 100%;
    width: 100%;
  }
  
  .dish-image {
    height: 120px;
  }
  
  .kinny-analysis-container {
    max-width: 80px;
  }
  
  .kinny-gif {
    width: 80px;
    height: 80px;
  }
  
  /* 移动端分析进度tuning */
  .analysis-title {
    font-size: 1.1rem;
    margin-bottom: 1rem;
  }
  
  .analysis-steps-list {
    padding: 1rem;
    margin-bottom: 1rem;
  }
  
  .analysis-step-item {
    gap: 0.75rem;
    padding: 0.5rem;
    margin-bottom: 0.4rem;
  }
  
  .step-icon {
    font-size: 1rem;
    min-width: 20px;
  }
  
  .step-text {
    font-size: 0.8rem;
  }
  
  .current-analysis-hint {
    padding: 0.75rem;
  }
  
  .hint-text {
    font-size: 0.8rem;
  }
  
  .patience-hint {
    font-size: 0.75rem;
  }
  
  .sparkle-effects {
    width: 140px;
    height: 140px;
  }
  
  .sparkle {
    font-size: 0.9rem;
  }
  
  .loading-title {
    font-size: 1.2rem;
    margin-bottom: 0.75rem;
    line-height: 1.4;
  }
  
  .loading-text {
    font-size: 0.9rem;
    margin-bottom: 0.75rem;
  }
  
  .simple-hint {
    margin-top: 1rem;
    padding: 0.75rem;
  }
  
  .hint-text {
    font-size: 0.75rem;
  }
  
  /* 移动端沉浸式提示tuning */
  .immersive-hint {
    margin-top: 1rem;
    padding: 1rem;
  }
  
  .primary-hint {
    font-size: 1rem;
  }
  
  .secondary-hint {
    font-size: 0.8rem;
  }
  
  .waiting-options {
    margin-top: 1rem;
    padding: 0.75rem;
  }
  
  .analysis-steps {
    gap: 0.4rem;
  }
  
  .analysis-step {
    font-size: 0.75rem;
  }
  
  .result-stage {
    padding: 1rem;
  }
  
  /* 移动端结果taste.giftuning */
  .result-taste-gif,
  .taste-fallback {
    width: 80px;
    height: 80px;
  }
  
  .result-header {
    flex-direction: column;
    text-align: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }
  
  .score-badge {
    width: 60px;
    height: 60px;
  }
  
  .score-number {
    font-size: 1.5rem;
  }
  
  .score-label {
    font-size: 0.7rem;
  }
  
  .judgment-title {
    font-size: 1.2rem;
  }
  
  .score-item {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
    padding: 0.75rem;
  }
  
  .score-item-top {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .score-name {
    min-width: auto;
    flex: 1;
    font-size: 0.9rem;
  }
  
  .score-value {
    min-width: 25px;
    font-size: 0.9rem;
  }
  
  .score-bar {
    width: 100%;
    margin-top: 0.25rem;
  }
  
  .ai-comment {
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }
  
  .comment-bubble {
    padding: 1rem;
    font-size: 0.9rem;
    border-radius: 16px 16px 16px 4px;
  }
  
  .kinny-avatar {
    font-size: 1.5rem;
    text-align: center;
  }
  
  .confidence-indicator {
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem;
    margin-bottom: 1rem;
  }
  
  .confidence-indicator-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }
  
  .confidence-label {
    min-width: auto;
    font-size: 0.8rem;
  }
  
  .confidence-value {
    min-width: 30px;
    font-size: 0.8rem;
  }
  
  .confidence-bar {
    width: 100%;
    margin-top: 0.25rem;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
  }
  
  .nav-btn {
    width: 100%;
    font-size: 0.9rem;
    padding: 0.75rem 1rem;
  }
  
  .close-btn {
    font-size: 0.9rem;
  }
  
  .error-stage {
    padding: 2rem 1rem;
  }
  
  .error-title {
    font-size: 1.2rem;
  }
  
  .error-message {
    font-size: 0.9rem;
  }
}

/* ──────────── 超小屏幕tuning ──────────── */
@media (max-width: 400px) {
  .judgment-card {
    margin: 0.25rem;
    border-radius: 8px;
  }
  
  .loading-stage {
    padding: 1rem 0.75rem;
  }
  
  /* 超小屏幕菜品扫描tuning */
  .dish-scan-container {
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  .dish-image {
    height: 100px;
  }
  
  .kinny-analysis-container {
    max-width: 60px;
  }
  
  .kinny-gif {
    width: 60px;
    height: 60px;
  }
  
  /* 超小屏幕分析进度tuning */
  .analysis-title {
    font-size: 1rem;
    margin-bottom: 0.75rem;
  }
  
  .analysis-steps-list {
    padding: 0.75rem;
    margin-bottom: 0.75rem;
  }
  
  .analysis-step-item {
    gap: 0.5rem;
    padding: 0.4rem;
    margin-bottom: 0.3rem;
  }
  
  .step-icon {
    font-size: 0.9rem;
    min-width: 18px;
  }
  
  .step-text {
    font-size: 0.75rem;
  }
  
  .current-analysis-hint {
    padding: 0.5rem;
  }
  
  .hint-text {
    font-size: 0.75rem;
  }
  
  .patience-hint {
    font-size: 0.7rem;
  }
  
  .sparkle-effects {
    width: 120px;
    height: 120px;
  }
  
  .loading-title {
    font-size: 1rem;
    margin-bottom: 0.5rem;
  }
  
  .loading-text {
    font-size: 0.8rem;
  }
  
  .simple-hint {
    margin-top: 0.75rem;
    padding: 0.5rem;
  }
  
  .hint-text {
    font-size: 0.7rem;
  }
  
  /* 超小屏幕沉浸式提示tuning */
  .immersive-hint {
    margin-top: 0.75rem;
    padding: 0.75rem;
  }
  
  .primary-hint {
    font-size: 0.9rem;
  }
  
  .secondary-hint {
    font-size: 0.75rem;
  }
  
  .waiting-options {
    margin-top: 0.75rem;
    padding: 0.5rem;
  }
  
  .option-text {
    font-size: 0.7rem;
  }
  
  .analysis-step {
    font-size: 0.7rem;
  }
  
  .return-hint {
    font-size: 0.65rem;
  }
  
  .result-stage {
    padding: 0.75rem;
  }
  
  /* 超小屏幕结果taste.giftuning */
  .result-taste-gif,
  .taste-fallback {
    width: 60px;
    height: 60px;
  }
  
  .taste-fallback {
    font-size: 1.5rem;
  }
  
  .score-badge {
    width: 50px;
    height: 50px;
  }
  
  .score-number {
    font-size: 1.2rem;
  }
  
  .judgment-title {
    font-size: 1rem;
  }
  
  .score-item {
    padding: 0.5rem;
  }
  
  .score-name {
    font-size: 0.8rem;
  }
  
  .score-value {
    font-size: 0.8rem;
  }
  
  .comment-bubble {
    padding: 0.75rem;
    font-size: 0.8rem;
  }
  
  .action-buttons {
    padding: 0.75rem;
  }
  
  .nav-btn {
    font-size: 0.8rem;
    padding: 0.5rem 0.75rem;
  }
}
</style>

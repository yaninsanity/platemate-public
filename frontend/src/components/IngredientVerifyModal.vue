<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-backdrop" @click.self="onCancel">
      <div class="game-modal">
        <!-- Quest Header -->
        <div class="quest-header">
          <h2 class="quest-title">🍽️ INGREDIENT QUEST</h2>
          <div class="target-ingredient">
            <span class="target-label">Target:</span>
            <span class="ingredient-name">{{ task.ingredient.name }}</span>
          </div>
          <button class="close-btn" @click="onCancel">×</button>
        </div>

        <!-- Camera Hunt Mode -->
        <div v-if="status === 'idle'" class="hunt-mode">
          <div class="reference-showcase">
            <div class="ref-frame">
              <img 
                :src="resolvedIngredientImage" 
                alt="target" 
                class="target-image"
              />
              <div class="target-overlay">
                <span class="target-icon">🎯</span>
              </div>
            </div>
            <p class="hunt-instruction">Find and capture this ingredient!</p>
          </div>

          <div class="camera-hunt-area" @click="trigger">
            <div class="camera-reticle">
              <div class="reticle-corner reticle-tl"></div>
              <div class="reticle-corner reticle-tr"></div>
              <div class="reticle-corner reticle-bl"></div>
              <div class="reticle-corner reticle-br"></div>
              <div class="camera-center">
                <div class="camera-icon">📸</div>
                <div class="hunt-text">TAP TO HUNT</div>
              </div>
            </div>
            <input
              ref="fileIn"
              type="file"
              accept="image/*"
              capture="environment"
              style="display: none"
              @change="onFile"
            />
          </div>
        </div>

        <!-- Photo Preview Mode -->
        <div v-else-if="status === 'preview'" class="preview-mode">
          <div class="captured-frame">
            <img v-if="preview" :src="preview" alt="captured" class="captured-image" />
            <div class="capture-overlay">
              <span class="capture-badge">📷 CAPTURED!</span>
            </div>
          </div>
          
          <div class="preview-actions">
            <button class="action-btn secondary" @click="reset">
              🔄 Retake
            </button>
            <button 
              class="action-btn primary" 
              :disabled="busy" 
              @click="submit"
            >
              {{ busy ? '🔍 Scanning...' : '🚀 Analyze' }}
            </button>
          </div>
        </div>

        <!-- AI Analysis Mode -->
        <!-- Kinny's Thinking Mode -->
        <div v-else-if="status === 'analyzing'" class="analysis-mode">
          <AIDetectionLoader />
          <div class="dev-warning">
            ⚠️ Developer Mode: Kinny's Training Simulation Active
          </div>
        </div>        <!-- Success Mode -->
        <div v-else-if="status === 'success'" class="success-mode">
          <div class="success-celebration">
            <div class="trophy">🏆</div>
            <h3 class="success-title">INGREDIENT VERIFIED!</h3>
            
            <!-- Kinny's Magical Response (Primary) -->
            <div v-if="kinnyMessage" class="kinny-message-box success">
              <div class="kinny-avatar">🐱</div>
              <div class="kinny-bubble">
                <p class="kinny-text">{{ kinnyMessage }}</p>
                <div class="kinny-badge">✨ Kinny Magic</div>
              </div>
            </div>
            
            <!-- Sweet Backup Message (Only if Kinny is quiet) -->
            <p v-else class="success-message">Amazing! You found the {{ task.ingredient.name }}!</p>
            
            <div class="success-stats">
              <div class="stat">
                <span class="stat-icon">🎯</span>
                <span class="stat-label">Accuracy: {{ Math.round((aiConfidence || 0.95) * 100) }}%</span>
              </div>
              <div class="stat">
                <span class="stat-icon">⚡</span>
                <span class="stat-label">Kinny Powered</span>
              </div>
            </div>

            <!-- Smooth Transition Magic -->
            <div class="transition-hint">
              <div class="countdown-ring">
                <div class="countdown-text">{{ autoCloseCountdown }}</div>
              </div>
              <p class="auto-close-text">Auto-continuing in {{ autoCloseCountdown }}s...</p>
            </div>
          </div>
          <div class="success-actions">
            <button class="action-btn secondary" @click="pauseAutoClose">
              ⏸️ Wait
            </button>
            <button class="action-btn victory" @click="confirm">
              🎉 CONTINUE NOW
            </button>
          </div>
        </div>

        <!-- Fail Mode -->
        <div v-else-if="status === 'failed'" class="fail-mode">
          <div class="fail-feedback">
            <div class="fail-icon">😔</div>
            <h3 class="fail-title">INGREDIENT NOT DETECTED</h3>
            
            <!-- Kinny's AI-Generated Fail Message (Primary) -->
            <div v-if="kinnyMessage" class="kinny-message-box fail">
              <div class="kinny-avatar">🐱</div>
              <div class="kinny-bubble">
                <p class="kinny-text">{{ kinnyMessage }}</p>
                <div class="kinny-badge fail">✨ Kinny's Advice</div>
              </div>
            </div>
            
            <!-- Technical Error Message (Only if no Kinny message) -->
            <p v-else class="fail-message">{{ errMsg }}</p>
            
            <!-- 简洁的照片对比 -->
            <div class="simple-photo-compare">
              <div class="compare-item">
                <img 
                  :src="resolvedIngredientImage" 
                  alt="target" 
                  class="compare-photo target"
                />
                <div class="photo-tag target">🎯 Target</div>
              </div>
              <div class="vs-divider">VS</div>
              <div class="compare-item">
                <img v-if="preview" :src="preview" alt="your photo" class="compare-photo yours" />
                <div v-else class="compare-photo-empty">📷</div>
                <div class="photo-tag yours">📸 Yours</div>
              </div>
            </div>

            <!-- Kinny的快速建议 -->
            <div class="kinny-quick-tips">
              <div class="tips-header">
                <span class="kinny-mini">🐱</span>
                <span class="tips-text">Kinny's Quick Tips</span>
              </div>
              <div class="tips-row">
                <div class="tip-bubble" @click="highlightTip('lighting')">
                  ☀️ Better Light
                </div>
                <div class="tip-bubble" @click="highlightTip('distance')">
                  🔍 Get Closer
                </div>
                <div class="tip-bubble" @click="highlightTip('angle')">
                  📐 Good Angle
                </div>
              </div>
            </div>
          </div>
          
          <div class="fail-actions">
            <button class="action-btn secondary" @click="onCancel">
              🚪 Give Up
            </button>
            <button class="action-btn retry" @click="reset">
              🎯 Try Again
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import api from '@/plugins/axios'
import { useAIStore } from '@/stores/aiStore'
import type { Task } from '@/models/task'
import AIDetectionLoader from './AIDetectionLoader.vue'
import defaultIngredient from '@/assets/default-ingredient.png'
import { resolveURL } from '@/utils/resolveURL'
import { useTaskStore } from '@/stores/taskStore'

const props = defineProps<{ visible: boolean; task: Task }>()
const emit  = defineEmits<{ cancel: []; confirm: []; success: []}>()
const taskStore = useTaskStore()

const fileIn   = ref<HTMLInputElement>()
const photo    = ref<File | null>(null)
const preview  = ref<string | null>(null)
const status   = ref<'idle'|'preview'|'analyzing'|'success'|'failed'>('idle')
const busy     = ref(false)
const errMsg   = ref('')
const kinnyMessage = ref('')
const aiConfidence = ref(0.95)
const autoCloseCountdown = ref(0)
const autoCloseTimer = ref<NodeJS.Timeout | null>(null)
const autoClosePaused = ref(false)

const resolvedIngredientImage = computed(() => normalizeIngredientImage(props.task.ingredient.default_picture))

function normalizeIngredientImage(raw?: string | null): string {
  if (!raw) return defaultIngredient
  if (/^https?:\/\//i.test(raw) || raw.startsWith('//') || raw.startsWith('/media/') || raw.startsWith('media/')) {
    return resolveURL(raw) ?? defaultIngredient
  }
  return raw
}

// 🎵 Kinny's Magical Sound System
const successAudio = ref<HTMLAudioElement | null>(null)
const failAudio = ref<HTMLAudioElement | null>(null)

// Initialize Kinny's Adorable Sound Effects
function initAudio() {
  try {
    successAudio.value = new Audio('/assets/sounds/verify-success.wav')
    failAudio.value = new Audio('/assets/sounds/verify-fail.wav')
    
    // Preload sound effects
    successAudio.value.preload = 'auto'
    failAudio.value.preload = 'auto'
    
    console.log('🎵 Kinny\'s Sound System Ready to Rock!')
  } catch (error) {
    console.log('🔇 Audio not available in this environment')
  }
}

// 🎉 Kinny celebration success sound effect
function playKinnySuccess() {
  try {
    if (successAudio.value) {
      successAudio.value.currentTime = 0
      successAudio.value.play().catch(e => console.warn('🔇 Kinny celebration sound failed:', e))
    }
  } catch (error) {
    console.warn('🔇 Kinny celebration sound error:', error)
  }
}

// 😿 Kinny encouragement retry sound effect
function playKinnyEncouragement() {
  try {
    if (failAudio.value) {
      failAudio.value.currentTime = 0
      failAudio.value.play().catch(e => console.warn('🔇 Kinny encouragement sound failed:', e))
    }
  } catch (error) {
    console.warn('🔇 Kinny encouragement sound error:', error)
  }
}

function reset() {
  photo.value = null; preview.value = null
  status.value = 'idle'; errMsg.value = ''
  kinnyMessage.value = ''
  aiConfidence.value = 0.95
  autoCloseCountdown.value = 0
  autoClosePaused.value = false
  if (autoCloseTimer.value) {
    clearInterval(autoCloseTimer.value)
    autoCloseTimer.value = null
  }
  if (fileIn.value) fileIn.value.value = ''
}

function pauseAutoClose() {
  autoClosePaused.value = true
  if (autoCloseTimer.value) {
    clearInterval(autoCloseTimer.value)
    autoCloseTimer.value = null
  }
  emit('success')
}

function startAutoClose() {
  if (autoClosePaused.value) return
  
  autoCloseCountdown.value = 3 // 3秒倒计时
  autoCloseTimer.value = setInterval(() => {
    autoCloseCountdown.value--
    if (autoCloseCountdown.value <= 0) {
      if (autoCloseTimer.value) {
        clearInterval(autoCloseTimer.value)
        autoCloseTimer.value = null
      }
      confirm()
    }
  }, 1000)
}

function trigger() { fileIn.value?.click() }

function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) {
    photo.value = f
    preview.value = URL.createObjectURL(f)
    status.value = 'preview'
  }
}

const ai = useAIStore()

async function submit() {
  if (!photo.value) return
  busy.value = true
  status.value = 'analyzing'

  try {
    const form = new FormData()
    form.append('task', String(props.task.id))
    form.append('image', photo.value)

    // Call the AI detection endpoint
    const { data } = await api.post(
      '/recipes/ingredient-photo-proofs/',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )

    // Handle AI detection result
    console.log('🤖 AI Detection Response:', data)
    
    // 提取Kinny的消息和置信度
    kinnyMessage.value = data.message || ''
    aiConfidence.value = data.confidence || 0.95
    
    // 严格验证AI检测结果
    if (!data.match || data.match === false) {
      const detectedList = Array.isArray(data.detected) ? data.detected.join(', ') : 'nothing'
      // 如果有Kinny消息就不显示默认错误消息
      if (!kinnyMessage.value) {
        errMsg.value = data.error || 
          `❌ Kinny couldn't detect "${props.task.ingredient.name}". Found: ${detectedList}. Please try again with a clearer photo.`
      }
      status.value = 'failed'
      
      // Play failure sound effect
      playKinnyEncouragement()
    } else {
      // Only exact matches count as success
      console.log('🎉 Kinny Detection Success - ingredient verified:', data.detected)
      status.value = 'success'
      
      // Play success sound effect
      playKinnySuccess()
      
      // Start smooth auto-close countdown
      setTimeout(() => {
        if (status.value === 'success' && !autoClosePaused.value) {
          startAutoClose()
        }
      }, 800) // 0.8s delay before countdown starts, let user see success message first
    }
  } catch (err: any) {
    console.error('❌ Kinny Detection API Error:', err)
    errMsg.value = err.response?.data?.error
                || err.response?.data?.detail
                || err.message
                || 'Kinny detection service temporarily unavailable. Please try again.'
    status.value = 'failed'
    
    // 🐱 Kinny给出鼓励
    playKinnyEncouragement()
  } finally {
    busy.value = false
  }
}

function confirm() { emit('confirm'); reset() }
function onCancel() { 
  if (status.value === 'success') emit('success')
  else emit('cancel')
  reset()
}

function scrollToTop() {
  // 滚动到模态框顶部，给用户视觉反馈
  const modal = document.querySelector('.game-modal')
  if (modal) {
    modal.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function highlightTip(tipType: string) {
  // 游戏化反馈 - 高亮提示并提供振动反馈
  const cards = document.querySelectorAll('.power-up-card')
  cards.forEach(card => card.classList.remove('highlighted'))
  
  const targetCard = document.querySelector(`.power-up-card.${tipType}`)
  if (targetCard) {
    targetCard.classList.add('highlighted')
    
    // 轻微震动效果（如果支持）
    if (navigator.vibrate) {
      navigator.vibrate(50)
    }
    
    // 移除高亮
    setTimeout(() => {
      targetCard.classList.remove('highlighted')
    }, 1500)
  }
  
  console.log(`🎮 Power-up tip selected: ${tipType}`)
}

watch(() => props.visible, v => {
  if (v) {
    reset()
    initAudio() // Initialize sound effects
  }
})
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: backdropFadeIn 0.3s ease;
}

@keyframes backdropFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.game-modal {
  background: linear-gradient(145deg, #1a1a2e, #16213e);
  border-radius: 20px;
  width: 90vw;
  max-width: 420px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 
    0 25px 50px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  animation: modalSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalSlideIn {
  from { 
    opacity: 0; 
    transform: translateY(30px) scale(0.9); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0) scale(1); 
  }
}

/* Quest Header */
.quest-header {
  position: relative;
  background: linear-gradient(135deg, #667eea, #764ba2);
  padding: 20px;
  border-radius: 20px 20px 0 0;
  text-align: center;
}

.quest-title {
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
  margin: 0 0 10px 0;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.target-ingredient {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
}

.target-label {
  color: rgba(255,255,255,0.8);
  font-size: 0.9rem;
}

.ingredient-name {
  color: #ffd700;
  font-weight: bold;
  font-size: 1.1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: rgba(255,255,255,0.1);
  border: none;
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255,255,255,0.2);
  transform: scale(1.1);
}

/* Hunt Mode */
.hunt-mode {
  padding: 24px;
}

.reference-showcase {
  text-align: center;
  margin-bottom: 24px;
}

.ref-frame {
  position: relative;
  display: inline-block;
  margin-bottom: 12px;
}

.target-image {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  object-fit: cover;
  border: 3px solid #ffd700;
  box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
}

.target-overlay {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #ff6b6b;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.hunt-instruction {
  color: #a0a0a0;
  font-size: 0.9rem;
  margin: 0;
}

.camera-hunt-area {
  position: relative;
  cursor: pointer;
  transition: transform 0.2s;
}

.camera-hunt-area:hover {
  transform: scale(1.02);
}

.camera-reticle {
  position: relative;
  width: 200px;
  height: 200px;
  margin: 0 auto;
  border: 2px dashed #4ecdc4;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(78, 205, 196, 0.1), rgba(102, 126, 234, 0.1));
  animation: reticlePulse 2s infinite;
}

@keyframes reticlePulse {
  0%, 100% { border-color: #4ecdc4; }
  50% { border-color: #67e6dc; }
}

.reticle-corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 3px solid #ffd700;
}

.reticle-tl { top: -3px; left: -3px; border-right: none; border-bottom: none; }
.reticle-tr { top: -3px; right: -3px; border-left: none; border-bottom: none; }
.reticle-bl { bottom: -3px; left: -3px; border-right: none; border-top: none; }
.reticle-br { bottom: -3px; right: -3px; border-left: none; border-top: none; }

.camera-center {
  text-align: center;
}

.camera-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 8px;
  animation: cameraFloat 2s ease-in-out infinite;
}

@keyframes cameraFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.hunt-text {
  color: #4ecdc4;
  font-weight: bold;
  font-size: 0.9rem;
  letter-spacing: 1px;
}

/* Preview Mode */
.preview-mode {
  padding: 24px;
}

.captured-frame {
  position: relative;
  margin-bottom: 20px;
}

.captured-image {
  width: 100%;
  max-height: 250px;
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}

.capture-overlay {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(76, 175, 80, 0.9);
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: bold;
}

.preview-actions {
  display: flex;
  gap: 12px;
}

/* Success Mode */
.success-mode {
  padding: 24px;
  text-align: center;
}

.success-celebration {
  margin-bottom: 24px;
}

.trophy {
  font-size: 4rem;
  margin-bottom: 16px;
  animation: trophyBounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes trophyBounce {
  0% { transform: scale(0) rotate(-180deg); }
  50% { transform: scale(1.2) rotate(-10deg); }
  100% { transform: scale(1) rotate(0deg); }
}

.success-title {
  color: #4caf50;
  font-size: 1.3rem;
  font-weight: bold;
  margin: 0 0 8px 0;
}

.success-message {
  color: #a0a0a0;
  margin: 16px 0;
  padding: 12px;
  background: rgba(78, 205, 196, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(78, 205, 196, 0.2);
  text-align: center;
  font-size: 0.9rem;
  line-height: 1.4;
}

.success-stats {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(76, 175, 80, 0.1);
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.stat-icon {
  font-size: 1.2rem;
}

.stat-label {
  color: #4caf50;
  font-size: 0.8rem;
  font-weight: bold;
}

/* Fail Mode */
.fail-mode {
  padding: 24px;
  text-align: center;
}

.fail-feedback {
  margin-bottom: 24px;
}

.fail-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  animation: failShake 0.5s ease-in-out;
}

@keyframes failShake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.fail-title {
  color: #f44336;
  font-size: 1.2rem;
  font-weight: bold;
  margin: 0 0 8px 0;
}

.fail-message {
  color: #a0a0a0;
  margin: 16px 0;
  padding: 12px;
  background: rgba(255, 107, 107, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(255, 107, 107, 0.2);
  text-align: center;
  font-size: 0.85rem;
  line-height: 1.4;
  max-height: 100px;
  overflow-y: auto;
}

/* ============ 简洁照片对比 ============ */
.simple-photo-compare {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin: 20px 0;
  padding: 16px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(78, 205, 196, 0.2);
}

.compare-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.compare-photo {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  object-fit: cover;
  transition: transform 0.2s ease;
}

.compare-photo:hover {
  transform: scale(1.05);
}

.compare-photo.target {
  border: 2px solid #ffd700;
  box-shadow: 0 0 12px rgba(255, 215, 0, 0.4);
}

.compare-photo.yours {
  border: 2px solid #ff6b6b;
  box-shadow: 0 0 12px rgba(255, 107, 107, 0.4);
}

.compare-photo-empty {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  border: 2px dashed #64748b;
  background: rgba(100, 116, 139, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: #64748b;
}

.photo-tag {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: center;
}

.photo-tag.target {
  color: #ffd700;
}

.photo-tag.yours {
  color: #ff6b6b;
}

.vs-divider {
  font-size: 1.2rem;
  font-weight: bold;
  color: #a855f7;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #a855f7;
  animation: vsPulse 2s ease-in-out infinite;
}

@keyframes vsPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* ============ Kinny快速建议 ============ */
.kinny-quick-tips {
  margin: 16px 0;
  padding: 16px;
  background: rgba(78, 205, 196, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(78, 205, 196, 0.2);
}

.tips-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
}

.kinny-mini {
  font-size: 1.5rem;
  animation: kinnyWiggle 2s ease-in-out infinite;
}

@keyframes kinnyWiggle {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-5deg); }
  75% { transform: rotate(5deg); }
}

.tips-text {
  color: #4ecdc4;
  font-size: 0.9rem;
  font-weight: bold;
}

.tips-row {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.tip-bubble {
  padding: 8px 16px;
  background: rgba(51, 65, 85, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 20px;
  color: #e2e8f0;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.tip-bubble:hover {
  transform: translateY(-2px);
  border-color: rgba(78, 205, 196, 0.5);
  background: rgba(78, 205, 196, 0.2);
  color: #4ecdc4;
}

.tip-bubble.highlighted {
  border-color: #ffd700;
  background: rgba(255, 215, 0, 0.2);
  color: #ffd700;
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.3);
  animation: tipBounce 0.5s ease-out;
}

@keyframes tipBounce {
  0% { transform: scale(1); }
  50% { transform: scale(1.1) translateY(-4px); }
  100% { transform: scale(1); }
}

/* 响应式tuning */
@media (max-width: 480px) {
  .simple-photo-compare {
    gap: 12px;
    padding: 12px;
  }
  
  .compare-photo, .compare-photo-empty {
    width: 60px;
    height: 60px;
  }
  
  .tips-row {
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
}

/* ============ 失败时的图片回顾区域 ============ */
.simple-photo-compare {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin: 20px 0;
  padding: 16px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.photo-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.photo-frame {
  width: 80px;
  height: 80px;
  border-radius: 10px;
  overflow: hidden;
  border: 2px solid #64748b;
}

.photo-frame.target {
  border-color: #ffd700;
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}

.photo-frame.yours {
  border-color: #ff6b6b;
  box-shadow: 0 0 8px rgba(255, 107, 107, 0.3);
}

.photo-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-label {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
}

.vs-divider {
  font-size: 1.2rem;
  color: #a855f7;
  font-weight: bold;
  background: rgba(168, 85, 247, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

/* Kinny快速提示 */
.kinny-quick-tips {
  margin: 16px 0;
  padding: 12px;
  background: rgba(78, 205, 196, 0.1);
  border-radius: 10px;
  border: 1px solid rgba(78, 205, 196, 0.2);
}

.tips-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
}

.kinny-mascot {
  font-size: 1.5rem;
  animation: kinnyWink 4s ease-in-out infinite;
}

@keyframes kinnyWink {
  0%, 95%, 100% { transform: scale(1); }
  97% { transform: scale(1.1); }
}

.tips-title {
  color: #4ecdc4;
  font-size: 0.9rem;
  font-weight: bold;
  margin: 0;
}

.tips-bubbles {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.tip-bubble {
  background: rgba(51, 65, 85, 0.7);
  color: #e2e8f0;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tip-bubble:hover {
  background: rgba(78, 205, 196, 0.2);
  border-color: rgba(78, 205, 196, 0.4);
  transform: translateY(-1px);
}

.tip-bubble.highlighted {
  background: rgba(255, 215, 0, 0.2);
  border-color: #ffd700;
  color: #ffd700;
  animation: bubbleGlow 0.8s ease-out;
}

@keyframes bubbleGlow {
  0% { box-shadow: none; }
  50% { box-shadow: 0 0 12px rgba(255, 215, 0, 0.4); }
  100% { box-shadow: none; }
}

.tip-emoji {
  font-size: 1rem;
}

/* 响应式 */
@media (max-width: 480px) {
  .simple-photo-compare {
    gap: 12px;
    padding: 12px;
  }
  
  .photo-frame {
    width: 60px;
    height: 60px;
  }
  
  .tips-bubbles {
    flex-direction: column;
    align-items: center;
  }
  
  .tip-bubble {
    min-width: 120px;
    justify-content: center;
  }
}

/* Action Buttons */
.action-btn {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 10px;
  font-weight: bold;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn.primary {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  color: white;
  box-shadow: 0 4px 15px rgba(78, 205, 196, 0.3);
}

.action-btn.primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(78, 205, 196, 0.4);
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #a0a0a0;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.action-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.action-btn.victory {
  background: linear-gradient(135deg, #ffd700, #ffb300);
  color: #333;
  box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
  animation: victoryPulse 2s infinite;
}

@keyframes victoryPulse {
  0%, 100% { box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3); }
  50% { box-shadow: 0 6px 25px rgba(255, 215, 0, 0.5); }
}

.action-btn.retry {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: white;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
}

/* Kinny Message Styles */
.kinny-message-box {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin: 16px 0;
  padding: 16px;
  border-radius: 16px;
  animation: kinnyAppear 0.6s ease-out;
}

.kinny-message-box.success {
  background: linear-gradient(135deg, rgba(78, 205, 196, 0.15), rgba(68, 160, 141, 0.15));
  border: 2px solid rgba(78, 205, 196, 0.3);
}

.kinny-message-box.fail {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.15), rgba(238, 90, 82, 0.15));
  border: 2px solid rgba(255, 107, 107, 0.3);
}

.kinny-avatar {
  font-size: 2rem;
  animation: kinnyBounce 1s ease-in-out infinite;
  flex-shrink: 0;
}

.kinny-bubble {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
  min-height: 60px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.kinny-bubble::before {
  content: '';
  position: absolute;
  left: -8px;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-top: 8px solid transparent;
  border-bottom: 8px solid transparent;
  border-right: 8px solid rgba(255, 255, 255, 0.1);
}

.kinny-text {
  margin: 0 0 8px 0;
  color: #fff;
  font-size: 0.9rem;
  line-height: 1.4;
  font-weight: 500;
  flex: 1;
}

.kinny-badge {
  font-size: 0.75rem;
  color: rgba(78, 205, 196, 0.8);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
  align-self: flex-end;
  opacity: 0.8;
}

.kinny-badge.fail {
  color: rgba(255, 107, 107, 0.8);
}

@keyframes kinnyAppear {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.9);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes kinnyBounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.action-btn.retry:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
}

.preview-actions, .fail-actions {
  display: flex;
  gap: 12px;
}

/* Analysis Mode */
.analysis-mode {
  padding: 24px;
}

.kinny-working {
  text-align: center;
  margin-top: 16px;
}

.kinny-thinking {
  font-size: 3rem;
  margin-bottom: 16px;
  animation: kinnyThinking 2s ease-in-out infinite;
}

@keyframes kinnyThinking {
  0%, 100% { transform: scale(1) rotate(0deg); }
  25% { transform: scale(1.1) rotate(-5deg); }
  75% { transform: scale(1.1) rotate(5deg); }
}

.kinny-status {
  background: rgba(78, 205, 196, 0.1);
  border-radius: 12px;
  padding: 16px;
  margin-top: 12px;
}

.kinny-status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  color: #a0a0a0;
  font-size: 0.9rem;
}

.kinny-status-item:last-child {
  margin-bottom: 0;
}

.kinny-status-item .status-icon {
  font-size: 1.2rem;
}

.ai-status {
  margin: 20px 0;
  padding: 16px;
  background: rgba(78, 205, 196, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(78, 205, 196, 0.2);
}

.ai-status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 8px 0;
  color: #4ecdc4;
  font-size: 0.9rem;
  font-weight: 500;
}

.status-icon {
  font-size: 1.2rem;
  animation: statusPulse 2s ease-in-out infinite;
}

.status-text {
  opacity: 0.9;
}

@keyframes statusPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.dev-info {
  background: rgba(255, 193, 7, 0.15);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 8px;
  padding: 12px;
  margin-top: 16px;
  text-align: center;
}

.dev-info p {
  margin: 4px 0;
  color: #ffc107;
  font-size: 0.8rem;
  font-weight: 500;
}

/* ======== 流畅交互体验样式 ======== */

/* 自动关闭过渡提示 */
.transition-hint {
  margin-top: 20px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%);
  border: 2px solid rgba(34, 197, 94, 0.2);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  animation: hintFadeIn 0.5s ease-out;
}

@keyframes hintFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 倒计时圆环 */
.countdown-ring {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #22c55e 0%, #22c55e 25%, rgba(34, 197, 94, 0.2) 25%);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ringRotate 3s linear infinite;
}

@keyframes ringRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.countdown-text {
  font-size: 1rem;
  font-weight: bold;
  color: #22c55e;
  background: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.auto-close-text {
  font-size: 0.8rem;
  color: #16a34a;
  font-weight: 600;
  margin: 0;
  text-align: center;
}

/* 成功操作按钮组 */
.success-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

/* 暂停按钮特殊样式 */
.action-btn.secondary {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
  border: 1px solid rgba(107, 114, 128, 0.2);
}

.action-btn.secondary:hover {
  background: rgba(107, 114, 128, 0.15);
  color: #4b5563;
  transform: translateY(-1px);
}

/* 增强成功状态的动画 */
.success-celebration {
  animation: celebrationEnhanced 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes celebrationEnhanced {
  0% {
    opacity: 0;
    transform: scale(0.8) translateY(20px);
  }
  60% {
    opacity: 1;
    transform: scale(1.05) translateY(-5px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* 流畅的modal过渡增强 */
.modal-backdrop {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.game-modal {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
</style>

<template>
  <section class="composer">
    <!-- 游戏化头部 -->
    <div class="quest-header">
      <div class="quest-icon">🍳</div>
      <div class="quest-info">
        <h3 class="quest-title">Kitchen Quest</h3>
        <p class="quest-subtitle">Share your epic cooking adventure!</p>
      </div>
    </div>

    <!-- 🥘 recipe chips -->
    <div v-if="recipes.length" class="recipe-row">
      <button
        v-for="r in recipes" :key="r.id"
        :class="['recipe-chip', { on: selectedRecipe?.id === r.id }]"
        @click="selectRecipe(r)"
        :title="r.name"
      >
        <img v-if="r.default_picture" :src="r.default_picture" class="chip-img" />
        <span class="chip-txt">{{ r.name }}</span>
      </button>
    </div>

    <!-- ✏️ text with emoji picker -->
    <div class="text-input-container">
      <textarea
        ref="textareaRef"
        v-model="draft.content"
        rows="2"
        :placeholder="placeholder"
        class="new-input"
      />
      <button 
        class="emoji-trigger"
        @click="toggleEmojiPicker"
        type="button"
        title="Add emoji 😊"
      >
        😊
      </button>
      <div v-if="showEmojiPicker" class="emoji-picker-overlay" @click="closeEmojiPicker">
        <div class="emoji-picker-wrapper" @click.stop>
          <EmojiPicker 
            @select="onEmojiSelect"
            :native="true"
            :hide-search="false"
            :hide-group-icons="false"
            :hide-skin-tone="true"
            :disable-skin-tones="true"
            :group-names="{
              smileys_people: '😊 Moods',
              food_drink: '🍳 Food',
              activities: '🎮 Game',
              animals_nature: '🌿 Nature',
              objects: '⚡ Items'
            }"
            :display-recent="true"
            :recent-length="16"
          />
        </div>
      </div>
    </div>

    <!-- 📸 uploader -->
    <div class="upload-grid">
      <div
        v-for="(_, i) in 4"
        :key="i"
        class="upload-slot"
        :class="{ selected: highlight === i, pop: slotJustAdded === i }"
        @mousedown="pressStart(i)"
        @mouseup="pressEnd(i)"
      >
        <img
          v-if="previews[i]"
          :src="previews[i]"
          class="slot-img"
          @click.stop="toggleHighlight(i)"
        />
        <i v-else class="fas fa-plus slot-icon"></i>
        <span v-if="highlight === i && previews[i]" class="star">⭐</span>

        <input
          type="file" accept="image/*" hidden
          :ref="el => (inputs[i] = el as HTMLInputElement | null)"
          @change="onFile(i, $event)"
        />
      </div>
    </div>

    <!-- � STEP 4: THE GRAND FINALE - 游戏终极挑战区 -->
    <div class="step4-boss-zone">
      <!-- Kinny引导 - 超精简 -->
      <div class="kinny-guide">
        <span class="kinny-face">🐰</span>
        <p class="kinny-text">{{ kinnyPrompt }}</p>
      </div>

      <!-- 🏅 横向Badge快选 - 一行搞定 -->
      <div class="badge-quick-select">
        <button
          v-for="b in badges" :key="b.key"
          :class="['badge-btn', { selected: draft.mood === b.key }]"
          @click="selectBadge(b.key)"
          :title="b.desc"
        >
          <span class="badge-icon">{{ b.emoji }}</span>
          <span class="badge-name">{{ b.label }}</span>
          <div v-if="draft.mood === b.key" class="active-ring"></div>
        </button>
      </div>

      <!-- 🚀 Boss级提交按钮 - AAA游戏体验 -->
      <button 
        class="btn-boss-submit" 
        :class="{ 
          success: submitSuccess, 
          error: !!submitError,
          loading: isSubmitting,
          ready: canPost 
        }" 
        :disabled="!canPost || isSubmitting" 
        @click="submit"
      >
        <div v-if="!isSubmitting && !submitSuccess && !submitError" class="btn-content-boss">
          <span class="btn-icon-boss">🚀</span>
          <div class="btn-text-boss">
            <span class="btn-main">Share Epic Quest</span>
            <span class="btn-sub">Kinny awaits!</span>
          </div>
        </div>
        
        <div v-else-if="isSubmitting" class="btn-content-boss loading">
          <div class="progress-ring-boss">
            <svg width="24" height="24" viewBox="0 0 24 24">
              <circle 
                cx="12" cy="12" r="10" 
                fill="none" 
                stroke="currentColor" 
                stroke-width="2.5"
                stroke-dasharray="62.8"
                :stroke-dashoffset="62.8 - (62.8 * submitProgress / 100)"
                transform="rotate(-90 12 12)"
              />
            </svg>
          </div>
          <div class="btn-text-boss">
            <span class="btn-main">{{ submitStep }}</span>
            <span class="btn-sub">{{ submitProgress }}%</span>
          </div>
        </div>
        
        <div v-else-if="submitSuccess" class="btn-content-boss success">
          <span class="btn-icon-boss celebration">🎉</span>
          <div class="btn-text-boss">
            <span class="btn-main">Quest Complete!</span>
            <span class="btn-sub">Legend!</span>
          </div>
        </div>
        
        <div v-else-if="submitError" class="btn-content-boss error">
          <span class="btn-icon-boss">⚠️</span>
          <div class="btn-text-boss">
            <span class="btn-main">Retry Quest</span>
            <span class="btn-sub">Don't give up!</span>
          </div>
        </div>
      </button>

      <!-- 错误/提示横幅 - 精简 -->
      <div v-if="submitError" class="error-compact">
        <span>💥</span>
        <p>{{ submitError }} - Try again!</p>
      </div>

      <div v-if="missingMsg && !isSubmitting" class="hint-compact">
        <span>💡</span>
        <p>{{ missingMsg }}</p>
      </div>
    </div>
  </section>

  <!-- 🎮 AI判断弹窗 - 独立组件 -->
  <AIJudgmentModal 
    :key="`ai-judgment-${aiJudgmentKey}`"
    v-model="showAIJudgmentModal"
    :entry-id="currentEntryIdForJudgment"
s    :highlighted-image-url="highlight !== -1 && previews[highlight] ? previews[highlight] : null"
  />
  
  <!-- 调试信息 - 开发环境可见 -->
  <!-- Debug: Modal visible: {{ showAIJudgmentModal }}, Entry ID: {{ currentEntryIdForJudgment }}, Highlight: {{ highlight }}, Preview: {{ highlight !== -1 ? previews[highlight] : 'none' }} -->
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter }            from 'vue-router'
import { useCoupleMemoryStore } from '@/stores/couplememoryStore'
import { useRecipesStore }      from '@/stores/recipeStore'
import { useUserStore }         from '@/stores/userStore'
import type { Recipe }          from '@/models/recipes'
import api                      from '@/plugins/axios'
import EmojiPicker from 'vue3-emoji-picker'
import 'vue3-emoji-picker/css'
import AIJudgmentModal from './AIJudgmentModal.vue'
import heic2any from 'heic2any'

/* ─────────── store / router ─────────── */
const store  = useCoupleMemoryStore()
const recipeStore = useRecipesStore()
const userStore = useUserStore()
const router = useRouter()

/* ─────────── AI判断弹窗状态 ─────────── */
const showAIJudgmentModal = ref(false)
const currentEntryIdForJudgment = ref<number | null>(null)
// 🎯 确保每次提交都获得全新的AI判断
const aiJudgmentKey = ref(0)

/* ─────────── emoji picker ─────────── */
const showEmojiPicker = ref(false)
const textareaRef = ref<HTMLTextAreaElement>()

function toggleEmojiPicker() {
  showEmojiPicker.value = !showEmojiPicker.value
}

function closeEmojiPicker() {
  showEmojiPicker.value = false
}

function onEmojiSelect(emoji: any) {
  const textarea = textareaRef.value
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const emojiChar = emoji.i || emoji.n || emoji
    draft.content = draft.content.slice(0, start) + emojiChar + draft.content.slice(end)
    
    // 保持焦点并设置光标位置
    nextTick(() => {
      textarea.focus()
      const newPos = start + emojiChar.length
      textarea.setSelectionRange(newPos, newPos)
    })
  }
  showEmojiPicker.value = false
}

// ESCkey closes the emoji picker
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && showEmojiPicker.value) {
    closeEmojiPicker()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

// 清理事件监听器
onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

/* ─────────── 今日可选菜谱 ─────────── */
const recipes = computed<Recipe[]>(() => store.current?.recipes ?? [])

/* ─────────── 随机 placeholder ─────────── */
const placeholders = [
  'Chef secret move goes here… ✨',
  'Share your culinary adventure! 🍳',
  '🔥 RNG in kitchen: tell us what happened!',
]
const placeholder = placeholders[Math.floor(Math.random() * placeholders.length)]

/* ─────────── draft state ─────────── */
interface Draft { content: string; mood: string; files: (File | null)[] }
const draft = reactive<Draft>({
  content: '',
  mood   : 'nailed',
  files  : [null, null, null, null],
})

/* ─────────── recipe selection ─────────── */
const selectedRecipe = ref<Recipe | null>(null)
function selectRecipe(r: Recipe) { selectedRecipe.value = r }
onMounted(() => {
  recipeStore.init().then(() => {
    selectedRecipe.value = recipeStore.currentBracket?.recipe ?? null
  })
})

/* ─────────── uploader refs & previews ─────────── */
const inputs          = ref<(HTMLInputElement | null)[]>([null, null, null, null])
const previews        = ref<string[]>(['', '', '', ''])
const highlight       = ref(-1)
const slotJustAdded   = ref(-1)

/* 预览图 revoke */
watch(() => [...draft.files], (n, o) => {
  o.forEach((f, i) => {
    if (f && f !== n[i]) URL.revokeObjectURL(previews.value[i])
  })
  previews.value = n.map(f => (f ? URL.createObjectURL(f) : ''))
})

/* add / del handlers */
let timer: number | null = null
function pressStart(i: number) {
  timer = window.setTimeout(() => remove(i), 600)
}
function pressEnd(i: number) {
  if (timer) {
    clearTimeout(timer)
    timer = null
    if (!draft.files[i]) add(i)
  }
}
function add(i: number) { nextTick(() => inputs.value[i]?.click()) }
function onFile(i: number, e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0] ?? null
  draft.files.splice(i, 1, f)
  if (f) {
    slotJustAdded.value = i
    setTimeout(() => (slotJustAdded.value = -1), 450)
  }
}
function toggleHighlight(i: number) {
  if (!draft.files[i]) return
  highlight.value = highlight.value === i ? -1 : i
}
function remove(i: number) {
  if (!draft.files[i]) return
  URL.revokeObjectURL(previews.value[i])
  draft.files.splice(i, 1, null)
  if (highlight.value === i) highlight.value = -1
}

/* ─────────── badges ─────────── */
const badges = [
  { key: 'nailed', emoji: '🏆', label: 'Nailed',  desc: 'Perfect dish!' },
  { key: 'grind',  emoji: '🛠', label: 'Grinding',desc: 'Training arc…' },
  { key: 'love',   emoji: '💖', label: 'Loved',   desc: 'Bonding boost' },
  { key: 'lucky',  emoji: '🎲', label: 'Lucky',   desc: 'Crit success!' },
  { key: 'chaos',  emoji: '🔥', label: 'Chaos',   desc: 'Kitchen wipe-out' },
]

const selectedBadge = computed(() => badges.find(b => b.key === draft.mood))

/* ─────────── Kinny游戏化提示语 - 根据完成度动态变化 ─────────── */
const kinnyPrompts = {
  needRecipe: "Hey chef! Pick your quest recipe first! 🍳",
  needPhoto: "Looking good! Now show me that epic dish! 📸",
  needHighlight: "Nice shots! Tap your best one to make it shine! ⭐",
  needContent: "Almost there! Tell me your cooking story! ✍️",
  needMood: "How did it feel, chef? Choose your victory badge! 🏆",
  ready: "PERFECT! Ready to share your legend with the world? 🚀"
}

const kinnyPrompt = computed(() => {
  if (!recipeOk.value) return kinnyPrompts.needRecipe
  if (!photoOk.value) return kinnyPrompts.needPhoto
  if (!highlightOk.value) return kinnyPrompts.needHighlight
  if (!contentOk.value) return kinnyPrompts.needContent
  if (canPost.value) return kinnyPrompts.ready
  return kinnyPrompts.needMood
})

/* ─────────── Badge选择动效 ─────────── */
function selectBadge(key: string) {
  draft.mood = key
  // 触发音效或震动反馈（可选）
  if (window.navigator?.vibrate) {
    window.navigator.vibrate(50)
  }
}

/* ─────────── guards & hints ─────────── */
const contentOk   = computed(() => draft.content.trim().length > 0)
const photoOk     = computed(() => draft.files.some(Boolean))
const highlightOk = computed(() => highlight.value !== -1 && !!draft.files[highlight.value])
const recipeOk    = computed(() => !!selectedRecipe.value)
const posted      = computed(() => store.current?.entries?.some(e => e.author === userStore.user?.id))

const canPost = computed(
  () => contentOk.value && photoOk.value && highlightOk.value && recipeOk.value && !posted.value
)

const missingMsg = computed(() => {
  if (posted.value)        return 'You have already shared your dish!'
  if (!recipeOk.value)     return 'Pick a recipe to accept today quest!'
  if (!photoOk.value)      return 'Add at least one cooking photo 📸'
  if (!highlightOk.value)  return 'Tap a photo to mark ⭐ highlight'
  if (!contentOk.value)    return 'A short tale makes judges happy 😊'
  return ''
})

/* ─────────── loading state & game experience ─────────── */
const isSubmitting = ref(false)
const submitProgress = ref(0)
const submitStep = ref('')
const submitSuccess = ref(false)
const submitError = ref('')

// 游戏化提交步骤
const SUBMIT_STEPS = [
  { key: 'creating', label: '🏗️ Forging your epic tale...', progress: 20 },
  { key: 'uploading', label: '📸 Uploading battle evidence...', progress: 60 },
  { key: 'analyzing', label: '🤖 PlateMate analyzing your masterpiece...', progress: 80 },
  { key: 'complete', label: '🎉 Quest completed successfully!', progress: 100 },
]

function updateSubmitProgress(stepKey: string) {
  const step = SUBMIT_STEPS.find(s => s.key === stepKey)
  if (step) {
    submitStep.value = step.label
    submitProgress.value = step.progress
  }
}

/* ─────────── AAA级提交函数 - 精准联动后端 ─────────── */
async function submit() {
  if (!canPost.value || !selectedRecipe.value || isSubmitting.value) return

  // 🎯 重置状态 - 确保全新提交体验
  isSubmitting.value = true
  submitProgress.value = 0
  submitStep.value = ''
  submitSuccess.value = false
  submitError.value = ''
  
  // 🚀 重置AI判断相关状态，确保不会显示之前的结果
  currentEntryIdForJudgment.value = null
  showAIJudgmentModal.value = false
  aiJudgmentKey.value++ // 强制重新渲染AI判断组件

  try {
    // 步骤1: 创建Entry - 确保当前 round 存在
    updateSubmitProgress('creating')
    console.log('🎮 Starting quest submission...')
    
    // 先确保有当前round
    if (!store.current) {
      await store.fetchCurrent()
    }
    
    const entry = await store.createEntry(
      selectedRecipe.value.id,
      draft.content.trim(),
      draft.mood
    )
    
    if (!entry?.id) {
      throw new Error('Failed to create memory entry')
    }

    console.log(`✅ Entry ${entry.id} created successfully`)

    // 步骤2: 串行上传媒体文件（确保稳定性）
    updateSubmitProgress('uploading')
    let uploadedCount = 0
    const totalFiles = draft.files.filter(Boolean).length
    
    for (let index = 0; index < draft.files.length; index++) {
      var file = draft.files[index]
      if (!file) continue
      if (file.name.toUpperCase().endsWith('.HEIC') || file.name.toUpperCase().endsWith('.HEIF')) {
        try {
          const conversionResult = await heic2any({
            blob: file,
            toType: "image/png",
            quality: 0.8
          });
          
          // Convert the result to a File object
          const convertedFile = new File(
            [conversionResult as Blob], 
            file.name.replace(/\.(HEIC|HEIF)$/i, '.png'),
            { type: 'image/png' }
          );
          file = convertedFile;
          
        } catch (error) {
          console.error('HEIC/HEIF conversion failed:', error);
          // Handle error - maybe show a message to user
        }
      }
      
      try {
        await store.addMedia(entry.id, file, index === highlight.value)
        uploadedCount++
        console.log(`📸 Media ${uploadedCount}/${totalFiles} uploaded successfully`)
        
        // 更新进度
        const uploadProgress = 60 + (20 * uploadedCount / totalFiles)
        submitProgress.value = uploadProgress
        
      } catch (error) {
        console.warn(`⚠️ Media ${index + 1} upload failed:`, error)
        // 单个媒体上传失败不阻断流程
      }
    }

    console.log(`📸 Media upload completed: ${uploadedCount}/${totalFiles} files`)

    // 步骤3: 🤖 启动AI分析监控流程
    updateSubmitProgress('analyzing')
    submitSuccess.value = true
    
    console.log('🎉 Quest completed! Entry created, media uploaded.')
    console.log('📋 Created entry details:', { id: entry.id, recipe: selectedRecipe.value?.name })

    // 🎯 立即启动AI判断流程，不等待后台完成
    setTimeout(() => {
      isSubmitting.value = false
      
      if (!entry.id) {
        console.error('🚨 Entry created but no ID returned:', entry)
        submitError.value = 'Entry created but unable to start AI analysis'
        return
      }
      
      // 🍽️ 立即显示AI分析界面，确保taste.gif可见
      console.log('🎮 Triggering AI judgment modal with taste.gif for entry:', entry.id)
      startAIJudgmentFlow(entry.id)
      
      // 🎮 重置表单，为下一次提交做准备
      resetFormAfterSuccess()
    }, 500) // 进一步缩短到0.5秒，确保快速显示taste.gif

  } catch (error) {
    console.error('❌ Quest submission failed:', error)
    
    // 提供更友好的错误信息
    let errorMessage = 'Submission failed'
    const errorStr = (error as Error).message || ''
    
    if (errorStr.includes('Current round not loaded')) {
      errorMessage = 'Unable to load current round. Please refresh and try again.'
    } else if (errorStr.includes('create entry')) {
      errorMessage = 'Failed to create memory entry. Please check your connection.'
    } else if (errorStr.includes('upload')) {
      errorMessage = 'Some media uploads failed. Your entry was created but please check photos.'
    } else if (errorStr.includes('network') || errorStr.includes('timeout')) {
      errorMessage = 'Network connection issue. Please try again.'
    }
    
    submitError.value = errorMessage
    
    // 🔄 5秒后清除错误并允许重试
    setTimeout(() => {
      if (submitError.value) {
        submitError.value = ''
        isSubmitting.value = false
        console.log('🔄 Submit error cleared, ready for retry')
      }
    }, 5000)
  }
}

/* ─────────── AI判断流程 ─────────── */
function startAIJudgmentFlow(entryId: number) {
  console.log('🎮 Starting AI judgment flow for entry:', entryId)
  
  if (!entryId) {
    console.error('🚨 Invalid entryId passed to AI judgment flow:', entryId)
    return
  }
  
  // 🎯 确保使用全新的Entry ID，避免缓存旧的AI判断
  currentEntryIdForJudgment.value = entryId
  aiJudgmentKey.value++ // 强制AI判断组件完全重新初始化
  
  // 🍽️ 确保弹窗立即显示并包含taste.gif
  nextTick(() => {
    showAIJudgmentModal.value = true
    console.log('✅ AI judgment modal with taste.gif should now be visible')
    console.log('🔄 Entry ID:', entryId, 'AI judgment key:', aiJudgmentKey.value)
  })
}

// 重置表单的独立函数
function resetForm() {
  // 清理预览URL
  previews.value.forEach(url => url && URL.revokeObjectURL(url))
  
  // 重置所有状态
  Object.assign(draft, { 
    content: '', 
    mood: 'nailed', 
    files: [null, null, null, null] 
  })
  previews.value = ['', '', '', '']
  highlight.value = -1
  selectedRecipe.value = null
  
  // 重置提交状态
  isSubmitting.value = false
  submitProgress.value = 0
  submitStep.value = ''
  submitSuccess.value = false
}

// 🎯 成功提交后的表单重置 - 专门为新提交准备
function resetFormAfterSuccess() {
  console.log('🎮 Resetting form after successful submission')
  
  // 清理预览URL
  previews.value.forEach(url => url && URL.revokeObjectURL(url))
  
  // 重置表单数据
  Object.assign(draft, { 
    content: '', 
    mood: 'nailed', 
    files: [null, null, null, null] 
  })
  previews.value = ['', '', '', '']
  highlight.value = -1
  
  // 🔄 leave selectedRecipe alone so the user stays on the same recipe
  // selectedRecipe.value = null
  
  console.log('✅ Form reset completed, ready for next submission')
}

// 导航到结果页面
function navigateToResults(roundId?: number) {
  if (roundId) {
    router.replace(`/battle/${roundId}`)
  } else {
    router.replace('/battle')
  }
}
</script>

<style scoped>
/******** container ********/
.composer {
  width: 100%;
  max-width: 100%;
  background: linear-gradient(135deg, rgba(255,255,255,.95) 0%, rgba(252,231,243,.9) 100%);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 8px 24px rgba(124, 58, 237, 0.15);
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  border: 1px solid rgba(124, 58, 237, 0.1);
}

.title {
  font-size: 1rem;
  font-weight: 700;
  text-align: center;
  color: #7c3aed;
  margin: 0;
  text-shadow: 0 1px 2px rgba(124, 58, 237, 0.1);
}

/******** 游戏化头部 ********/
.quest-header {
  background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
  border-radius: 0.8rem;
  padding: 0.8rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: white;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.quest-icon {
  font-size: 1.8rem;
  background: rgba(255,255,255,0.2);
  border-radius: 50%;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.quest-info {
  flex: 1;
}

.quest-title {
  font-size: 1rem;
  font-weight: 800;
  margin: 0 0 0.2rem 0;
  text-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.quest-subtitle {
  font-size: 0.7rem;
  margin: 0;
  opacity: 0.9;
  font-weight: 500;
}

/******** recipe chips ********/
.recipe-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.recipe-chip {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.6rem 0.3rem 0.4rem;
  background: rgba(255,255,255,0.8);
  border: 1px solid rgba(124, 58, 237, 0.2);
  border-radius: 0.6rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  line-height: 1;
}

.recipe-chip:hover {
  background: rgba(255,255,255,1);
  border-color: #7c3aed;
  transform: translateY(-1px);
}

.recipe-chip.on {
  background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.chip-img {
  width: 1.2rem;
  height: 1.2rem;
  border-radius: 50%;
  object-fit: cover;
}

.chip-txt {
  white-space: nowrap;
  text-overflow: ellipsis;
  max-width: 6rem;
  overflow: hidden;
}

/******** text input with emoji picker ********/
.text-input-container {
  position: relative;
  width: 100%;
}

.emoji-trigger {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(124, 58, 237, 0.1);
  border: 1px solid rgba(124, 58, 237, 0.2);
  border-radius: 0.4rem;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 2;
}

.emoji-trigger:hover {
  background: rgba(124, 58, 237, 0.2);
  transform: scale(1.05);
}

.emoji-picker-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1999;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.emoji-picker-wrapper {
  border-radius: 0.8rem;
  overflow: hidden;
  box-shadow: 0 16px 48px rgba(0,0,0,0.3);
  background: white;
  border: 2px solid rgba(124, 58, 237, 0.3);
  max-height: 80vh;
  max-width: 95vw;
  width: 400px;
  min-height: 300px;
  animation: scaleIn 0.2s ease-out;
}

@keyframes scaleIn {
  from { 
    opacity: 0;
    transform: scale(0.9);
  }
  to { 
    opacity: 1;
    transform: scale(1);
  }
}

/* 覆盖emoji picker默认样式，保持游戏主题 */
.text-input-container :deep(.v3-emoji-picker) {
  border: none !important;
  box-shadow: none !important;
  font-family: inherit;
  max-height: 80vh;
  overflow: hidden;
  border-radius: 0.8rem;
}

.text-input-container :deep(.v3-emoji-picker .v3-header) {
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%) !important;
  color: white !important;
  position: sticky;
  top: 0;
  z-index: 10;
  border-radius: 0.8rem 0.8rem 0 0;
  padding: 0.8rem 1rem;
  font-weight: 600;
}

.text-input-container :deep(.v3-emoji-picker .v3-emoji:hover) {
  background: rgba(124, 58, 237, 0.15) !important;
  border-radius: 0.3rem;
  transform: scale(1.1);
  transition: all 0.2s ease;
}

.text-input-container :deep(.v3-emoji-picker .v3-body) {
  max-height: calc(80vh - 120px);
  overflow-y: auto;
  padding: 0.5rem;
}

.text-input-container :deep(.v3-emoji-picker .v3-emojis) {
  max-height: none !important;
  padding: 0.25rem;
}

.text-input-container :deep(.v3-emoji-picker .v3-tabs) {
  background: rgba(124, 58, 237, 0.05) !important;
  border-top: 1px solid rgba(124, 58, 237, 0.1);
  padding: 0.5rem;
}

.text-input-container :deep(.v3-emoji-picker .v3-tab) {
  color: #7c3aed !important;
  border-radius: 0.4rem;
  transition: all 0.2s ease;
}

.text-input-container :deep(.v3-emoji-picker .v3-tab.active) {
  background: #7c3aed !important;
  color: white !important;
}

/* 隐藏肤色选择器 */
.text-input-container :deep(.v3-emoji-picker .v3-skin-tone-picker) {
  display: none !important;
}

/******** textarea ********/
.new-input {
  width: 100%;
  padding: 0.8rem;
  border: 1px solid rgba(124, 58, 237, 0.2);
  border-radius: 0.6rem;
  font-size: 0.85rem;
  background: rgba(255,255,255,0.9);
  resize: none;
  transition: all 0.25s ease;
}

.new-input:focus {
  outline: none;
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
}

/******** uploader ********/
.upload-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.upload-slot {
  position: relative;
  padding-top: 100%;
  border: 2px dashed #d1d5db;
  border-radius: 0.6rem;
  background: rgba(249,250,251,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s ease;
}

.upload-slot:hover {
  border-color: #7c3aed;
  background: rgba(124, 58, 237, 0.05);
}

.upload-slot.selected {
  border-color: #facc15;
  border-style: solid;
  box-shadow: 0 0 0 3px rgba(250, 204, 21, 0.3);
}

.slot-icon {
  font-size: 1.5rem;
  color: #c1beca;
  pointer-events: none;
}

.slot-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 0.4rem;
}

.star {
  position: absolute;
  top: 4px;
  right: 4px;
  background: linear-gradient(135deg, #171756 0%, #220f47 100%);
  color: #fff;
  border-radius: 0.3rem;
  font-size: 0.7rem;
  padding: 0.2rem;
  pointer-events: none;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(245, 158, 11, 0.4);
}

@keyframes pop {
  0% { transform: scale(0.6) rotate(-4deg); }
  60% { transform: scale(1.05) rotate(4deg); }
  100% { transform: scale(1) rotate(0); }
}

.pop { animation: pop 0.4s ease-out; }

/******** 🎮 STEP 4: Boss战终极区 - 零Scroll AAA游戏体验 ********/
.step4-boss-zone {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.9rem;
  background: linear-gradient(135deg, 
    rgba(124, 58, 237, 0.06) 0%, 
    rgba(236, 72, 153, 0.04) 100%);
  border-radius: 0.9rem;
  border: 2px solid rgba(124, 58, 237, 0.25);
  box-shadow: 
    0 6px 20px rgba(124, 58, 237, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  position: relative;
}

/* Kinny引导 - 超精简行内设计 */
.kinny-guide {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.2rem 0.5rem;
  background: linear-gradient(135deg, #ffffff 0%, rgba(255, 255, 255, 0.95) 100%);
  border-radius: 0.65rem;
  border: 1.5px solid rgba(124, 58, 237, 0.2);
  box-shadow: 0 3px 10px rgba(124, 58, 237, 0.15);
  animation: guideSlideIn 0.4s ease-out;
}

@keyframes guideSlideIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.kinny-face {
  font-size: 1.2rem;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 6px rgba(124, 58, 237, 0.3));
  animation: faceBounce 2s ease-in-out infinite;
}

@keyframes faceBounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); }
}

.kinny-text {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  color: #7c3aed;
  line-height: 1.3;
  letter-spacing: 0.2px;
  text-shadow: 0 1px 2px rgba(124, 58, 237, 0.1);
  flex: 1;
}

/* Badge横向快选 - 一行完美布局 */
.badge-quick-select {
  display: flex;
  gap: 0.45rem;
  width: 100%;
  justify-content: space-between;
}

.badge-btn {
  flex: 1;
  position: relative;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.95) 0%, 
    rgba(252, 231, 243, 0.7) 100%);
  border: 2px solid rgba(236, 72, 153, 0.2);
  border-radius: 0.7rem;
  padding: 0.6rem 0.35rem;
  cursor: pointer;
  transition: all 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  min-height: 3.5rem;
}

.badge-btn:hover:not(.selected) {
  transform: translateY(-3px) scale(1.03);
  border-color: rgba(124, 58, 237, 0.5);
  background: linear-gradient(135deg, #ffffff 0%, rgba(252, 231, 243, 0.9) 100%);
  box-shadow: 0 5px 15px rgba(124, 58, 237, 0.2);
}

.badge-btn.selected {
  background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
  border-color: #facc15;
  transform: translateY(-4px) scale(1.05);
  box-shadow: 
    0 8px 24px rgba(124, 58, 237, 0.45),
    0 0 0 3px rgba(250, 204, 21, 0.25);
  animation: badgeWin 0.5s ease-out;
}

@keyframes badgeWin {
  0% { transform: translateY(-4px) scale(1.05); }
  40% { transform: translateY(-6px) scale(1.08) rotate(-3deg); }
  70% { transform: translateY(-6px) scale(1.08) rotate(3deg); }
  100% { transform: translateY(-4px) scale(1.05); }
}

.badge-icon {
  font-size: 1.5rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  transition: transform 0.28s ease;
}

.badge-btn.selected .badge-icon {
  filter: drop-shadow(0 3px 6px rgba(255, 255, 255, 0.4));
  animation: iconPop 0.5s ease-in-out;
}

@keyframes iconPop {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2) rotate(8deg); }
}

.badge-name {
  font-size: 0.65rem;
  font-weight: 800;
  color: #7c3aed;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  text-align: center;
  transition: color 0.28s ease;
  line-height: 1.1;
}

.badge-btn.selected .badge-name {
  color: #ffffff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.active-ring {
  position: absolute;
  inset: -4px;
  border-radius: 0.7rem;
  background: linear-gradient(135deg, #facc15 0%, #f59e0b 100%);
  opacity: 0.5;
  z-index: -1;
  animation: ringGlow 1.8s ease-in-out infinite;
}

@keyframes ringGlow {
  0%, 100% { 
    opacity: 0.35; 
    transform: scale(1);
    filter: blur(6px);
  }
  50% { 
    opacity: 0.6; 
    transform: scale(1.04);
    filter: blur(9px);
  }
}

/******** 🚀 Boss级提交按钮 - AAA游戏终极体验 ********/
.btn-boss-submit {
  width: 100%;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: #fff;
  border: none;
  border-radius: 0.85rem;
  font-weight: 800;
  padding: 0.5rem 1rem;
  font-size: 0.95rem;
  box-shadow: 
    0 6px 18px rgba(34, 197, 94, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  min-height: 3.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2.5px solid rgba(34, 197, 94, 0.3);
}

.btn-boss-submit::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.25), 
    transparent);
  transition: left 0.45s ease;
}

.btn-boss-submit.ready:not(:disabled):hover {
  transform: translateY(-3px) scale(1.015);
  box-shadow: 
    0 10px 28px rgba(34, 197, 94, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.btn-boss-submit.ready:not(:disabled):hover::before {
  left: 100%;
}

.btn-boss-submit.loading {
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  box-shadow: 
    0 6px 18px rgba(124, 58, 237, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  border-color: rgba(124, 58, 237, 0.3);
  cursor: wait;
  animation: loadingPulse 1.8s infinite ease-in-out;
}

.btn-boss-submit.success {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
  box-shadow: 
    0 6px 18px rgba(245, 158, 11, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  border-color: #facc15;
  animation: successExplosion 0.7s ease-out;
}

.btn-boss-submit.error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 
    0 6px 18px rgba(239, 68, 68, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  border-color: rgba(239, 68, 68, 0.3);
  animation: errorShake 0.5s ease-out;
}

.btn-boss-submit:disabled:not(.loading):not(.success) {
  background: linear-gradient(135deg, #6b7280 0%, #9ca3af 100%);
  box-shadow: none;
  cursor: not-allowed;
  opacity: 0.45;
  border-color: rgba(107, 114, 128, 0.3);
}

.btn-content-boss {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  width: 100%;
}

.btn-content-boss.loading {
  animation: contentPulse 1.8s infinite ease-in-out;
}

.btn-icon-boss {
  font-size: 1.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.25));
  transition: transform 0.28s ease;
}

.btn-icon-boss.celebration {
  animation: iconVictory 1s ease-out;
}

@keyframes iconVictory {
  0%, 100% { transform: scale(1) rotate(0deg); }
  30% { transform: scale(1.25) rotate(-12deg); }
  60% { transform: scale(1.3) rotate(12deg); }
  85% { transform: scale(1.25) rotate(-8deg); }
}

.btn-text-boss {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.1rem;
}

.btn-main {
  font-weight: 800;
  font-size: 0.9rem;
  line-height: 1.15;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  letter-spacing: 0.25px;
}

.btn-sub {
  font-weight: 600;
  font-size: 0.7rem;
  opacity: 0.88;
  line-height: 1;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.progress-ring-boss {
  position: relative;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.progress-ring-boss svg {
  transform: rotate(-90deg);
  transition: stroke-dashoffset 0.4s ease;
  filter: drop-shadow(0 2px 4px rgba(255, 255, 255, 0.3));
  animation: ringRotate 1.8s linear infinite;
}

@keyframes ringRotate {
  from { transform: rotate(-90deg); }
  to { transform: rotate(270deg); }
}

/* 错误/提示精简横幅 - 最小化空间占用 */
.error-compact {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, 
    rgba(239, 68, 68, 0.12) 0%, 
    rgba(220, 38, 38, 0.08) 100%);
  border: 1.5px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.65rem;
  padding: 0.55rem 0.75rem;
  animation: compactSlideIn 0.3s ease-out;
}

.error-compact span {
  font-size: 1.3rem;
  flex-shrink: 0;
  animation: errorShake 0.5s ease-out;
}

.error-compact p {
  margin: 0;
  color: #dc2626;
  font-weight: 700;
  font-size: 0.72rem;
  line-height: 1.25;
  flex: 1;
}

.hint-compact {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, 
    rgba(251, 191, 36, 0.12) 0%, 
    rgba(245, 158, 11, 0.08) 100%);
  border: 1.5px solid rgba(251, 191, 36, 0.3);
  border-radius: 0.65rem;
  padding: 0.5rem 0.5rem;
  animation: compactSlideIn 0.3s ease-out;
}

.hint-compact span {
  font-size: 1.3rem;
  flex-shrink: 0;
  animation: hintPulse 2s ease-in-out infinite;
}

@keyframes hintPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.12); }
}

.hint-compact p {
  margin: 0;
  color: #d97706;
  font-weight: 700;
  font-size: 0.72rem;
  line-height: 1.25;
  flex: 1;
}

@keyframes compactSlideIn {
  from { 
    opacity: 0; 
    transform: translateY(6px);
  }
  to { 
    opacity: 1; 
    transform: translateY(0);
  }
}

/* ======== AAA游戏级动画效果 ======== */
@keyframes successExplosion {
  0% { 
    transform: scale(1); 
    box-shadow: 0 8px 24px rgba(245, 158, 11, 0.5);
  }
  30% { 
    transform: scale(1.08); 
    box-shadow: 0 12px 40px rgba(245, 158, 11, 0.7);
  }
  60% { 
    transform: scale(0.98); 
    box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
  }
  100% { 
    transform: scale(1); 
    box-shadow: 0 8px 24px rgba(245, 158, 11, 0.5);
  }
}

@keyframes errorShake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-8px); }
  20%, 40%, 60%, 80% { transform: translateX(8px); }
}

@keyframes loadingPulse {
  0%, 100% { 
    opacity: 1; 
    transform: scale(1);
  }
  50% { 
    opacity: 0.8; 
    transform: scale(1.02);
  }
}

@keyframes contentPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

/******** Mobile Responsive - AAAtuning ********/
@media (max-width: 480px) {
  .composer {
    padding: 0.8rem;
    gap: 0.6rem;
    max-width: 100%;
  }
  
  .quest-header {
    padding: 0.6rem 0.8rem;
  }
  
  .quest-icon {
    width: 2rem;
    height: 2rem;
    font-size: 1.5rem;
  }
  
  .quest-title {
    font-size: 0.9rem;
  }
  
  .quest-subtitle {
    font-size: 0.65rem;
  }
  
  /* Step 4 mobile tuning - Boss战区 */
  .step4-boss-zone {
    padding: 0.75rem;
    gap: 0.55rem;
  }
  
  .kinny-face {
    font-size: 1.4rem;
  }
  
  .kinny-guide {
    padding: 0.45rem 0.6rem;
  }
  
  .kinny-text {
    font-size: 0.72rem;
  }
  
  .badge-quick-select {
    gap: 0.35rem;
  }
  
  .badge-btn {
    padding: 0.5rem 0.3rem;
    min-height: 3.2rem;
    border-width: 1.8px;
  }
  
  .badge-btn:hover:not(.selected) {
    transform: translateY(-2.5px) scale(1.02);
  }
  
  .badge-btn.selected {
    transform: translateY(-3.5px) scale(1.04);
  }
  
  .badge-icon {
    font-size: 1.3rem;
  }
  
  .badge-name {
    font-size: 0.6rem;
  }
  
  .btn-boss-submit {
    padding: 0.85rem 1.2rem;
    min-height: 3.2rem;
    border-width: 2px;
  }
  
  .btn-icon-boss {
    font-size: 1.4rem;
  }
  
  .btn-main {
    font-size: 0.85rem;
  }
  
  .btn-sub {
    font-size: 0.65rem;
  }
  
  .error-compact, .hint-compact {
    padding: 0.5rem 0.65rem;
  }
  
  .error-compact span, .hint-compact span {
    font-size: 1.2rem;
  }
  
  .error-compact p, .hint-compact p {
    font-size: 0.68rem;
  }
  
  .recipe-chip {
    padding: 0.25rem 0.5rem 0.25rem 0.35rem;
    font-size: 0.7rem;
  }
  
  .chip-img {
    width: 1rem;
    height: 1rem;
  }
  
  .new-input {
    font-size: 0.8rem;
    padding: 0.7rem;
  }
}

@media (max-width: 360px) {
  .composer {
    padding: 0.6rem;
  }
  
  .step4-boss-zone {
    padding: 0.65rem;
    gap: 0.5rem;
  }
  
  .badge-quick-select {
    gap: 0.3rem;
  }
  
  .badge-btn {
    padding: 0.45rem 0.25rem;
    min-height: 3rem;
  }
  
  .badge-icon {
    font-size: 1.2rem;
  }
  
  .badge-name {
    font-size: 0.55rem;
  }
  
  .btn-boss-submit {
    padding: 0.75rem 1rem;
    min-height: 3rem;
  }
  
  .btn-icon-boss {
    font-size: 1.3rem;
  }
  
  .btn-main {
    font-size: 0.8rem;
  }
  
  .btn-sub {
    font-size: 0.62rem;
  }
  
  .chip-txt {
    max-width: 4.5rem;
  }
}

/* === AAA游戏级别CSS动画增强 === */

/* 进度条发光效果 */
.v-progress-linear {
  background: linear-gradient(
    90deg,
    rgba(79, 172, 254, 0.1) 0%,
    rgba(79, 172, 254, 0.3) 50%,
    rgba(79, 172, 254, 0.1) 100%
  );
  background-size: 468px 100%;
  animation: progressShimmer 1.5s infinite;
}

/* 按钮增强效果 */
.v-btn--variant-elevated {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.v-btn--variant-elevated:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(79, 172, 254, 0.3);
}

.v-btn--variant-elevated:active {
  transform: translateY(0);
  transition: all 0.1s;
}

/* 成功状态样式 */
.submit-success {
  animation: successPulse 0.6s ease-in-out;
}

/* 错误状态样式 */
.submit-error {
  animation: errorShake 0.5s ease-in-out;
}

/* 加载状态脉冲 */
.submit-loading {
  background: linear-gradient(
    90deg,
    rgba(79, 172, 254, 0.8) 0%,
    rgba(79, 172, 254, 1) 50%,
    rgba(79, 172, 254, 0.8) 100%
  );
  background-size: 200% 100%;
  animation: progressShimmer 1.5s infinite;
}
</style>

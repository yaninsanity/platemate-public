<!-- 弹幕留言墙 - 实时情侣互动评论系统 -->
<template>
  <div class="danmaku-comment-wall">
    <!-- 弹幕显示区域 -->
  <div ref="displayRef" class="danmaku-display" :class="{ 'solo-mode': soloMode }" :style="wallpaperStyle">
      <!-- 空状态提示 -->
      <div v-if="comments.length === 0 && activeComments.length === 0" class="empty-danmaku-state">
        <div class="empty-icon">💬</div>
        <p>{{ soloMode ? 'Leave a comment to start the conversation!' : 'No comments yet - be the first to comment!' }}</p>
        <div class="floating-emoji">
          <span v-for="emoji in ['💕', '🍽️', '👨‍🍳', '✨']" :key="emoji" class="float-emoji">{{ emoji }}</span>
        </div>
      </div>
      
      <!-- 弹幕评论 - 拆分单元组件，稳定动画 -->
      <DanmakuBubble
        v-for="comment in activeComments"
        :key="`${comment.id}-${comment.animationId}`"
        :data-animation-id="comment.animationId"
        :username="comment.username"
        :text="comment.text"
        :avatar="comment.avatar"
        :animation-id="comment.animationId"
        :style-object="comment.style"
        @click="onDanmakuClick(comment)"
      />
    </div>

    <!-- 评论输入栏 -->
    <div class="comment-input-bar" v-if="isActive && !hideInputBar">
      <div class="input-container">
        <textarea 
          ref="textareaRef"
          v-model="newComment"
          @keyup.enter="submitComment"
          :placeholder="getPlaceholderText()"
          class="comment-input"
          maxlength="50"
          rows="1"
        ></textarea>
        <button @click="toggleEmojiPicker" class="emoji-btn">
          😊
        </button>
        <button @click="submitComment" class="send-btn" :disabled="!newComment.trim()">
          <span class="send-icon">💕</span>
        </button>
      </div>

      <!-- Emoji Picker -->
      <div v-if="showEmojiPicker" class="emoji-picker-overlay" @click="closeEmojiPicker">
        <div class="emoji-picker-wrapper" @click.stop>
          <EmojiPicker 
            @select="onEmojiSelect"
            :display-recent="true"
            :disable-skin-tones="true"
            :disable-groups="['activities', 'travel', 'objects', 'symbols', 'flags']"
            theme="dark"
            picker-type="modern"
          />
        </div>
      </div>

  <!-- Removed comment type selector for simplified UX -->
    </div>

    <!-- 统计信息 -->
    <div class="comment-stats" v-if="!soloMode">
      <div class="stat-item">
        <span class="stat-number">{{ totalComments }}</span>
        <span class="stat-label">Comments</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">{{ activeUsers }}</span>
        <span class="stat-label">Active</span>
      </div>
      <!-- Removed type-based Praise stat -->
    </div>
  </div>

  <!-- Full Comment Modal (独立组件) -->
  <DanmakuModal
    :open="showModal"
    :username="modalComment?.username"
    :text="modalComment?.text"
    :avatar="modalComment?.avatar || placeholderAvatar"
    :timestamp="modalComment?.timestamp"
    @close="closeModal"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, onBeforeUnmount, nextTick } from 'vue'
import EmojiPicker from 'vue3-emoji-picker'
import 'vue3-emoji-picker/css'
import DanmakuBubble from './DanmakuBubble.vue'
import DanmakuModal from './DanmakuModal.vue'
import { createBackgroundManager } from '@/utils/backgroundManager'

interface CommentData {
  id: string | number
  username: string
  text: string
  timestamp: number
  avatar?: string
  type?: string
}

interface DanmakuComment extends CommentData {
  style?: any
  animationId?: number
  originalId?: string | number
  fullText?: string
}

const props = withDefaults(
  defineProps<{
    comments: CommentData[]
    isActive?: boolean
    soloMode?: boolean
    hideInputBar?: boolean
  }>(),
  {
    comments: () => [],
    isActive: true,
    soloMode: false,
    hideInputBar: false
  }
)

const emit = defineEmits<{
  addComment: [text: string, type?: string]
}>()

// reactive state
const newComment = ref('')
const activeComments = ref<DanmakuComment[]>([])
const danmakuTimer = ref<NodeJS.Timeout | null>(null)
const showEmojiPicker = ref(false)
const textareaRef = ref<HTMLTextAreaElement>()
const displayedComments = ref<Set<string>>(new Set())
const danmakuQueue = ref<DanmakuComment[]>([])
const animationId = ref<number>(0)
// 轮询指针与冷却跟踪
const rrIndex = ref<number>(0)
const lastShownAt = ref<Map<string, number>>(new Map())
// 最近一次点击的弹幕，用于关闭后恢复
const lastClickedAnimationId = ref<number | null>(null)

// Placeholder avatar
const placeholderAvatar = new URL('@/assets/avatar_placeholder.svg', import.meta.url).href

// Modal state
const showModal = ref(false)
const modalComment = ref<{ username: string; text: string; timestamp: number; avatar?: string } | null>(null)
// Display area ref for precise width/height measurements
const displayRef = ref<HTMLElement | null>(null)
// Track container width for accurate animation distances
const containerWidth = ref<number>(430)
let resizeObserver: ResizeObserver | null = null

// 🎮 统一背景管理 - 使用全局背景管理器
const bgManager = createBackgroundManager()
const wallpaperStyle = computed(() => {
  const style = bgManager.getStyle(0.25)  // 轻度渐变叠加，适合弹幕墙
  return {
    ...style,
    backgroundAttachment: 'scroll, scroll',
  } as Record<string, string>
})

// 轨道系统 - 防止重叠
const lanes = ref<number[]>([]) // 存储已占用的Y位置（正在使用的轨道索引）
const laneHeight = 60 // 每条轨道的垂直空间
const nextLane = ref<number>(0) // 轮询选择轨道，避免集中在前几行
const spawnTimeout = ref<number | null>(null) // 自适应调度器

// computed
const totalComments = computed(() => props.comments.length)

const activeUsers = computed(() => {
  const users = new Set(props.comments.map(c => c.username))
  return users.size
})

// 获取占位符文本
const getPlaceholderText = () => {
  if (props.soloMode) {
    return "Give some encouragement... 💕"
  }
  
  const placeholders = [
    "Cheer for your favorite chef! 👏",
    "Share your cooking thoughts... 🍳",
    "Send love to the cooks! ❤️",
    "What do you think about this dish? 🤔"
  ]
  return placeholders[Math.floor(Math.random() * placeholders.length)]
}

// 获取可用轨道 - 智能分配防止重叠
const getLaneCount = (): number => {
  const displayHeight = props.soloMode ? 240 : 240
  return Math.max(1, Math.floor(displayHeight / laneHeight))
}

const getAvailableLane = (): number => {
  const laneCount = getLaneCount()

  // 清理已完成的轨道（仍在使用的轨道保留）
  lanes.value = lanes.value.filter(lane => {
    const isOccupied = activeComments.value.some(comment => {
      const commentY = parseFloat(comment.style?.top || '0')
      const laneY = lane * laneHeight + 30
      return Math.abs(commentY - laneY) < laneHeight / 2
    })
    return isOccupied
  })

  // 轮询优先的空轨道选择，保证分布均匀
  for (let k = 0; k < laneCount; k++) {
    const i = (nextLane.value + k) % laneCount
    if (!lanes.value.includes(i)) {
      lanes.value.push(i)
      nextLane.value = (i + 1) % laneCount
      return i
    }
  }

  // when every lane is taken, allow slight overlap by picking the lane nearest nextLane
  const i = nextLane.value % laneCount
  nextLane.value = (nextLane.value + 1) % laneCount
  return i
}

// Emoji picker方法
const toggleEmojiPicker = () => {
  showEmojiPicker.value = !showEmojiPicker.value
}

const closeEmojiPicker = () => {
  showEmojiPicker.value = false
}

const onEmojiSelect = (emoji: any) => {
  const textarea = textareaRef.value
  if (textarea) {
    const start = textarea.selectionStart || 0
    const end = textarea.selectionEnd || 0
    const emojiChar = emoji.i || emoji.n || emoji
    newComment.value = newComment.value.slice(0, start) + emojiChar + newComment.value.slice(end)
    
    // 保持焦点并设置光标位置
    nextTick(() => {
      textarea.focus()
      const newPos = start + emojiChar.length
      textarea.setSelectionRange(newPos, newPos)
    })
  }
  showEmojiPicker.value = false
}

const submitComment = () => {
  if (!newComment.value.trim()) return
  
  emit('addComment', newComment.value.trim())
  newComment.value = ''
  closeEmojiPicker()
}

// 弹幕交互方法
const onDanmakuClick = (comment: DanmakuComment) => {
  // 点击弹幕时的特效
  const commentEl = document.querySelector(`[data-animation-id="${comment.animationId}"]`) as HTMLElement
  if (commentEl) {
    // commentEl.classList.add('clicked-effect')
    
    // 创建点击波纹效果
    const ripple = document.createElement('div')
    ripple.className = 'click-ripple'
    ripple.style.cssText = `
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.6);
      transform: scale(0);
      animation: ripple-expand 0.6s ease-out;
      pointer-events: none;
      width: 20px;
      height: 20px;
      top: 50%;
      left: 50%;
      margin: -10px 0 0 -10px;
    `
    commentEl.appendChild(ripple)
    
    setTimeout(() => {
      // commentEl?.classList.remove('clicked-effect')
      ripple?.remove()
    }, 600)

    // 暂停当前弹幕并轻微“回头”靠右，避免一点击就飘走
    try {
      // 标记暂停，让动画帧循环让位
      commentEl.dataset.paused = '1'
    // 记录暂停开始时间
    commentEl.dataset.pStart = String(performance.now())
      // 读取当前 translateX
      const style = getComputedStyle(commentEl)
      const m = style.transform
      let currentX = 0
      if (m && m !== 'none') {
        const parts = m.match(/matrix\(([^)]+)\)/)
        if (parts && parts[1]) {
          const nums = parts[1].split(',').map(v => parseFloat(v.trim()))
          // matrix(a,b,c,d,tx,ty) => tx at index 4
          if (nums.length >= 6) currentX = nums[4]
        }
      }
      // 小幅回退 60px，并稍微放大
      commentEl.style.transition = 'filter 220ms, opacity 220ms ease'
      // commentEl.style.transform = `translateX(${currentX + 60}px) translateZ(0)`
      commentEl.style.filter = 'brightness(1.12) saturate(1.1)'
      commentEl.style.zIndex = '1200000'
    } catch {}
  }

  // 打开完整评论弹窗
  showModal.value = true
  lastClickedAnimationId.value = comment.animationId ?? null
  modalComment.value = {
    username: comment.username,
    text: comment.fullText || comment.text,
    timestamp: comment.timestamp,
    avatar: comment.avatar || placeholderAvatar
  }
}

const onDanmakuHover = (comment: DanmakuComment, event: MouseEvent) => {
  const commentEl = event.target as HTMLElement
  if (commentEl) {
    commentEl.style.filter = 'brightness(1.3) saturate(1.2)'
    commentEl.style.transform += ' translateY(-2px)'
    commentEl.style.zIndex = '999'
  }
}

const onDanmakuLeave = (comment: DanmakuComment, event: MouseEvent) => {
  const commentEl = event.target as HTMLElement
  if (commentEl) {
    commentEl.style.filter = comment.style?.filter || 'none'
    commentEl.style.transform = commentEl.style.transform.replace(' translateY(-2px)', '')
    commentEl.style.zIndex = comment.style?.zIndex || '10'
  }
}

// 弹幕动画系统 - 增强版支持长文字多行显示和轨道分配
const createDanmaku = (comment: DanmakuComment, isNew = false) => {
  const commentId = String(comment.id)
  console.log('🎯 Creating danmaku:', { 
    comment, 
    isNew, 
    commentId,
    displayed: displayedComments.value.has(commentId),
    currentDisplayed: Array.from(displayedComments.value),
    isActive: props.isActive
  })
  
  // 如果组件未激活，不创建弹幕
  if (!props.isActive) {
    console.log('❌ Component not active, skipping danmaku creation')
    return
  }
  
  // 避免重复显示同一条评论
  if (displayedComments.value.has(commentId)) {
    console.log('❌ Comment already displayed, skipping:', commentId)
    if (isNew) {
      createSpecialEffect(comment)
    }
    return
  }
  
  // 标记为飞行中，防止同一时刻重复
  displayedComments.value.add(commentId)
  console.log('✅ Added comment to displayed set, now has:', displayedComments.value.size, 'comments')
  
  // 简化：单行弹幕，避免一个评论拆分为多行引发“12行限制”观感
  const fullText = comment.text
  const maxLineLength = 36
  const textToShow = fullText.length > maxLineLength
    ? fullText.slice(0, maxLineLength - 1) + '…'
    : fullText
  const finalLines = [textToShow]
  
  // 简化的弹幕尺寸计算
  // measure the visible width at runtime, so nothing starts off-screen
  const displayWidth = containerWidth.value || displayRef.value?.clientWidth || 430
  // 更稳定的速度：避免过快导致中途消失
  // 使用基于像素的速度，保证跨屏一致体验
  const isMobile = window.innerWidth <= 480
  const pxPerSec = isMobile ? 90 : 130
  // move on X with transform and pin left to 0, so the two do not both offset移
  const startX = displayWidth + 20 // 从右侧偏外启动
  const endX = -800 // 仅占位，实际以元素宽度重新计算
  const laneIndex = getAvailableLane()
  const baseY = laneIndex * laneHeight + 15 + Math.random() * 15
  const lineHeight = 0
  
  finalLines.forEach((lineText, lineIndex) => {
    const currentAnimationId = ++animationId.value
    const lineY = baseY + (lineIndex * lineHeight)
    
  const delay = lineIndex * 300 // 单行基本为0，多行时轻微错峰
  // speed 已弃用，使用像素速度统一体验
    
    const animatedComment = {
      ...comment,
      id: `${comment.id}-line-${lineIndex}`,
      text: lineText,
      animationId: currentAnimationId,
      originalId: comment.id,
      fullText: fullText,
      style: {
        // 简化的绝对定位
        position: 'absolute',
        left: '0px',
        top: `${lineY}px`,
        transform: 'translateX(0) translateZ(0)',
        // driven by requestAnimationFrame; no CSS transition fallback
        zIndex: 999999 + Math.floor(Math.random() * 100),
        opacity: isNew ? 1 : 0.95,
        // 增强发光效果
        filter: isNew 
          ? 'drop-shadow(0 0 15px rgba(78, 205, 196, 0.8)) drop-shadow(0 0 30px rgba(255, 255, 255, 0.4))' 
          : 'drop-shadow(0 0 8px rgba(78, 205, 196, 0.5))',
        animationDelay: `${delay}ms`,
        // 确保背景色足够明显
        backgroundColor: isNew 
          ? 'rgba(78, 205, 196, 0.98)' 
          : 'rgba(78, 205, 196, 0.92)',
        // 确保边框清晰
        border: isNew 
          ? '3px solid rgba(255, 255, 255, 0.9)' 
          : '3px solid rgba(255, 255, 255, 0.7)',
        // 基础可见性
        visibility: 'visible',
        display: 'block',
        // 移除任何遮罩或裁剪
        clipPath: 'none',
        mask: 'none',
        clip: 'unset',
        // 硬件加速和渲染tuning
        transformStyle: 'preserve-3d',
        willChange: 'transform, opacity',
        backfaceVisibility: 'visible',
        contain: 'none',
        isolation: 'isolate',
        mixBlendMode: 'normal',
        // 强制元素进入独立渲染层
        webkitTransform: 'translateZ(0)'
      }
    }
    
  setTimeout(() => {
      console.log('🚀 Pushing animated comment to activeComments:', animatedComment)
      activeComments.value.push(animatedComment)
      
  nextTick(() => {
        const el = document.querySelector(`[data-animation-id="${currentAnimationId}"]`) as HTMLElement
        if (!el) return

        // 强制可见与稳定层叠
        el.style.setProperty('position', 'absolute', 'important')
        el.style.setProperty('display', 'block', 'important')
        el.style.setProperty('visibility', 'visible', 'important')
        el.style.setProperty('opacity', isNew ? '1' : '0.98', 'important')
        el.style.setProperty('z-index', String(1000000 + Math.floor(Math.random() * 100)), 'important')

        // start the animation after layout via requestAnimationFrame, so it cannot vanish mid-way
        // X is driven entirely by transform, measured against the container width
        const containerW = containerWidth.value || displayRef.value?.clientWidth || displayWidth
        const elWidth = el.offsetWidth
        const margin = 24
        const startXLocal = containerW + margin
        const endXLocal = -elWidth - margin
        // 先设置到起始位置与初始透明度，避免第一帧跳跃
        el.style.transform = `translateX(${startXLocal}px) translateZ(0)`
        el.style.opacity = isNew ? '0' : (el.style.opacity || '0.95')
        el.style.transition = 'opacity 220ms ease-out'
        // 轻微延迟后淡入
        setTimeout(() => { el.style.opacity = '1' }, 0)

  // 距离与时长（轻微抖动，避免同步感过强）
  const distance = startXLocal - endXLocal
  const speed = pxPerSec * (0.94 + Math.random() * 0.12)
  const durationMs = Math.max(2200, Math.round((distance / speed) * 1000))

        // 帧循环
        const start = performance.now()
        let rafId = 0
        const step = (t: number) => {
          // 若暂停，保持当前位置但继续下一帧检查，以便随时恢复
          if (el.dataset.paused === '1') {
            el.dataset.animRunning = '0'
            rafId = requestAnimationFrame(step)
            return
          }
          // 扣除累计暂停时间，做到真正的“暂停/恢复”
          const pausedAccum = parseFloat(el.dataset.pAccum || '0') || 0
          const elapsed = Math.max(0, t - start - pausedAccum)
          const progress = Math.min(1, elapsed / durationMs)
          const x = startXLocal + (endXLocal - startXLocal) * progress
          el.style.transform = `translateX(${x}px) translateZ(0)`
          // 在末尾阶段淡出更自然
          if (progress > 0.92) {
            const fade = Math.max(0, 1 - (progress - 0.92) / 0.08)
            el.style.opacity = String(0.2 + fade * 0.8)
          }
          if (progress < 1) {
            el.dataset.animRunning = '1'
            rafId = requestAnimationFrame(step)
          } else {
            el.dataset.animRunning = '0'
            // 动画完成后清理并释放轨道
            const index = activeComments.value.findIndex(c => c.animationId === currentAnimationId)
            if (index > -1) {
              activeComments.value.splice(index, 1)
            }
            const laneToRemove = lanes.value.indexOf(laneIndex)
            if (laneToRemove > -1) lanes.value.splice(laneToRemove, 1)
            // 结束时从飞行集中移除，并记录展示时间用于冷却
            const origId = String(comment.originalId ?? comment.id)
            displayedComments.value.delete(origId)
            lastShownAt.value.set(origId, Date.now())
          }
        }
        rafId = requestAnimationFrame(step)

        if (lineIndex === 0 && isNew) {
          el.classList.add('new-comment-glow')
          setTimeout(() => el.classList.remove('new-comment-glow'), 1500)
        }
        if (finalLines.length > 1) el.classList.add('multi-line-danmaku')
      })
      
      // 不再使用固定超时移除，改为在动画完成时清理
      
    }, delay)
  })
  
  // 不再使用固定长延迟清理，改为动画完成时清理（见上）
}

// 创建特殊交互效果
const createSpecialEffect = (comment: CommentData) => {
  const existingComment = activeComments.value.find(c => c.id === comment.id)
  if (existingComment) {
    const commentEl = document.querySelector(`[data-animation-id="${existingComment.animationId}"]`) as HTMLElement
    if (commentEl) {
      commentEl.classList.add('combo-effect')
      commentEl.style.filter = 'drop-shadow(0 0 12px rgba(255, 107, 107, 0.8)) saturate(1.5)'
      commentEl.style.transform += ' scale(1.1)'
      
      const comboEl = document.createElement('div')
      comboEl.className = 'combo-counter'
      comboEl.textContent = '+1'
      comboEl.style.cssText = `
        position: absolute;
        top: -20px;
        right: -10px;
        color: #ff6b6b;
        font-weight: bold;
        font-size: 0.8rem;
        animation: combo-bounce 0.6s ease-out;
        pointer-events: none;
        z-index: 100;
      `
      commentEl.appendChild(comboEl)
      
      setTimeout(() => {
        commentEl?.classList.remove('combo-effect')
        commentEl.style.filter = existingComment.style?.filter || 'none'
        commentEl.style.transform = commentEl.style.transform.replace(' scale(1.1)', '')
        comboEl?.remove()
      }, 800)
    }
  }
}

// 智能弹幕队列系统（按轨道上限发射）
const processDanmakuQueue = () => {
  if (danmakuQueue.value.length === 0) return

  const laneCount = getLaneCount()
  if (activeComments.value.length >= laneCount) return

  const nextComment = danmakuQueue.value.shift()
  if (nextComment) {
    createDanmaku(nextComment, false)
  }
}

// 计算最小重复间隔，评论越多间隔越长
const getMinRepeatGapMs = (count: number): number => {
  if (count <= 3) return 2500
  if (count <= 6) return 4000
  if (count <= 12) return 6500
  if (count <= 24) return 9000
  return 12000
}

// 轮询选取下一条评论（考虑冷却和在飞行中排除）
const enqueueNextRoundRobin = () => {
  const total = props.comments.length
  if (total === 0) return

  const now = Date.now()
  const minGap = getMinRepeatGapMs(total)
  let pickedIndex: number | null = null
  let oldestIdx: number | null = null
  let oldestTime = Infinity

  for (let k = 0; k < total; k++) {
    const idx = (rrIndex.value + k) % total
    const c = props.comments[idx]
    const id = String(c.id)
    // 跳过正在飞行或已在队列中的
    if (displayedComments.value.has(id) || danmakuQueue.value.some(q => String(q.id) === id)) {
      continue
    }
    const last = lastShownAt.value.get(id) || 0
    const gapOk = now - last >= minGap
    if (gapOk && pickedIndex === null) {
      pickedIndex = idx
    }
    // 记录最久未显示者作为保底
    const elapsed = now - last
    if (elapsed < oldestTime) {
      oldestTime = elapsed
      oldestIdx = idx
    }
    if (pickedIndex !== null) break
  }

  const useIdx = pickedIndex ?? oldestIdx
  if (useIdx !== null) {
    const c = props.comments[useIdx]
    danmakuQueue.value.push(c)
    rrIndex.value = (useIdx + 1) % total
  }
}

// 启动弹幕系统
const scheduleNextSpawn = () => {
  // the emit interval adapts to the backlog, with jitter so nothing arrives in lockstep
  const backlog = danmakuQueue.value.length
  const base = backlog > 20 ? 380 : backlog > 10 ? 520 : backlog > 5 ? 800 : 1200
  const jitter = base * (0.7 + Math.random() * 0.6) // 70% - 130%
  spawnTimeout.value = window.setTimeout(() => {
    processDanmakuQueue()

    // 队列为空就按轮询补一条，确保持续输出
    if (danmakuQueue.value.length === 0) enqueueNextRoundRobin()

    scheduleNextSpawn()
  }, jitter)
}

const startDanmaku = () => {
  if (spawnTimeout.value) return
  scheduleNextSpawn()
}

const stopDanmaku = () => {
  if (spawnTimeout.value) {
    clearTimeout(spawnTimeout.value)
    spawnTimeout.value = null
  }
}

// 监听评论变化
watch(() => props.comments, (newComments, oldComments) => {
  console.log('Comments changed:', { 
    oldCount: oldComments?.length || 0, 
    newCount: newComments.length
  })
  
  const oldIds = new Set((oldComments || []).map(c => String(c.id)))
  const trulyNew = newComments.filter(c => !oldIds.has(String(c.id)))
  
  // 新增评论优先进入队列，由调度器平滑发射
  trulyNew.forEach(comment => {
    const id = String(comment.id)
    if (!danmakuQueue.value.some(q => String(q.id) === id)) {
      danmakuQueue.value.push(comment)
    }
  })

  // 移除已删除评论的冷却记录
  const newIds = new Set(newComments.map(c => String(c.id)))
  for (const key of Array.from(lastShownAt.value.keys())) {
    if (!newIds.has(key)) lastShownAt.value.delete(key)
  }

  // 防止 rrIndex 越界
  if (newComments.length > 0) rrIndex.value = rrIndex.value % newComments.length
}, { deep: true })

// 监听激活状态
watch(() => props.isActive, (active) => {
  console.log('🔄 isActive changed:', active)
  if (active) {
    displayedComments.value.clear()
    danmakuQueue.value = []
    activeComments.value = []
    lanes.value = []
    nextLane.value = 0
    bgManager.randomize() // 🎮 刷新随机背景
    // 将现有评论批量放入队列，交给调度器匀速发射
    props.comments.forEach(c => danmakuQueue.value.push(c))
    startDanmaku()
  } else {
    // 非激活时完全停止并清除所有弹幕
    console.log('❌ Component deactivated, stopping and clearing all danmaku')
    stopDanmaku()
    activeComments.value = []
    danmakuQueue.value = []
    displayedComments.value.clear()
    lanes.value = []
  }
}, { immediate: true })

// ESCkey closes the emoji picker
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && showEmojiPicker.value) {
    closeEmojiPicker()
  }
  if (e.key === 'Escape' && showModal.value) {
    closeModal()
  }
}

onMounted(() => {
  console.log('🎮 DanmakuCommentWall mounted:', { 
    isActive: props.isActive, 
    commentsCount: props.comments.length,
    comments: props.comments,
    hideInputBar: props.hideInputBar
  })

  // 立即启动弹幕系统
  setTimeout(() => {
    console.log('🚀 Starting danmaku system on mount...')
    startDanmaku()
  }, 100)
  // 初始化与监听显示区域尺寸
  nextTick(() => {
    if (displayRef.value) {
      containerWidth.value = displayRef.value.clientWidth
      try {
        resizeObserver = new ResizeObserver(entries => {
          for (const entry of entries) {
            if (entry.contentRect) {
              containerWidth.value = Math.max(0, Math.floor(entry.contentRect.width))
            }
          }
        })
        resizeObserver.observe(displayRef.value)
      } catch {}
    }
  })
  
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  console.log('🧹 DanmakuCommentWall unmounting - complete cleanup')
  stopDanmaku()
  // 彻底清除所有弹幕状态
  activeComments.value = []
  danmakuQueue.value = []
  displayedComments.value.clear()
  lanes.value = []
  document.removeEventListener('keydown', handleKeydown)
  if (resizeObserver && displayRef.value) {
    try { resizeObserver.unobserve(displayRef.value) } catch {}
  }
  resizeObserver = null
})

onBeforeUnmount(() => {
  console.log('🚨 DanmakuCommentWall before unmount - emergency cleanup')
  // 紧急清理，确保没有残留的动画或定时器
  stopDanmaku()
  activeComments.value.splice(0)
  danmakuQueue.value.splice(0)
  displayedComments.value.clear()
  lanes.value.splice(0)
})

// Modal helpers
const closeModal = () => {
  showModal.value = false
  modalComment.value = null
  // 关闭弹窗时恢复最近一次点击的弹幕
  try {
    if (lastClickedAnimationId.value != null) {
      const el = document.querySelector(`[data-animation-id="${lastClickedAnimationId.value}"]`) as HTMLElement | null
      if (el) {
        const pStart = parseFloat(el.dataset.pStart || '0') || 0
        const accum = parseFloat(el.dataset.pAccum || '0') || 0
        if (pStart > 0) {
          const now = performance.now()
          el.dataset.pAccum = String(accum + Math.max(0, now - pStart))
        }
        delete el.dataset.pStart
        delete el.dataset.paused
        // 恢复样式到正常流
        el.style.transition = ''
        el.style.filter = ''
        el.style.zIndex = ''
      }
    }
  } catch {}
}

const copyComment = async () => {
  if (!modalComment.value) return
  try {
    await navigator.clipboard.writeText(modalComment.value.text)
  } catch (e) {
    // noop
  }
}

const formatTime = (ts?: number) => {
  if (!ts) return ''
  const now = Date.now()
  const diff = Math.max(0, now - ts)
  const sec = Math.floor(diff / 1000)
  if (sec < 10) return 'just now'
  if (sec < 60) return `${sec}s ago`
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const d = Math.floor(hr / 24)
  return `${d}d ago`
}
</script>

<style scoped>
.danmaku-comment-wall {
  position: relative;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 16px;
  backdrop-filter: blur(5px);
  overflow: hidden;
  height: 100%;
}

/* 弹幕显示区域 - 增强版确保背景和弹幕都正确显示 */
.danmaku-display {
  position: relative; /* 作为绝对定位弹幕的定位上下文 */
  height: 300px;
  /* 确保弹幕动画可见，不被裁剪 */
  overflow: visible !important;
  /* 背景样式由 wallpaperStyle 内联控制 */
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  border-radius: 16px 16px 0 0;
  /* 强制显示 */
  display: block !important;
  visibility: visible !important;
  /* 超高优先级 z-index */
  z-index: 1000 !important;
  isolation: isolate;
  /* 移除任何可能阻挡背景的效果 */
  backdrop-filter: none !important;
  filter: none !important;
  /* 确保边界不影响内容 */
  box-sizing: border-box;
  /* 创建弹幕渲染上下文 */
  contain: layout style;
  /* 确保变换正确应用 */
  transform-style: preserve-3d;
}

/* 当父组件隐藏时，确保弹幕完全隐藏 */
.danmaku-comment-wall[style*="display: none"] .danmaku-display,
.danmaku-comment-wall[style*="display: none"] .danmaku-item {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
}

.danmaku-display::before {
  /* DISABLE overlay to prevent blocking danmaku visibility */
  display: none;
}

.danmaku-display > * {
  position: relative;
  z-index: 2;
}

.danmaku-display.solo-mode {
  height: 200px;
}

/* 空状态样式 */
.empty-danmaku-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  z-index: 1;
  pointer-events: none;
  padding: 20px;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 15px;
  opacity: 0.9;
  animation: gentle-pulse 3s ease-in-out infinite;
  filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.3));
}

.empty-danmaku-state p {
  margin: 0;
  font-size: 1.1rem;
  margin-bottom: 20px;
  font-weight: 500;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.floating-emoji {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.float-emoji {
  font-size: 1.2rem;
  animation: float-gentle 3s ease-in-out infinite;
}

.float-emoji:nth-child(1) { animation-delay: 0s; }
.float-emoji:nth-child(2) { animation-delay: 0.5s; }
.float-emoji:nth-child(3) { animation-delay: 1s; }
.float-emoji:nth-child(4) { animation-delay: 1.5s; }

/* interaction lives in the Bubble component; base styles are not repeated here to avoid conflicts */

.danmaku-item.interactive-danmaku {
  position: relative;
  overflow: visible;
}

.danmaku-display :deep(.danmaku-item:hover) {
  /* transform: translateY(-4px) scale(1.08) !important; */
  filter: brightness(1.4) saturate(1.4) !important;
  box-shadow: 
    0 12px 35px rgba(0, 0, 0, 0.3), 
    0 0 25px rgba(78, 205, 196, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  z-index: 999 !important;
}

.danmaku-display :deep(.danmaku-item.new-comment-glow) {
  animation: new-comment-pulse 1.5s ease-in-out;
  box-shadow: 
    0 0 25px rgba(255, 107, 107, 0.8), 
    0 0 40px rgba(255, 193, 7, 0.6),
    0 4px 20px rgba(0, 0, 0, 0.15);
  background: linear-gradient(135deg, 
    rgba(255, 107, 107, 0.4) 0%, 
    rgba(255, 193, 7, 0.3) 50%, 
    rgba(255, 235, 59, 0.4) 100%);
}

.danmaku-display :deep(.danmaku-item.combo-effect) {
  animation: combo-shake 0.3s ease-in-out;
}

.danmaku-display :deep(.danmaku-item.clicked-effect) {
  animation: click-bounce 0.6s ease-out;
}

/* 多行弹幕特效 */
.danmaku-display :deep(.danmaku-item.multi-line-danmaku) {
  border-left: 3px solid rgba(78, 205, 196, 0.6);
  padding-left: 12px;
  font-weight: 600;
}

.danmaku-display :deep(.danmaku-item.multi-line-danmaku::before) {
  content: '';
  position: absolute;
  left: -6px;
  top: 50%;
  width: 6px;
  height: 6px;
  background: rgba(78, 205, 196, 0.8);
  border-radius: 50%;
  /* transform: translateY(-50%); */
  animation: multi-line-pulse 1.5s ease-in-out infinite;
}

@keyframes multi-line-pulse {
  0%, 100% { 
    transform: translateY(-50%) scale(1);
    opacity: 0.6;
  }
  50% { 
    transform: translateY(-50%) scale(1.3);
    opacity: 1;
  }
}

.danmaku-trail {
  position: absolute;
  top: 0;
  left: -10px;
  right: -10px;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  border-radius: 25px;
  opacity: 0;
  animation: trail-sweep 2s ease-in-out infinite;
  pointer-events: none;
}

.danmaku-display :deep(.danmaku-item.praise) {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.9), rgba(255, 142, 83, 0.9));
  color: white;
  box-shadow: 0 0 15px rgba(255, 107, 107, 0.4), 0 4px 15px rgba(0, 0, 0, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.danmaku-display :deep(.danmaku-item.suggestion) {
  background: linear-gradient(135deg, rgba(78, 205, 196, 0.9), rgba(68, 160, 141, 0.9));
  color: white;
  box-shadow: 0 0 15px rgba(78, 205, 196, 0.4), 0 4px 15px rgba(0, 0, 0, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.danmaku-display :deep(.danmaku-item.cheer) {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.9), rgba(255, 179, 0, 0.9));
  color: #2d3748;
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.4), 0 4px 15px rgba(0, 0, 0, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.4);
  font-weight: 600;
}

.comment-user {
  font-weight: bold;
  margin-right: 6px;
}

.comment-text {
  margin-right: 6px;
}

.comment-emoji {
  font-size: 1rem;
}

/* 小头像样式（弹幕内） */
.comment-avatar {
  display: inline-flex;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 6px;
  vertical-align: middle;
  border: 2px solid rgba(255,255,255,0.5);
  box-shadow: 0 0 8px rgba(255,255,255,0.25);
}
.comment-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 评论输入栏 */
.comment-input-bar {
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.input-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.comment-input {
  flex: 1;
  padding: 14px 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 25px;
  background: rgba(255, 255, 255, 0.12);
  color: white;
  font-size: 0.95rem;
  font-weight: 500;
  backdrop-filter: blur(15px);
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.comment-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
  font-weight: 400;
}

.comment-input:focus {
  outline: none;
  border-color: rgba(78, 205, 196, 0.8);
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.2), 0 6px 15px rgba(0, 0, 0, 0.15);
  transform: scale(1.02);
}

.quick-emojis {
  display: flex;
  gap: 4px;
}

.emoji-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.emoji-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: scale(1.1);
}

.send-btn {
  background: linear-gradient(135deg, #ff6b6b, #ff8e53);
  border: none;
  color: white;
  padding: 12px 20px;
  border-radius: 22px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.5), 0 0 15px rgba(255, 255, 255, 0.2);
  filter: brightness(1.1);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.comment-types {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.type-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.8);
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s ease;
}

.type-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.type-btn.active { display: none; }

/* 统计信息 */
.comment-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0 0 16px 16px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 1.2rem;
  font-weight: bold;
  color: #4ecdc4;
}

.stat-label {
  display: block;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 2px;
}

/* Modal styles */
.danmaku-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.danmaku-modal {
  width: min(640px, 92vw);
  max-height: 80vh;
  background: rgba(30, 41, 59, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  color: #fff;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35);
  padding: 16px 16px 12px;
  display: flex;
  flex-direction: column;
}

.modal-close {
  position: absolute;
  top: 10px;
  right: 14px;
  background: transparent;
  border: none;
  color: rgba(255,255,255,0.8);
  font-size: 1rem;
  cursor: pointer;
}

.modal-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 10px;
}

.modal-user { font-weight: 700; }
.modal-time { color: rgba(255,255,255,0.6); font-size: 0.85rem; }

.modal-content {
  overflow: auto;
  padding: 8px 2px 8px 0;
}

.modal-text { white-space: pre-wrap; line-height: 1.6; }

.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.copy-btn {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  color: #fff;
  border: none;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
}

/* 弹幕动画 */
@keyframes danmaku-slide {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-1000px);
  }
}

@keyframes new-comment-pulse {
  0% { 
    box-shadow: 
      0 0 20px rgba(255, 107, 107, 0.6), 
      0 0 30px rgba(255, 193, 7, 0.4),
      0 4px 20px rgba(0, 0, 0, 0.15);
    transform: scale(1);
    filter: brightness(1) saturate(1) hue-rotate(0deg);
  }
  25% { 
    box-shadow: 
      0 0 35px rgba(255, 107, 107, 0.9), 
      0 0 45px rgba(255, 193, 7, 0.7),
      0 6px 25px rgba(0, 0, 0, 0.2);
    transform: scale(1.05);
    filter: brightness(1.15) saturate(1.3) hue-rotate(15deg);
  }
  50% { 
    box-shadow: 
      0 0 45px rgba(255, 107, 107, 1.2), 
      0 0 60px rgba(255, 193, 7, 1),
      0 8px 30px rgba(0, 0, 0, 0.25);
    transform: scale(1.1);
    filter: brightness(1.3) saturate(1.5) hue-rotate(30deg);
  }
  75% { 
    box-shadow: 
      0 0 35px rgba(255, 107, 107, 0.9), 
      0 0 45px rgba(255, 193, 7, 0.7),
      0 6px 25px rgba(0, 0, 0, 0.2);
    transform: scale(1.05);
    filter: brightness(1.15) saturate(1.3) hue-rotate(15deg);
  }
  100% { 
    box-shadow: 
      0 0 20px rgba(255, 107, 107, 0.6), 
      0 0 30px rgba(255, 193, 7, 0.4),
      0 4px 20px rgba(0, 0, 0, 0.15);
    transform: scale(1);
    filter: brightness(1) saturate(1) hue-rotate(0deg);
  }
}

@keyframes combo-shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
  20%, 40%, 60%, 80% { transform: translateX(2px); }
}

@keyframes click-bounce {
  0% { transform: scale(1); }
  50% { transform: scale(1.15); }
  100% { transform: scale(1); }
}

@keyframes ripple-expand {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
}

@keyframes combo-bounce {
  0% {
    transform: translateY(0) scale(0.8);
    opacity: 0;
  }
  50% {
    transform: translateY(-15px) scale(1.2);
    opacity: 1;
  }
  100% {
    transform: translateY(-25px) scale(0.9);
    opacity: 0;
  }
}

@keyframes trail-sweep {
  0%, 100% { opacity: 0; transform: translateX(-20px); }
  50% { opacity: 0.3; transform: translateX(20px); }
}

@keyframes gentle-pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}

@keyframes float-gentle {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* 游戏化交互特效 */
.click-ripple {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.8) 0%, rgba(78, 205, 196, 0.4) 70%, transparent 100%);
  transform: scale(0);
  animation: ripple-expand 0.6s ease-out;
  pointer-events: none;
  width: 20px;
  height: 20px;
  top: 50%;
  left: 50%;
  margin: -10px 0 0 -10px;
}

.combo-counter {
  position: absolute;
  top: -20px;
  right: -10px;
  color: #ff6b6b;
  font-weight: bold;
  font-size: 0.8rem;
  text-shadow: 0 0 4px rgba(255, 107, 107, 0.8);
  animation: combo-bounce 0.6s ease-out;
  pointer-events: none;
  z-index: 100;
}

/* 高级游戏化动画效果 */
@keyframes gaming-glow {
  0% {
    box-shadow: 0 0 5px rgba(78, 205, 196, 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(78, 205, 196, 0.8), 0 0 30px rgba(78, 205, 196, 0.4);
  }
  100% {
    box-shadow: 0 0 5px rgba(78, 205, 196, 0.3);
  }
}

@keyframes power-up-effect {
  0% {
    transform: scale(1) rotate(0deg);
    filter: hue-rotate(0deg);
  }
  25% {
    transform: scale(1.1) rotate(2deg);
    filter: hue-rotate(90deg);
  }
  50% {
    transform: scale(1.15) rotate(-2deg);
    filter: hue-rotate(180deg);
  }
  75% {
    transform: scale(1.1) rotate(1deg);
    filter: hue-rotate(270deg);
  }
  100% {
    transform: scale(1) rotate(0deg);
    filter: hue-rotate(360deg);
  }
}

@keyframes spark-trail {
  0% {
    opacity: 0;
    transform: translateX(-100%) scale(0.5);
  }
  50% {
    opacity: 1;
    transform: translateX(0%) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateX(100%) scale(0.5);
  }
}

/* 增强的弹幕特效 */
.danmaku-display :deep(.danmaku-item::before) {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  border-radius: 27px;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.danmaku-display :deep(.danmaku-item:hover::before) {
  opacity: 1;
  animation: spark-trail 1.5s ease-in-out infinite;
}

.danmaku-display :deep(.danmaku-item.new-comment-glow::after) {
  content: '✨';
  position: absolute;
  top: -10px;
  right: -10px;
  font-size: 0.8rem;
  animation: power-up-effect 2s ease-in-out infinite;
  pointer-events: none;
}

/* Emoji Picker 样式tuning */
.emoji-picker-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(5px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.emoji-picker-wrapper {
  background: rgba(30, 41, 59, 0.95);
  border-radius: 16px;
  padding: 8px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

/* responsive layout */
@media (max-width: 768px) {
  .danmaku-display {
    height: 250px;
  }
  
  .danmaku-display.solo-mode {
    height: 150px;
  }
  
  .input-container {
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .comment-input {
    min-width: 200px;
  }
  
  .comment-types {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .type-btn {
    font-size: 0.8rem;
    padding: 6px 12px;
  }
  
  .comment-stats {
    gap: 20px;
  }
}

@media (max-width: 480px) {
  .danmaku-display {
    height: 200px;
  }
  
  .comment-input-bar {
    padding: 12px;
  }
  
  .danmaku-item {
    font-size: 0.8rem;
    padding: 4px 8px;
  }
  
  .danmaku-trail {
    animation-duration: 1.5s;
  }
  
  .combo-counter {
    font-size: 0.7rem;
    top: -15px;
    right: -8px;
  }
  
  .danmaku-item.new-comment-glow::after {
    font-size: 0.6rem;
    top: -8px;
    right: -8px;
  }
}

/* 移动端触摸反馈tuning */
@media (max-width: 768px) {
  .danmaku-item {
    transition: all 0.2s ease;
  }
  
  .danmaku-item:active {
    /* transform: scale(0.95); */
    filter: brightness(1.3);
  }
  
  .click-ripple {
    width: 30px;
    height: 30px;
    margin: -15px 0 0 -15px;
  }
  
  .emoji-picker-wrapper {
    max-width: 90vw;
    max-height: 70vh;
    overflow: auto;
  }
}

/* 高性能动画tuning */
@media (prefers-reduced-motion: reduce) {
  .danmaku-item,
  .click-ripple,
  .combo-counter,
  .danmaku-trail {
    animation-duration: 0.1s;
  }
  
  /* .danmaku-item:hover {
    transform: none;
  } */
  
  .danmaku-item::before,
  .danmaku-item::after {
    animation: none;
  }
}

/* 深色模式tuning */
@media (prefers-color-scheme: dark) {
  .danmaku-item {
    backdrop-filter: blur(15px);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .click-ripple {
    background: radial-gradient(circle, rgba(78, 205, 196, 0.8) 0%, rgba(255, 255, 255, 0.3) 70%, transparent 100%);
  }
  
  .emoji-picker-wrapper {
    background: rgba(15, 23, 42, 0.95);
  }
}
</style>
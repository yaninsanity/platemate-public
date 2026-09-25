<template>
  <div class="main-comment-wall">

  <!-- Comments Section with toggle (moved up for diary-first flow) -->
    <div class="comments-section">
      <!-- 游戏化通知栏 - 只在wall模式显示 -->
      <ScrollNotice
        v-show="commentMode === 'wall'"
        :messages="gamifiedNoticeMessages"
        class="gaming-notice-bar"
      />
      
      <!-- 游戏化标题栏 -->
      <div class="gaming-comments-header">
        <div class="battle-zone-title">
          <v-icon size="20" class="battle-icon animated-icon">mdi-sword-cross</v-icon>
          <h3 class="zone-title"></h3>
          <div class="comment-counter">
            <span class="counter-number">{{ comments.length }}</span>
            <span class="counter-label">comments</span>
          </div>
        </div>
        <v-btn
          @click="toggleMode"
          :class="['mode-pill', commentMode === 'wall' ? 'wall-mode' : 'list-mode']"
          variant="elevated"
        >
          <v-icon 
            start 
            size="16" 
            class="mode-icon"
          >
            {{ commentMode === 'wall' ? 'mdi-target' : 'mdi-view-list' }}
          </v-icon>
          <span class="mode-text">
            {{ commentMode === 'wall' ? 'Change Layout' : 'Change Layout' }}
          </span>
          <div class="mode-glow"></div>
        </v-btn>
      </div>

      <!-- Toggle content with stable height -->
      <div class="comments-content" @touchstart.passive="onTouchStart" @touchend.passive="onTouchEnd">
        <!-- v-if rather than v-show, so the component really unmounts -->
        <div v-if="commentMode === 'wall'" class="battle-comment-wall">
          <DanmakuCommentWall
            :comments="danmakuComments"
            :is-active="true"
            :solo-mode="soloMode"
            :hide-input-bar="true"
            @add-comment="handleDanmakuComment"
          />
        </div>
        <div v-if="commentMode === 'list'" class="comments-list scroll-area">
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-header">
              <v-avatar size="28">
                <v-img :src="getAvatarFor(comment.username)" />
              </v-avatar>
              <div class="comment-author">{{ comment.username }}</div>
              <div class="comment-time">{{ formatCommentTime(comment.timestamp) }}</div>
            </div>
            <div class="comment-text">{{ comment.text }}</div>
          </div>
        </div>
      </div>

      <!-- Add New Comment - 游戏化战斗输入 -->
      <div class="battle-input-section">
        <div class="battle-input-header">
          <div class="weapon-icon">⚔️</div>
          <span class="input-title">Post Your Comment</span>
          <div class="energy-bar">
            <div class="energy-fill" :style="{ width: Math.min(100, (newCommentText.length / 50) * 100) + '%' }"></div>
          </div>
        </div>
        <div class="battle-input-container">
          <v-avatar size="36" class="warrior-avatar glowing-avatar">
            <v-img :src="currentUserAvatar" />
            <div class="avatar-ring"></div>
          </v-avatar>
          <v-textarea
            v-model="newCommentText"
            :placeholder="getBattlePlaceholder()"
            variant="outlined"
            rows="2"
            max-rows="3"
            class="battle-input"
            hide-details
            ref="commentTextareaRef"
            maxlength="50"
          />
          <v-btn 
            icon 
            variant="text" 
            class="spell-toggle magical-btn" 
            @click="toggleEmojiPicker" 
            :aria-pressed="showEmojiPicker"
          >
            <v-icon class="magic-icon">mdi-auto-fix</v-icon>
            <div class="magic-sparkles"></div>
          </v-btn>
        </div>
        <div class="battle-actions">
          <div class="combat-stats">
            <span class="char-counter">{{ newCommentText.length }}/50</span>
            <span class="power-level" :class="getPowerLevel()">{{ getPowerText() }}</span>
          </div>
          <v-btn
            variant="elevated"
            class="launch-btn epic-button"
            size="small"
            @click="submit"
            :disabled="!newCommentText.trim()"
          >
            <v-icon start size="16" class="launch-icon">mdi-rocket-launch</v-icon>
            <span class="btn-text">Post</span>
            <div class="btn-trail"></div>
            <div class="btn-glow"></div>
          </v-btn>
        </div>
      </div>
      <!-- Emoji Picker Overlay -->
      <div v-if="showEmojiPicker" class="emoji-picker-overlay" @click="closeEmojiPicker">
        <div class="emoji-picker-wrapper" @click.stop>
          <EmojiPicker @select="onEmojiSelect" theme="dark" />
        </div>
      </div>
    </div>

    <!-- Memory Posts Section -->
    <div v-if="roundSummary" class="memory-posts-section">
      <div class="memory-post-card">
        <div class="post-header">
          <v-icon size="18" color="orange">mdi-memory</v-icon>
          <span class="post-label">Memory</span>
        </div>
        <div class="post-content">{{ roundSummary }}</div>
      </div>
    </div>

    <!-- Compact VS Battle Preview -->
    <!-- <div class="compact-vs-preview">
      <div class="vs-preview-header">
        <span class="battle-title">Battle Preview</span>
      </div>
      <div class="mini-vs-container">
        <div class="mini-fighter">
          <v-avatar size="36" class="mini-avatar">
            <v-img :src="currentUserAvatar" />
          </v-avatar>
          <div class="mini-info">
            <span class="mini-name">{{ userUsername || 'You' }}</span>
            <span class="mini-count">{{ userEntriesCount }} dishes</span>
          </div>
        </div>

        <div class="mini-vs vs-pulse">VS</div>

        <div class="mini-fighter">
          <v-avatar size="36" class="mini-avatar">
            <v-img :src="partnerAvatar" />
          </v-avatar>
          <div class="mini-info">
            <span class="mini-name">{{ partnerUsername || 'Partner' }}</span>
            <span class="mini-count">{{ partnerEntriesCount }} dishes</span>
          </div>
        </div>
      </div>
    </div> -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import DanmakuCommentWall from '@/components/DanmakuCommentWall.vue'
import ScrollNotice from '@/components/ScrollNotice.vue'
import EmojiPicker from 'vue3-emoji-picker'
import 'vue3-emoji-picker/css'

interface SimpleComment {
  id: string | number
  username: string
  text: string
  timestamp: number
  avatar?: string
}

const props = defineProps<{
  comments: SimpleComment[]
  currentUserAvatar: string
  partnerAvatar: string
  userUsername?: string | null
  partnerUsername?: string | null
  userEntriesCount: number
  partnerEntriesCount: number
  soloMode: boolean
  userTopSummary?: string | null
  partnerTopSummary?: string | null
  roundSummary?: string | null
}>()

const emit = defineEmits<{
  addComment: [text: string]
}>()

const newCommentText = ref('')
const commentMode = ref<'wall' | 'list'>('wall')
// Resolve avatar for a username (fallback to known users)
const getAvatarFor = (username?: string | null): string => {
  if (!username) return props.currentUserAvatar
  if (props.userUsername && username === props.userUsername) return props.currentUserAvatar
  if (props.partnerUsername && username === props.partnerUsername) return props.partnerAvatar
  // If comments already carry avatar, prefer that on mapping below
  return props.currentUserAvatar
}

const toggleMode = () => {
  commentMode.value = commentMode.value === 'wall' ? 'list' : 'wall'
}

const danmakuComments = computed(() => props.comments.map(c => ({
  id: String(c.id),
  username: c.username,
  text: c.text,
  timestamp: c.timestamp,
  avatar: c.avatar || getAvatarFor(c.username)
})))

// Forward add-comment from wall to parent
const handleDanmakuComment = (text: string, _type?: string) => {
  emit('addComment', text)
}

// Emoji picker state
const showEmojiPicker = ref(false)
const commentTextareaRef = ref<any>(null)

const toggleEmojiPicker = () => {
  showEmojiPicker.value = !showEmojiPicker.value
}

const closeEmojiPicker = () => {
  showEmojiPicker.value = false
}

const onEmojiSelect = (emoji: any) => {
  const el = (commentTextareaRef.value?.$el as HTMLElement)?.querySelector('textarea') as HTMLTextAreaElement | null
  const emojiChar = emoji.i || emoji.n || emoji.emoji || emoji || ''
  if (!emojiChar) {
    console.warn('⚠️ No emoji character found in:', emoji)
    return
  }
  
  if (el) {
    const start = el.selectionStart || 0
    const end = el.selectionEnd || 0
    const val = newCommentText.value
    newCommentText.value = val.slice(0, start) + emojiChar + val.slice(end)
    nextTick(() => {
      el.focus()
      const newPos = start + String(emojiChar).length
      el.setSelectionRange(newPos, newPos)
    })
  } else {
    newCommentText.value += emojiChar
  }
  showEmojiPicker.value = false
}

const submit = () => {
  if (!newCommentText.value.trim()) return
  emit('addComment', newCommentText.value.trim())
  newCommentText.value = ''
}

// 游戏化功能函数
const getBattlePlaceholder = () => {
  const placeholders = [
    'Ready your battle cry... ⚔️',
    'What\'s your next move, warrior? 🛡️',
    'Cast your spell of words... ✨',
    'Fire your comment projectile! 🚀',
    'Charge into battle with words! ⚡',
  ]
  return placeholders[Math.floor(Math.random() * placeholders.length)]
}

const getPowerLevel = () => {
  const length = newCommentText.value.length
  if (length < 10) return 'power-low'
  if (length < 25) return 'power-medium'
  if (length < 40) return 'power-high'
  return 'power-max'
}

const getPowerText = () => {
  const length = newCommentText.value.length
  if (length < 10) return 'Gathering Power...'
  if (length < 25) return 'Combat Ready!'
  if (length < 40) return 'Epic Strike!'
  return 'LEGENDARY!'
}

// (deduped above)

const formatCommentTime = (timestamp: number): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString('en-US')
}

// (removed) legacy noticeMessages; replaced by gamifiedNoticeMessages above the wall

// 游戏化通知消息 - 专门为弹幕墙设计
const gamifiedNoticeMessages = computed(() => [
  '⚔️ Battle Mode Active - Comments become flying projectiles!',
  '🚀 Quick fire: Short messages travel faster across the battlefield!',
  '💥 Combo System: Chain comments for epic visual effects!',
  '🎮 Pro tip: Click flying comments to view battle details!',
  '🌟 Achievement unlocked: Every comment counts towards victory!',
])

// Mobile swipe to switch modes
const touchStartX = ref(0)
const onTouchStart = (e: TouchEvent) => {
  touchStartX.value = e.changedTouches[0]?.clientX || 0
}
const onTouchEnd = (e: TouchEvent) => {
  const endX = e.changedTouches[0]?.clientX || 0
  const diff = endX - touchStartX.value
  // Swipe threshold
  if (Math.abs(diff) < 50) return
  if (diff < 0) {
    // Swipe left -> go to list
    commentMode.value = 'list'
  } else {
    // Swipe right -> back to wall
    commentMode.value = 'wall'
  }
}
</script>

<style scoped>
.gaming-notice-bar {
  margin-bottom: 8px !important;
  /* 确保不与弹幕区域叠加 */
  position: relative;
  z-index: 5;
  background: linear-gradient(135deg, rgba(255, 87, 34, 0.9), rgba(255, 152, 0, 0.9)) !important;
  border: 2px solid rgba(255, 193, 7, 0.6);
  box-shadow: 0 0 20px rgba(255, 152, 0, 0.3), inset 0 0 20px rgba(255, 255, 255, 0.1);
}

/* 游戏化标题栏 */
.gaming-comments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(13, 71, 161, 0.8), rgba(25, 118, 210, 0.8));
  border-radius: 12px;
  border: 2px solid rgba(33, 150, 243, 0.5);
  position: relative;
  overflow: hidden;
}

.gaming-comments-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: scan 3s ease-in-out infinite;
}

@keyframes scan {
  0% { left: -100%; }
  50% { left: 100%; }
  100% { left: 100%; }
}

.battle-zone-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-right: 12px;
}

.battle-icon {
  color: #ffc107;
  filter: drop-shadow(0 0 8px rgba(255, 193, 7, 0.6));
}

.animated-icon {
  animation: weaponGlow 2s ease-in-out infinite alternate;
}

@keyframes weaponGlow {
  0% { transform: rotate(-5deg) scale(1); filter: drop-shadow(0 0 8px rgba(255, 193, 7, 0.6)); }
  100% { transform: rotate(5deg) scale(1.1); filter: drop-shadow(0 0 12px rgba(255, 193, 7, 0.9)); }
}

.zone-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
  background: linear-gradient(45deg, #ffffff, #64b5f6);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.comment-counter {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(255, 193, 7, 0.2);
  border: 1px solid rgba(255, 193, 7, 0.4);
  border-radius: 8px;
  padding: 4px 8px;
  min-width: 50px;
}

.counter-number {
  font-size: 1.2rem;
  font-weight: 900;
  color: #ffc107;
  line-height: 1;
  text-shadow: 0 0 8px rgba(255, 193, 7, 0.8);
}

.counter-label {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 战斗模式切换器 */

.mode-pill {
  border-radius: 20px !important;
  position: relative;
  text-transform: none !important;
  font-weight: 700 !important;
  padding: 8px 16px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  overflow: hidden;
  border: 2px solid rgba(255, 193, 7, 0.4);
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.5);
}

.mode-pill.wall-mode {
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.3), rgba(255, 87, 34, 0.3)) !important;
  color: #ff5722 !important;
}

.mode-pill.list-mode {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.3), rgba(139, 195, 74, 0.3)) !important;
  color: #8bc34a !important;
}

.mode-pill:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}

.battle-mode-toggle :deep(.v-btn--active.wall-mode) {
  background: linear-gradient(135deg, #f44336, #ff5722) !important;
  color: white !important;
  box-shadow: 0 0 20px rgba(244, 67, 54, 0.6), inset 0 0 20px rgba(255, 255, 255, 0.1);
}

.battle-mode-toggle :deep(.v-btn--active.list-mode) {
  background: linear-gradient(135deg, #4caf50, #8bc34a) !important;
  color: white !important;
  box-shadow: 0 0 20px rgba(76, 175, 80, 0.6), inset 0 0 20px rgba(255, 255, 255, 0.1);
}

.mode-icon {
  filter: drop-shadow(0 0 4px currentColor);
}

.mode-text {
  font-size: 0.85rem;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.mode-glow {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.mode-pill:hover .mode-glow {
  left: 100%;
}

.main-comment-wall {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.memory-posts-section { margin-bottom: 12px; }
.memory-post-card { background: rgba(255, 167, 38, 0.1); border: 1px solid rgba(255, 167, 38, 0.3); border-radius: 12px; padding: 12px; margin-bottom: 8px; }
.post-header { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.post-label { font-size: 0.8rem; font-weight: 600; color: #ffa726; }
.post-content { font-size: 0.9rem; line-height: 1.4; color: rgba(255, 255, 255, 0.9); }

.compact-vs-preview { background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 10px; border: 1px solid rgba(255, 255, 255, 0.1); }
.vs-preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.battle-title { font-size: 0.8rem; font-weight: 600; color: rgba(255, 255, 255, 0.8); }
.mini-vs-container { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.mini-fighter { display: flex; align-items: center; gap: 8px; flex: 1; }
.mini-avatar { border: 1px solid rgba(255, 167, 38, 0.5); }
.mini-info { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.mini-name { font-size: 0.75rem; font-weight: 600; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mini-count { font-size: 0.65rem; color: rgba(255, 255, 255, 0.7); }
.mini-vs { font-size: 0.7rem; font-weight: 900; color: #ffa726; padding: 0 8px; }
.vs-pulse { text-shadow: 0 0 8px rgba(255, 167, 38, 0.7); animation: vsPulse 1.6s ease-in-out infinite; }
@keyframes vsPulse {
  0%, 100% { transform: scale(1); opacity: 0.9; }
  50% { transform: scale(1.1); opacity: 1; }
}

.comments-section { background: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 10px; border: 1px solid rgba(255, 255, 255, 0.1); }
.comments-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.comments-header h3 { margin: 0; font-size: 1rem; font-weight: 600; color: #81c784; }

.comments-list { 
  height: 100% !important;
  max-height: 340px; 
  overflow-y: auto; 
  padding-right: 8px; 
  z-index: 20;
  /* 确保 list 模式正常显示 */
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}
.scroll-area { height: 100%; overflow-y: auto; }
.comment-item { background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 12px; margin-bottom: 12px; border: 1px solid rgba(255, 255, 255, 0.1); transition: all 0.3s ease; }
.comment-item:hover { background: rgba(255, 255, 255, 0.08); transform: translateX(4px); }
.comment-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.comment-author { font-weight: 600; color: #4fc3f7; font-size: 0.9rem; }
.comment-time { font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); margin-left: auto; }
.comment-text { color: rgba(255, 255, 255, 0.9); line-height: 1.5; font-size: 0.9rem; }

/* 战斗输入区域样式 */
.battle-input-section {
  background: linear-gradient(135deg, rgba(63, 81, 181, 0.1), rgba(103, 58, 183, 0.1));
  border: 2px solid rgba(63, 81, 181, 0.3);
  border-radius: 16px;
  padding: 16px;
  position: relative;
  overflow: hidden;
}

.battle-input-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.05) 50%, transparent 70%);
  pointer-events: none;
}

.battle-input-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  position: relative;
}

.weapon-icon {
  font-size: 1.2rem;
  animation: weaponFloat 2s ease-in-out infinite;
  filter: drop-shadow(0 0 8px rgba(255, 193, 7, 0.6));
}

@keyframes weaponFloat {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-3px) rotate(5deg); }
}

.input-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: #7986cb;
  text-shadow: 0 0 8px rgba(121, 134, 203, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.energy-bar {
  flex: 1;
  height: 4px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 2px;
  overflow: hidden;
  margin-left: auto;
  width: 80px;
}

.energy-fill {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #8bc34a, #ffc107);
  border-radius: 2px;
  transition: width 0.3s ease;
  position: relative;
}

.energy-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
  animation: energyFlow 1.5s ease-in-out infinite;
}

@keyframes energyFlow {
  0% { left: -100%; }
  100% { left: 100%; }
}

.battle-input-container {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 12px;
}

.warrior-avatar {
  flex-shrink: 0;
  margin-top: 8px;
  position: relative;
}

.glowing-avatar {
  box-shadow: 0 0 20px rgba(33, 150, 243, 0.4);
  border: 2px solid rgba(33, 150, 243, 0.6);
}

.avatar-ring {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border: 2px solid transparent;
  border-radius: 50%;
  background: linear-gradient(45deg, #2196f3, #03a9f4, #00bcd4, #2196f3);
  background-size: 200% 200%;
  animation: ringRotate 3s linear infinite;
  z-index: -1;
}

@keyframes ringRotate {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.battle-input {
  flex: 1;
}

.battle-input :deep(.v-field) {
  background: rgba(0, 0, 0, 0.2) !important;
  border: 2px solid rgba(121, 134, 203, 0.3) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease !important;
}

.battle-input :deep(.v-field--focused) {
  border-color: rgba(121, 134, 203, 0.8) !important;
  box-shadow: 0 0 20px rgba(121, 134, 203, 0.3) !important;
  transform: translateY(-2px);
}

.spell-toggle {
  align-self: stretch;
  margin-top: 2px;
  position: relative;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 152, 0, 0.2)) !important;
  border: 1px solid rgba(255, 193, 7, 0.4) !important;
  border-radius: 8px !important;
}

.magical-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 0 15px rgba(255, 193, 7, 0.5);
}

.magic-icon {
  color: #ffc107;
  animation: magicSparkle 2s ease-in-out infinite;
}

@keyframes magicSparkle {
  0%, 100% { transform: rotate(0deg) scale(1); }
  25% { transform: rotate(-10deg) scale(1.1); }
  75% { transform: rotate(10deg) scale(1.1); }
}

.magic-sparkles {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 4px;
  height: 4px;
  background: #ffc107;
  border-radius: 50%;
  animation: sparkles 1.5s ease-in-out infinite;
}

@keyframes sparkles {
  0%, 100% { opacity: 0; transform: translate(-50%, -50%) scale(0); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
}

.battle-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.combat-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.char-counter {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 600;
}

.power-level {
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
}

.power-low { color: #9e9e9e; }
.power-medium { color: #2196f3; text-shadow: 0 0 8px rgba(33, 150, 243, 0.5); }
.power-high { color: #ff9800; text-shadow: 0 0 8px rgba(255, 152, 0, 0.5); }
.power-max { 
  color: #f44336; 
  text-shadow: 0 0 12px rgba(244, 67, 54, 0.8);
  animation: powerPulse 1s ease-in-out infinite;
}

@keyframes powerPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.launch-btn {
  position: relative;
  background: linear-gradient(135deg, #4caf50, #8bc34a) !important;
  color: white !important;
  border: 2px solid rgba(76, 175, 80, 0.5) !important;
  border-radius: 20px !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.epic-button:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4), 0 0 30px rgba(76, 175, 80, 0.3);
}

.epic-button:active {
  transform: translateY(-1px) scale(1.02);
}

.epic-button:disabled {
  background: linear-gradient(135deg, #616161, #757575) !important;
  border-color: rgba(97, 97, 97, 0.5) !important;
  opacity: 0.6;
}

.launch-icon {
  filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.5));
  animation: rocketPrepare 2s ease-in-out infinite;
}

@keyframes rocketPrepare {
  0%, 100% { transform: translateX(0px); }
  50% { transform: translateX(2px); }
}

.btn-text {
  font-size: 0.8rem;
  font-weight: 900;
  z-index: 2;
  position: relative;
}

.btn-trail {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.5s ease;
}

.epic-button:hover .btn-trail {
  left: 100%;
}

.btn-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #4caf50, #8bc34a, #66bb6a, #4caf50);
  background-size: 200% 200%;
  border-radius: 22px;
  z-index: -1;
  opacity: 0;
  animation: glowRotate 2s linear infinite;
  transition: opacity 0.3s ease;
}

.epic-button:hover .btn-glow {
  opacity: 0.7;
}

@keyframes glowRotate {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.add-comment-section {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 14px;
  padding: 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.comment-input-container { display: flex; gap: 16px; align-items: flex-start; margin-bottom: 16px; }
.user-avatar { flex-shrink: 0; margin-top: 8px; }
.comment-input { flex: 1; }
.comment-actions { display: flex; justify-content: flex-end; }

/* 稳定的评论视窗以避免切换时崩塌 */
.comments-content {
  height: 340px;
  position: relative;
  /* 确保弹幕不被裁剪，同时避免与通知栏叠加 */
  overflow: visible !important;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 6px;
  margin-bottom: 12px;
  /* 确保在通知栏之上但不阻挡弹幕 */
  z-index: 10;
}

.battle-comment-wall { 
  height: 100%; 
  width: 100%;
  position: relative;
  /* 确保墙体在内容区域之上 */
  z-index: 15;
}

/* 确保弹幕显示区域在最高层级且不被任何元素遮挡 */
.battle-comment-wall :deep(.danmaku-display) {
  height: 100% !important;
  width: 100% !important;
  /* 超高优先级 z-index */
  z-index: 1000 !important;
  position: relative !important;
  /* 确保边界不裁剪弹幕 */
  overflow: visible !important;
}

/* 超高优先级弹幕项目样式 */
.battle-comment-wall :deep(.danmaku-item) {
  /* 超高 z-index 确保始终在最顶层 */
  z-index: 999999 !important;
  pointer-events: auto !important;
  /* 确保定位正确 */
  position: absolute !important;
  /* 确保变换正常工作 */
  transform-style: preserve-3d !important;
  will-change: transform !important;
  /* 确保不被背景色遮挡 */
  background-color: rgba(78, 205, 196, 0.9) !important;
  /* 确保边框可见 */
  border: 2px solid rgba(255, 255, 255, 0.5) !important;
  /* 确保阴影可见 */
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3), 0 0 20px rgba(78, 205, 196, 0.4) !important;
}

/* 修复 list view 显示 */
.comments-list { 
  height: 100% !important;
  max-height: 340px; 
  overflow-y: auto; 
  padding-right: 8px; 
  z-index: 20;
}

/* Emoji Picker overlay */
.emoji-toggle { align-self: stretch; margin-top: 2px; }
.emoji-picker-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(5px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.emoji-picker-wrapper {
  background: rgba(30, 41, 59, 0.95);
  border-radius: 16px;
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35);
}

/* Playful mobile-friendly toggle */
.playful-toggle { border-radius: 999px; overflow: hidden; }
.toggle-pill { text-transform: none !important; font-weight: 800 !important; }
.playful-toggle :deep(.v-btn--active) { box-shadow: 0 6px 16px rgba(129, 199, 132, 0.35); }

@media (max-width: 768px) {
  .comments-content { height: 300px; }
}

@media (max-width: 480px) {
  .comments-content { height: 260px; }
}
</style>

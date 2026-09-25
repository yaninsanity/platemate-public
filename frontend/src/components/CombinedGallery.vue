<template>
  <div class="combined-gallery" ref="galleryRef">
    <!-- 若两边都没图 ➜ 占位 -->
    <div v-if="galleryEntries.length === 0" class="no-media">
      <div class="no-media-content">
        <div class="camera-animation">
          <v-icon size="48" color="grey-lighten-2" class="camera-icon">mdi-camera-plus</v-icon>
          <div class="camera-flash"></div>
        </div>
        <p class="text-grey-lighten-1 no-media-text">No photos yet – start cooking!</p>
        <div class="cooking-hint">
          <span class="hint-emoji">👨‍🍳</span>
          <span>Create memories together</span>
        </div>
      </div>
    </div>

    <!-- 有图时：增强的游戏化画廊 -->
    <div v-else class="gallery-container">
      <!-- 进度指示器 -->
      <!-- <div class="progress-container" v-if="galleryEntries.length > 1">
        <div 
          v-for="(_, idx) in galleryEntries" 
          :key="`progress-${idx}`"
          class="progress-dot"
          :class="{ 
            'active': idx === active,
            'completed': idx < active,
            'upcoming': idx > active
          }"
          @click="goToSlide(idx)"
        >
          <div class="dot-inner"></div>
          <div class="dot-glow"></div>
        </div>
      </div> -->

      <!-- 主画廊窗口 -->
      <v-window
        v-model="active"
        continuous
        class="gallery-window"
        :reverse="isReverse"
        @update:model-value="onSlideChange"
      >
        <v-window-item
          v-for="(entry, idx) in galleryEntries"
          :key="`slide-${entry.id || idx}`"
          class="window-item"
          :class="{ 
            'item-active': idx === active,
            'item-prev': idx === active - 1 || (active === 0 && idx === galleryEntries.length - 1),
            'item-next': idx === active + 1 || (active === galleryEntries.length - 1 && idx === 0)
          }"
        >
          <!-- 预渲染的 RoundGallery -->
          <RoundGallery 
            :entry="entry" 
            :interval="interval" 
            :is-active="idx === active"
            :preload-adjacent="Math.abs(idx - active) <= 1"
            :lazy-load="Math.abs(idx - active) > 2"
            class="round-gallery-instance"
            @media-loaded="onMediaLoaded(idx)"
            @interaction="onGalleryInteraction"
          />

          <!-- 增强的作者信息卡片 -->
          <div 
            class="author-chip-enhanced" 
            :class="{ 
              'chip-visible': showAuthorChip,
              'chip-single': galleryEntries.length === 1
            }"
          >
            <div class="author-avatar-container">
              <div class="avatar-wrapper">
                <img
                  v-if="getAvatar(entry)"
                  :src="getAvatar(entry)"
                  :alt="entry.author_username"
                  class="author-avatar-img"
                  loading="lazy"
                  @error="onAvatarError"
                  @load="onAvatarLoad"
                />
                <div v-else class="avatar-fallback">
                  {{ getInitials(entry.author_username || '') }}
                </div>
              </div>
              <div class="avatar-status-ring" v-if="entry.author_username && isUserOnline(entry.author_username)"></div>
            </div>
            <div class="author-info">
              <span class="author-name">{{ truncateUsername(entry.author_username || '') }}</span>
              <span class="photo-count">{{ entry.media?.length || 0 }} photo{{ (entry.media?.length || 0) !== 1 ? 's' : '' }}</span>
            </div>
            <div class="love-indicator" v-if="(entry as any).is_favorite">
              <v-icon size="16" color="red">mdi-heart</v-icon>
            </div>
          </div>

          <!-- 互动提示 -->
          <div class="interaction-hints" v-if="showHints && idx === active">
            <div class="hint-item swipe-hint" v-if="galleryEntries.length > 1">
              <v-icon size="16">mdi-gesture-swipe-horizontal</v-icon>
              <span>Swipe to explore</span>
            </div>
            <div class="hint-item tap-hint" v-if="entry.media && entry.media.length > 1">
              <v-icon size="16">mdi-gesture-tap</v-icon>
              <span>Tap to browse</span>
            </div>
          </div>

          <!-- 媒体计数器 -->
          <!-- <div class="media-counter" v-if="entry.media && entry.media.length > 1">
            <div class="counter-bg">
              <v-icon size="14" class="counter-icon">mdi-camera-burst</v-icon>
              <span class="counter-text">{{ getCurrentMediaIndex(idx) + 1 }}/{{ entry.media.length }}</span>
            </div>
          </div> -->
        </v-window-item>
      </v-window>

      <!-- 导航控制 -->
      <!-- <div class="navigation-controls" v-if="galleryEntries.length > 1">
        <button 
          class="nav-btn nav-prev"
          @click="previousSlide"
          :disabled="galleryEntries.length <= 1"
          aria-label="Previous photos"
        >
          <v-icon>mdi-chevron-left</v-icon>
          <div class="nav-btn-glow"></div>
        </button>
        
        <button 
          class="nav-btn nav-next"
          @click="nextSlide"
          :disabled="galleryEntries.length <= 1"
          aria-label="Next photos"
        >
          <v-icon>mdi-chevron-right</v-icon>
          <div class="nav-btn-glow"></div>
        </button>
      </div> -->

      <!-- 重新设计的作者快速切换 -->
      <div class="author-tabs-container" v-if="galleryEntries.length > 1">
        <div class="author-tabs">
          <div 
            v-for="(entry, idx) in galleryEntries"
            :key="`tab-${idx}`"
            class="author-tab"
            :class="{ 'tab-active': idx === active }"
            @click="goToSlide(idx)"
            :title="entry.author_username"
          >
            <div class="tab-avatar-wrapper">
              <img
                v-if="getAvatar(entry)"
                :src="getAvatar(entry)"
                :alt="entry.author_username"
                class="tab-avatar-img"
                loading="lazy"
                @error="onTabAvatarError"
              />
              <div v-else class="tab-fallback">
                {{ getInitials(entry.author_username || '') }}
              </div>
            </div>
            <div class="tab-indicator"></div>
            <div class="tab-tooltip">{{ entry.author_username }}</div>
          </div>
        </div>
      </div>

      <!-- 作者切换按钮（当空间不足时） -->
      <!-- <div class="author-switcher" v-if="galleryEntries.length > 1 && showCompactSwitcher">
        <button 
          class="switcher-btn"
          @click="showAuthorSelector = !showAuthorSelector"
          :aria-expanded="showAuthorSelector"
        >
          <div class="current-author-avatar">
            <img
              v-if="getAvatar(galleryEntries[active])"
              :src="getAvatar(galleryEntries[active])"
              :alt="galleryEntries[active].author_username"
              class="switcher-avatar-img"
            />
            <div v-else class="switcher-fallback">
              {{ getInitials(galleryEntries[active].author_username || '') }}
            </div>
          </div>
          <v-icon size="16" class="switcher-arrow">mdi-chevron-down</v-icon>
        </button> -->
        
        <!-- 下拉选择器 -->
        <!-- <div class="author-selector" v-if="showAuthorSelector">
          <div 
            v-for="(entry, idx) in galleryEntries"
            :key="`selector-${idx}`"
            class="selector-item"
            :class="{ 'selector-active': idx === active }"
            @click="selectAuthor(idx)"
          >
            <div class="selector-avatar">
              <img
                v-if="getAvatar(entry)"
                :src="getAvatar(entry)"
                :alt="entry.author_username"
                class="selector-avatar-img"
              />
              <div v-else class="selector-fallback">
                {{ getInitials(entry.author_username || '') }}
              </div>
            </div>
            <div class="selector-info">
              <span class="selector-name">{{ entry.author_username }}</span>
              <span class="selector-count">{{ entry.media?.length || 0 }} photos</span>
            </div>
          </div>
        </div>
      </div> -->
    </div>

    <!-- 加载状态覆盖 -->
    <div class="loading-overlay" v-if="isLoading">
      <div class="loading-content">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <p class="loading-text">Loading memories...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import RoundGallery from '@/components/RoundGallery.vue'
import { useUserStore } from '@/stores/userStore'
import type { MemoryEntry } from '@/models/couplememory'

/* ── Props ── */
const props = withDefaults(
  defineProps<{
    entries: (MemoryEntry | null)[]
    interval?: number
    autoPlay?: boolean
    showHints?: boolean
    preloadAll?: boolean
    compactMode?: boolean
  }>(),
  { 
    interval: 4000,
    autoPlay: false,
    showHints: true,
    preloadAll: false,
    compactMode: false
  }
)

/* ── Emits ── */
const emit = defineEmits<{
  'slide-change': [index: number, entry: MemoryEntry]
  'gallery-interaction': [type: string, data: any]
  'media-loaded': [index: number, entry: MemoryEntry]
}>()

/* ── 状态管理 ── */
const galleryRef = ref<HTMLElement>()
const active = ref(0)
const isReverse = ref(false)
const isLoading = ref(false)
const showAuthorChip = ref(true)
const showAuthorSelector = ref(false)
const showCompactSwitcher = ref(false)
const loadedSlides = ref<Set<number>>(new Set())
const currentMediaIndices = ref<Map<number, number>>(new Map())
const userStore = useUserStore()

/* ── computed ── */
const galleryEntries = computed(() =>
  props.entries.filter(
    (e): e is MemoryEntry =>
      !!e && !!e.media && e.media.length > 0
  )
)

/* ── 自动播放逻辑 ── */
let autoPlayTimer: NodeJS.Timeout | null = null

const startAutoPlay = () => {
  if (!props.autoPlay || galleryEntries.value.length <= 1) return
  
  stopAutoPlay()
  autoPlayTimer = setInterval(() => {
    nextSlide()
  }, props.interval * 2)
}

const stopAutoPlay = () => {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
}

/* ── 预加载逻辑 ── */
const preloadImages = async (entry: MemoryEntry) => {
  if (!entry.media) return
  
  const promises = entry.media.map(media => {
    return new Promise<void>((resolve) => {
      const img = new Image()
      img.onload = () => resolve()
      img.onerror = () => resolve()
      img.src = media.url || ''
    })
  })
  
  await Promise.allSettled(promises)
}

const preloadAdjacentSlides = async () => {
  const toPreload: number[] = []
  
  toPreload.push(active.value)
  
  if (galleryEntries.value.length > 1) {
    const prevIndex = active.value === 0 ? galleryEntries.value.length - 1 : active.value - 1
    const nextIndex = active.value === galleryEntries.value.length - 1 ? 0 : active.value + 1
    toPreload.push(prevIndex, nextIndex)
  }
  
  for (const index of toPreload) {
    if (!loadedSlides.value.has(index) && galleryEntries.value[index]) {
      await preloadImages(galleryEntries.value[index])
      loadedSlides.value.add(index)
    }
  }
}

/* ── 交互处理 ── */
const goToSlide = (index: number) => {
  if (index === active.value) return
  
  isReverse.value = index < active.value
  active.value = index
  showAuthorSelector.value = false
  
  if (navigator.vibrate) {
    navigator.vibrate(50)
  }
  
  emit('slide-change', index, galleryEntries.value[index])
}

const nextSlide = () => {
  const nextIndex = active.value === galleryEntries.value.length - 1 ? 0 : active.value + 1
  goToSlide(nextIndex)
}

const previousSlide = () => {
  const prevIndex = active.value === 0 ? galleryEntries.value.length - 1 : active.value - 1
  goToSlide(prevIndex)
}

const selectAuthor = (index: number) => {
  goToSlide(index)
}

const onSlideChange = (newIndex: number) => {
  if (newIndex !== active.value) {
    active.value = newIndex
    preloadAdjacentSlides()
    emit('slide-change', newIndex, galleryEntries.value[newIndex])
  }
}

const onMediaLoaded = (slideIndex: number) => {
  loadedSlides.value.add(slideIndex)
  emit('media-loaded', slideIndex, galleryEntries.value[slideIndex])
}

const onGalleryInteraction = (type: string, data: any) => {
  emit('gallery-interaction', type, data)
  
  if (props.showHints) {
    setTimeout(() => {
      showAuthorChip.value = false
    }, 2000)
  }
}

const getCurrentMediaIndex = (slideIndex: number): number => {
  return currentMediaIndices.value.get(slideIndex) || 0
}

/* ── 头像相关函数 ── */
function getAvatar(e: MemoryEntry): string {
  if ((e as any).author_avatar_url) return (e as any).author_avatar_url
  const name = e.author_username
  if (name === userStore.user?.username) return userStore.user?.avatar_url || ''
  return userStore.couple?.members?.find(m => m.username === name)?.avatar_url || ''
}

function getInitials(username: string): string {
  if (!username) return '?'
  const words = username.trim().split(/\s+/)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return username.slice(0, 2).toUpperCase()
}

function truncateUsername(username: string, maxLength: number = 12): string {
  if (!username || username.length <= maxLength) return username
  return username.slice(0, maxLength) + '...'
}

function isUserOnline(username: string): boolean {
  // 这里可以添加在线状态检查逻辑
  return username === userStore.user?.username
}

const onAvatarError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

const onAvatarLoad = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'block'
}

const onTabAvatarError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

/* ── 响应式处理 ── */
const checkCompactMode = () => {
  if (galleryRef.value) {
    const width = galleryRef.value.offsetWidth
    showCompactSwitcher.value = width < 400 || props.compactMode
  }
}

/* ── 键盘控制 ── */
const handleKeydown = (event: KeyboardEvent) => {
  if (!galleryRef.value?.contains(document.activeElement)) return
  
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      previousSlide()
      break
    case 'ArrowRight':
      event.preventDefault()
      nextSlide()
      break
    case ' ':
      event.preventDefault()
      if (props.autoPlay) {
        autoPlayTimer ? stopAutoPlay() : startAutoPlay()
      }
      break
    case 'Escape':
      showAuthorSelector.value = false
      break
  }
}

/* ── 触摸手势 ── */
let touchStartX = 0
let touchStartY = 0

// Not functioning at all, cannot detect touch start

// const handleTouchStart = (event: TouchEvent) => {
//   touchStartX = event.touches[0].clientX
//   touchStartY = event.touches[0].clientY
// }

// const handleTouchEnd = (event: TouchEvent) => {
//   const touchEndX = event.changedTouches[0].clientX
//   const touchEndY = event.changedTouches[0].clientY
//   const deltaX = touchEndX - touchStartX
//   const deltaY = touchEndY - touchStartY
//   if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
//     if (deltaX > 0) {
//       previousSlide()
//     } else {
//       nextSlide()
//     }
//   }
// }

/* ── 点击外部关闭选择器 ── */
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement
  if (!target.closest('.author-switcher')) {
    showAuthorSelector.value = false
  }
}

/* ── 生命周期 ── */
watch(galleryEntries, async (newEntries) => {
  if (newEntries.length > 0) {
    isLoading.value = true
    active.value = 0
    loadedSlides.value.clear()
    
    await nextTick()
    await preloadAdjacentSlides()
    checkCompactMode()
    
    isLoading.value = false
    
    if (props.autoPlay) {
      startAutoPlay()
    }
  }
}, { immediate: true })

watch(active, () => {
  preloadAdjacentSlides()
})

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('resize', checkCompactMode)
  
  // if (galleryRef.value) {
  //   galleryRef.value.addEventListener('touchstart', handleTouchStart, { passive: true })
  //   galleryRef.value.addEventListener('touchend', handleTouchEnd, { passive: true })
  // }
  
  checkCompactMode()
  
  if (props.preloadAll) {
    galleryEntries.value.forEach((entry, index) => {
      preloadImages(entry).then(() => {
        loadedSlides.value.add(index)
      })
    })
  }
})

onUnmounted(() => {
  stopAutoPlay()
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('resize', checkCompactMode)
  
  // if (galleryRef.value) {
  //   galleryRef.value.removeEventListener('touchstart', handleTouchStart)
  //   galleryRef.value.removeEventListener('touchend', handleTouchEnd)
  // }
})

// 暴露方法给父组件
defineExpose({
  goToSlide,
  nextSlide,
  previousSlide,
  startAutoPlay,
  stopAutoPlay,
  preloadAll: () => {
    galleryEntries.value.forEach((entry, index) => {
      preloadImages(entry).then(() => {
        loadedSlides.value.add(index)
      })
    })
  }
})
</script>

<style scoped>
.combined-gallery {
  width: 100%;
  min-height: 220px;
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.combined-gallery:hover {
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
}

/* 空状态样式 */
.no-media {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 2rem;
}

.no-media-content {
  text-align: center;
  animation: fadeInUp 0.6s ease;
}

.camera-animation {
  position: relative;
  margin-bottom: 1rem;
}

.camera-icon {
  animation: float 3s ease-in-out infinite;
}

.camera-flash {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.8) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  animation: flash 4s ease-in-out infinite;
  pointer-events: none;
}

.no-media-text {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.cooking-hint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6c757d;
  font-size: 0.9rem;
}

.hint-emoji {
  font-size: 1.2rem;
  animation: bounce 2s ease-in-out infinite;
}

/* 画廊容器 */
.gallery-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.gallery-window,
.window-item {
  width: 100%;
  height: 100%;
  min-height: 220px;
}

.window-item {
  position: relative;
  overflow: hidden;
  background: #000;
}

.round-gallery-instance {
  width: 100%;
  height: 100%;
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.item-active .round-gallery-instance {
  transform: scale(1);
  opacity: 1;
}

.item-prev .round-gallery-instance,
.item-next .round-gallery-instance {
  transform: scale(0.95);
  opacity: 0.8;
}

/* 进度指示器 */
.progress-container {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 6px;
  z-index: 20;
}

.progress-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  backdrop-filter: blur(10px);
}

.progress-dot.active {
  background: #ffffff;
  transform: scale(1.2);
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.6);
}

.progress-dot.completed {
  background: rgba(76, 175, 80, 0.8);
}

.progress-dot.upcoming {
  background: rgba(255, 255, 255, 0.3);
}

.dot-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.progress-dot.active .dot-glow {
  opacity: 1;
  animation: pulse 2s ease-in-out infinite;
}

/* 增强的作者信息 */
.author-chip-enhanced {
  position: absolute;
  bottom: 16px;
  left: 16px;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(20px);
  color: #fff;
  padding: 10px 14px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.85rem;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 15;
  max-width: calc(100% - 32px);
}

.chip-visible {
  transform: translateY(0);
  opacity: 1;
}

.chip-single {
  bottom: 20px;
  left: 20px;
}

.author-avatar-container {
  position: relative;
  flex-shrink: 0;
}

.avatar-wrapper {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  position: relative;
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.author-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  display: block;
}

.avatar-fallback {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-weight: 700;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-status-ring {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border-radius: 50%;
  border: 2px solid #4CAF50;
  animation: pulse-ring 2s ease-in-out infinite;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.author-name {
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.photo-count {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  white-space: nowrap;
}

.love-indicator {
  margin-left: auto;
  flex-shrink: 0;
  animation: heartbeat 1.5s ease-in-out infinite;
}

/* 导航控制 */
.navigation-controls {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  transform: translateY(-50%);
  display: flex;
  justify-content: space-between;
  pointer-events: none;
  z-index: 10;
  padding: 0 12px;
}

.nav-btn {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(10px);
  border: none;
  border-radius: 50%;
  width: 44px;
  height: 44px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  pointer-events: auto;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.nav-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.7);
  transform: scale(1.1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-btn-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.2) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.nav-btn:hover .nav-btn-glow {
  opacity: 1;
}

/* 重新设计的作者标签页 */
.author-tabs-container {
  position: absolute;
  bottom: 16px;
  right: 16px;
  z-index: 15;
}

.author-tabs {
  display: flex;
  gap: 10px;
  align-items: center;
}

.author-tab {
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(15px);
  padding: 4px;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.author-tab:hover {
  background: rgba(0, 0, 0, 0.6);
  transform: scale(1.05);
}

.author-tab.tab-active {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
  border-color: rgba(255, 255, 255, 0.4);
}

.tab-avatar-wrapper {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.tab-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  display: block;
}

.tab-fallback {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-weight: 700;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tab-indicator {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4CAF50;
  opacity: 0;
  transition: all 0.3s ease;
}

.author-tab.tab-active .tab-indicator {
  opacity: 1;
  animation: pulse-indicator 2s ease-in-out infinite;
}

.tab-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: all 0.3s ease;
  margin-bottom: 8px;
}

.author-tab:hover .tab-tooltip {
  opacity: 1;
}

/* 紧凑模式作者切换器 */
.author-switcher {
  position: absolute;
  bottom: 16px;
  right: 16px;
  z-index: 15;
}

.switcher-btn {
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  color: white;
  padding: 6px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.switcher-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}

.current-author-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.switcher-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.switcher-fallback {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-weight: 700;
  font-size: 0.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.switcher-arrow {
  transition: transform 0.3s ease;
}

.author-switcher[aria-expanded="true"] .switcher-arrow {
  transform: rotate(180deg);
}

.author-selector {
  position: absolute;
  bottom: 100%;
  right: 0;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  min-width: 180px;
  max-height: 200px;
  overflow-y: auto;
}

.selector-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.selector-item:last-child {
  border-bottom: none;
}

.selector-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.selector-item.selector-active {
  background: rgba(76, 175, 80, 0.3);
}

.selector-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea, #764ba2);
  flex-shrink: 0;
}

.selector-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.selector-fallback {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-weight: 700;
  font-size: 0.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.selector-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.selector-name {
  font-weight: 600;
  font-size: 0.8rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selector-count {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
}

/* 交互提示 */
.interaction-hints {
  position: absolute;
  top: 50%;
  right: 16px;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
}

.hint-item {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  color: white;
  padding: 6px 10px;
  border-radius: 16px;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 4px;
  animation: slideInRight 0.5s ease, fadeOut 0.5s ease 3s;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 媒体计数器 */
.media-counter {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 15;
}

.counter-bg {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.counter-icon {
  opacity: 0.8;
}

.counter-text {
  font-weight: 600;
}

/* 加载状态 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(248, 249, 250, 0.9);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.loading-content {
  text-align: center;
}

.loading-spinner {
  position: relative;
  width: 60px;
  height: 60px;
  margin: 0 auto 1rem;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-ring:nth-child(2) {
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  animation-delay: -0.3s;
  border-top-color: #764ba2;
}

.spinner-ring:nth-child(3) {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  animation-delay: -0.6s;
  border-top-color: #4CAF50;
}

.loading-text {
  color: #6c757d;
  font-weight: 500;
  margin: 0;
}

/* 动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes flash {
  0%, 90%, 100% { opacity: 0; }
  5%, 15% { opacity: 1; }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.7; }
}

@keyframes pulse-ring {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.6; }
}

@keyframes pulse-indicator {
  0%, 100% { transform: translateX(-50%) scale(1); }
  50% { transform: translateX(-50%) scale(1.2); }
}

@keyframes heartbeat {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* responsive layout */
@media (max-width: 768px) {
  .combined-gallery {
    border-radius: 12px;
  }
  
  .author-chip-enhanced {
    bottom: 12px;
    left: 12px;
    padding: 8px 12px;
    font-size: 0.8rem;
    max-width: calc(100% - 80px);
  }
  
  .avatar-wrapper {
    width: 28px;
    height: 28px;
  }
  
  .navigation-controls {
    padding: 0 8px;
  }
  
  .nav-btn {
    width: 36px;
    height: 36px;
  }
  
  .interaction-hints {
    right: 12px;
  }
  
  .hint-item {
    font-size: 0.7rem;
    padding: 4px 8px;
  }
  
  .author-tabs-container {
    bottom: 12px;
    right: 12px;
  }
  
  .author-tabs {
    gap: 8px;
  }
  
  .tab-avatar-wrapper {
    width: 24px;
    height: 24px;
  }
}

@media (max-width: 480px) {
  .progress-container {
    top: 8px;
  }
  
  .progress-dot {
    width: 6px;
    height: 6px;
  }
  
  .author-chip-enhanced {
    padding: 6px 10px;
    font-size: 0.75rem;
    max-width: calc(100% - 60px);
  }
  
  .avatar-wrapper {
    width: 24px;
    height: 24px;
  }
  
  .media-counter {
    top: 12px;
    right: 12px;
  }
  
  .counter-bg {
    padding: 3px 6px;
    font-size: 0.7rem;
  }
  
  .author-tabs {
    gap: 6px;
  }
  
  .tab-avatar-wrapper {
    width: 20px;
    height: 20px;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .combined-gallery {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  }
  
  .no-media {
    background: linear-gradient(135deg, #2d2d2d 0%, #3d3d3d 100%);
  }
  
  .loading-overlay {
    background: rgba(26, 26, 26, 0.9);
  }
}

/* 高对比度模式 */
@media (prefers-contrast: high) {
  .author-chip-enhanced,
  .nav-btn,
  .hint-item,
  .counter-bg,
  .switcher-btn,
  .author-selector {
    border: 2px solid #ffffff;
    background: #000000;
  }
  
  .progress-dot,
  .author-tab {
    border: 1px solid #ffffff;
  }
}

/* 减少动画模式 */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
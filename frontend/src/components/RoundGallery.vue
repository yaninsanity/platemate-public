<!-- File: src/components/RoundGallery.vue -->
<template>
  <div class="round-gallery">
    <!-- 自动轮播 -->
    <v-carousel
      v-if="images.length"
      v-model="current"
      cycle
      :interval="interval"
      hide-delimiter-background
      show-arrows="hover"
      height="100%"
      continuous
      progress="#ff5e9c"
      touch
      class="carousel"
    >
      <v-carousel-item
        v-for="(img, i) in images"
        :key="i"
        class="carousel-item"
      >
        <div class="image-wrapper">
          <v-img
            :src="img.url"
            cover
            :alt="`photo-${i}`"
            :aspect-ratio="1"
            class="carousel-img"
          />
          <div v-if="img.is_highlight" class="highlight-star">
            <span class="star-icon">⭐</span>
          </div>
        </div>
      </v-carousel-item>
    </v-carousel>

    <!-- 没图占位 -->
    <div v-else class="empty">
      <v-icon size="48" color="grey-lighten-2">mdi-camera-plus</v-icon>
    </div>

    <!-- 进度环 -->
    <!-- <div v-if="images.length" class="progress-ring">
      <svg viewBox="0 0 36 36">
        <path
          class="circle-track"
          d="M18 2.0845
             a 15.9155 15.9155 0 0 1 0 31.831
             a 15.9155 15.9155 0 0 1 0 -31.831"
        />
        <path
          class="circle-progress"
          :stroke-dasharray="`${progress}, 100`"
          d="M18 2.0845
             a 15.9155 15.9155 0 0 1 0 31.831
             a 15.9155 15.9155 0 0 1 0 -31.831"
        />
      </svg>
    </div> -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import type { MemoryEntry } from '@/models/couplememory'

/* ── Props ── */
const props = withDefaults(
  defineProps<{
    entry: MemoryEntry
    interval?: number   // 轮播间隔（毫秒）
  }>(),
  { interval: 3500 }
)

/* ── 图片数组 ── */
const images = computed(() => props.entry.media || [])

/* ── 当前页 & 计时 ── */
const current = ref(0)
let timer: number | undefined

onMounted(() => {
  if (images.value.length > 1) {
    timer = window.setInterval(() => {
      current.value = (current.value + 1) % images.value.length
    }, props.interval)
  }
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})

/* ── 进度环百分比 ── */
const progress = computed(() =>
  images.value.length
    ? ((current.value + 1) / images.value.length) * 100
    : 0
)

/* 当人工切换时，同步进度环 */
watch(current, () => {
  // progress 会自动刷新
})
</script>

<style scoped>
.round-gallery {
  position: relative;
  width: 100%;
  min-height: 220px;
  overflow: hidden;
  border-radius: 12px;
}

.carousel-item {
  display: flex;
  align-items: center;
  justify-content: center;
}

.carousel-img {
  transition: transform 0.5s ease;
}
.carousel-img:hover {
  transform: scale(1.05);
}

.image-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.highlight-star {
  position: absolute;
  top: 10px;
  left: 10px;
  background-color: #facc15;
  border-radius: 9999px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
}

.star-icon {
  font-size: 16px;
}

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
}

.progress-ring {
  position: absolute;
  bottom: 10px;
  right: 10px;
  width: 36px;
  height: 36px;
}

.circle-track {
  fill: none;
  stroke: #ffffff55;
  stroke-width: 3;
}

.circle-progress {
  fill: none;
  stroke: #ffffff;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.4s ease;
}
</style>

<template>
  <button
    class="bgm-btn"
    :class="{ playing }"
    :title="label"
    :aria-label="playing ? `Mute ${label}` : `Unmute ${label}`"
    @click="toggle"
    @mousedown="ripple($event)"
  >
    <!-- 播放 / 静音 图标 -->
    <svg class="icon" viewBox="0 0 24 24">
      <path
        v-if="playing"
        d="M3 9v6h4l5 5V4L7 9H3z"
        fill="currentColor"
      />
      <path
        v-else
        d="M3 9v6h4l5 5V4l-5 5H3zM17 7l4 4m0-4-4 4"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        fill="none"
      />
    </svg>
    <!-- 点击涟漪容器 -->
    <span class="ripple-container"><span class="ripple"/></span>
  </button>

  <audio
    ref="audioEl"
    :src="src"
    preload="auto"
    :loop="loop"
    @ended="handleEnded"
  />
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const props = defineProps<{
  src    : string
  label  : string
  auto?  : boolean
  volume?: number
  loop?  : boolean
}>()
const emit = defineEmits<{ 'update:playing':[boolean] }>()

const playing = ref(true)
const audioEl = ref<HTMLAudioElement|null>(null)

function ensurePlaying() {
  if (audioEl.value?.paused) audioEl.value.play().catch(()=>{})
}

function toggle() {
  if (!audioEl.value) return
  playing.value = !playing.value
  audioEl.value.muted = !playing.value
  ensurePlaying()
}

function handleEnded() {
  playing.value = false
}

watch(playing, v => emit('update:playing', v))

onMounted(() => {
  if (!audioEl.value) return
  audioEl.value.volume = props.volume ?? 1
  audioEl.value.muted  = !playing.value
  audioEl.value.loop   = props.loop !== false
  if (props.auto) ensurePlaying()
})

// 简单涟漪效果
function ripple(e: MouseEvent) {
  const btn = (e.currentTarget as HTMLElement)
  const circle = btn.querySelector<HTMLElement>('.ripple')!
  circle.classList.remove('animate')
  // 定位涟漪中心
  const rect = btn.getBoundingClientRect()
  const d = Math.max(rect.width, rect.height)
  circle.style.width = circle.style.height = d + 'px'
  circle.style.left = e.clientX - rect.left - d/2 + 'px'
  circle.style.top  = e.clientY - rect.top - d/2 + 'px'
  circle.classList.add('animate')
}
</script>

<style scoped>
.bgm-btn {
  width: 28px; height: 28px;
  border: none; border-radius: 50%;
  background: rgba(30,30,40,0.6);
  backdrop-filter: blur(6px);
  box-shadow:
    inset 0 0 4px rgba(255,255,255,0.1),
    0 2px 6px rgba(0,0,0,0.3);
  display: flex; align-items: center; justify-content: center;
  position: fixed;
  left: 1rem; bottom: 1rem;
  z-index: 1000;
  overflow: hidden;
  transform: perspective(100px) rotateX(6deg);
  transition: transform .2s ease, box-shadow .3s ease;
  cursor: pointer;
}
.bgm-btn:hover {
  transform: perspective(100px) rotateX(6deg) scale(1.1);
  box-shadow:
    inset 0 0 6px rgba(255,255,255,0.15),
    0 4px 10px rgba(0,0,0,0.4);
}
.bgm-btn:active {
  transform: perspective(100px) rotateX(6deg) scale(0.9);
}

/* 双脉冲环 */
.bgm-btn::before,
.bgm-btn::after {
  content: '';
  position: absolute; border-radius: 50%;
  border: 2px solid #4cafef;
  opacity: 0; pointer-events: none;
}
.bgm-btn.playing::before {
  width: 36px; height: 36px; inset: -4px;
  animation: pulse1 1.6s ease-out infinite;
}
.bgm-btn.playing::after {
  width: 44px; height: 44px; inset: -8px;
  animation: pulse2 2.4s ease-out infinite;
}
@keyframes pulse1 {
  0%   { transform: scale(0.5); opacity: 0.6 }
  100% { transform: scale(1.2); opacity: 0 }
}
@keyframes pulse2 {
  0%   { transform: scale(0.5); opacity: 0.4 }
  100% { transform: scale(1.5); opacity: 0 }
}

/* SVG 图标 */
.icon {
  width: 16px; height: 16px;
  color: #fff;
  transition: color .3s ease;
}
.bgm-btn.playing .icon {
  color: #4cafef;
}

/* 涟漪效果 */
.ripple-container {
  position: absolute; inset: 0;
}
.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.3);
  transform: scale(0);
  pointer-events: none;
}
.ripple.animate {
  animation: ripple-drop .6s ease-out;
}
@keyframes ripple-drop {
  to {
    transform: scale(1);
    opacity: 0;
  }
}
</style>

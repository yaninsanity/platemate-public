<template>
  <!-- 支持 dynamic island 时渲染 -->
  <component
    v-if="hasIsland && DynamicIsland"
    :is="DynamicIsland"
    ref="islandRef"
    v-model:visible="visible"
    :top="topPx"
    :small-width="120"
    :small-height="38"
    :large-width="400"
    :large-height="140"
    :large-radius="38"
    trigger-type="manual"
    :initial-animation="true"
    class-name="couple-theme"
    style="z-index:3000; pointer-events:none;" 
  >
    <template #default>
      <div class="island-content" style="pointer-events:auto;">
        <img src="/assets/logo4.png" alt="logo" class="island-logo" />
        <span class="island-text">{{ currentMsg }}</span>
      </div>
    </template>
  </component>

  <!-- fallback：不支持/没装库时 -->
  <transition name="fade">
    <div
      v-if="fallbackVisible && !hasIsland"
      class="fallback-island"
      :style="{ top: topPx }"
    >
      <div class="island-content fallback-content">
        <img src="/assets/logo4.png" alt="logo" class="island-logo" />
        <span class="island-text">{{ currentMsg }}</span>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
/* ---------------- only the necessary imports ---------------- */
import { ref, shallowRef, onMounted, onUnmounted, computed } from 'vue'  // <-- 加了 shallowRef / onUnmounted
import '/styles/dynamic-island.css'

/* ---------------- Props，supply defaults so nothing is undefined ---------------- */
const props = withDefaults(defineProps<{
  top?: number | string
  duration?: number
  interval?: number
  forceFallback?: boolean    // 调试用：true 时只用 fallback
  forceVisible?: boolean     // 调试用：true 时加载后立即显示
}>(), {
  top: 'calc(env(safe-area-inset-top, 0px) + 12px)',
  duration: 4000,
  interval: 60000,
  forceFallback: false,
  forceVisible: false,
})

/* the top offset is computed once; the template no longer uses $props */
const topPx = computed(() =>
  typeof props.top === 'number' ? `${props.top}px` : props.top
)

/* ---------------- 文案池 ---------------- */
const coupleMessages = [
  '💌 Send a sweet message to your partner!',
  '🎮 Challenge your partner to a fun quiz!',
  '💖 Give your partner a virtual hug!',
  '🌟 Plan your next date adventure together!',
  '🥰 Share your favorite memory today!',
  '🕹️ Unlock a new couple achievement!',
  '💬 Time for a cozy chat session!',
  '🎁 Surprise your partner with a virtual gift!',
  '👩‍❤️‍👨 Check in: How’s your partner feeling?',
  '🎉 Celebrate your relationship milestones!',
]

/* ---------------- State ---------------- */
const visible          = ref(false)
const fallbackVisible  = ref(false)
const currentMsg       = ref<string>('')
const timer            = ref<number | null>(null)
const islandRef        = ref<any>(null)
const DynamicIsland    = shallowRef<any>(null)
const hasIsland        = ref(false)

/* ---------------- 对外暴露方法 ---------------- */
function showMessage(msg: string) {
  currentMsg.value = msg
  visible.value = true
  fallbackVisible.value = true

  islandRef.value?.expand?.()

  window.setTimeout(() => {
    visible.value = false
    fallbackVisible.value = false
    islandRef.value?.shrink?.()
  }, props.duration)
}
defineExpose({ showMessage })

/* ---------------- 内部轮播 ---------------- */
function cycleMessage() {
  const next = coupleMessages[Math.floor(Math.random() * coupleMessages.length)]
  showMessage(next)
}

/* ---------------- 动态加载库 ---------------- */
async function loadIslandLib() {
  if (props.forceFallback) {
    hasIsland.value = false
    return
  }
  try {
    const mod = await import('v-dynamic-island')
    DynamicIsland.value = mod.default
    hasIsland.value = true

    // vite-ignore keeps the build from failing the exports check
    await import(/* @vite-ignore */ '/styles/dynamic-island.css')
  } catch (e) {
    console.warn('[DynamicIsland] fallback: ', e)
    hasIsland.value = false
  }
}

onMounted(async () => {
  await loadIslandLib()

  // first pass: forceVisible always shows; otherwise show one anyway
  cycleMessage()

  timer.value = window.setInterval(cycleMessage, props.interval)

  // 方便控制台调试
  // @ts-ignore
  window.__island = { showMessage }
})

onUnmounted(() => {
  if (timer.value) clearInterval(timer.value)
})
</script>

<style scoped>
.fallback-island {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3000;
  pointer-events: none;
}
.island-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 0.9rem;
  font-weight: 700;
  
  /* 🎮 AAA级暗色游戏主题 - 与BaseHeader完美融合 */
  color: rgba(255, 255, 255, 0.95);
  background: linear-gradient(135deg, 
    rgba(20, 20, 30, 0.95) 0%, 
    rgba(15, 15, 25, 0.98) 100%);
  backdrop-filter: blur(25px) saturate(1.6);
  
  /* 🌟 game border in the green energy theme, matching PetHudRow */
  border: 2px solid rgba(168, 230, 207, 0.3);
  border-radius: 24px;
  padding: 10px 16px;
  
  /* ✨ 多层阴影 - 立体悬浮感 */
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    0 0 40px rgba(168, 230, 207, 0.12);
  
  /* 🎭 能量场光效 */
  position: relative;
  overflow: visible;
}

/* 🎭 能量场动画背景 - 与PetHudRow统一 */
.island-content::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 30% 50%, 
    rgba(168, 230, 207, 0.1) 0%, 
    transparent 60%);
  opacity: 0.7;
  animation: islandEnergyPulse 4s ease-in-out infinite;
  pointer-events: none;
  border-radius: 24px;
}

@keyframes islandEnergyPulse {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 0.9; transform: scale(1.02); }
}

/* 🎯 Logo渲染完美修复 - 与PetHudRow统一风格 */
.island-logo {
  /* ✨ 超稳定尺寸渲染系统 */
  width: 32px;
  height: 32px;
  min-width: 32px;
  min-height: 32px;
  max-width: 32px;
  max-height: 32px;
  object-fit: contain;
  object-position: center;
  flex-shrink: 0;
  
  /* 🌟 energy border matching the pet avatar in PetHudRow exactly */
  border-radius: 50%;
  border: 2px solid rgba(168, 230, 207, 0.6);
  
  /* 💎 AAA级三层阴影 - 能量光晕效果 */
  box-shadow: 
    0 0 20px rgba(168, 230, 207, 0.5),
    0 4px 15px rgba(0, 0, 0, 0.4),
    inset 0 1px 2px rgba(255, 255, 255, 0.2);
  
  /* 🎭 平滑过渡动画 */
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  
  /* 🔥 能量脉动 - 与PetHudRow同步 */
  animation: logoEnergyPulse 3s ease-in-out infinite;
}

.island-logo:hover {
  transform: scale(1.1) rotate(8deg);
  border-color: rgba(168, 230, 207, 0.8);
  box-shadow: 
    0 0 28px rgba(168, 230, 207, 0.7),
    0 6px 20px rgba(0, 0, 0, 0.5),
    inset 0 1px 3px rgba(255, 255, 255, 0.3);
}

@keyframes logoEnergyPulse {
  0%, 100% { 
    box-shadow: 
      0 0 20px rgba(168, 230, 207, 0.5),
      0 4px 15px rgba(0, 0, 0, 0.4),
      inset 0 1px 2px rgba(255, 255, 255, 0.2);
  }
  50% { 
    box-shadow: 
      0 0 28px rgba(168, 230, 207, 0.7),
      0 6px 18px rgba(0, 0, 0, 0.5),
      inset 0 1px 2px rgba(255, 255, 255, 0.25);
  }
}
.island-text {
  max-width: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  
  /* 🎯 高对比度文字 - 与CoupleTimeClock统一 */
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.8),
    0 0 10px rgba(0, 0, 0, 0.6);
  -webkit-text-stroke: 0.3px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.5px;
}
.fallback-content {
  flex-direction: row;
}

/* 过渡 */
.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from,  .fade-leave-to      { opacity: 0; }
</style>

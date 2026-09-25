<!-- src/components/BaseNav.vue -->
<template>
  <div class="base-nav">
    <!-- ① 底部中央：用户头像 / Home-button -->
    <button class="nav-toggle" @click="toggle">
      <img :src="avatarSrc" alt="avatar" />
    </button>

    <!-- ② 半圆彩虹菜单 -->
    <button
      v-for="(item, i) in items"
      :key="item.to"
      class="nav-item"
      :style="itemStyle(i)"
      @click="goTo(item)"
      @mouseenter="hover = i"
      @mouseleave="hover = null"
    >
      <span class="mdi" :class="item.icon"></span>
      <span v-if="item.notification" class="badge">{{ item.notification }}</span>
      <div v-if="hover === i" class="tooltip">
        {{ item.label }}
        <span class="tooltip-arrow"></span>
      </div>
    </button>

    <!-- ③ 打开时的柔光 -->
    <div v-if="open" class="glow-effect"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import defaultAvatar from '@/assets/default-avatar.png'
import type { NavItem } from '@/models/navigation'

const items: NavItem[] = [
  { to: '/',        icon: 'mdi-home-variant',   label: 'Home',     color: '#FF8A80' },
  { to: '/couple',  icon: 'mdi-heart-multiple',  label: 'Couple',   color: '#FF5252' },
  { to: '/pet',     icon: 'mdi-paw',             label: 'Pet',      color: '#448AFF' },
  { to: '/cooking', icon: 'mdi-chef-hat',        label: 'Cooking',  color: '#FF9800' },
  { to: '/tasks',   icon: 'mdi-clipboard-text',  label: 'Tasks',    notification: 5, color: '#7C4DFF' },
  { to: '/markets', icon: 'mdi-shopping-search', label: 'Markets',  color: '#69F0AE' },
  { to: '/store',   icon: 'mdi-storefront',      label: 'Store',    color: '#00C853' },
  { to: '/album',   icon: 'mdi-image-multiple',  label: 'Album',    color: '#FFD740' },
  { to: '/about',   icon: 'mdi-information',     label: 'About',    color: '#90A4AE' },
  { to: '/settings',icon: 'mdi-cog',             label: 'Settings', color: '#B0BEC5' },
]

// 头像：可通过 prop 覆盖，否则用默认
const props = defineProps<{ avatar?: string }>()
const avatarSrc = computed(() => props.avatar || defaultAvatar)

// 状态 & 路由
const open = ref(false)
const hover = ref<number|null>(null)
const router = useRouter()
function toggle() { open.value = !open.value }
function goTo(item: NavItem) {
  router.push(item.to)
  open.value = false
}

// 半圆位置计算
const R      = 130
const SPREAD = 180
const OFFSET = -90 - SPREAD / 2
function itemStyle(i: number) {
  if (!open.value) return { opacity: 0, pointerEvents: 'none' as const }
  
  const angle = OFFSET + (i / (items.length - 1)) * SPREAD
  const rad = (angle * Math.PI) / 180
  const x = R * Math.cos(rad)
  const y = R * Math.sin(rad)
  
  return {
    transform: `translate(${x}px, ${y}px)`,
    backgroundColor: items[i].color,
    opacity: 1,
    pointerEvents: 'all' as const,
    zIndex: hover.value === i ? 200 : 100
  }
}

// add bottom padding to body on mount and remove it on unmount, so nothing is covered
onMounted(() => {
  document.body.style.paddingBottom = '6rem'
})
onUnmounted(() => {
  document.body.style.paddingBottom = ''
})
</script>

<style scoped>
.base-nav {
  position: fixed;
  left: 50%;
  bottom: 1.75rem;
  transform: translateX(-50%);
  width: 72px;
  height: 72px;
  pointer-events: none; /* 父容器本身不拦截，子元素按 style 决定 */
  z-index: 1000;
}

.nav-toggle {
  width: 72px;
  height: 72px;
  border: none;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 8px 22px rgba(0,0,0,.25);
  overflow: hidden;
  cursor: pointer;
  pointer-events: all;
  transition: transform .25s;
}
.nav-toggle:hover {
  transform: scale(1.08);
}
.nav-toggle img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.nav-item {
  position: absolute;
  top: 0; left: 0;
  width: 52px; height: 52px;
  border-radius: 50%;
  border: 3px solid #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
  box-shadow: 0 4px 15px rgba(0,0,0,.2);
  cursor: pointer;
}

.nav-item:hover {
  transform: scale(1.2) !important;
}

.badge {
  position: absolute;
  top: -4px; right: -4px;
  width: 20px; height: 20px;
  border-radius: 50%;
  background: #FF4081;
  color: #fff;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
  font-weight: 700;
}

.tooltip {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%) scale(.8);
  opacity: 0;
  background: rgba(0,0,0,.8);
  color: #fff;
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 13px;
  white-space: nowrap;
  animation: fade .2s forwards;
}
.tooltip-arrow {
  position: absolute;
  top: 100%; left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right:6px solid transparent;
  border-top:6px solid rgba(0,0,0,.8);
}
@keyframes fade {
  to {
    opacity: 1;
    transform: translateX(-50%) scale(1);
  }
}

.glow-effect {
  position: absolute;
  inset: -110px;
  background: radial-gradient(circle, rgba(255,64,129,.15) 0, rgba(255,64,129,0) 70%);
  pointer-events: none;
  animation: pulse 2s infinite alternate;
}
@keyframes pulse {
  from { opacity: .4 }
  to   { opacity: .85 }
}

@media(max-width:768px) {
  .base-nav { bottom: 1rem; }
  .nav-toggle { width:64px; height:64px; }
  .nav-item { width:46px; height:46px; font-size:19px; border-width:2px; }
}
</style>

<!-- PetNav.vue -->
<template>
  <!-- Heart FAB always mounts into body -->
  <teleport to="body">
    <v-fab-transition>
      <v-btn
        v-show="dockOpen"
        class="fab-heart"
        icon="mdi-heart-circle-outline"
        color="pink-darken-2"
        size="xl"
        elevation="12"
        @click.stop="toggleMenu"
      />
    </v-fab-transition>
  </teleport>

  <!-- Radial menu backdrop + items -->
  <teleport to="body">
    <transition name="fade">
      <div
        v-if="open"
        class="nav-backdrop"
        @click.self="closeMenu"
      >
        <div class="core" :style="anchorStyle">
          <transition-group name="item" tag="div">
            <v-btn
              v-for="(item, i) in items"
              :key="item.label"
              class="nav-item"
              :style="itemStyle(i, items.length)"
              :prepend-icon="item.icon"
              color="pink"
              rounded="xl"
              size="large"
              elevation="6"
              variant="flat"
              @click.stop="select(item)"
            >
              {{ item.label }}
            </v-btn>
          </transition-group>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface PetNavItem {
  name: string
  label: string
  icon: string
  route?: string
  anim?: string
  action?: string
}

// 当前 dock 展开/收起 & navVisible & items 列表
const props = defineProps<{
  open: boolean    // nav 是否可见
  dockOpen: boolean // dock 是否展开（决定 FAB 显示）
  items: PetNavItem[]
  anchor?: { x: number; y: number } // 可选锚点，默认为屏幕中心
}>()

const emit = defineEmits<{
  (e: 'open'): void
  (e: 'close'): void
  (e: 'select', it: PetNavItem): void
}>()

// FAB 切换
function toggleMenu() {
  props.open ? emit('close') : emit('open')
}
// 点击空白或 FAB 关闭
function closeMenu() {
  emit('close')
}
// 选中某项
function select(it: PetNavItem) {
  emit('select', it)
}

// 传入 anchor，默认为视窗中心
const anchorStyle = computed(() => {
  const x = props.anchor?.x ?? window.innerWidth / 2
  const y = props.anchor?.y ?? window.innerHeight / 2
  return {
    position: 'absolute' as const,
    left: `${x}px`,
    top: `${y}px`,
    transform: 'translate(-50%, -50%)'
  }
})

/**
 * 计算极坐标布局
 */
function itemStyle(idx: number, total: number) {
  const angle = (2 * Math.PI / total) * idx - Math.PI / 2
  const radius = Math.min(window.innerWidth, window.innerHeight) * 0.18
  const x = Math.cos(angle) * radius
  const y = Math.sin(angle) * radius
  return {
    transform: `translate(${x}px, ${y}px)`,
    transitionDelay: `${idx * 60}ms`
  }
}
</script>

<style scoped>
/* Backdrop 遮罩 */
.nav-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(255, 182, 193, 0.35);
  backdrop-filter: blur(12px);
}

/* 核心容器，定位在 anchorStyle 定义的位置 */
.core {
  position: absolute;
  width: 0;
  height: 0;
}

/* Nav 按钮 */
.nav-item {
  position: absolute;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.94) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
  font-weight: 500;
}

/* 入场 */
.item-enter-active {
  animation: pop-in 0.4s ease-out forwards;
}
.item-leave-active {
  animation: pop-out 0.3s ease-in forwards;
}
@keyframes pop-in {
  0%   { transform: scale(0.2); opacity: 0; }
  80%  { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(1); }
}
@keyframes pop-out {
  0%   { transform: scale(1); opacity: 1; }
  100% { transform: scale(0.2); opacity: 0; }
}

/* Heart FAB */
.fab-heart {
  position: fixed;
  right: 28px;
  bottom: 88px;
  z-index: 10000;
  animation: pulse 2s infinite ease-in-out;
}
@keyframes pulse {
  0%,100% { transform: scale(1); }
  50%     { transform: scale(1.25); }
}

/* Fade 过渡 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>

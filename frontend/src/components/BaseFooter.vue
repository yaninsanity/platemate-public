<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useDisplay } from 'vuetify'

const { mdAndUp } = useDisplay()          // 仅桌面显示
const year = new Date().getFullYear()

/* ── 滚动隐藏 ─────────────────────────────── */
const hidden = ref(false)
let last = window.scrollY
function onScroll () {
  if (!mdAndUp.value) return
  const cur = window.scrollY
  hidden.value = cur > last && cur > 120   // 向下滚且离顶部足够远
  last = cur
}
onMounted  (() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <!-- 仅桌面 -->
  <v-footer
    v-if="mdAndUp"
    height="120"
    class="platemate-footer"
    :class="{ 'is-hidden': hidden }"
    app
  >
    <!-- 背景玻璃 / 噪点 / 渐变 -->
    <div class="bg-layer"></div>

    <!-- 星屑 -->
    <div class="starfield" aria-hidden="true"></div>

    <v-container
      class="footer-inner d-flex align-center justify-space-between px-6"
    >
      <div class="d-flex align-center">
        <v-icon size="22" class="mr-2">mdi-paw</v-icon>
        © {{ year }} PlateMate
      </div>

      <div class="meta-links">
        <slot name="links" />
        <span class="version">v0.4.7</span>
      </div>
    </v-container>
  </v-footer>
</template>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

/* ───────────────────────── 外框 ───────────────────────── */
.platemate-footer {
  position: sticky; bottom: 0;
  transition: transform .35s $ease-in-out;
  &.is-hidden { transform: translateY(100%) }

  /* 背景玻璃 + 噪点 + 低饱和渐变 */
  .bg-layer {
    position: absolute; inset: 0;
    backdrop-filter: blur(14px) saturate(145%);
    background: linear-gradient(
      135deg,
      rgba($color-primary,   .55) 0%,
      rgba($color-accent,    .50) 40%,
      rgba($color-secondary, .55) 100%
    );
    &::after {
      content: ''; position: absolute; inset: 0; opacity: .5;
      background-image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 4 4'>\
<path fill='%23ffffff12' d='M0 0h1v1H0ZM2 0h1v1H2ZM1 1h1v1H1ZM3 1h1v1H3ZM0 2h1v1H0ZM2 2h1v1H2ZM1 3h1v1H1ZM3 3h1v1H3Z'/>\
</svg>");
    }
  }

  /* ─── 星屑 ─── */
  .starfield {
    position: absolute; inset: 0; pointer-events: none;
    --c:#fff;
    &::before,&::after{
      content:''; position:absolute; width:2px; height:2px; border-radius:50%;
      top:0; left:0;
      box-shadow:
        5vw 15vh 0 0 var(--c),
        15vw 55vh 0 1px var(--c),
        35vw 35vh 0 0 var(--c),
        55vw 75vh 0 1px var(--c),
        75vw 45vh 0 0 var(--c),
        90vw 20vh 0 1px var(--c);
      animation: starBlink 8s ease-in-out infinite alternate;
    }
    &::after { transform: rotate(35deg); animation-duration:11s }
  }

  /* 文案 */
  .footer-inner {
    position: relative; z-index: 1; color:#fff;
    font-family:$font-heading; font-size:$font-size-sm;
    .meta-links { display:flex; gap:$space-md; flex-wrap:wrap }
    .version    { opacity:.7; font-family:$font-base }
  }
}

/* 动画 */
@media (prefers-reduced-motion:no-preference){
  @keyframes starBlink{
    0%{opacity:.2;transform:translateY(0) scale(.8)}
    50%{opacity:1;transform:translateY(-4px) scale(1.2)}
    100%{opacity:.2;transform:translateY(0) scale(.8)}
  }
}
</style>

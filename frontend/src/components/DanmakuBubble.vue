<template>
  <div
    class="danmaku-item interactive-danmaku"
    :data-animation-id="animationId"
    :style="styleObject"
    :title="'Click to view full comment'"
    @click="$emit('click')"
  role="button"
  aria-label="Danmaku comment"
  >
    <span class="comment-avatar" v-if="avatar">
      <img :src="avatar" alt="avatar" @error="(e:any)=> (e.target.style.display='none')" />
    </span>
    <span class="comment-user">{{ username }}:</span>
    <span class="comment-text">{{ text }}</span>
    <span class="comment-emoji">💬</span>
    <div class="danmaku-trail"></div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  username: string
  text: string
  avatar?: string
  animationId?: number
  styleObject?: Record<string, string | number>
}

defineProps<Props>()
defineEmits<{ (e: 'click'): void }>()
</script>

<style scoped>
/* AAA 级弹幕单元样式（封装于 Bubble 组件，独立可控） */

/* 基础样式：高对比、硬件加速、移动优先 */
.danmaku-item {
  position: absolute !important;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  max-width: 92vw; /* 防止过宽导致不可见 */
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 10px 14px;
  border-radius: 999px;
  font-size: 0.95rem;
  line-height: 1;
  font-weight: 800;
  color: #fff;
  user-select: none;
  -webkit-tap-highlight-color: transparent;

  /* 视觉风格（可用 CSS 变量覆盖） */
  background: linear-gradient(135deg, var(--dmk-bg-a, rgba(129, 236, 236, 0.95)), var(--dmk-bg-b, rgba(78, 205, 196, 0.95)));
  border: 2px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 4px 24px rgba(78, 205, 196, 0.35), 0 0 0 1px rgba(0,0,0,0.08);

  /* 渲染与performance tuning */
  will-change: transform, opacity;
  backface-visibility: hidden;
  /* transform: translateZ(0); */
  contain: layout paint style;
  z-index: 2;
  pointer-events: auto;
  isolation: isolate;
}

.interactive-danmaku {
  position: relative;
  overflow: visible;
  cursor: pointer;
  transition: filter 0.2s ease, transform 0.2s ease;
}

.danmaku-item:hover {
  /* transform: translateZ(0) scale(1.06); */
  filter: brightness(1.12) saturate(1.15);
}

/* .danmaku-item:active {
  transform: translateZ(0) scale(0.97);
} */

/* 文本与元素 */
.comment-user { font-weight: 900; margin-right: 2px; text-shadow: 0 2px 6px rgba(0,0,0,.35); }
.comment-text { margin-right: 2px; text-shadow: 0 2px 6px rgba(0,0,0,.35); }
.comment-emoji { font-size: 1rem; filter: drop-shadow(0 1px 2px rgba(0,0,0,.25)); }

/* 头像（可选） */
.comment-avatar {
  display: inline-flex;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 2px;
  border: 2px solid rgba(255,255,255,0.5);
  box-shadow: 0 0 8px rgba(255,255,255,0.25);
}
.comment-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 尾迹效果（可选美化） */
.danmaku-trail {
  position: absolute;
  inset: -2px;
  border-radius: 999px;
  pointer-events: none;
  opacity: 0.0;
  background: radial-gradient(closest-side, rgba(255,255,255,0.18), transparent 60%);
  animation: trailPulse 2.4s ease-in-out infinite;
}

@keyframes trailPulse {
  0%, 100% { opacity: 0.0; }
  50% { opacity: 0.2; }
}

/* 语义变体（如有需要可在父级添加 class 控制） */
.danmaku-item.praise {
  --dmk-bg-a: rgba(255, 107, 107, 0.95);
  --dmk-bg-b: rgba(255, 142, 83, 0.95);
}
.danmaku-item.suggestion {
  --dmk-bg-a: rgba(78, 205, 196, 0.95);
  --dmk-bg-b: rgba(68, 160, 141, 0.95);
}
.danmaku-item.cheer {
  --dmk-bg-a: rgba(255, 215, 0, 0.95);
  --dmk-bg-b: rgba(255, 179, 0, 0.95);
  color: #2d3748;
}

/* 多行样式（如父层生成多行时可复用） */
.danmaku-item.multi-line-danmaku {
  border-left: 3px solid rgba(78, 205, 196, 0.6);
  padding-left: 12px;
  font-weight: 700;
  white-space: normal;
}

/* mobile tuning */
@media (max-width: 480px) {
  .danmaku-item {
    padding: 8px 12px;
    font-size: 0.85rem;
    border-width: 1.5px;
  max-width: 96vw;
    gap: 4px;
  }
  .comment-avatar { width: 18px; height: 18px; }
  .comment-emoji { font-size: 0.95rem; }
}

/* 降低动画偏好时减少特效，保证可访问性 */
@media (prefers-reduced-motion: reduce) {
  .danmaku-item { transition: none; }
  .danmaku-trail { animation: none; opacity: 0; }
}
</style>

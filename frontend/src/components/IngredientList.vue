<!-- src/components/IngredientList.vue -->
<template>
  <section v-if="normItems.length" class="ings">
    <h4 v-if="title" class="ings-title">{{ title }}</h4>

    <div class="ing-grid">
      <div
        v-for="(it, index) in normItems"
        :key="it.id"
        class="chip"
        :class="[sizeClass, hoverGlow && 'hover']"
        :title="it.tooltip"
        :style="{
          '--animation-delay': `${index * 0.05}s`
        }"
      >
        <!-- 缩略图 -->
        <img
          v-if="it.picture"
          :src="it.picture"
          :alt="it.name"
          class="thumb"
          loading="lazy"
          @error="onBroken"
          :style="{
            '--animation-duration': isMobile ? '0.2s' : '0.3s'
          }"
        />

        <!-- 数量徽章（永远显示） -->
        <span v-if="it.qty" class="qty">{{ it.qty }}</span>

        <!-- 名称 -->
        <span v-if="showName" class="name">{{ it.name }}</span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import type { Ingredient } from '@/models/recipes'

// 移动端检测
const isMobile = ref(false)

onMounted(() => {
  // 检测移动设备性能
  const checkMobile = () => {
    isMobile.value = window.innerWidth <= 768 || 
                     (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) ||
                     ('ontouchstart' in window)
  }
  
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

/* props --------------------------------------------------------- */
const props = withDefaults(
  defineProps<{
    items:( | Ingredient
            | {ingredient:Ingredient;quantity?:string|number}
            | {id:number;name:string;default_picture?:string;quantity?:string|number})[],
    title?:string,
    showName?:boolean,
    chipSize?:'sm'|'md'|'lg',
    hoverGlow?:boolean
  }>(),
  {title:'🧩 Ingredients', showName:true, chipSize:'md', hoverGlow:true},
)

/* size classes ---------------------------------------------------- */
const sizeClass = {sm:'chip-sm', md:'chip-md', lg:'chip-lg'}[props.chipSize]

/* URL correction ------------------------------------------------------ */
const ORIGIN = import.meta.env.VITE_API_BASE_URL?.replace('/api', '') || location.origin
const fix = (u?: string) => {
  if (!u) return ''
  if (u.startsWith('http')) {
    // Handle various source URLs:
    // - web:911 (docker container)
    // - localhost:911 (local dev)
    // - <PRODUCTION_HOST>:911 (production)
    return u.replace(
      /^https?:\/\/(web|localhost|45\.79\.163\.242):\d+/i, 
      ORIGIN
    )
  }
  // For relative URLs, prepend with correct origin
  return ORIGIN + u
}

/* normalisation -------------------------------------------------------- */
interface Norm{ id:number;name:string;picture:string;qty:string|null;tooltip:string }
const normItems = computed<Norm[]>(()=>props.items.map((raw:any)=>({
  id:(raw.ingredient??raw).id,
  name:(raw.ingredient??raw).name,
  picture:fix((raw.ingredient??raw).default_picture),
  qty:raw.quantity!=null?String(raw.quantity):null,
  tooltip:(raw.ingredient??raw).info||(raw.ingredient??raw).name,
})))

/* fallback mobile tuning -------------------------------------------------- */
function onBroken(e:Event){
  const img = e.target as HTMLImageElement
  // 移动端使用更简单的占位符
  const isMobile = window.innerWidth <= 768
  if (isMobile) {
    img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCA4MCA4MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iNDAiIGN5PSI0MCIgcj0iNDAiIGZpbGw9IiNGM0Y0RjYiLz4KPHRleHQgeD0iNDAiIHk9IjQ1IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOUI5QjlCIj4/PC90ZXh0Pgo8L3N2Zz4K'
  } else {
    img.src = 'https://placehold.co/80x80?text=?'
  }
}
</script>

<style scoped>
/* mobile performance ---------------------------------------- */
.chip {
  --animation-duration: 0.3s;
  --animation-delay: 0s;
  
  /* 启用硬件加速 */
  transform: translateZ(0);
  will-change: transform, opacity;
  
  /* 动画延迟 */
  animation-delay: var(--animation-delay);
  transition-duration: var(--animation-duration);
}

.thumb {
  /* mobile tuning图片渲染 */
  will-change: auto;
  transform: translateZ(0);
  transition-duration: var(--animation-duration, 0.3s);
}

/* 移动端简化动画 */
@media (max-width: 768px) {
  .chip {
    --animation-duration: 0.2s;
  }
  
  .chip:hover {
    /* 移动端简化悬停效果 */
    transform: translateZ(0) scale(1.02);
  }
}

/* further tuning for low-powered devices */
@media (prefers-reduced-motion: reduce) {
  .chip, .thumb {
    animation: none !important;
    transition: none !important;
  }
}

/* original styles -------------------------------------------- */
/* ====== 整体布局 ====== */
.ings-title{font-size:1rem;font-weight:700;margin-bottom:.45rem;color:#be185d}
.ing-grid{display:flex;flex-wrap:wrap;gap:.6rem;margin-bottom:.85rem}

/* ====== 卡牌基类 ====== */
.chip{
  --sz:4.6rem;                           /* 默认 md 尺寸 */
  width:var(--sz);min-width:var(--sz);
  padding:.42rem .42rem .6rem;           /* 预留下方给名称 */
  display:flex;flex-direction:column;align-items:center;
  border:1px solid #e5e7eb;border-radius:.95rem;background:#fff;
  box-shadow:0 2px 4px rgba(0,0,0,.06);
  position:relative;overflow:visible;
  transition:transform .25s,box-shadow .25s;
}

/* ====== mobile tuning ====== */
@media (max-width: 768px) {
  .chip {
    --animation-duration: 0.2s;
    will-change: auto;
  }
  
  .hover:hover {
    transform: translateY(-2px) scale(1.04);
    box-shadow: 0 6px 12px rgba(0,0,0,.12);
  }
  
  .thumb {
    transition: filter var(--animation-duration, 0.2s);
  }
}

/* 动画tuning */
.chip {
  --animation-duration: 0.3s;
  transform: translateZ(0);
  backface-visibility: hidden;
  will-change: transform;
}

.thumb{
  width:100%;aspect-ratio:1/1;object-fit:contain;pointer-events:none;
  transition:filter var(--animation-duration, 0.25s);
  transform: translateZ(0);
}
.name{
  margin-top:.26rem;font-size:.68rem;font-weight:600;line-height:1.05;text-align:center;
  word-break:break-word;
  color: black;
}

/* ====== hover 效果 ====== */
.hover:hover{transform:translateY(-4px) scale(1.08);box-shadow:0 10px 22px rgba(0,0,0,.16)}
.hover:hover .thumb{filter:drop-shadow(0 0 8px rgba(251,191,36,.55))}

/* ====== 数量徽章 ====== */
.qty{
  position:absolute;right:-7px;bottom:-7px;
  min-width:1.45rem;height:1.2rem;
  display:flex;justify-content:center;align-items:center;
  padding:0 .3rem;
  background:#6366f1;color:#fff;font-weight:700;font-size:0.8rem;
  border-radius:9999px;line-height:1;user-select:none;pointer-events:none;
  box-shadow:0 0 0 2px #fff, 0 0 6px rgba(99,102,241,.45);
}

/* ====== 尺寸变体 ====== */
.chip-sm{--sz:3.7rem}.chip-sm .name{font-size:.6rem}.chip-sm .qty{font-size:.5rem;min-width:1.2rem;height:1.05rem}
.chip-lg{--sz:6.2rem}.chip-lg .name{font-size:.78rem}.chip-lg .qty{font-size:.64rem;min-width:1.7rem;height:1.35rem}
</style>

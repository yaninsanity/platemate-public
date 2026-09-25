<template>
  <div
    v-if="modelValue"
    class="photo-overlay"
    role="dialog"
    :aria-labelledby="headingId"
    aria-modal="true"
    tabindex="-1"
    ref="overlayEl"
    @keydown.stop.prevent="onKeydown"
  >
    <div class="overlay-backdrop" @click="close" />

    <div class="overlay-content" ref="contentEl">
      <header class="overlay-header">
        <h2 :id="headingId" class="visually-hidden">Photo detail</h2>
        <div class="counter" :aria-label="`Image ${currentIndex + 1} of ${photos.length}`">{{ currentIndex + 1 }} / {{ photos.length }}</div>
        <button class="close-btn" @click="close" aria-label="Close photo viewer">×</button>
      </header>

      <main class="overlay-main">
        <button class="nav-btn prev" @click="prev" aria-label="Previous image" :disabled="photos.length <= 1">‹</button>

        <figure class="photo-stage">
          <img
            v-if="currentPhoto"
            class="photo-img"
            :src="currentPhoto.url"
            :alt="photoAlt(currentPhoto)"
            ref="imageEl"
          />
          <figcaption v-if="currentPhoto?.content" class="photo-caption">
            <span class="caption-text">{{ currentPhoto.content }}</span>
          </figcaption>
        </figure>

        <button class="nav-btn next" @click="next" aria-label="Next image" :disabled="photos.length <= 1">›</button>
      </main>

      <aside class="ai-panel" v-if="currentEntry">
        <div class="ai-header" id="ai-panel-title">
          <span class="ai-title">Kinny Analysis</span>
          <span v-if="entryScore(currentEntry) !== null" class="ai-score" aria-label="Overall score">{{ Math.round(entryScore(currentEntry) || 0) }} pts</span>
        </div>

        <div v-if="entryMetrics(currentEntry)" class="ai-metrics">
          <div class="metric-row">
            <span class="metric-label">Visual</span>
            <div class="metric-bar" :style="{ ['--val' as any]: entryMetrics(currentEntry)!.visual_appeal + '%' }" aria-hidden="true" />
            <span class="metric-val">{{ Math.round(entryMetrics(currentEntry)!.visual_appeal) }}</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Technique</span>
            <div class="metric-bar" :style="{ ['--val' as any]: entryMetrics(currentEntry)!.cooking_technique + '%' }" aria-hidden="true" />
            <span class="metric-val">{{ Math.round(entryMetrics(currentEntry)!.cooking_technique) }}</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Freshness</span>
            <div class="metric-bar" :style="{ ['--val' as any]: entryMetrics(currentEntry)!.ingredient_freshness + '%' }" aria-hidden="true" />
            <span class="metric-val">{{ Math.round(entryMetrics(currentEntry)!.ingredient_freshness) }}</span>
          </div>
        </div>

        <div class="ai-comment" aria-labelledby="ai-panel-title">
          <span class="ai-comment-label">Comment</span>
          <p class="ai-comment-text">{{ effectiveComment(currentEntry) }}</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'

type Photo = { id?: string | number; url: string; entryId?: number | null; content?: string; author_username?: string }

const props = defineProps<{
  modelValue: boolean
  photos: Photo[]
  startIndex?: number
  entries?: any[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'changeIndex', idx: number): void
}>()

const overlayEl = ref<HTMLElement | null>(null)
const contentEl = ref<HTMLElement | null>(null)
const imageEl = ref<HTMLImageElement | null>(null)
const headingId = `photo-overlay-title-${Math.random().toString(36).slice(2)}`

const currentIndex = ref(props.startIndex ?? 0)
watch(() => props.startIndex, (v) => {
  if (typeof v === 'number') currentIndex.value = v
})

const currentPhoto = computed(() => props.photos?.[currentIndex.value])
const currentEntry = computed(() => {
  const eid = currentPhoto.value?.entryId
  if (!eid || !props.entries) return null
  return props.entries.find((e: any) => e.id === eid) || null
})

const close = () => emit('update:modelValue', false)

const prev = () => {
  if (!props.photos?.length) return
  currentIndex.value = (currentIndex.value - 1 + props.photos.length) % props.photos.length
  emit('changeIndex', currentIndex.value)
}
const next = () => {
  if (!props.photos?.length) return
  currentIndex.value = (currentIndex.value + 1) % props.photos.length
  emit('changeIndex', currentIndex.value)
}

const onKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') { e.preventDefault(); close(); return }
  if (e.key === 'ArrowLeft') { e.preventDefault(); prev(); return }
  if (e.key === 'ArrowRight') { e.preventDefault(); next(); return }
  if (e.key === 'Tab') {
    // simple focus trap
    const focusables = getFocusable()
    if (focusables.length === 0) return
    const idx = focusables.indexOf(document.activeElement as HTMLElement)
    const dir = e.shiftKey ? -1 : 1
    const nextIdx = (idx + dir + focusables.length) % focusables.length
    e.preventDefault()
    focusables[nextIdx].focus()
  }
}

function getFocusable(): HTMLElement[] {
  const root = contentEl.value || overlayEl.value
  if (!root) return []
  const sel = 'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
  return Array.from(root.querySelectorAll(sel)) as HTMLElement[]
}

function photoAlt(p?: Photo) {
  if (!p) return 'Dish photo'
  if (p.content) return p.content
  return 'Dish photo'
}

function entryMetrics(entry: any) {
  const j = entry?.ai_judgment
  if (!j) return null
  return {
    visual_appeal: j.visual_appeal ?? 0,
    cooking_technique: j.cooking_technique ?? 0,
    ingredient_freshness: j.ingredient_freshness ?? 0,
  }
}

function entryScore(entry: any) {
  const j = entry?.ai_judgment
  if (j && typeof j.overall_score === 'number') return j.overall_score
  return entry?.effective_ai_score ?? entry?.ai_score ?? null
}

function effectiveComment(entry: any) {
  const j = entry?.ai_judgment || {}
  return j.individual_comment || j.ai_comment || 'Kinny is analyzing this dish...'
}

// Body scroll lock and initial focus
watch(() => props.modelValue, async (open) => {
  if (open) {
    const prev = document.body.style.overflow
    document.body.dataset.prevOverflow = prev
    document.body.style.overflow = 'hidden'
    await nextTick()
    overlayEl.value?.focus()
  } else {
    const prev = document.body.dataset.prevOverflow
    document.body.style.overflow = prev ?? ''
  }
})

onMounted(() => {
  if (props.modelValue) {
    document.body.dataset.prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    nextTick(() => overlayEl.value?.focus())
  }
})

onUnmounted(() => {
  const prev = document.body.dataset.prevOverflow
  document.body.style.overflow = prev ?? ''
})
</script>

<style scoped>
/* Overlay container */
.photo-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000002; /* above danmaku 999999 */
  display: grid;
  place-items: center;
  outline: none;
}

.overlay-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.72);
  -webkit-backdrop-filter: blur(2px);
  backdrop-filter: blur(2px);
}

.overlay-content {
  position: relative;
  width: min(96vw, 1200px);
  height: min(90vh, 800px);
  background: #0d0f1a;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  display: grid;
  grid-template-rows: auto 1fr;
  grid-template-columns: 1fr 340px;
  overflow: hidden;
}

.overlay-header {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(255,255,255,0.04);
  border-bottom: 1px solid rgba(255,255,255,0.12);
}

.counter { color: #fff; font-weight: 700; font-size: 0.9rem; }

.close-btn {
  margin-left: auto;
  background: #1f2335;
  color: #fff;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
}
.close-btn:focus { outline: 2px solid #64b5f6; outline-offset: 2px; }

.overlay-main {
  grid-column: 1 / 2;
  position: relative;
  display: grid;
  grid-template-columns: 60px 1fr 60px;
  align-items: center;
  background: radial-gradient(120% 100% at 50% 50%, rgba(255,255,255,0.06), rgba(0,0,0,0.2));
}

.photo-stage { position: relative; width: 100%; height: 100%; display: grid; place-items: center; }
.photo-img { max-width: 100%; max-height: 100%; object-fit: contain; }

.photo-caption {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px 12px;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
}
.caption-text { color: #fff; text-shadow: 0 2px 6px rgba(0,0,0,0.6); font-weight: 600; word-wrap: break-word; word-break: break-word; hyphens: auto; }

.nav-btn {
  background: rgba(255,255,255,0.08);
  color: #fff;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px;
  width: 44px; height: 44px;
  display: inline-grid; place-items: center;
  cursor: pointer;
}
.nav-btn:disabled { opacity: 0.4; cursor: default; }
.nav-btn:focus { outline: 2px solid #64b5f6; outline-offset: 2px; }

.ai-panel {
  grid-column: 2 / 3;
  display: flex; flex-direction: column; gap: 10px;
  padding: 12px;
  background: rgba(255,255,255,0.02);
  border-left: 1px solid rgba(255,255,255,0.12);
}
.ai-header { display: flex; align-items: center; justify-content: space-between; color: #ba68c8; font-weight: 800; }
.ai-title { font-size: 0.95rem; }
.ai-score { background: rgba(186,104,200,0.2); border: 1px solid rgba(186,104,200,0.4); border-radius: 8px; padding: 4px 8px; color: #fff; font-weight: 800; }

.ai-metrics { display: flex; flex-direction: column; gap: 8px; }
.metric-row { display: grid; grid-template-columns: 64px 1fr 40px; gap: 8px; align-items: center; }
.metric-label { font-size: 0.8rem; color: rgba(255,255,255,0.9); }
.metric-val { font-size: 0.85rem; color: rgba(255,255,255,0.95); font-weight: 800; text-align: right; }
.metric-bar { height: 10px; border-radius: 6px; position: relative; }
.metric-bar::after { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: var(--val, 0%); background: linear-gradient(90deg, #26c6da, #ab47bc); border-radius: 6px; }

.ai-comment { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; padding: 10px; }
.ai-comment-label { font-size: 0.75rem; color: rgba(255,255,255,0.7); }
.ai-comment-text { color: rgba(255,255,255,0.98); font-weight: 600; line-height: 1.4; margin: 6px 0 0; }

.visually-hidden { position: absolute !important; clip: rect(1px, 1px, 1px, 1px) !important; padding: 0 !important; border: 0 !important; height: 1px !important; width: 1px !important; overflow: hidden !important; white-space: nowrap !important; }

@media (max-width: 960px) {
  .overlay-content { grid-template-columns: 1fr; height: min(92vh, 860px); }
  .ai-panel { grid-column: 1 / -1; border-left: none; border-top: 1px solid rgba(255,255,255,0.12); }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .overlay-content, .overlay-backdrop { transition: none !important; animation: none !important; }
}
</style>
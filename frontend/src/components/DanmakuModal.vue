<template>
  <div
    v-if="open"
    class="danmaku-modal-overlay"
    role="dialog"
    aria-modal="true"
    @click="$emit('close')"
  >
    <div class="danmaku-modal" @click.stop>
      <button class="modal-close" @click="$emit('close')" aria-label="Close">✕</button>
      <div class="modal-header">
        <img v-if="avatar" :src="avatar" alt="avatar" class="modal-avatar" />
        <div class="modal-user">{{ username }}</div>
        <div class="modal-time">{{ time }}</div>
      </div>
      <div class="modal-content">
        <p class="modal-text">{{ text }}</p>
      </div>
      <div class="modal-actions">
        <button class="copy-btn" @click="copy">Copy</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  open: boolean
  username?: string
  text?: string
  avatar?: string
  timestamp?: number
}>()

const emit = defineEmits<{ (e: 'close'): void }>()

const time = computed(() => {
  const ts = props.timestamp
  if (!ts) return ''
  const now = Date.now()
  const diff = Math.max(0, now - ts)
  const sec = Math.floor(diff / 1000)
  if (sec < 10) return 'just now'
  if (sec < 60) return `${sec}s ago`
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const d = Math.floor(hr / 24)
  return `${d}d ago`
})

const copy = async () => {
  if (!props.text) return
  try { await navigator.clipboard.writeText(props.text) } catch {}
}
</script>

<style scoped>
.danmaku-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.6); display:flex; align-items:center; justify-content:center; z-index:2000; }
.danmaku-modal { width: min(640px, 92vw); max-height: 80vh; background: rgba(30,41,59,.95); border:1px solid rgba(255,255,255,.12); border-radius:16px; color:#fff; box-shadow: 0 20px 40px rgba(0,0,0,.35); padding:16px 16px 12px; display:flex; flex-direction:column; position: relative; }
.modal-close { position:absolute; top:10px; right:14px; background:transparent; border:none; color:rgba(255,255,255,.8); font-size:1rem; cursor:pointer; }
.modal-header { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.modal-avatar { width:28px; height:28px; border-radius:50%; object-fit:cover; border:1px solid rgba(255,255,255,.2); }
.modal-user { font-weight:700; }
.modal-time { color: rgba(255,255,255,.6); font-size:.85rem; margin-left:auto; }
.modal-content { overflow:auto; padding:8px 2px 8px 0; }
.modal-text { white-space: pre-wrap; line-height:1.6; }
.modal-actions { display:flex; justify-content:flex-end; gap:8px; margin-top:8px; }
.copy-btn { background: linear-gradient(135deg, #4ecdc4, #44a08d); color:#fff; border:none; padding:8px 14px; border-radius:10px; cursor:pointer; }
</style>

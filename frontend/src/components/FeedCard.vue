<!-- File: src/components/FeedCard.vue -->
<template>
  <div class="feed-card-wrapper">
    <v-card class="feed-card d-flex flex-column">

      <!-- ── Header ── -->
      <header class="feed-head d-flex align-center px-4 py-3 gap-3">
        <v-icon size="22" color="white">mdi-heart-multiple-outline</v-icon>
        <span class="date flex-grow-1">{{ roundRange }}</span>

        <!-- 积分水晶 -->
        <button v-if="showScore" class="score-crystal" type="button">
          <v-icon size="14" class="mr-1">mdi-star-four-points</v-icon>
          <span class="val">{{ totalPoints }}</span>
        </button>
      </header>

      <!-- 菜名 (可选) -->
      <div v-if="recipeTitle" class="dish py-1 px-4">
        🍽️ {{ recipeTitle }}
      </div>

      <!-- ── Couple Row ── -->
      <section class="couple-row px-4 py-2">
        <template v-for="(e, i) in pairedEntries" :key="'cp-' + i">
          <div v-if="e" class="player d-flex align-center gap-3">
            <!-- 头像 + mood -->
            <div class="avatar-wrap">
              <v-avatar size="60" class="avatar" :class="{ 'has-img': !!getAuthorAvatar(e) }">
                <img
                  v-if="getAuthorAvatar(e)"
                  :src="getAuthorAvatar(e)"
                  :alt="e.author_username"
                />
                <span v-else>{{ e.author_username?.[0] || '?' }}</span>
              </v-avatar>
              <div class="mood-dot" :class="`m-${e.mood}`">
                {{ getMoodEmoji(e.mood) }}
              </div>
            </div>

            <div class="info">
              <span class="name">{{ e.author_username }}</span>
              <span class="mood-pill" :class="`m-${e.mood}`">{{ getMoodText(e.mood) }}</span>
            </div>

            <div v-if="showScore" class="hex-score" :class="hexClass(e.ai_score)">
              {{ Math.round(e.ai_score || 0) }}
            </div>
          </div>

          <!-- 等待位 -->
            <div v-else class="waiting">
              <v-icon size="30">mdi-account-plus</v-icon>
              <span class="wait-label">Join</span>
            </div>
        </template>
      </section>

      <!-- ── 共享 Gallery ── -->
      <div class="gallery flex-grow-1">
        <CombinedGallery :entries="pairedEntries" :interval="3600" :show-hints="false" />
      </div>

      <!-- ── 评论墙 ── -->
      <v-divider />
      <v-card-text class="wall px-4 py-3" ref="wallRef">
        <div class="wall-head">
          <v-icon size="16" color="white">mdi-comment-text-multiple</v-icon>
          <span>{{ allComments.length }} {{ allComments.length === 1 ? 'comment' : 'comments' }}</span>
        </div>

        <v-list
          v-if="allComments.length"
          density="compact"
          class="c-list"
        >
          <v-list-item
            v-for="c in allComments"
            :key="c.id"
            class="c-item"
          >
            <template #prepend>
              <v-avatar size="38" class="c-ava">
                <img
                  v-if="getCommentAvatar(c)"
                  :src="getCommentAvatar(c) || ''"
                  :alt="c.author_username"
                />
                <span
                  v-else
                  :style="{ backgroundColor: colorOf(c.author_username) }"
                >
                  {{ c.author_username?.[0] || '?' }}
                </span>
              </v-avatar>
            </template>

            <v-list-item-title class="c-body">
              <strong>{{ c.author_username }}</strong>
              <span class="c-text">{{ c.content }}</span>
            </v-list-item-title>

            <template #append>
              <span class="c-time">{{ since(c.created_at) }}</span>
            </template>
          </v-list-item>
        </v-list>

        <!-- 0 评论 CTA -->
        <div v-else class="wall-cta">
          <div class="cta-bubble" @click="focusInput">
             <img :src="petWriteIcon" alt="Write comment" class="cta-icon" />
          </div>
          <p class="cta-title">Write a sweet memory! 💕</p>
          <p class="cta-sub">
            Your words here become part of your **roundly legacy**.
          </p>
        </div>
      </v-card-text>

      <!-- ── 评论输入 ── -->
      <v-divider />
      <v-card-actions class="input-bar px-4 py-3 gap-2">
        <div class="me-wrapper">
          <v-avatar size="38" class="me-avatar">
            <img
              v-if="userStore.user?.avatar_url"
              :src="userStore.user.avatar_url"
              :alt="userStore.user.username"
            />
            <span v-else>{{ userStore.user?.username?.[0] || 'U' }}</span>
          </v-avatar>
          <span class="pulse-ring"></span>
        </div>

        <v-text-field
          ref="inputRef"
          v-model="draft"
          placeholder="Leave a lovely note…"
          hide-details
          density="comfortable"
          class="flex-grow-1 comment-input"
          variant="outlined"
          :counter="180"
          @keyup.enter="send"
        />

        <v-btn
          icon
            :disabled="!draft.trim()"
            @click="send"
            class="send-btn"
            size="small"
            :title="draft.trim() ? 'Send' : 'Type something first'"
          >
          <v-icon size="20">mdi-send</v-icon>
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import petWriteIcon from '/assets/pet_write.png'
import { ref, computed, watch, nextTick } from 'vue'
import dayjs from 'dayjs'
import relTime from 'dayjs/plugin/relativeTime'
import CombinedGallery from '@/components/CombinedGallery.vue'
import { useCoupleMemoryStore } from '@/stores/couplememoryStore'
import { useRecipesStore } from '@/stores/recipeStore'
import { useUserStore } from '@/stores/userStore'
import type { MemoryEntry } from '@/models/couplememory'
dayjs.extend(relTime)

/* props & stores */
const props = withDefaults(
  defineProps<{ entries?: MemoryEntry[]; roundStart?: string; roundEnd?: string }>(),
  { entries: () => [] }
)
const cmStore = useCoupleMemoryStore()
const recipesStore = useRecipesStore()
const userStore = useUserStore()

/* mood config */
const moodCfg = {
  nailed: { e: '🏆', t: 'Nailed it!' },
  grind:  { e: '🛠️', t: 'Grinding' },
  love:   { e: '💖', t: 'With love' },
  lucky:  { e: '🎲', t: 'Lucky' },
  chaos:  { e: '🔥', t: 'Chaos' },
  happy:  { e: '😊', t: 'Happy' }
} as const
const getMoodEmoji = (m: string) => moodCfg[m as keyof typeof moodCfg]?.e || '😊'
const getMoodText  = (m: string) => moodCfg[m as keyof typeof moodCfg]?.t || 'Cooking'

/* avatar helpers */
function getAuthorAvatar(e: MemoryEntry | null) {
  if (!e) return ''
  if ((e as any).author_avatar_url) return (e as any).author_avatar_url
  const uname = e.author_username
  if (uname === userStore.user?.username) return userStore.user?.avatar_url || ''
  return userStore.couple?.members?.find(m => m.username === uname)?.avatar_url || ''
}
function getCommentAvatar(c: { author_username?: string }) {
  const n = c.author_username
  if (n === userStore.user?.username) return userStore.user?.avatar_url || ''
  return userStore.couple?.members?.find(m => m.username === n)?.avatar_url || ''
}
const colorOf = (u?: string) =>
  ['#ff6584', '#ffd166', '#06d6a0', '#118ab2', '#ef476f'][
    [...(u || '')].reduce((a, ch) => a + ch.charCodeAt(0), 0) % 5
  ]

/* computed */
const pairedEntries = computed(() => [props.entries[0] || null, props.entries[1] || null])

const roundRange = computed(() =>
  props.roundStart && props.roundEnd
    ? `${dayjs(props.roundStart).format('MMM D')} – ${dayjs(props.roundEnd).format('MMM D')}`
    : dayjs(pairedEntries.value[0]?.created_at || Date.now()).format('MMM D, YYYY')
)

const totalPoints = computed(() =>
  pairedEntries.value.reduce((s, e) => s + (e?.ai_score || 0), 0)
)

const allComments = computed(() => props.entries.flatMap(e => e.comments || []))

const recipeTitle = computed(() => {
  const rid = pairedEntries.value.find(e => e)?.recipe
  if (rid) return recipesStore.recipes.find(r => r.id === rid)?.name || ''
  const br = recipesStore.currentBracket?.recipe
  if (typeof br === 'object') return br?.name || ''
  if (typeof br === 'number') return recipesStore.recipes.find(r => r.id === br)?.name || ''
  return ''
})

/* score class */
const showScore = false // Hide score for now
function hexClass(v?: number | null) {
  const s = v || 0
  if (s >= 90) return 'hex-ex'
  if (s >= 75) return 'hex-good'
  if (s >= 60) return 'hex-ok'
  return 'hex-poor'
}

/* comment handling */
const draft = ref('')
const inputRef = ref()
const emit = defineEmits(['comment-added'])
async function send() {
  if (!draft.value.trim() || !pairedEntries.value[0]) return
  const created = await cmStore.createComment(pairedEntries.value[0]!.id, draft.value.trim())
  if (created) emit('comment-added')
  draft.value = ''
  nextTick(() => inputRef.value?.focus?.())
}
function focusInput() {
  nextTick(() => inputRef.value?.focus?.())
}
const since = (t: string) => dayjs(t).fromNow()

/* auto scroll */
const wallRef = ref<HTMLElement>()
watch(allComments, () => {
  nextTick(() =>
    wallRef.value?.scrollTo({
      top: wallRef.value.scrollHeight,
      behavior: 'smooth'
    })
  )
})
</script>

<style scoped>
/* ================== THEME TOKENS ================== */
:root {
  --bg-panel: #1d1f27;
  --bg-panel-alt: #12141b;
  --bg-soft: #f7f7f7;
  --gradient-main: linear-gradient(135deg,#6f63ff 0%,#9150ff 38%,#ff58b2 72%,#ffce55 100%);
  --gradient-accent: linear-gradient(135deg,#ff9ad2 0%,#ffce55 100%);
  --border-soft: rgba(255,255,255,0.08);
  --radius-card: 18px;
  --anim-spring: cubic-bezier(.22,1.25,.32,1);
  --text-light: #f5f6fa;
  --text-dim: #b7bcc9;
  --shadow-soft: 0 4px 14px -4px rgba(0,0,0,.4);
  --hex-size: 60px;
}

/* ================== WRAPPER ================== */
.feed-card-wrapper { perspective: 1000px; }
.feed-card {
  background: var(--bg-panel);
  border-radius: var(--radius-card);
  position: relative;
  overflow: hidden;
  transform: rotateX(.5deg) rotateY(-.5deg);
}
.feed-card::before {
  content:"";
  position:absolute; inset:0;
  background:
    linear-gradient(180deg,rgba(255,255,255,.08),transparent 30%),
    radial-gradient(circle at 85% 15%,rgba(255,255,255,.18),transparent 60%),
    var(--gradient-main);
  mix-blend-mode: overlay;
  opacity:.15;
  pointer-events:none;
}
.feed-card::after { /* noise */
  content:"";
  position:absolute; inset:0;
  background:url('/noise.svg');
  opacity:.05;
  pointer-events:none;
}

/* ================== HEADER ================== */
.feed-head {
  background: var(--gradient-main);
  color:#fff;
  position: relative;
  z-index:2;
  border-bottom:1px solid rgba(255,255,255,.15);
}
.date { font-weight:700; font-size:.95rem; letter-spacing:.5px; }

.score-crystal {
  position:relative;
  border:none;
  cursor:default;
  display:flex;
  align-items:center;
  gap:4px;
  padding:5px 15px;
  font-weight:800;
  font-size:.8rem;
  border-radius:999px;
  background:radial-gradient(circle at 30% 30%,#fff 0%,#ffe98f 90%);
  color:#332400;
  box-shadow:0 2px 6px rgba(0,0,0,.4),0 0 0 2px rgba(255,255,255,.25);
  isolation:isolate;
  animation:crystalPulse 4.5s ease-in-out infinite;
}
@keyframes crystalPulse {
  0%,100% { transform:translateY(0); filter:brightness(1); }
  50% { transform:translateY(-2px); filter:brightness(1.08); }
}

/* ================== DISH ================== */
.dish {
  background:linear-gradient(90deg,#fff5d6 0%,#ffe9b4 100%);
  font-weight:600;
  font-size:.87rem;
  color:#5a4100;
  border-bottom:1px solid #ffdca2;
}

/* ================== COUPLE ROW ================== */
.couple-row {
  display:flex;
  gap:26px;
  overflow-x:auto;
  scrollbar-width:none;
  background:var(--bg-soft);
  justify-content: center;
}
.couple-row::-webkit-scrollbar { display:none; }

.player { display:flex; align-items:center; gap:12px; }
.avatar-wrap { position:relative; }
.avatar {
  border:2px solid #fff;
  background:#5b57ff;
  color:#fff;
  font-weight:900;
  box-shadow:0 3px 6px rgba(0,0,0,.45);
  transition:transform .28s var(--anim-spring);
}
.avatar img { width:100%; height:100%; object-fit:cover; border-radius:50%; }
.avatar span { display:flex; align-items:center; justify-content:center; height:100%; }
.avatar:hover { transform:scale(1.06); }

.mood-dot {
  position:absolute;
  bottom:-5px; right:-5px;
  width:30px; height:30px;
  border-radius:50%;
  border:2px solid #fff;
  font-size:16px;
  display:flex; align-items:center; justify-content:center;
  box-shadow:0 2px 6px rgba(0,0,0,.4);
  background:#ff80c8;
}
.mood-pill {
  display: inline-flex;
  align-items: center;
  background: #f3f4f6;
  border-radius: .85rem;
  padding: .24rem .55rem;
  font-size: .58rem;
  margin-left: 4px;
}
.m-nailed { background: #ffc400; color: #7c5c00; }
.m-grind  { background: #ff7043; color: #fff; }
.m-love   { background: #ff69b4; color: #fff; }
.m-lucky  { background: #4caf50; color: #fff; }
.m-chaos  { background: #e91e63; color: #fff; }
.m-happy  { background: #ff9800; color: #fff; } 

.info .name { font-weight:700; font-size:.9rem; line-height:1; color:#222; }
.info .mood-text { font-size:.7rem; color:#666; margin-top:2px; }

.hex-score {
  --s: var(--hex-size);
  width:var(--s);
  height:calc(var(--s)*0.58);
  clip-path:polygon(25% 0,75% 0,100% 50%,75% 100%,25% 100%,0 50%);
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight:800;
  font-size:.8rem;
  color:#fff;
  filter:drop-shadow(0 4px 6px rgba(0,0,0,.45));
  transition:transform .28s var(--anim-spring), filter .28s var(--anim-spring);
  position:relative;
}
.hex-score::after {
  content:"";
  position:absolute; inset:0;
  background:inherit;
  filter:blur(8px) brightness(1.3);
  opacity:.55;
  z-index:-1;
  transform:scale(.9);
}
.hex-score:hover { transform:scale(1.08); filter:drop-shadow(0 6px 10px rgba(0,0,0,.5)); }
.hex-ex  { background:linear-gradient(135deg,#27c24c,#9dff7b); }
.hex-good{ background:linear-gradient(135deg,#2196f3,#6ed6ff); }
.hex-ok  { background:linear-gradient(135deg,#ffb300,#ffd86b); }
.hex-poor{ background:linear-gradient(135deg,#8d8d8d,#c9c9c9); }

.waiting {
  width:60px;
  height:60px;
  border-radius:50%;
  background:#e4e4e4;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:2px;
  color:#7d7d7d;
  font-size:.65rem;
  font-weight:600;
}
.wait-label { text-transform:uppercase; letter-spacing:.5px; }

/* ================== GALLERY ================== */
.gallery { min-height: 268px; background:#000; }

/* ================== WALL (comments) ================== */
.wall {
  background: var(--bg-panel-alt);
  max-height: 230px;
  overflow-y:auto;
  color: var(--text-light);
  scrollbar-width: thin;
  scrollbar-color: #444 transparent;
}
.wall::-webkit-scrollbar { width:8px; }
.wall::-webkit-scrollbar-thumb { background:#2f3138; border-radius:6px; }

.wall-head {
  display:flex;
  align-items:center;
  gap:8px;
  font-size:.74rem;
  font-weight:700;
  text-transform:uppercase;
  letter-spacing:.8px;
  margin-bottom:8px;
  color:#fff;
}

.c-list { --v-list-gap:0; }
.c-item {
  padding:6px 0;
  border-bottom:1px solid var(--border-soft);
  transition:background .25s;
}
.c-item:last-child { border-bottom:none; }
.c-item:hover { background:rgba(255,255,255,.04); }

.c-ava {
  box-shadow:0 2px 4px rgba(0,0,0,.55);
  border:2px solid #ffffff29;
  background:#393c45;
  font-weight:700;
}
.c-ava img { width:100%; height:100%; object-fit:cover; }
.c-ava span {
  display:flex;
  align-items:center;
  justify-content:center;
  width:100%;
  height:100%;
  color:#fff;
  font-weight:700;
}

.c-body { font-size:.8rem; line-height:1.35; font-weight:500; }
.c-body strong { color:#fff; font-weight:700; }
.c-text { color:#38393c; }
.c-time { font-size:.65rem; color:var(--text-dim); margin-left:8px; white-space:nowrap; }

.wall-cta {
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:10px;
  padding:22px 0 10px;
  text-align:center;
}
.cta-bubble img {
  width: 52px;
  height: 52px;
}
.cta-bubble {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--gradient-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px -4px rgba(0,0,0,.55);
  animation: bounce 2s infinite;
}
.cta-bubble {
  width:60px;
  height:60px;
  border-radius:50%;
  background:var(--gradient-accent);
  display:flex;
  align-items:center;
  justify-content:center;
  cursor:pointer;
  box-shadow:0 4px 12px -4px rgba(0,0,0,.55);
  animation:bounce 2s infinite;
}
@keyframes bounce {
  0%,100% { transform:translateY(0); }
  50%     { transform:translateY(-6px); }
}
.cta-title {
  font-size:.85rem;
  font-weight:600;
  background:linear-gradient(90deg,#ffb4e4,#ffe07b);
  -webkit-background-clip:text;
  color:transparent;
}
.cta-sub {
  font-size:.7rem;
  color:#8d93a3;
  max-width:220px;
  line-height:1.3;
}

/* ================== INPUT BAR ================== */
.input-bar {
  background: var(--bg-panel);
  display:flex;
  align-items:center;
  gap:10px;
}
.me-wrapper {
  position:relative;
  width:38px; height:38px;
}
.me-avatar {
  width:38px; height:38px;
  background:#5b57ff;
  color:#fff;
  font-weight:800;
  border:2px solid #fff;
  box-shadow:0 2px 6px rgba(0,0,0,.5);
}
.me-avatar img { width:100%; height:100%; object-fit:cover; }
.me-avatar span { display:flex; align-items:center; justify-content:center; height:100%; }
.pulse-ring {
  position:absolute;
  inset:0;
  border-radius:50%;
  background:radial-gradient(circle at 50% 50%,rgba(255,255,255,.45),transparent 70%);
  animation:pulse 3s ease-in-out infinite;
  pointer-events:none;
  mix-blend-mode:overlay;
}
@keyframes pulse {
  0%,100% { transform:scale(.95); opacity:.35; }
  50% { transform:scale(1.15); opacity:.05; }
}

.comment-input {
  --v-theme-overlay-multiplier: 0; /* 清除 Vuetify overlay */
}
.comment-input :deep(.v-field) {
  background:#dfdfdf;
  border:1px solid #838da8;
  border-radius:12px;
  transition:border-color .25s, background .25s;
}
.comment-input :deep(.v-field:hover){
  border-color:#b6c2de;
}
.comment-input :deep(.v-field--focused){
  border-color:#e787ff;
  box-shadow:0 0 0 2px rgba(245, 135, 255, 0.3);
  background:#dbb6de;
}
.comment-input :deep(input){
  color:var(--text-light);
  font-size:.84rem;
}
.comment-input :deep(input::placeholder){
  color:#5d626d;
}

.send-btn {
  background:linear-gradient(135deg,#6c63ff 0%,#ff63c0 100%);
  color:#fff;
  box-shadow:0 3px 10px -3px rgba(0,0,0,.55);
  transition:transform .25s var(--anim-spring), box-shadow .25s;
}
.send-btn:disabled {
  filter:grayscale(.4);
  opacity:.45;
  box-shadow:none;
}
.send-btn:not(:disabled):hover {
  transform:translateY(-2px);
  box-shadow:0 6px 16px -6px rgba(0,0,0,.7);
}

/* ================== RESPONSIVE ================== */
@media (max-width: 640px) {
  :root { --hex-size: 50px; }
  .player { gap:10px; }
  .info .name { font-size:.82rem; }
  .hex-score { font-size:.72rem; }
  .avatar { width:56px !important; height:56px !important; }
  .mood-dot { width:26px; height:26px; font-size:14px; }
  .gallery { min-height:240px; }
}

/* Avoid text selection highlight ugliness */
.feed-card ::selection {
  background:#ffbde5;
  color:#222;
}
</style>

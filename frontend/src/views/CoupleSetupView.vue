<template>
  <!-- 整体容器，顶栏高度 padding 防遮挡 -->
  <div class="couple-setup-screen">
    <main class="main-body share-target">
      <!-- 已配对 -->
      <template v-if="isCoupled">
        <!-- ① 头像 & SVG 心形 -->
        <header class="faces-row">
          <figure class="face" tabindex="0">
            <img :src="meAvatar" alt="You" class="face-img" />
            <figcaption>{{ meName }}<br /><span>(You)</span></figcaption>
          </figure>

          <svg class="connector" viewBox="0 0 100 50" preserveAspectRatio="none">
            <path
              d="M0,25 C25,0 75,50 100,25"
              stroke="#ff6fa5" stroke-width="4" fill="none"
            />
          </svg>

          <figure class="face" tabindex="0">
            <img :src="paAvatar" alt="Partner" class="face-img" />
            <figcaption>{{ paName }}<br /><span>(Partner)</span></figcaption>
          </figure>
        </header>

        <!-- ② 宠物区 -->
        <section class="pet-zone">
          <!-- 蛋未孵化 -->
          <template v-if="!hasPet">
            <div class="egg-wrapper" @click="bounceEgg" role="button" aria-label="Hatch Egg">
              <PetRenderer
                ref="egg"
                class="egg"
                :base="ASSET_DIR"
                :initial-anim="eggFile"
              />
              <div class="egg-glow"></div>
            </div>
            <p class="tap-tip">🎮 Tap the egg to hatch your companion!</p>
          </template>

          <!-- 已孵化 -->
          <template v-else>
            <div class="pet-wrapper">
              <div :class="['pet-card', { celebrating }]" @animationend="celebrating = false">
                <PetStage :status="petStatus" :size="200" bg="#e9f3ff" />
                <!-- 庆祝动画 -->
                <div v-if="celebrating" class="sparkle"></div>
              </div>

              <!-- 宠物名称 & 等级 -->
              <div class="pet-info">
                <h3 class="pet-name">{{ pet.nickname }}</h3>
                <p class="pet-level">Lv {{ pet.level }}</p>
              </div>

              <!-- XP 进度条 -->
              <div class="xp-bar">
                <div class="xp-fill" :style="{ width: xpPercent + '%' }"></div>
              </div>

              <!-- 心情 -->
              <p class="mood">{{ moodEmoji }} Feeling {{ moodText }}</p>
            </div>
          </template>
        </section>

        <!-- ③ 情侣信息卡 -->
        <section class="couple-card">
          <h2>{{ coupleName }}</h2>
          <p class="code">Code · <strong>{{ coupleCode }}</strong></p>
          <p class="since">🕒 {{ hoursSince }}h together</p>

          <div class="btn-row">
            <button class="btn copy" :disabled="copying" @click="copyCode">
              <span v-if="!copying">✂️ Copy</span>
              <span v-else class="loader"></span>
            </button>
            <button class="btn share" :disabled="sharing" @click="onShare">
              <span v-if="!sharing">📷 Share</span>
              <span v-else class="loader"></span>
            </button>
            <button class="btn memory" @click="goMemories">📖 Memories</button>
          </div>

          <p class="encourage">
            Keep unlocking memories together—cook up the next level! 🍳
          </p>
        </section>
      </template>

      <!-- 未配对 -->
      <template v-else>
        <CoupleInvite />
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { usePetStore } from '@/stores/petStore'
import defaultAvatar from '@/assets/default-avatar.png'
import PetRenderer from '@/components/PetRenderer.vue'
import PetStage from '@/components/PetStage.vue'

const router    = useRouter()
const userStore = useUserStore()
const petStore  = usePetStore()

// Couple
const couple     = computed(() => userStore.couple)
const isCoupled  = computed(() => !!couple.value &&
  (couple.value.is_complete || (couple.value.members?.length || 0) >= 2)
)
const meAvatar   = computed(() => userStore.user?.avatar_url || defaultAvatar)
const meName     = computed(() => userStore.user?.username || 'You')
const partnerUser= computed(() => couple.value?.members?.find(m => m.id !== userStore.user?.id))
const paAvatar   = computed(() => partnerUser.value?.avatar_url || defaultAvatar)
const paName     = computed(() => partnerUser.value?.username || 'Partner')
const coupleCode = computed(() => couple.value?.code || '')
const coupleName = computed(() => couple.value?.name || '')
const hoursSince = computed(() => {
  const t = couple.value?.created_at
  return t ? Math.floor((Date.now() - Date.parse(t)) / 36e5) : 0
})

// Pet
const ASSET_DIR   = '/biped/'
const eggFile     = 'egg.glb'
const pet         = computed(() => petStore.pet!)
const petStatus   = computed(() => petStore.petStatus)
const hasPet      = computed(() => !!petStore.pet)
const celebrating = ref(false)

// XP 百分比
const xpPercent = computed(() => {
  const p = pet.value
  if (!p) return 0
  // Calculate next level XP based on current level (100 XP per level)
  const nextLevelXp = (p.level + 1) * 100
  const currentLevelXp = p.level * 100
  const xpInCurrentLevel = p.xp - currentLevelXp
  return Math.min(100, Math.floor((xpInCurrentLevel / (nextLevelXp - currentLevelXp)) * 100))
})

// 心情
const moodValue = computed(() => (petStatus.value as any)?.happiness ?? 0)
const moodEmoji = computed(() => {
  const h = moodValue.value
  return h >= 80 ? '😄'
       : h >= 60 ? '🙂'
       : h >= 40 ? '😐'
       : h >= 20 ? '🙁'
       : '😢'
})
const moodText  = computed(() => {
  const h = moodValue.value
  return h >= 80 ? 'Awesome'
       : h >= 60 ? 'Good'
       : h >= 40 ? 'Okay'
       : h >= 20 ? 'Sad'
       : 'Down'
})

// Toast
const toast = ref('')
function showToast(msg: string) {
  toast.value = msg
  setTimeout(() => (toast.value = ''), 2500)
}

// Copy / Share
const copying = ref(false)
const sharing = ref(false)
async function copyCode() {
  if (!coupleCode.value) return
  copying.value = true
  await navigator.clipboard.writeText(coupleCode.value)
  copying.value = false
  showToast('Code copied! 🎉')
}
async function onShare() {
  const root = document.querySelector<HTMLElement>('.share-target')
  if (!root) { showToast('Nothing to capture'); return }
  sharing.value = true
  try {
    // @ts-ignore
    const dataUrl = await (window as any).htmlToImage.toPng(root, {
      cacheBust: true,
      pixelRatio: Math.min(devicePixelRatio, 2)
    })
    const blob = await fetch(dataUrl).then(r => r.blob())
    const file = new File([blob], 'platemate-couple.png', { type: 'image/png' })
    if (navigator.canShare?.({ files: [file] })) {
      await navigator.share({ files: [file], title: 'Our PlateMate Couple' })
      showToast('Shared! 🔗')
    } else {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(file)
      a.download = file.name
      a.click()
      URL.revokeObjectURL(a.href)
      showToast('Downloaded! 💾')
    }
  } catch {
    showToast('Snapshot failed 😢')
  } finally {
    sharing.value = false
  }
}

// 蛋抖动
import type { ComponentPublicInstance } from 'vue'
const egg = ref<ComponentPublicInstance>()
function bounceEgg() {
  const el = (egg.value as any)?.$el as HTMLElement
  if (!el) return
  el.classList.add('bounce')
  setTimeout(() => el.classList.remove('bounce'), 600)
}

// 跳转 Memories
function goMemories() {
  router.push('/memories')
}

// 初始化
onMounted(async () => {
  await nextTick()
  await userStore.fetchProfile().catch(() => {})
  if (isCoupled.value) {
    await petStore.fetchPet().catch(() => {})
    celebrating.value = hasPet.value
  }
})
</script>


<style scoped>
/* :root { --nav-h: 56px } */

.couple-setup-screen {
  /* Match your header heights as defined in BaseHeader.vue */
  --nav-mobile: 56px;  /* Mobile header height */
  --nav-desktop: 68px; /* Desktop header height */
  
  /* Use correct variable for padding-top based on screen size */
  /* padding-top: var(--nav-mobile); */
  /* min-height: calc(100vh - var(--nav-mobile)); */
  background: linear-gradient(135deg, #e6f1ff, #fff0f8);
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Adjust for desktop sizes */
@media (min-width: 600px) {
  .couple-setup-screen {
    padding-top: var(--nav-desktop);
    min-height: calc(100vh - var(--nav-desktop));
  }
}

.main-body {
  flex: 1;
  padding: 1rem 0.6rem 1.2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(135deg, #e6f1ff, #ffeef8);
}


/* 头像 & 连线 */
.faces-row {
  position: relative; 
  z-index: 2;
  display: flex; 
  align-items: center; 
  gap: 1rem;
  margin-bottom: 1.2rem;
}

.face { text-align: center; font-size: 0.9rem; }
.face-img {
  width: 72px; height: 72px; border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
  transition: transform .3s;
}
.face:hover .face-img { transform: scale(1.05) }
.connector {
  flex: 1; height: 50px; overflow: visible;
  animation: wave 3s infinite ease-in-out;
}
@keyframes wave {
  0%,100%{transform: translateY(0)}50%{transform: translateY(3px)}
}
.connector-path { stroke-linecap: round; }

/* 蛋 / 宠物 */
.pet-zone { text-align: center; margin-bottom: 1.6rem; }
.egg-wrapper { position: relative; width:130px; height:130px; cursor:pointer; }
.egg-glow {
  position:absolute; inset:0;
  box-shadow: 0 0 20px 8px rgba(255,111,165,0.5);
  border-radius:50%; opacity:0;
  animation: glow 0.8s ease-out forwards;
}
@keyframes glow { from{opacity:1} to{opacity:0} }
.egg { width:100%; height:100%; }
.egg.bounce { animation:bounce 0.6s; }
@keyframes bounce { 0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)} }
.pet-wrapper { display: flex; flex-direction: column; align-items: center; }
.pet-card {
  width:200px;height:200px;background:#e9f3ff;border-radius:18px;
  box-shadow:0 8px 18px rgba(0,0,0,0.08);
  display:flex;justify-content:center;align-items:center;
  position:relative; overflow:hidden;
  animation: float 4s ease-in-out infinite;
}
@keyframes float { 0%,100%{transform: translateY(0)}50%{transform: translateY(-5px)} }
.pet-card.celebrating { animation: celebrate 0.8s ease-in-out; }
@keyframes celebrate { 0%{transform:scale(1)}50%{transform:scale(1.07)}100%{transform:scale(1)} }
.sparkle {
  position:absolute; inset:0;
  background:url('https://cdn.jsdelivr.net/gh/niklasvh/html2canvas-tests@main/assets/fireworks.gif')
    center/cover no-repeat; mix-blend-mode: screen; pointer-events:none;
}
.pet-info { margin-top:0.6rem; text-align:center; }
.pet-name { font-size:1.2rem; font-weight:700; color:#222; }
.pet-level { font-size:0.95rem; color:#555; margin-top:0.2rem; }
.xp-bar {
  width:180px; height:8px; background:#ddd; border-radius:4px;
  overflow:hidden; margin:0.6rem auto 0;
}
.xp-fill { height:100%; background:#4cafef; }
.mood { margin-top:0.4rem; font-size:0.9rem; color:#444; }

/* 情侣卡片 */
.couple-card {
  width:100%; max-width:360px;
  background:rgba(255,255,255,0.85); padding:1rem;
  border-radius:16px; text-align:center;
  box-shadow:0 4px 12px rgba(0,0,0,0.05);
}
.couple-card h2 { font-size:1.25rem; font-weight:700; margin-bottom:0.4rem; }
.code, .since { margin:0.3rem 0; color:#555; }
.btn-row {
  display:flex; gap:0.5rem; justify-content:center; margin-top:0.6rem;
}
.btn {
  flex:1; padding:0.5rem 0; border:none; border-radius:8px;
  color:#fff; font-weight:600; cursor:pointer; transition:filter .2s;
  display:flex; justify-content:center; align-items:center;
}
.btn.copy { background:#ff8fa3; }
.btn.share { background:#5a9eff; }
.btn.memory { background:#8e44ad; }
.btn:disabled { opacity:0.6; cursor:not-allowed }
.btn:hover:not(:disabled){ filter:brightness(.9) }
.loader {
  width:1em; height:1em;
  border:2px solid rgba(255,255,255,0.6);
  border-top-color:#fff; border-radius:50%;
  animation:spin .8s linear infinite;
}
@keyframes spin { to{transform:rotate(360deg)} }
.encourage { margin-top:0.8rem; font-size:0.85rem; color:#555; }

/* Toast */
.toast {
  position:fixed; top:var(--nav-h); left:50%;
  transform:translateX(-50%);
  background:rgba(0,0,0,0.75); color:#fff;
  padding:0.5rem 1rem; border-radius:12px;
  box-shadow:0 6px 18px rgba(0,0,0,0.3); z-index:9999;
}
.toast-enter-from, .toast-leave-to {
  opacity:0; transform:translate(-50%,-20px);
}
.toast-enter-active, .toast-leave-active {
  transition:0.25s;
}

/* Mobile */
@media (max-width:480px) {
  .face-img { width:60px; height:60px; }
  .pet-card { width:180px; height:180px; }
  .xp-bar { width:160px; }
}

/* monkey patch for full‐height background & remove white gap */
html, body, #app, .v-application {
  height: 100%;
  margin: 0;
  padding: 0;
}

/* drop the white background from v-main */
.v-application .v-main {
  background: transparent !important;
}

/* couple-setup-screen 拉伸到底部 */
.couple-setup-screen {
  position: absolute;
  top: var(--nav-mobile);    /* both variables are already defined in the component */
  bottom: 0;
  left: 0;
  right: 0;
  overflow-y: auto;
}



</style>

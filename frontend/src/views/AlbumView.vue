<!-- src/components/BipedAlbum.vue -->
<template>
  <div class="album-root">
    <!-- 左右导航 -->
    <button class="nav-arrow left" @click="prevPage" :disabled="currentPage===0">
      ‹
    </button>
    <button class="nav-arrow right" @click="nextPage" :disabled="currentPage+1===pages">
      ›
    </button>

    <!-- 走马灯区 -->
    <div class="carousel">
      <transition :name="slideDirection === 'right' ? 'slide-right' : 'slide-left'" mode="out-in">
        <div class="card" :key="currentStatus">
          <div class="model-area">
            <PetRenderer
              :base="ASSET_DIR"
              :initial-anim="statusMap[currentStatus]"
              loop
              class="model"
            />
          </div>
          <div class="info">
            <h3>{{ humanize(currentStatus) }}</h3>
            <p>{{ storyMap[currentStatus] }}</p>
          </div>
        </div>
      </transition>

      <!-- 小圆点进度 -->
      <div class="bullets">
        <span
          v-for="(s,i) in keys"
          :key="s"
          class="bullet"
          :class="{ active: i===currentPage }"
        ></span>
      </div>
    </div>

    <!-- 底部 CTA -->
    <button class="learn-more" @click="goToAbout">
      Learn More About PlateMate’s Story
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import PetRenderer from '@/components/PetRenderer.vue'

const ASSET_DIR = '/biped/'
const statusMap: Record<string,string> = {
  egg:    'egg.glb',
  idle:   'Animation_You_Groove_withSkin.glb',
  walk:   'Animation_Walking_withSkin.glb',
  run:    'Animation_RunFast_withSkin.glb',
  running:'Animation_Running_withSkin.glb',
  dance:  'Animation_Boom_Dance_withSkin.glb',
  hype:   'Animation_All_Night_Dance_withSkin.glb',
  skill:  'Animation_Skill_01_withSkin.glb',
  gesture:'Animation_Agree_Gesture_withSkin.glb',
  tired:  'Animation_Slow_Orc_Walk_withSkin.glb',
  dizzy:  'Animation_Unsteady_Walk_withSkin.glb',
  woman:  'Animation_Walking_Woman_withSkin.glb',
  boxing: 'Animation_Boxing_Practice_withSkin.glb',
  arise:  'Animation_Arise_withSkin.glb',
  dead:   'Animation_Dead_withSkin.glb',
}

const storyMap: Record<string,string> = {
  egg:    'Every PlateMate journey starts as an egg… crack it open to reveal your inner sprite!',
  idle:   'When idle, PlateMate hums softly—waiting for your next culinary cue.',
  walk:   'PlateMate strolls through flavors, gathering spice essences.',
  run:    'PlateMate dashes between stations, ingredients flying!',
  running:'Full speed ahead—PlateMate races the sizzling wok.',
  dance:  'Recipe nailed? Time for PlateMate’s signature boom dance!',
  hype:   'Party mode on—PlateMate goes all-night hype dance!',
  skill:  'Watch PlateMate showcase its master seasoning skill.',
  gesture:'Well done, chef—PlateMate gives an approving nod.',
  tired:  'After endless chopping, PlateMate slows down—time for a breather.',
  dizzy:  'Too many spins? PlateMate is feeling dizzy—steady now!',
  woman:  'Ice in its veins—PlateMate struts with confident flair.',
  boxing: 'Sparring mood? PlateMate throws punches—cooking is its arena!',
  arise:  'Rise and shine—PlateMate leaps into action as flame ignites.',
  dead:   'Oops—PlateMate’s out cold. Better restart the session!',
}

const keys = Object.keys(statusMap)
const pages = computed(() => keys.length)

const currentPage = ref(0)
const slideDirection = ref<'left' | 'right'>('right')
function prevPage() {
  slideDirection.value = 'left'
  if (currentPage.value > 0) currentPage.value--
}
function nextPage() {
  slideDirection.value = 'right'
  if (currentPage.value + 1 < pages.value) currentPage.value++
}

const currentStatus = computed(() => keys[currentPage.value])

function humanize(k: string) {
  return k.charAt(0).toUpperCase() + k.slice(1)
}

const router = useRouter()
function goToAbout() {
  router.push('/about')
}

// 保持内容不被 header/footer 遮挡
const updateRootHeight = () => {
  const root = document.querySelector('.album-root') as HTMLElement
  const headerH = window.innerWidth < 600 ? 56 : 68
  root.style.top = `${headerH}px`
  root.style.bottom = `${parseInt(getComputedStyle(root).getPropertyValue('--safe-bottom'))}px`
}
onMounted(updateRootHeight)
onBeforeUnmount(() => window.removeEventListener('resize', updateRootHeight))
</script>

<style scoped>
:root {
  --safe-bottom: env(safe-area-inset-bottom,16px);
  --bg-start:      #e6f1ff;
  --bg-end:        #fff0f8;
  --accent-dark:   #ff1e9d;
  --text-main:     #333;
  --text-secondary:#555;
}

/* root container, absolutely positioned between the header and the bottom safe area */
.album-root {
  position: absolute;
  left: 0; right: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, var(--bg-start), var(--bg-end));
  box-sizing: border-box;
}

/* 走马灯 + 箭头区域 */
.nav-arrow {
  position: absolute;
  top: 50%; transform: translateY(-50%);
  width: 48px; height: 48px;
  border: none; background: rgba(255,255,255,0.8);
  color: var(--accent-dark); font-size: 1.5rem;
  border-radius: 50%; cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  z-index: 10;
  transition: background 150ms;
}
.nav-arrow:hover {
  background: rgba(255,255,255,1);
}
.nav-arrow:disabled {
  opacity: 0.3; cursor: default;
}
.nav-arrow.left  { left: 1rem; }
.nav-arrow.right { right: 1rem; }

/* Carousel 中心对齐 */
.carousel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 1rem;
}

/* 卡片与滑动效果 */
.slide-right-enter-active, .slide-right-leave-active,
.slide-left-enter-active, .slide-left-leave-active {
  transition: all 300ms ease;
}
.slide-right-enter-from { transform: translateX(100%); opacity: 0; }
.slide-right-leave-to   { transform: translateX(-100%); opacity: 0; }

.slide-left-enter-from { transform: translateX(-100%); opacity: 0; }
.slide-left-leave-to   { transform: translateX(100%); opacity: 0; }

.card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  overflow: hidden;
  width: 80%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
}

/* 3:2 模型区 */
.model-area {
  position: relative;
  width: 100%;
  padding-top: 66.66%;
  background: radial-gradient(circle at 50% 40%, rgba(255,110,196,0.1), rgba(255,30,157,0.05));
}
.model {
  position: absolute; inset: 0;
}

/* 文本信息 */
.info {
  padding: 1rem 1.2rem 1.5rem;
}
.info h3 {
  margin: 0 0 0.5rem;
  font-size: 1.3rem;
  color: var(--accent-dark);
  font-weight: 600;
}
.info p {
  margin: 0;
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* 分页小圆点 */
.bullets {
  position: absolute;
  bottom: 1.5rem; left: 50%;
  transform: translateX(-50%);
  display: flex; gap: 0.5rem;
}
.bullet {
  width: 10px; height: 10px;
  background: rgba(0,0,0,0.2);
  border-radius: 50%;
  transition: background 150ms;
}
.bullet.active {
  background: var(--accent-dark);
}

/* 底部 CTA */
.learn-more {
  margin: 0 auto 1rem;
  padding: 0.8rem 2rem;
  background: #0f83d7;
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(0,0,0,0.1);
  transition: transform 150ms, box-shadow 150ms;
}
.learn-more:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 26px rgba(0,0,0,0.15);
}

/* 移动端调整 */
@media (max-width: 767px) {
  .nav-arrow { width: 40px; height: 40px; font-size:1.2rem; }
  .info h3 { font-size: 1.2rem; }
  .learn-more { width: 90%; }
}
</style>

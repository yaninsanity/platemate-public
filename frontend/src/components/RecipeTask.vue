<template>
  <div class="tasks-card md:flex md:gap-8">
    <!-- ——— 左侧 / 顶部：Ingredient 任务 ——— -->
    <section class="flex-1">

      <h2 class="text-3xl font-extrabold text-indigo-600 mb-6 text-center whitespace-nowrap">
        🔍 Cooking&nbsp;&amp;&nbsp;Cuddle&nbsp;Mission
      </h2>

      <!-- 单任务：大卡 -->
      <div
        v-if="!store.loading && !store.error && store.tasks.length === 1"
        class="relative"
        @click="onBadgeClick(store.tasks[0], $event)"
      >
        <div
          class="big-card rounded-3xl overflow-hidden bg-gradient-to-br from-indigo-50 to-indigo-100 shadow-md cursor-pointer
                 transition-transform duration-500 group flex flex-col items-center p-6 md:p-8"
          :class="{ halo: !store.tasks[0].is_verified, 'rotate-y': store.tasks[0].is_verified }"
        >
          <!-- 图片 -->
          <img
            class="w-48 h-48 md:w-56 md:h-56 object-contain mb-4 select-none pointer-events-none"
            :src="resolveUrl(store.tasks[0].ingredient.default_picture || defaultPic)"
            :alt="store.tasks[0].ingredient.name"
          />

          <!-- Partner Completion Indicator -->
          <div v-if="getPartnerStatus(store.tasks[0])" class="partner-completion-badge">
            <span class="partner-icon">💕</span>
            <span class="partner-text">{{ getPartnerStatus(store.tasks[0]) }} completed this!</span>
          </div>

          <!-- ① 食材名字：粉嫩胶囊 -->
          <span class="ingredient-name-pill select-none">
            {{ store.tasks[0].ingredient.name }}
          </span>

          <!-- ② 状态文案：更可爱 -->
          <p
            class="mt-3 text-sm font-medium transition-colors"
            :class="{
              'text-emerald-600': store.tasks[0].is_verified,
              'text-pink-500': getPartnerStatus(store.tasks[0]) && !store.tasks[0].is_verified,
              'text-indigo-500 group-hover:text-indigo-700': !store.tasks[0].is_verified && !getPartnerStatus(store.tasks[0])
            }"
          >
            {{ getTaskStatusText(store.tasks[0]) }}
          </p>
        </div>
      </div>

      <!-- ================= ② 多任务：宫格 ================= -->
      <div
        v-else-if="!store.loading && !store.error"
        class="grid grid-cols-2 gap-4"
        role="list"
        aria-label="Today's cooking missions"
      >
        <div
          v-for="(task, idx) in store.tasks"
          :key="task.id"
          class="task-badge relative group"
          :class="getTaskStatusClass(task)"
          @click="onBadgeClick(task, $event)"
        >
          <!-- 完成遮罩 -->
          <div
            v-if="task.is_verified"
            class="absolute inset-0 bg-indigo-900 bg-opacity-50 flex items-center justify-center z-10 rounded-lg pointer-events-none"
          >
            <span class="text-4xl text-white">✔️</span>
          </div>

          <!-- Partner Completed Indicator -->
          <div
            v-else-if="getPartnerStatus(task)"
            class="absolute inset-0 bg-pink-500 bg-opacity-40 flex items-center justify-center z-10 rounded-lg pointer-events-none"
          >
            <span class="text-2xl text-white">💕</span>
          </div>

          <div
            class="card-inner"
            :class="{ 'rotate-y': task.is_verified }"
          >
            <!-- front -->
            <div
              class="card-front flex flex-col items-center justify-center p-3 rounded-lg bg-gradient-to-br from-indigo-50 to-indigo-100"
            >
              <span class="badge-num">{{ idx + 1 }}</span>
              <div class="img-box">
                <img
                  :src="resolveUrl(task.ingredient.default_picture || defaultPic)"
                  :alt="task.ingredient.name"
                  class="ingredient-img"
                />
              </div>
              <p class="font-medium text-gray-800 text-xs capitalize truncate">
                {{ task.ingredient.name }}
              </p>
            </div>

            <!-- back -->
            <div
              class="card-back flex flex-col items-center justify-center p-3 rounded-lg"
            >
              <span class="text-4xl animate-bounce-fast">🎉</span>
              <p class="text-xs mt-1 font-semibold text-indigo-600">Great!</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading / Error -->
      <p
        v-if="store.loading"
        class="text-center text-gray-400 animate-pulse py-6"
      >
        🔄 Loading mission…
      </p>
      <p
        v-if="store.error"
        class="text-center text-red-600 py-6"
      >
        ⚠️ {{ store.error }}
      </p>

      <!-- Enhanced Passion Meter with Partner Progress -->
      <div v-if="store.tasks.length" class="mt-8">
        <div class="flex justify-between items-center mb-1">
          <span class="font-medium text-gray-700">❤️ Passion Meter</span>
          <span class="font-mono text-sm">{{ store.doneCount }}/{{ store.tasks.length }}</span>
        </div>
        <div class="w-full bg-gray-200 h-3 rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 transition-all duration-500"
            :style="{ width: store.heatPercent + '%' }"
          />
        </div>
        
        <!-- Partner Progress Display -->
        <div v-if="store.hasPartner" class="mt-4 space-y-2">
          <div v-for="partner in store.partnerNames" :key="partner" class="partner-progress">
            <div class="flex justify-between items-center mb-1">
              <span class="font-medium text-pink-600 flex items-center">
                💕 {{ partner }}'s Progress
              </span>
              <span class="font-mono text-sm text-pink-600">
                {{ store.getPartnerProgress(partner)?.completed_tasks || 0 }}/{{ store.getPartnerProgress(partner)?.total_tasks || 0 }}
              </span>
            </div>
            <div class="w-full bg-pink-100 h-2 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-pink-300 to-pink-500 transition-all duration-500"
                :style="{ 
                  width: store.getPartnerProgress(partner) 
                    ? (store.getPartnerProgress(partner)!.completed_tasks / Math.max(store.getPartnerProgress(partner)!.total_tasks, 1) * 100) + '%' 
                    : '0%' 
                }"
              />
            </div>
          </div>
          
          <!-- Combined Couple Progress -->
          <div class="couple-combined-progress mt-3 pt-3 border-t border-gray-200">
            <div class="flex justify-between items-center mb-1">
              <span class="font-bold text-purple-700 flex items-center">
                👫 Together
              </span>
              <span class="font-mono text-sm text-purple-700">
                {{ store.overallCoupleProgress?.combined?.completed || 0 }}/{{ store.overallCoupleProgress?.combined?.total || 0 }}
              </span>
            </div>
            <div class="w-full bg-purple-100 h-4 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400 transition-all duration-500"
                :style="{ 
                  width: (store.overallCoupleProgress?.combined?.total || 0) > 0 
                    ? ((store.overallCoupleProgress?.combined?.completed || 0) / (store.overallCoupleProgress?.combined?.total || 1) * 100) + '%' 
                    : '0%' 
                }"
              />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ——— 右侧 / 底部：探店支线 ——— -->
    <aside class="mt-8 md:mt-0 md:w-80">
      <MarketScanner />
    </aside>

    <!-- 验证模态 -->
    <IngredientVerifyModal
      :visible="Boolean(selected)"
      :task="selected!"
      :loading="store.loading"
      @cancel="onCancel"
      @confirm="onVerifyConfirm"
    />
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import defaultPic from '@/assets/default-ingredient.png'
import IngredientVerifyModal from './IngredientVerifyModal.vue'
import MarketScanner from '@/components/MarketScanner.vue'
import { useTaskStore } from '@/stores/taskStore'
import { useUserStore } from '@/stores/userStore'
import type { Task } from '@/models/task'

/* —— props & emits —— */
const props = defineProps<{ recipeId?: number }>()
const emit  = defineEmits(['unlocked'])

/* —— store & state —— */
const store    = useTaskStore()
const userStore = useUserStore()
const selected = ref<Task | null>(null)

/* —— utils —— */
const ORIGIN = window.location.origin
const resolveUrl = (u: string) => u.replace(/^https?:\/\/web:\d+/, ORIGIN)

function ripple(e: MouseEvent) {
  const el = e.currentTarget as HTMLElement
  const circle = document.createElement('span')
  const size = Math.max(el.clientWidth, el.clientHeight)
  Object.assign(circle.style, {
    width: `${size}px`, height: `${size}px`,
    left: `${e.offsetX - size / 2}px`, top: `${e.offsetY - size / 2}px`,
  })
  circle.className = 'ripple'
  el.appendChild(circle)
  setTimeout(() => circle.remove(), 600)
}

function onBadgeClick(t: Task, e: MouseEvent) {
  if (t.is_verified) return
  
  // 用户级别验证：确保任务属于当前用户
  if (t.user && userStore.user?.id && t.user !== userStore.user.id) {
    console.warn('Task belongs to different user, cannot verify')
    return
  }
  
  // an unassigned task belonging to a couple is assigned to the current user
  if (!t.user && userStore.user?.id) {
    console.log('Task not assigned, will be assigned to current user during verification')
  }
  
  ripple(e)
  selected.value = t
}
const onCancel = () => (selected.value = null)
const onVerifyConfirm = async () => {
  if (!selected.value) return
  
  // 最后检查：确保验证的是当前用户的任务或未分配的任务
  if (selected.value.user && userStore.user?.id && selected.value.user !== userStore.user.id) {
    console.error('Cannot verify task belonging to different user')
    selected.value = null
    return
  }
  
  try {
    await store.verifyTask(selected.value.id)
    console.log('Task verified successfully, state refreshed')
  } catch (error) {
    console.error('Verification failed:', error)
  }
  
  selected.value = null
}

/* —— Enhanced partner interaction helpers —— */
function getPartnerStatus(task: Task): string | null {
  if (!task.ingredient?.id) return null
  
  // 重要：只有当前用户任务未完成时，才显示伴侣完成状态
  if (task.is_verified) return null
  
  // 使用新的store方法检查是否应该显示伴侣状态
  if (!store.shouldShowPartnerStatus(task.id, task.ingredient.id)) return null
  
  // has the partner finished the same ingredient?
  const partnerInfo = store.getPartnerWhoCompletedIngredient(task.ingredient.id)
  return partnerInfo ? partnerInfo.partnerName : null
}

function getTaskStatusClass(task: Task): string {
  // 首先检查当前用户的任务状态
  if (task.is_verified) return 'user-completed'
  
  // 只有当前用户未完成时，才检查伴侣状态
  if (getPartnerStatus(task)) return 'partner-completed'
  
  return 'pending'
}

function getTaskStatusText(task: Task): string {
  // 优先显示当前用户的状态
  if (task.is_verified) return 'Captured ✔︎'
  
  // 只有当前用户未完成时，才提示伴侣已完成
  const partner = getPartnerStatus(task)
  if (partner) return `${partner} got this! 💕`
  
  return 'Hold to snap 📸'
}

/* —— load —— */
async function reload() {
  store.clear()
  if (props.recipeId !== undefined) {
    await store.fetchTasks(props.recipeId)
  }
}
onMounted(reload)
watch(() => props.recipeId, reload)
watch(() => store.allDone, v => v && emit('unlocked'))
</script>
<style scoped>
:root{
  --r:1rem;                /* radius */
  --sh-sm:0 2px 5px rgba(0,0,0,.08);
  --sh-lg:0 4px 12px rgba(0,0,0,.12);
}

/* ——— 容器 —— */
.tasks-card{
  max-width:420px;padding:1rem .9rem 1.75rem;margin:1.6rem auto;
  background:#fff;border-radius:var(--r);box-shadow:var(--sh-lg);
}
@media(min-width:768px){.tasks-card{max-width:720px;padding:1.5rem 1.6rem 2rem}}

/* ——— 单任务大卡 —— */
.big-card{
  aspect-ratio:1/1;background:linear-gradient(135deg,#eef2ff,#e0e7ff);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:.8rem;border-radius:var(--r);box-shadow:var(--sh-sm);transition:.5s;
}
.big-card img{width:65%;max-width:9rem;object-fit:contain}
.rotate-y{transform:rotateY(180deg)}
.halo{position:relative}
.halo::after{
  content:'';position:absolute;inset:-3px;border-radius:inherit;
  background:radial-gradient(circle at center,rgba(99,102,241,.25),transparent 70%);
  animation:halo 2.1s infinite
}
@keyframes halo{0%,100%{transform:scale(.9);opacity:.4}50%{transform:scale(1.07);opacity:1}}
.ingredient-name-pill{
  padding:.18rem .9rem;font-size:.9rem;font-weight:600;
  background:#f4f4ff;border:1px solid rgba(99,102,241,.1);border-radius:9999px;
  color:#4338ca;box-shadow:0 1px 3px rgba(0,0,0,.04)
}

/* ——— 多任务宫格 —— */
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.55rem}
@media(max-width:420px){.grid{grid-template-columns:repeat(2,1fr)}}
.task-badge{height:8rem;perspective:1000px}
.card-inner{width:100%;height:100%;position:relative;transform-style:preserve-3d;transition:.5s}
.rotate-y .card-inner{transform:rotateY(180deg)}
.card-front,.card-back{
  position:absolute;inset:0;border-radius:.75rem;display:flex;flex-direction:column;
  align-items:center;justify-content:center;background:#eef2ff
}
.card-back{transform:rotateY(180deg)}
.img-box{width:2.9rem;height:2.9rem;border-radius:.4rem;overflow:hidden;margin-bottom:.25rem}
.ingredient-img{width:100%;height:100%;object-fit:cover}
.badge-num{
  position:absolute;top:.3rem;left:.3rem;width:1.4rem;height:1.4rem;
  line-height:1.4rem;background:#fff;border-radius:50%;font-size:.65rem;
  font-weight:700;color:#6366f1;box-shadow:var(--sh-sm)
}

/* 任务完成遮罩 & 翻面 */
.task-badge .completed{
  position:absolute;inset:0;background:rgba(31,41,55,.6);border-radius:.75rem;
  display:flex;align-items:center;justify-content:center;font-size:1.8rem;color:#fff;z-index:10
}

/* ——— 动效 —— */
@keyframes bounce-fast{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
.animate-bounce-fast{animation:bounce-fast .9s infinite}
.ripple{
  position:absolute;border-radius:50%;background:rgba(255,255,255,.6);
  transform:scale(0);animation:rip .55s ease-out forwards;pointer-events:none
}
@keyframes rip{to{transform:scale(3);opacity:0}}

/* ——— Enhanced Partner Interaction Styles —— */
.partner-completion-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #fce7f3, #fdf2f8);
  border: 1px solid #f9a8d4;
  border-radius: 999px;
  margin-bottom: 0.5rem;
  animation: gentlePulse 2s infinite;
}

.partner-icon {
  font-size: 1.2rem;
}

.partner-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: #be185d;
}

@keyframes gentlePulse {
  0%, 100% { transform: scale(1); opacity: 0.9; }
  50% { transform: scale(1.02); opacity: 1; }
}

/* Task Status Classes */
.task-badge.user-completed {
  box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
}

.task-badge.partner-completed {
  box-shadow: 0 0 15px rgba(236, 72, 153, 0.4);
  border: 2px solid rgba(236, 72, 153, 0.3);
}

.task-badge.partner-completed .card-front {
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
}

.task-badge.pending {
  box-shadow: 0 2px 5px rgba(0,0,0,.08);
}

/* Partner Progress Styles */
.partner-progress {
  padding: 0.75rem;
  background: linear-gradient(135deg, #fef7ff, #fdf4ff);
  border: 1px solid #f3e8ff;
  border-radius: 0.75rem;
  margin-bottom: 0.5rem;
}

.couple-combined-progress {
  padding: 0.75rem;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
}

/* ——— Passion Meter —— */
.mt-8{margin-top:1.2rem}
.mt-8 .flex{margin-bottom:.35rem}
.w-full{height:.5rem}
.w-full div{transition:width .4s ease;background:linear-gradient(90deg,#6366f1,#a855f7,#ec4899)}
</style>

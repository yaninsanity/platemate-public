<template>
  <div class="pet-ecosystem">
    <!-- backdrop at z-index 1; it only blurs what is behind -->
    <transition name="overlay-fade">
      <div 
        v-if="expanded" 
        class="background-overlay" 
        @click="toggleExpanded"
      />
    </transition>

    <!-- 主容器：z-index 10，保持在遮罩之上 -->
    <div class="pet-container" :class="{ expanded }">
      <div class="pet-stage" @click="toggleExpanded">
        <PetRenderer 
          ref="pet" 
          :initial-anim="animations[0]" 
          :background-color="expanded ? '#f0f4f8' : 'transparent'"
        />
      </div>

      <!-- 操作面板：z-index 20，确保在容器最顶层 -->
      <transition name="controls-slide">
        <div v-if="expanded" class="action-panel">
          <div class="panel-header">
            <h3 class="panel-title">Pet Actions</h3>
            <v-btn 
              icon="mdi-close" 
              variant="text" 
              size="small"
              @click="toggleExpanded"
            />
          </div>
          <div class="actions-grid">
            <v-card
              v-for="item in navItems"
              :key="item.label"
              class="action-card"
              elevation="2"
              @click="handleAction(item)"
            >
              <div class="card-icon">
                <v-icon :icon="item.icon" size="32" />
              </div>
              <v-card-title class="card-title">{{ item.label }}</v-card-title>
            </v-card>
          </div>
        </div>
      </transition>

      <!-- 快捷按钮：z-index 30，始终可点 -->
      <div class="quick-actions">
        <v-btn
          v-for="f in animations"
          :key="f"
          class="quick-action-btn"
          density="comfortable"
          variant="flat"
          color="primary"
          rounded="lg"
          @click.stop="play(f)"
        >
          <v-icon :icon="getAnimationIcon(f)" size="20" class="mr-1" />
          {{ prettyName(f) }}
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import PetRenderer from './PetRenderer.vue'

const router = useRouter()
const animations = [
  'Animation_Walking_withSkin.glb',
  'Animation_RunFast_withSkin.glb',
  'Animation_You_Groove_withSkin.glb'
]

interface Item { 
  label: string; icon: string; route?: string; anim?: string; action?: string 
}

const navItems: Item[] = [
  { label: 'Cook Together', icon: 'mdi-chef-hat', action: 'cook' },
  { label: 'Feed Pet',       icon: 'mdi-bone',       action: 'feed' },
  { label: 'Walk',           icon: 'mdi-walk',       anim: animations[0] },
  { label: 'Run',            icon: 'mdi-run-fast',   anim: animations[1] },
  { label: 'Groove',         icon: 'mdi-music',      anim: animations[2] },
  { label: 'Profile',        icon: 'mdi-account',    route: '/profile' },
  { label: 'Home',           icon: 'mdi-home',       route: '/' }
]

const expanded = ref(false)
const pet      = ref<InstanceType<typeof PetRenderer>|null>(null)

function toggleExpanded() {
  expanded.value = !expanded.value
}

function play(file: string) { 
  pet.value?.play(file) 
}

function handleAction(item: Item) {
  if (item.route) router.push(item.route)
  if (item.anim)   play(item.anim)
  if (item.action) window.dispatchEvent(new CustomEvent('platemate-action',{ detail:item.action }))
  // 触发后自动收起
  setTimeout(()=> expanded.value = false, 300)
}

function prettyName(f: string) { 
  return f.replace(/^Animation_|_withSkin\.glb$/g,'').replace(/_/g,' ') 
}

function getAnimationIcon(file: string) {
  if (file.includes('Walking'))    return 'mdi-walk'
  if (file.includes('RunFast'))     return 'mdi-run-fast'
  if (file.includes('Groove'))      return 'mdi-music'
  return 'mdi-paw'
}
</script>

<style scoped>
.pet-ecosystem {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 100;
  transition: all 0.4s cubic-bezier(0.33,1,0.68,1);
}

/* Overlay: 只模糊背景，z-index:1 */
.background-overlay {
  position: fixed;
  inset: 0;
  z-index: 1;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(8px);
}

/* 主容器: z-index:10 */
.pet-container {
  position: relative;
  z-index: 10;
  width: 240px; height: 240px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  transition: all 0.4s cubic-bezier(0.33,1,0.68,1);
  background: linear-gradient(145deg,#ffffff,#f0f0f0);
  border: 1px solid rgba(255,255,255,0.5);
}
.pet-container.expanded {
  width: 90vw; max-width:800px;
  height: 80vh; max-height:700px;
  border-radius: 20px;
}

/* 点击区 */
.pet-stage {
  position: absolute; inset:0;
  cursor: pointer; z-index: 10;
}

/* 操作面板: z-index:20 */
.action-panel {
  position: absolute; top:0; right:0;
  z-index: 20;
  width: 300px; height:100%;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(10px);
  padding:20px; box-sizing:border-box;
  box-shadow: -5px 0 15px rgba(0,0,0,0.05);
  border-left:1px solid rgba(0,0,0,0.05);
}

/* Panel Header */
.panel-header {
  display:flex; justify-content:space-between; align-items:center;
  margin-bottom:20px; padding-bottom:15px;
  border-bottom:1px solid rgba(0,0,0,0.08);
}
.panel-title { font-size:1.4rem; font-weight:600; color:#333; margin:0; }

/* Actions Grid */
.actions-grid {
  display:grid; grid-template-columns:repeat(2,1fr);
  gap:16px; height:calc(100% - 60px); overflow-y:auto; padding-right:8px;
}

/* Action Card */
.action-card {
  cursor:pointer; transition:all .25s;
  border-radius:14px; overflow:hidden;
  height:120px; display:flex; flex-direction:column;
  justify-content:center; align-items:center;
  background: rgba(255,255,255,0.7);
  border:1px solid rgba(0,0,0,0.05);
}
.action-card:hover {
  transform:translateY(-5px);
  box-shadow:0 8px 20px rgba(0,0,0,0.1);
}
.card-icon {
  width:60px; height:60px; border-radius:50%;
  background:linear-gradient(135deg,#f093fb,#f5576c);
  display:flex; justify-content:center; align-items:center;
  margin-bottom:12px;
}
.card-icon .v-icon { color:#fff; }
.card-title { font-size:.95rem; font-weight:500; text-align:center; padding:0 8px; }

/* Quick Actions: z-index:30 */
.quick-actions {
  position:absolute; bottom:16px; left:50%;
  transform:translateX(-50%);
  display:flex; gap:8px; z-index:30; width:90%; justify-content:center;
}
.quick-action-btn {
  backdrop-filter: blur(6px);
  background:rgba(255,255,255,0.8)!important;
  border:1px solid rgba(255,255,255,0.5)!important;
  box-shadow:0 4px 12px rgba(0,0,0,0.08)!important;
  transition:all .2s ease;
}
.quick-action-btn:hover {
  transform:translateY(-3px);
  box-shadow:0 6px 16px rgba(0,0,0,0.12)!important;
}

/* Transitions */
.overlay-fade-enter-active,
.overlay-fade-leave-active { transition:opacity .3s ease; }
.overlay-fade-enter-from,
.overlay-fade-leave-to { opacity:0; }

.controls-slide-enter-active,
.controls-slide-leave-active { transition:transform .4s cubic-bezier(.33,1,.68,1); }
.controls-slide-enter-from,
.controls-slide-leave-to { transform:translateX(100%); }

/* Responsive */
@media (max-width:768px) {
  .pet-container.expanded { width:95vw; height:85vh; }
  .action-panel {
    width:100%; height:auto; top:auto; bottom:0;
    border-left:none; border-top:1px solid rgba(0,0,0,0.08);
  }
  .actions-grid {
    grid-template-columns:repeat(3,1fr);
    height:auto; max-height:200px;
  }
  .quick-actions { flex-wrap:wrap; bottom:8px; }
  .quick-action-btn {
    padding:0 12px; height:36px; font-size:.8rem;
  }
}
</style>

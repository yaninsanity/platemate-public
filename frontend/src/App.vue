<template>
  <v-app>
    <!-- transparent top HUD, rendered immediately with no loading gate -->
   <BaseHeader
    v-if="isAuthenticated"
    :status="pet.status"           
    :unread="mailUnread"
/>

    <!-- 主内容：手动留出 52px 顶部空隙 -->
    <v-main class="app-main">
      <router-view/>
    </v-main>

    <!-- 底部圆形导航 / 脚注 / BGM …… -->
    <!-- <BaseNav v-if="isAuthenticated" /> -->
    <!-- <BaseFooter/> -->
    <BaseBgmRadio
      src="/assets/sounds/bgm.mp3"
      label="BGM • blossmom"
      :auto="true"
      :volume="0.6"
    />
  </v-app>
</template>

<script setup lang="ts">
/* Root app shell: avoid calling usePetStore() at module load time */
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { usePetStore } from '@/stores/petStore'
import type { Pet, PetStatus } from '@/models/pet'

// 🎯 精准改善：实时认证状态监听，立即响应无loading
const isAuthenticated = ref(!!localStorage.getItem('auth_token'))

function updateAuthState() {
  const newAuthState = !!localStorage.getItem('auth_token')
  if (isAuthenticated.value !== newAuthState) {
    // 🎯 精准改善：极简切换，避免长时间loading
    isAuthenticated.value = newAuthState
    console.log('[App] Auth state changed:', newAuthState)
    
    // 🎯 精准改善：立即同步更新，无延迟响应
    if (newAuthState) {
      console.log('[App] User logged in - Header should render immediately')
      // 立即初始化pet数据，不阻塞UI
      initializePetData()
    } else {
      console.log('[App] User logged out - Header should hide immediately')
      // 清理pet数据
      try {
        const petStore = getStore()
        petStore.stopPolling()
      } catch (e) { /* ignore */ }
    }
  }
}

// 🎯 新增：强制刷新认证状态的方法
function forceAuthRefresh() {
  console.log('[App] Force auth refresh triggered')
  updateAuthState()
  // 强制Vue重新渲染
  nextTick(() => {
    if (isAuthenticated.value) {
      console.log('[App] Forcing header re-render after auth change')
    }
  })
}

// Lazy store initialization to avoid calling before Pinia is installed
let store: ReturnType<typeof usePetStore> | null = null
function getStore() {
  if (!store) {
    store = usePetStore()
  }
  return store
}

// Get pet status from backend via store instead of hardcoding
const pet = computed<Pet>(() => {
  try {
    const petStore = getStore()
    return {
      id: petStore.pet?.id || 0,
      nickname: petStore.pet?.nickname || '',
      skin: petStore.pet?.skin || '',
      level: petStore.level,
      xp: petStore.xp,
      status: {
        hunger: petStore.health,
        happiness: petStore.energy,
        hygiene: petStore.hygiene,
      },
    }
  } catch (error) {
    // Fallback when store is not ready
    return {
      id: 0,
      nickname: '',
      skin: '',
      level: 1,
      xp: 0,
      status: {
        hunger: 0,
        happiness: 0,
        hygiene: 0,
      },
    }
  }
})

const mailUnread = ref(0)

// Initialize pet data when authenticated
async function initializePetData() {
  try {
    const petStore = getStore()
    
    // 1. Load from cache first to reduce white screen
    const cache = localStorage.getItem('platemate_pet_cache')
    if (cache) {
      try { 
        petStore.pet = JSON.parse(cache)
        console.log('[App] Loaded pet from cache:', petStore.pet)
      } catch { /* ignore invalid cache */ }
    }

    // 2. Immediately fetch fresh data from server
    console.log('[App] Fetching fresh pet data...')
    await petStore.fetchPet()
    
    // 3. Start polling for future updates
    petStore.startPolling()
    console.log('[App] Pet data initialized successfully')
  } catch (error) {
    console.error('[App] Failed to initialize pet data:', error)
  }
}

// 🎯 精准改善：统一的认证更新处理
function updateAuth() {
  updateAuthState()
}

onMounted(() => {
  // 🎯 performance tuning：立即检查认证状态
  updateAuthState()
  
  // 🎯 performance tuning：只监听必要的事件，避免重复触发
  window.addEventListener('auth-changed', forceAuthRefresh)
  
  // 🎯 listen to storage only, for cross-tab sync; popstate is unnecessary
  window.addEventListener('storage', (e) => {
    // 只关心token变化
    if (e.key === 'auth_token' || e.key === 'refresh_token') {
      console.log('[App] Storage changed - token updated')
      updateAuthState()
    }
  })
  
  window.addEventListener('beforeunload', () => {
    // 页面卸载前保存状态
    try {
      const petStore = getStore()
      localStorage.setItem('platemate_pet_cache', JSON.stringify(petStore.pet))
    } catch (e) { /* ignore */ }
  })
  
  // 🎯 performance tuning：移除轮询，改用事件驱动
  // 不需要每5秒检查，因为：
  // 1. 登录/登出时会触发 'auth-changed' 事件
  // 2. 跨标签页时会触发 'storage' 事件
  // 3. userStore的缓存机制会避免重复API调用
  
  // 如果已认证则立即初始化
  if (isAuthenticated.value) {
    console.log('[App] Already authenticated on mount, initializing...')
    initializePetData()
  }
  
  // 清理函数
  onUnmounted(() => {
    window.removeEventListener('auth-changed', forceAuthRefresh)
    window.removeEventListener('storage', updateAuthState)
    
    // 停止轮询
    try {
      const petStore = getStore()
      petStore.stopPolling()
    } catch (error) {
      console.warn('[App] Error stopping polling on unmount:', error)
    }
  })
})

import BaseHeader   from '@/components/BaseHeader.vue'
import BaseFooter   from '@/components/BaseFooter.vue'
import BaseBgmRadio from '@/components/BaseBgmRadio.vue'

// reserved hook for future mail actions
function onMail () {}
</script>

<style>
/* v-main 自己留出 HUD 高度，避免内容被遮 */
.app-main{
  padding-top: 70px;          /* 🎯 与 BaseHeader height=70 对齐 */
}

/* 响应式适配 BaseHeader 高度 */
@media (max-width: 768px) {
  .app-main {
    padding-top: 64px;        /* 🎯 与移动端 BaseHeader height=64 对齐 */
  }
}

@media (max-width: 480px) {
  .app-main {
    padding-top: 58px;        /* 🎯 与小屏 BaseHeader height=58 对齐 */
  }
}
</style>

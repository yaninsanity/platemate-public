<template>
  <v-app-bar
    flat
    absolute
    height="70"
    class="game-hud"
    color="transparent"
    :style="{ 'z-index': 2000 }"
  >
    <!-- 左侧区域：Profile Navigation -->
    <div class="hud-left">
      <!-- 🎮 AAAprofile navigation button, deliberately game-like -->
      <button 
        ref="avatarButtonRef"
        class="profile-nav-btn" 
        @click="toggleProfileMenu"
        :class="{ 'menu-open': showProfileMenu, 'avatar-loading': avatarLoading }"
      >
        <div class="profile-glow"></div>
        <div class="profile-energy-ring"></div>
        
        <!-- 头像容器 - 精准渲染管理 -->
        <div class="avatar-container">
          <img 
            :src="avatarSrc" 
            class="profile-avatar" 
            alt="Player Avatar"
            :class="{ 'avatar-error': avatarError }"
            @error="handleAvatarError"
            @load="handleAvatarLoad"
          />
          <!-- 加载指示器 -->
          <div v-if="avatarLoading" class="avatar-loading-spinner"></div>
        </div>
        
        <div class="profile-ring"></div>
        <div class="profile-pulse"></div>
      </button>
      
      <!-- 🍽️ Feed Island 组件化 - 精准Header一体化设计 -->
      <FeedIsland class="header-feed" :hunger="health" @open-feed="onHungerClick" />
    </div>

    <!-- centre: PetHUDRow, the core game HUD, shown off the home page only -->
    <div v-if="showPetHUD" class="hud-center" :class="{ 'hud-center-visible': showPetHUD }">
      <Transition name="hud-slide-fade" mode="out-in">
        <PetHUDRow 
          class="header-pet-hud"
          :status="petStore.petStatus"
          :msg="currentHudMessage"
          :size="petHudSize"
          :countdown="10000"
          @hide="nextHudMessage"
        />
      </Transition>
    </div>
 
    <!-- 右侧区域：Logo (仅Home页面显示) -->
    <div class="hud-right">
      <div v-if="isHomePage" class="home-logo-corner" @click="goToRecipes">
        <img src="/assets/logo4.png" class="corner-logo" alt="PlateMate Logo" />
      </div>
    </div>
  </v-app-bar>

  <!-- 🍽️ FeedPanel弹窗 -->
  <FeedPanel 
    v-model="showFeedPanel" 
    :current-hunger="health" 
    @feed="handleFeed"
  />

  <!-- 🎮 Enhanced Navigation Panel -->
  <NavigationPanel
    :is-visible="showProfileMenu"
    :avatar-src="avatarSrc"
    @close="closeNavigation"
    @home="handleHomeClick"
    @messages="handleMessagesClick"
    @battle="handleBattleClick"
    @about="handleAboutClick"
    @profile="handleProfileClick"
    @logout="handleSignoutClick"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import DynamicIsland    from '@/components/DynamicIsland.vue'
import FeedPanel        from '@/components/FeedPanel.vue'
import FeedIsland       from '@/components/FeedIsland.vue'
import NavigationPanel  from '@/components/NavigationPanel.vue'
import PetHUDRow        from '@/components/PetHudRow.vue'
import { useUserStore } from '@/stores/userStore'
import { usePetStore } from '@/stores/petStore'

/* ---------- Stores & Router ---------- */
// 🎯 initialise the user store defensively so login and logout do not glitch rendering
const router = useRouter()
const emit = defineEmits<{ (e: 'click-mail'): void; (e: 'hunger-updated', value: number): void }>()

const userStore = ref<any>(null)
const isStoreInitialized = ref(false)

function initializeUserStore() {
  try {
    if (!userStore.value) {
      userStore.value = useUserStore()
      isStoreInitialized.value = true
    }
    return userStore.value
  } catch (error) {
    console.warn('[BaseHeader] UserStore not ready yet:', error)
    isStoreInitialized.value = false
    return null
  }
}

function getUserStore() {
  return initializeUserStore()
}

/* ---------- Props & Derived ---------- */
const props = defineProps<{
  status?: { hunger: number; happiness: number; hygiene: number }
  health?: number
  unread?: number
  icon?: 'mail' | 'bell'
}>()
const health = computed(() => props.status ? props.status.hunger : props.health ?? 0)
const unreadCount = computed(() => props.unread ?? 0)
const computedIcon = computed(() => (props.icon === 'bell' ? 'mdi-bell-outline' : 'mdi-email-outline'))
const homeIconSrc = computed(() => (health.value < 50 ? '/assets/hunger.png' : '/assets/home.png'))

/* ---------- FeedPanel State ---------- */
const showFeedPanel = ref(false)

/* ---------- PetHUDRow Message Logic (Backend Real Data - 仅非Home页面显示) ---------- */
const petStore = usePetStore()
const hudMessageIndex = ref(0)

// 🎯 当前是否为Home页面
const isHomePage = computed(() => {
  const currentRoute = router.currentRoute.value.path
  return currentRoute === '/' || currentRoute === '/home'
})

// 🎯 显示条件：不在Home页面 && 有真实消息数据
const showPetHUD = computed(() => {
  const hasMessages = petStore.stateMessages && petStore.stateMessages.length > 0
  return !isHomePage.value && hasMessages
})

// 🎮 响应式Pet尺寸 - 根据屏幕宽度调整
const petHudSize = computed(() => {
  if (typeof window === 'undefined') return 55
  const width = window.innerWidth
  if (width < 480) return 45  // 手机
  if (width < 768) return 50  // 平板
  return 55  // 桌面
})

// the HUD message on screen, taken from the backend stateMessages
const currentHudMessage = computed(() => {
  const messages = petStore.stateMessages
  if (!messages || messages.length === 0) {
    return 'Welcome! Start your cooking adventure! 🍳✨'
  }
  
  const message = messages[hudMessageIndex.value % messages.length]
  return String(message || 'Kinny is waiting for you! 🐾')
})

// 切换到下一条消息
function nextHudMessage() {
  const messages = petStore.stateMessages
  if (messages && messages.length > 0) {
    hudMessageIndex.value = (hudMessageIndex.value + 1) % messages.length
  }
}

/* ---------- Profile Dropdown State ---------- */
const showProfileMenu = ref(false)
const avatarButtonRef = ref<HTMLElement | null>(null)

// 切换profile菜单显示
function toggleProfileMenu() {
  showProfileMenu.value = !showProfileMenu.value
  
  // AAAhaptic feedback
  if (navigator.vibrate) {
    navigator.vibrate(30)
  }
}

// Profile dropdown handlers with navigation
function handleHomeClick() {
  goHome()
  showProfileMenu.value = false
}

function handleMessagesClick() {
  handleMailClick()
  showProfileMenu.value = false
}

function handleProfileClick() {
  router.push('/profile')
  showProfileMenu.value = false
}

function handleAboutClick() {
  router.push('/about')
  showProfileMenu.value = false
}

// Logo点击：跳转到Recipe页面
function goToRecipes() {
  router.push('/roundly-quest')
}

function handleSignoutClick() {
  handleLogout()
  showProfileMenu.value = false
}

function closeNavigation() {
  showProfileMenu.value = false
}

function handleBattleClick() {
  router.push('/battle_history')
  showProfileMenu.value = false
}

// AAA级点击交互
const onHungerClick = () => {
  // 打开FeedPanel弹窗
  showFeedPanel.value = true
  
  // 立即的视觉反馈
  const hungerEl = document.querySelector('.hunger-display-aaa')
  if (hungerEl) {
    hungerEl.classList.add('clicked')
    setTimeout(() => hungerEl.classList.remove('clicked'), 300)
  }
  
  // AAA级触觉和音效反馈
  if (navigator.vibrate) {
    navigator.vibrate([50, 25, 50]) // 复合震动反馈
  }
}

// 处理喂食完成
function handleFeed(food: any, newHunger: number) {
  // 这里可以调用API更新后端数据
  console.log(`Fed ${food.name}, new hunger: ${newHunger}%`)
  
  // AAA级成功反馈
  if (navigator.vibrate) {
    navigator.vibrate([100, 50, 100, 50, 200])
  }
  
  // 可以emit事件给父组件更新状态
  emit('hunger-updated', newHunger)
}

/* ---------- Avatar ---------- */
// 精准头像渲染管理 - 修复PNG加载问题
import defaultAvatar from '@/assets/default-avatar.png'
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
const avatarSrc = ref<string>(defaultAvatar)
const avatarLoading = ref<boolean>(false)
const avatarError = ref<boolean>(false)

async function loadAvatar() {
  if (avatarLoading.value) return // 防止重复加载
  
  try {
    avatarLoading.value = true
    avatarError.value = false
    
    const s = getUserStore()
    if (!s || !isStoreInitialized.value) {
      console.warn('[BaseHeader] UserStore not initialized, using default avatar')
      avatarSrc.value = defaultAvatar
      return
    }
    
    // 🎯 performance: fetchProfile serves from cache for two minutes
    await s.fetchProfile() // 内部已有缓存机制，不会重复调用API
    const userAvatar = fix(s.avatar)
    
    if (userAvatar && userAvatar !== defaultAvatar) {
      // 创建新的Image对象进行预加载
      const img = new Image()
      img.crossOrigin = 'anonymous' // 处理跨域问题
      
      await new Promise<void>((resolve, reject) => {
        img.onload = () => {
          avatarSrc.value = userAvatar
          avatarError.value = false
          resolve()
        }
        img.onerror = () => {
          console.warn('[BaseHeader] Failed to load user avatar, using default')
          avatarSrc.value = defaultAvatar
          avatarError.value = true
          resolve() // 不reject，使用默认头像
        }
        img.src = userAvatar
      })
    } else {
      avatarSrc.value = defaultAvatar
    }
  } catch (error) {
    console.error('[BaseHeader] Error loading avatar:', error)
    avatarSrc.value = defaultAvatar
    avatarError.value = true
  } finally {
    avatarLoading.value = false
  }
}

// 头像加载事件处理
function handleAvatarLoad() {
  avatarError.value = false
  avatarLoading.value = false
}

function handleAvatarError() {
  console.warn('[BaseHeader] Avatar load error, falling back to default')
  avatarSrc.value = defaultAvatar
  avatarError.value = true
  avatarLoading.value = false
}

onMounted(() => {
  // 🎯 performance: load once on mount and let the cache absorb the rest
  console.log('[BaseHeader] Mounting - initializing stores and avatar')
  
  // 立即初始化stores
  initializeUserStore()
  
  // 🎯 load on first mount only; later calls reuse the fetchProfile cache
  loadAvatar()
  
  // 🎯 performance tuning：只监听登出事件，避免重复调用API
  const handleLogout = () => {
    console.log('[BaseHeader] User logged out - clearing avatar')
    avatarSrc.value = defaultAvatar
  }
  
  // listen for logout only; logging in remounts the component anyway
  window.addEventListener('user-logout', handleLogout)
  
  // 清理函数
  onUnmounted(() => {
    window.removeEventListener('user-logout', handleLogout)
  })
})

/* ---------- Navigation Actions ---------- */
function handleMailClick() {
  router.push({ name: 'Messages' })
  emit('click-mail')
}
function goHome() { router.push('/') }

async function handleLogout() {
  // 🎯 精准 logout 处理：确保完整渲染和状态清理
  try {
    const s = getUserStore()
    if (s) {
      await s.logout()
    }
    
    // 立即触发认证状态更新
    window.dispatchEvent(new Event('auth-changed'))
    
    // 短暂延迟后跳转，确保状态更新完成
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // 使用replace而非直接跳转，避免浏览器历史问题
    router.replace('/login')
  } catch (error) {
    console.error('[BaseHeader] Logout error:', error)
    // 即使出错也要清理状态
    try { 
      const s = getUserStore()
      if (s) s.clearAuth() 
    } catch (e) { 
      localStorage.removeItem('auth_token') 
    }
    
    // 触发认证状态更新并跳转
    window.dispatchEvent(new Event('auth-changed'))
    router.replace('/login')
  }
}

// 保留原有的 logout 函数作为备用
async function logout() {
  const s = getUserStore()
  if (s) {
    await s.logout()
  }
  router.replace('/login')
  location.reload()
}
</script>

<style scoped>
/* 🎮 AAA级游戏HUD - 最佳实践设计 */
.game-hud {
  background: linear-gradient(180deg, 
    rgba(0,0,0,0.9) 0%, 
    rgba(0,0,0,0.6) 50%, 
    rgba(0,0,0,0.4) 100%
  );
  backdrop-filter: blur(20px);
  border-bottom: 2px solid rgba(255,255,255,0.1);
  box-shadow: 
    0 4px 32px rgba(0,0,0,0.4),
    inset 0 1px 0 rgba(255,255,255,0.1);
  position: relative;
  overflow: visible;
  height: 70px !important;
}

.game-hud::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255,255,255,0.3), 
    transparent
  );
}

.game-hud :deep(.v-toolbar__content) {
  /* 🎯 drop the max-width so this matches RoundlyBattleHistoryView填充整个视口 */
  margin: 0;
  padding: 0 1.5rem !important;
  display: grid !important;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  height: 100% !important;
  gap: 12px;
  width: 100%;
  box-sizing: border-box;
}

/* 左侧区域 - 精准固定布局 */
.hud-left {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-self: start;
  align-self: start;
  margin-top: 9px;
  flex-wrap: nowrap;
  position: relative; /* 精准：相对定位确保稳定 */
}

/* 🎮 FeedIsland tuning inside the header, fixing the overflow */
.header-feed :deep(.hunger-display-aaa) {
  width: clamp(360px, 42vw, 520px) !important;
  height: 54px !important;
  border: 2px solid rgba(255,255,255,0.25);
  background: linear-gradient(145deg, rgba(15,15,20,0.95), rgba(8,8,12,0.92));
  backdrop-filter: blur(25px) saturate(1.8);
  overflow: hidden; /* 精准防止超出 */
}

.header-feed :deep(.hunger-status-row) {
  margin-bottom: 0px !important; /* 精准控制间距 */
  padding-top: 1px !important; /* 微调位置 */
}

.header-feed :deep(.hunger-percentage) {
  font-size: 18px !important;
  min-width: 56px !important;
  max-width: 56px !important;
  font-weight: 900;
  text-shadow: 0 2px 6px rgba(0,0,0,0.9);
}

.header-feed :deep(.hunger-label) {
  font-size: 13px !important; /* 精准调整大小 */
  letter-spacing: 1.6px !important;
  margin-top: 0px !important; /* 消除多余边距 */
  font-weight: 900;
  line-height: 1.1 !important; /* 精准控制行高 */
  transform: translateY(0px) !important; /* 重置位置 */
}

.header-feed :deep(.hunger-status) {
  font-size: 13px !important; /* 匹配label大小 */
  letter-spacing: 1.0px !important;
  margin-top: 0px !important;
  font-weight: 900;
  line-height: 1.1 !important; /* 精准控制行高 */
  transform: translateY(0px) !important; /* 重置位置 */
}

.header-feed :deep(.hunger-icon-section),
.header-feed :deep(.hunger-action-aaa) { 
  height: 54px !important; 
}

/* 中央区域 - PetHUDRow AAA游戏设计 */
.hud-center {
  justify-self: center;
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 0;
  max-width: 900px;
  padding: 0 16px;
  position: relative;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.hud-center-visible {
  opacity: 1;
}

/* 🎮 Header中的PetHUDRow - AAA级一体化设计 */
.header-pet-hud {
  width: 100%;
  max-width: 100%;
}

/* deep style overrides for PetHUDRow inside the header */
.header-pet-hud :deep(.hud) {
  background: linear-gradient(135deg, 
    rgba(20, 20, 30, 0.75) 0%, 
    rgba(15, 15, 25, 0.85) 100%);
  backdrop-filter: blur(25px) saturate(1.6);
  border: 2px solid rgba(255, 255, 255, 0.15);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 0 40px rgba(168, 230, 207, 0.1);
  border-radius: 24px;
  padding: 0.7rem 0.95rem;
  height: 62px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  /* 🎯 精准固定宽度 - 防止内容变化导致Header跳动 */
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

.header-pet-hud :deep(.hud:hover) {
  background: linear-gradient(135deg, 
    rgba(25, 25, 35, 0.8) 0%, 
    rgba(18, 18, 28, 0.9) 100%);
  border-color: rgba(168, 230, 207, 0.3);
  box-shadow: 
    0 10px 40px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.25),
    0 0 50px rgba(168, 230, 207, 0.15);
  transform: translateY(-1px);
}

/* Pet头像 - 游戏级光效 */
.header-pet-hud :deep(.pet) {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  box-shadow: 
    0 0 20px rgba(168, 230, 207, 0.4),
    0 4px 12px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.header-pet-hud :deep(.pet:hover) {
  transform: scale(1.08);
  box-shadow: 
    0 0 30px rgba(168, 230, 207, 0.6),
    0 6px 16px rgba(0, 0, 0, 0.4);
}

/* 气泡 - AAA级文字显示 */
.header-pet-hud :deep(.bubble) {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.12) 0%, 
    rgba(255, 255, 255, 0.06) 100%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
  height: 48px;
  border-radius: 14px;
}

.header-pet-hud :deep(.bubble:hover) {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.16) 0%, 
    rgba(255, 255, 255, 0.08) 100%);
  border-color: rgba(168, 230, 207, 0.3);
}

.header-pet-hud :deep(.bubble-text) {
  color: rgba(255, 255, 255, 0.95);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.3px;
  text-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.6),
    0 0 8px rgba(168, 230, 207, 0.3);
  line-height: 1.35;
}

.header-pet-hud :deep(.bubble-icon) {
  font-size: 1.15em;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.4));
}

.header-pet-hud :deep(.bubble-progress) {
  background: linear-gradient(90deg, 
    rgba(168, 230, 207, 0.4) 0%, 
    rgba(168, 230, 207, 0.6) 50%,
    rgba(168, 230, 207, 0.4) 100%);
  height: 3px;
  bottom: 0;
  box-shadow: 0 0 8px rgba(168, 230, 207, 0.5);
}

/* HUD切换动画 - 游戏级过渡 */
.hud-slide-fade-enter-active,
.hud-slide-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.hud-slide-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.hud-slide-fade-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.95);
}

/* 右侧区域 - 精准定位Logo，防止溢出 */
.hud-right {
  display: flex;
  justify-content: flex-end; /* 🎯 确保内容靠右对齐 */
  gap: 8px;
  justify-self: end;
  flex-shrink: 0; /* 🎯 固定尺寸，防止压缩 */
  height: 100%; /* 🎯 占满整个header高度 */
  overflow: hidden; /* 🎯 防止溢出 */
}

/* 🎮 AAAprofile navigation button, precisely pinned */
.profile-nav-btn {
  width: 56px !important;
  height: 56px !important;
  min-width: 56px !important;
  min-height: 56px !important;
  border-radius: 50% !important;
  background: linear-gradient(145deg, 
    rgba(30,30,45,0.95) 0%, 
    rgba(20,20,35,0.9) 50%, 
    rgba(15,15,25,0.95) 100%) !important;
  border: 3px solid rgba(100,255,150,0.6);
  box-shadow: 
    0 0 20px rgba(100,255,150,0.3),
    0 8px 25px rgba(0,0,0,0.4),
    inset 0 2px 0 rgba(255,255,255,0.3),
    inset 0 -2px 0 rgba(0,0,0,0.3);
  cursor: pointer;
  position: relative;
  overflow: visible;
  transition: box-shadow 0.3s ease, border-color 0.3s ease; /* 精准：仅动画阴影和边框 */
  flex-shrink: 0;
  aspect-ratio: 1 / 1;
  backdrop-filter: blur(15px) saturate(1.5);
  z-index: 10;
  transform: none !important; /* 精准：强制禁用所有变换 */
  align-items: center;
  justify-items: center;
  margin-right: 1rem;
}

.profile-nav-btn:hover {
  border-color: rgba(100,255,150,0.9);
  box-shadow: 
    0 0 30px rgba(100,255,150,0.6),
    0 12px 40px rgba(0,0,0,0.5),
    0 0 0 8px rgba(100,255,150,0.2),
    inset 0 3px 0 rgba(255,255,255,0.4),
    inset 0 -3px 0 rgba(0,0,0,0.4);
  /* drop the transform so the position stays fixed */
}

.profile-nav-btn:active {
  box-shadow: 
    0 0 25px rgba(100,255,150,0.5),
    0 8px 20px rgba(0,0,0,0.4);
  /* drop the transform so the position stays fixed */
}

.profile-glow {
  position: absolute;
  top: -15px;
  left: -15px;
  right: -15px;
  bottom: -15px;
  background: radial-gradient(circle, rgba(100,255,150,0.4) 0%, transparent 70%);
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.4s ease;
  filter: blur(8px);
}

.profile-nav-btn:hover .profile-glow {
  opacity: 1;
  animation: profileGlowPulse 2.5s ease-in-out infinite;
}

/* 🎮 新增：能量环 */
.profile-energy-ring {
  position: absolute;
  top: -8px;
  left: -8px;
  right: -8px;
  bottom: -8px;
  border: 2px solid transparent;
  border-radius: 50%;
  background: conic-gradient(from 0deg, 
    rgba(100,255,150,0.8) 0%, 
    rgba(50,200,255,0.8) 33%, 
    rgba(255,100,200,0.8) 66%, 
    rgba(100,255,150,0.8) 100%);
  mask: radial-gradient(circle, transparent 68%, black 70%);
  -webkit-mask: radial-gradient(circle, transparent 68%, black 70%);
  animation: energyRingRotate 8s linear infinite;
  opacity: 0.7;
}

.profile-nav-btn:hover .profile-energy-ring {
  opacity: 1;
  animation: energyRingRotate 3s linear infinite;
}

@keyframes profileGlowPulse {
  0%, 100% { transform: scale(1); opacity: 0.4; }
  50% { transform: scale(1.15); opacity: 0.8; }
}

@keyframes energyRingRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 🎯 精准头像容器 - 固定定位，无位移 */
.avatar-container {
  position: relative;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  overflow: hidden;
  z-index: 12;
  transform: none !important; /* transforms disabled deliberately */
}

.profile-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  filter: drop-shadow(0 3px 6px rgba(0,0,0,0.4));
  transition: filter 0.3s ease; /* 精准：仅动画滤镜效果 */
  border: 2px solid rgba(255,255,255,0.6);
  box-shadow: 
    inset 0 1px 0 rgba(255,255,255,0.3),
    0 2px 8px rgba(0,0,0,0.3);
  background: linear-gradient(145deg, rgba(30,30,45,0.8), rgba(20,20,35,0.9));
  transform: none !important; /* transforms disabled deliberately */
}

.profile-avatar.avatar-error {
  filter: grayscale(50%) brightness(0.8);
}

.avatar-loading-spinner {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top: 2px solid rgba(100,255,150,0.8);
  border-radius: 50%;
  animation: avatarSpin 1s linear infinite;
  transform: translate(-50%, -50%);
  z-index: 13;
}

@keyframes avatarSpin {
  0% { transform: translate(-50%, -50%) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(360deg); }
}

.profile-nav-btn.avatar-loading .profile-energy-ring {
  animation: energyRingRotate 1s linear infinite;
}

.profile-nav-btn:hover .profile-avatar {
  filter: brightness(1.2) contrast(1.1) drop-shadow(0 3px 6px rgba(0,0,0,0.4));
  /* 精准：移除transform，仅保留滤镜效果 */
}

/* 🌟 粒子效果装饰 */
.profile-nav-btn::before {
  content: '';
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  background: radial-gradient(circle at 20% 80%, rgba(100,255,150,0.3) 0%, transparent 50%),
              radial-gradient(circle at 80% 20%, rgba(50,200,255,0.3) 0%, transparent 50%),
              radial-gradient(circle at 40% 40%, rgba(255,100,200,0.3) 0%, transparent 50%);
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 8;
  pointer-events: none;
}

.profile-nav-btn:hover::before {
  opacity: 1;
  animation: particleFloat 4s ease-in-out infinite;
}

@keyframes particleFloat {
  0%, 100% { transform: rotate(0deg) scale(1); }
  33% { transform: rotate(120deg) scale(1.05); }
  66% { transform: rotate(240deg) scale(0.95); }
}

.profile-ring {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border: 2px solid rgba(255,255,255,0);
  border-radius: 50%;
  transition: all 0.3s ease;
  z-index: 11;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.2);
}

.profile-nav-btn:hover .profile-ring {
  border-color: rgba(255,255,255,0.8);
  box-shadow: 
    0 0 0 1px rgba(255,255,255,0.3),
    0 0 20px rgba(255,255,255,0.2);
  animation: profileRingRotate 3s linear infinite;
}

@keyframes profileRingRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.profile-nav-btn::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 120%;
  height: 120%;
  border: 2px solid rgba(64, 255, 128, 0);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.3s ease;
  z-index: 9;
}

.profile-nav-btn:hover::after {
  border-color: rgba(64, 255, 128, 0.6);
  animation: profilePulse 2s ease-in-out infinite;
}

@keyframes profilePulse {
  0%, 100% { 
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.6;
  }
  50% { 
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0.3;
  }
}

/* 📱 移动端AAA级tuning */
@media (max-width: 768px) {
  .game-hud { height: 64px !important; }
  .game-hud :deep(.v-toolbar__content) { 
    padding: 0 1rem !important;  /* 🎯 matches RoundlyBattleHistoryView on mobile */
    gap: 10px; 
  }
  
  .hud-left, .hud-right {
    gap: 12px;
  }
  
  .hud-center {
    max-width: 700px;
    padding: 0 10px;
  }
  
  .header-pet-hud :deep(.hud) {
    height: 56px;
    padding: 0.65rem 0.8rem;
    border-radius: 20px;
  }
  
  .header-pet-hud :deep(.pet) {
    width: 48px;
    height: 48px;
  }
  
  .header-pet-hud :deep(.bubble) {
    height: 44px;
    border-radius: 12px;
  }
  
  .header-pet-hud :deep(.bubble-text) {
    font-size: 0.75rem;
    letter-spacing: 0.2px;
  }
  
  .profile-nav-btn {
    width: 52px !important;
    height: 52px !important;
    min-width: 52px !important;
    min-height: 52px !important;
    border: 3px solid rgba(255,255,255,0.6) !important;
    box-shadow: 
      0 8px 25px rgba(0,0,0,0.4),
      0 0 0 2px rgba(255,255,255,0.3),
      inset 0 2px 0 rgba(255,255,255,0.4);
    z-index: 15 !important;
    transform: none !important; /* 精准：移动端也禁用变换 */
  }
  
  .avatar-container {
    width: 38px;
    height: 38px;
    transform: none !important; /* 精准：移动端禁用变换 */
  }
  
  .profile-avatar {
    border: 3px solid rgba(255,255,255,0.6) !important;
    transform: none !important; /* 精准：移动端禁用变换 */
  }
  
  .profile-ring {
    z-index: 16 !important;
    box-shadow: 0 0 0 2px rgba(255,255,255,0.3);
  }
  
  .feed-wrapper :deep(.hunger-display-aaa) { width: clamp(320px, 62vw, 520px) !important; height: 50px !important; }
  .feed-wrapper :deep(.hunger-percentage) { font-size: 16px !important; min-width: 48px !important; max-width: 48px !important; }
  .inv-badge { top: -6px; right: -6px; width: 24px; height: 24px; font-size: 13px; }
}

@media (max-width: 480px) {
  .game-hud { height: 58px !important; }
  .game-hud :deep(.v-toolbar__content) { 
    padding: 0 1rem !important;  /* 🎯 保持与中等屏幕一致的 padding */
    gap: 6px; 
  }
  
  .hud-left, .hud-right {
    gap: 6px;
  }
  
  .hud-center {
    max-width: 600px;
    padding: 0 6px;
  }
  
  .header-pet-hud :deep(.hud) {
    height: 52px;
    padding: 0.5rem 0.65rem;
    border-radius: 18px;
  }
  
  .header-pet-hud :deep(.pet) {
    width: 44px;
    height: 44px;
  }
  
  .header-pet-hud :deep(.bubble) {
    height: 40px;
    border-radius: 11px;
  }
  
  .header-pet-hud :deep(.bubble-text) {
    font-size: 0.7rem;
    letter-spacing: 0.15px;
    line-height: 1.3;
  }
  
  .header-pet-hud :deep(.bubble-icon) {
    font-size: 1.05em;
  }
  
  .profile-nav-btn {
    width: 48px !important;
    height: 48px !important;
    min-width: 48px !important;
    min-height: 48px !important;
    border: 3px solid rgba(255,255,255,0.7) !important;
    z-index: 20 !important;
    transform: none !important; /* 精准：小屏幕也禁用变换 */
  }
  
  .avatar-container {
    width: 34px;
    height: 34px;
    transform: none !important; /* 精准：小屏幕禁用变换 */
  }
  
  .profile-avatar {
    border: 2px solid rgba(255,255,255,0.7) !important;
    transform: none !important; /* 精准：小屏幕禁用变换 */
  }
  
  .profile-ring {
    z-index: 21 !important;
  }
  
  .feed-wrapper :deep(.hunger-display-aaa) { width: clamp(280px, 90vw, 500px) !important; height: 46px !important; }
  .feed-wrapper :deep(.hunger-percentage) { font-size: 15px !important; min-width: 44px !important; max-width: 44px !important; }
  .feed-wrapper :deep(.hunger-label) { font-size: 12px !important; }
  .feed-wrapper :deep(.hunger-status) { font-size: 12px !important; }
  .inv-badge { top: -8px; right: -8px; width: 26px; height: 26px; font-size: 13px; }
}

/* 🎮 performance tuning - 精准固定 */
.profile-nav-btn {
  will-change: box-shadow, border-color; /* 精准：仅tuning非位移属性 */
}

/* 🌟 暗色主题tuning */
@media (prefers-color-scheme: dark) {
  .game-hud {
    background: linear-gradient(180deg, 
      rgba(10,10,15,0.95) 0%, 
      rgba(5,5,10,0.8) 50%, 
      rgba(0,0,5,0.6) 100%
    );
  }
}

/* 🎯 减少动画偏好 - 精准控制 */
@media (prefers-reduced-motion: reduce) {
  .profile-nav-btn,
  .profile-glow,
  .profile-ring,
  .profile-energy-ring {
    animation: none !important;
    transition-duration: 0.2s !important;
    transform: none !important; /* transforms disabled deliberately */
  }
}

/* � AAAgamified message HUD, rendered as a hologram and not clickable */
.kinny-message-hud {
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, 
    rgba(15, 10, 30, 0.95), 
    rgba(25, 15, 45, 0.92),
    rgba(35, 20, 55, 0.95)
  );
  backdrop-filter: blur(30px) saturate(2.2);
  border-radius: 32px;
  border: 2px solid rgba(138, 180, 248, 0.4);
  box-shadow:
    inset 0 2px 8px rgba(138, 180, 248, 0.25),
    inset 0 -1px 4px rgba(0, 0, 0, 0.7),
    0 8px 32px rgba(99, 102, 241, 0.4),
    0 4px 16px rgba(138, 180, 248, 0.3),
    0 0 80px rgba(99, 102, 241, 0.2);
  pointer-events: none;
  transition: all 400ms cubic-bezier(0.34, 1.56, 0.64, 1);
  min-width: 380px;
  max-width: clamp(380px, 55vw, 620px);
  width: 100%;
  height: 68px;
  position: relative;
  overflow: hidden;
  padding: 0 16px;
  animation: hudBreathing 4s ease-in-out infinite;
}

@keyframes hudBreathing {
  0%, 100% { 
    box-shadow:
      inset 0 2px 8px rgba(138, 180, 248, 0.25),
      inset 0 -1px 4px rgba(0, 0, 0, 0.7),
      0 8px 32px rgba(99, 102, 241, 0.4),
      0 4px 16px rgba(138, 180, 248, 0.3),
      0 0 80px rgba(99, 102, 241, 0.2);
  }
  50% { 
    box-shadow:
      inset 0 2px 10px rgba(138, 180, 248, 0.35),
      inset 0 -1px 4px rgba(0, 0, 0, 0.7),
      0 12px 40px rgba(99, 102, 241, 0.5),
      0 6px 20px rgba(138, 180, 248, 0.4),
      0 0 100px rgba(99, 102, 241, 0.3);
  }
}

/* 能量场 + 全息扫描 */
.energy-field {
  position: absolute;
  inset: -25px;
  background: radial-gradient(ellipse at 20% 50%, 
    rgba(99, 102, 241, 0.4), 
    transparent 60%
  ), radial-gradient(ellipse at 80% 50%, 
    rgba(138, 180, 248, 0.3), 
    transparent 60%
  );
  opacity: 0.7;
  animation: energyFieldPulse 3.5s ease-in-out infinite;
  pointer-events: none;
  filter: blur(15px);
}

@keyframes energyFieldPulse {
  0%, 100% { opacity: 0.7; transform: scale(1) rotate(0deg); }
  50% { opacity: 1; transform: scale(1.08) rotate(5deg); }
}

.hologram-scan {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent 0px,
    rgba(138, 180, 248, 0.08) 1px,
    transparent 2px,
    transparent 4px
  );
  animation: hologramScan 2s linear infinite;
  pointer-events: none;
  opacity: 0.6;
}

@keyframes hologramScan {
  0% { transform: translateY(0); }
  100% { transform: translateY(4px); }
}

/* Kinny头像标识 - 游戏化设计 */
.kinny-avatar-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  position: relative;
}

.avatar-glow-ring {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: conic-gradient(from 0deg,
    rgba(99, 102, 241, 0.6),
    rgba(138, 180, 248, 0.6),
    rgba(167, 139, 250, 0.6),
    rgba(99, 102, 241, 0.6)
  );
  animation: avatarRingRotate 3s linear infinite;
  opacity: 0.8;
  filter: blur(4px);
}

@keyframes avatarRingRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.kinny-emoji {
  font-size: 26px;
  position: relative;
  z-index: 2;
  filter: drop-shadow(0 0 12px rgba(138, 180, 248, 0.8))
          drop-shadow(0 4px 8px rgba(0, 0, 0, 0.6));
  animation: emojiFloat 2.5s ease-in-out infinite;
}

@keyframes emojiFloat {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-3px) scale(1.08); }
}

/* 消息显示区 - 游戏化字体渲染 */
.message-display-zone {
  flex: 1;
  display: flex;
  align-items: center;
  min-width: 0;
  padding: 0 10px;
  position: relative;
}

.message-hologram {
  width: 100%;
  display: flex;
  align-items: center;
  animation: hologramFlicker 0.15s infinite alternate;
}

@keyframes hologramFlicker {
  0% { opacity: 0.98; }
  100% { opacity: 1; }
}

.message-text-gaming {
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', sans-serif;
  font-size: 0.85rem;
  font-weight: 800;
  letter-spacing: 0.3px;
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 
    0 0 25px rgba(138, 180, 248, 0.9),
    0 0 15px rgba(99, 102, 241, 0.7),
    0 2px 8px rgba(0, 0, 0, 0.9),
    0 4px 12px rgba(0, 0, 0, 0.6);
  line-height: 1.45;
  white-space: normal;
  word-break: break-word;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 1), 
    rgba(200, 220, 255, 0.98),
    rgba(180, 200, 255, 0.95),
    rgba(220, 230, 255, 0.98)
  );
  -webkit-background-clip: text;
  background-clip: text;
  background-size: 200% 100%;
  animation: textShine 4s ease-in-out infinite;
  filter: drop-shadow(0 0 16px rgba(138, 180, 248, 0.8));
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  max-height: 2.5rem;
  width: 100%;
}

@keyframes textShine {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* 全息淡入淡出 */
.hologram-fade-enter-active,
.hologram-fade-leave-active {
  transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hologram-fade-enter-from {
  opacity: 0;
  transform: translateX(30px) scale(0.9);
  filter: blur(8px);
}

.hologram-fade-leave-to {
  opacity: 0;
  transform: translateX(-30px) scale(0.9);
  filter: blur(8px);
}

/* 状态指示器 - 游戏化动态点 */
.status-indicators {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  padding-right: 4px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, 
    rgba(138, 180, 248, 0.9),
    rgba(99, 102, 241, 0.9)
  );
  box-shadow: 
    0 0 12px rgba(138, 180, 248, 0.8),
    inset 0 1px 2px rgba(255, 255, 255, 0.5);
}

.pulse-1 {
  animation: statusPulse 1.2s ease-in-out infinite;
}

.pulse-2 {
  animation: statusPulse 1.2s ease-in-out infinite 0.2s;
}

.pulse-3 {
  animation: statusPulse 1.2s ease-in-out infinite 0.4s;
}

@keyframes statusPulse {
  0%, 100% { 
    opacity: 0.4; 
    transform: scale(0.8);
    box-shadow: 0 0 8px rgba(138, 180, 248, 0.5);
  }
  50% { 
    opacity: 1; 
    transform: scale(1.2);
    box-shadow: 0 0 16px rgba(138, 180, 248, 1);
  }
}

/* 能量粒子 - 游戏化装饰 */
.energy-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
}

.energy-particle {
  position: absolute;
  width: var(--size, 2.5px);
  height: var(--size, 2.5px);
  border-radius: 50%;
  background: radial-gradient(circle, 
    rgba(138, 180, 248, 1), 
    rgba(99, 102, 241, 0.8),
    transparent
  );
  box-shadow: 0 0 8px rgba(138, 180, 248, 0.9);
  top: 50%;
  left: 50%;
  animation: energyParticleOrbit 4s ease-in-out infinite;
  animation-delay: var(--delay, 0s);
  opacity: 0;
}

@keyframes energyParticleOrbit {
  0% {
    transform: translate(-50%, -50%) rotate(var(--angle, 0deg)) translateX(0) scale(0);
    opacity: 0;
  }
  25% {
    opacity: 1;
  }
  50% {
    transform: translate(-50%, -50%) rotate(var(--angle, 0deg)) translateX(var(--distance, 40px)) scale(1);
    opacity: 0.9;
  }
  75% {
    opacity: 0.6;
  }
  100% {
    transform: translate(-50%, -50%) rotate(var(--angle, 0deg)) translateX(0) scale(0);
    opacity: 0;
  }
}

/* 📱 移动端响应式tuning - 更弹性的布局 */
@media (max-width: 1024px) {
  .kinny-message-hud {
    min-width: 320px;
    max-width: clamp(320px, 60vw, 560px);
    height: 64px;
  }
  
  .message-text-gaming {
    font-size: 0.8rem;
  }
}

@media (max-width: 768px) {
  .kinny-message-hud {
    min-width: 280px;
    max-width: clamp(280px, 70vw, 480px);
    height: 60px;
    gap: 8px;
    padding: 0 12px;
  }
  
  .kinny-avatar-badge {
    width: 38px;
    height: 38px;
  }
  
  .kinny-emoji {
    font-size: 22px;
  }
  
  .message-text-gaming {
    font-size: 0.75rem;
    max-height: 2.3rem;
  }
  
  .status-dot {
    width: 5px;
    height: 5px;
  }
}

@media (max-width: 480px) {
  .kinny-message-hud {
    min-width: 240px;
    max-width: clamp(240px, 85vw, 400px);
    height: 56px;
    gap: 6px;
    padding: 0 10px;
  }
  
  .kinny-avatar-badge {
    width: 34px;
    height: 34px;
  }
  
  .kinny-emoji {
    font-size: 20px;
  }
  
  .message-text-gaming {
    font-size: 0.7rem;
    max-height: 2.1rem;
    letter-spacing: 0.2px;
  }
  
  .status-indicators {
    gap: 4px;
  }
  
  .status-dot {
    width: 4px;
    height: 4px;
  }
}

/* ——— 🏠 top-right logo container rendering logo4.png ——— */
.home-logo-corner {
  /* 🎯 完美居中对齐 */
  display: flex;
  align-items: center;
  justify-content: center;
  
  /* 🎯 绝对边界控制 - 确保不溢出 */
  overflow: hidden;
  border-radius: 21px; /* 圆角矩形，适配宽屏logo */
  flex-shrink: 0; /* 固定尺寸，防止被压缩 */
  
  /* 🎯 交互 */
  cursor: pointer;
  position: relative;
  z-index: 1001;
  pointer-events: auto;
  
  /* 🎯 微妙背景 - 玻璃态 */
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.08) 0%, 
    rgba(255, 255, 255, 0.04) 100%);
  backdrop-filter: blur(10px) saturate(1.2);
  border: 1.5px solid rgba(255, 255, 255, 0.15);
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  
  /* 🎯 平滑过渡 */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    background: linear-gradient(135deg, 
      rgba(255, 107, 157, 0.12) 0%, 
      rgba(255, 107, 157, 0.06) 100%);
    border-color: rgba(255, 107, 157, 0.35);
    box-shadow: 
      0 6px 20px rgba(255, 107, 157, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.3);
    transform: translateY(-1px);
  }
  
  &:active {
    transform: translateY(0) scale(0.98);
  }
  
  /* 🎯 响应式 - 保持2.47:1宽高比，适配logo4.png */
  @media (min-width: 1200px) {
    border-radius: 23px;
  }
  
  @media (max-width: 768px) {
    border-radius: 19px;
  }
  
  @media (max-width: 480px) {
    border-radius: 17px;
  }
}

.corner-logo {
  /* 🎯 logo4.png 精准渲染：1196x484 完整显示不裁剪 */
  height: 70px;

  /* 🎯 完美渲染 - contain确保完整显示，不裁剪 */
  object-fit: contain;
  object-position: center;
  flex-shrink: 0;

  /* 🎯 高清渲染tuning - 平滑缩放 */
  image-rendering: -webkit-optimize-contrast;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
  transform: translateZ(0);
  will-change: transform;

  /* 🎯 柔和阴影 */
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.12));
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  /* 🎯 Hover效果 - 无缩放避免溢出 */
  .home-logo-corner:hover & {
    filter: drop-shadow(0 3px 10px rgba(255, 107, 157, 0.35));
  }

  .home-logo-corner:active & {
    filter: brightness(0.9);
  }
}
</style>

// src/router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  /* public pages */
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { hideChrome: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { hideChrome: true }
  },

  /* protected pages */
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/roundly-quest',
    name: 'RoundlyQuest',
    component: () => import('@/views/RoundlyQuestView.vue')
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/AboutView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/couple',
    name: 'CoupleSetup',
    component: () => import('@/views/CoupleSetupView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/album',
    name: 'Album',
    component: () => import('@/views/AlbumView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/markets',
    name: 'Markets',
    component: () => import('@/views/MarketFindView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/badges',
    name: 'Badges',
    component: () => import('@/views/BadgeView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/diary',
    name: 'MemoryPost',
    component: () => import('@/views/MemoryPostView.vue'),
    meta: { requiresAuth: true }
  },
  {
  path: '/messages',
  name: 'Messages',
  component: () => import('@/views/MessageView.vue'),
  meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/family_menu',
    name: 'FamilyMenu',
    component: () => import('@/views/FamilyMenuView.vue'),
  },
  {
    path:'/battle_history',
    name: 'BattleHistory',
    component: () => import('@/views/RoundlyBattleHistoryView.vue'),
    meta: { requiresAuth: true }},
  {
    path : '/battle/:roundId(\\d+)',
    name : 'RoundlyBattle',
    component: () => import('@/views/RoundlyBattleView.vue'),
    meta : { requiresAuth: true },
  },
  /* fallback */
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ left: 0, top: 0 }),
})

/* ───────── global guard ───────── */
router.beforeEach((to, _from, next) => {
  const loggedIn = !!localStorage.getItem('auth_token')

  // 1. need auth but not logged in
  if (to.meta.requiresAuth && !loggedIn) {
    return next({ name: 'Login', query: { next: to.fullPath } })
  }

  // 2. already logged in & opening login/register
  if (loggedIn && to.meta.hideChrome) {
    return next({ name: 'Home' })
  }

  return next()
})

export default router

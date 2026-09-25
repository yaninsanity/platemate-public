// src/stores/user.ts
import { defineStore } from 'pinia'
import api, { TOKEN_KEY, REFRESH_KEY } from '@/plugins/axios'
import router from '@/router'
import type { CustomUser, Couple, JoinCouplePayload } from '@/models/user'
import defaultAvatar from '@/assets/default-avatar.png'

// refresh margin in milliseconds: five minutes early, sized for a three-hour token
const REFRESH_BUFFER_MS = 5 * 60 * 1000

// 🎯 performance tuning：Profile缓存配置（减少重复API调用）
const PROFILE_CACHE_DURATION = 2 * 60 * 1000 // 2分钟缓存

/** 解析 JWT payload，拿 exp 做预刷新 */
function decodeJwtExp(token: string | null): number | null {
  if (!token) return null
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = JSON.parse(atob(parts[1]))
    return typeof payload?.exp === 'number' ? payload.exp : null
  } catch {
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token:   localStorage.getItem(TOKEN_KEY)   as string | null,
    refresh: localStorage.getItem(REFRESH_KEY) as string | null,
    user:    null as CustomUser | null,
    couple:  null as Couple | null,

    _refreshTimer: null as number | null,      // 预刷新计时器句柄
    _lastProfileFetch: 0,                      // 🎯 performance tuning：上次fetchProfile的时间戳
  }),

  getters: {
    isLoggedIn: (s) => !!s.token,
    avatar:     (s) => s.user?.avatar_url || defaultAvatar,
  },

  actions: {
    /* ---------- 登录 ---------- */
    async login(username: string, password: string) {
      // 后端 LoginView 现在返回 { token, refresh, detail }
      const { data } = await api.post<{ token: string; refresh: string; detail: string }>(
        '/users/auth/login/',
        { username, password }
      )
      
      // 🎯 精准改善：立即保存token
      this._saveTokens(data.token, data.refresh)
      
      // 🎯 立即获取用户资料（只调用1次）
      await this.fetchProfile()
      
      // 🎯 精准改善：立即初始化 petStore
      const { usePetStore } = await import('./petStore')
      const petStore = usePetStore()
      await petStore.initializePetData()
      
      // 🎯 performance: signal the auth change without re-fetching the profile
      // already fetched above; calls within two minutes hit the cache
      window.dispatchEvent(new Event('auth-changed'))
      
      // 🎯 go straight to Home; mounting will call fetchProfile again
      // 但由于缓存机制，不会真正调用API
      router.replace({ name: 'Home' })
    },

    /* ---------- 注册后自动登录 ---------- */
    async register(payload: { username: string; password: string; email: string }) {
      await api.post('/users/auth/register/', payload)
      await this.login(payload.username, payload.password)
    },

    /* ---------- 退出 ---------- */
    async logout() {
      try {
        // 带着 refresh 发给后端黑名单
        await api.post('/users/auth/logout/', { refresh: this.refresh })
      } catch {
        // 忽略网络错误，直接本地清理
      }
      this.clearAuth()
      this._lastProfileFetch = 0 // 🎯 清除缓存时间戳
      
      // 🎯 performance: emit only the logout event, not a redundant auth-changed
      window.dispatchEvent(new Event('user-logout'))
      
      router.replace({ name: 'Login' })
    },

    /* ---------- 拉取资料 ---------- */
    async fetchProfile(forceRefresh = false) {
      const now = Date.now()
      
      // 🎯 performance tuning：2分钟内复用缓存，避免重复API调用
      if (!forceRefresh && this.user && (now - this._lastProfileFetch) < PROFILE_CACHE_DURATION) {
        console.log('[UserStore] 🚀 Using cached profile (last fetched:', 
          Math.round((now - this._lastProfileFetch) / 1000), 'seconds ago)')
        return
      }

      console.log('[UserStore] 📡 Fetching fresh profile from API')
      console.trace('[UserStore] Call stack:')  // 🔍 追踪调用来源
      
      // 🎯 performance: request user and couple in parallel to cut latency
      const [userResponse, coupleResponse] = await Promise.allSettled([
        api.get<CustomUser>('/users/me/'),
        api.get<Couple>('/users/me/couple/')
      ])
      
      // 处理 user 数据
      if (userResponse.status === 'fulfilled') {
        this.user = userResponse.value.data
      } else {
        console.error('[UserStore] Failed to fetch user:', userResponse.reason)
        throw userResponse.reason
      }
      
      // 处理 couple 数据（可选，失败不影响用户数据）
      if (coupleResponse.status === 'fulfilled') {
        this.couple = coupleResponse.value.data
        console.log('[UserStore] ✅ Couple data loaded')
      } else {
        this.couple = null
        console.log('[UserStore] ℹ️ No couple data (user not in couple)')
      }
      
      this._lastProfileFetch = now // 🎯 更新缓存时间戳
    },

    /* ---------- 更新资料 ---------- */
    async updateProfile(payload: Partial<CustomUser> | FormData) {
      const headers = payload instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
      const { data } = await api.patch<CustomUser>('/users/me/', payload, { headers })
      this.user = data
      
      // 🎯 bump the cache timestamp so later fetchProfile calls see fresh data
      this._lastProfileFetch = Date.now()
      console.log('[UserStore] ✅ Profile updated and cache refreshed')
    },

    /* ---------- Couple 相关 ---------- */
    async createCouple() {
      const { data } = await api.post<Couple>('/users/me/couple/create/')
      this.couple = data
    },
    async joinCouple(code: string) {
      const { data } = await api.post<Couple>('/users/me/couple/join/', { code } as JoinCouplePayload)
      this.couple = data
    },
    async leaveCouple() {
      await api.post('/users/me/couple/leave/')
      this.couple = null
    },

    /* ---------- 刷新 Token ---------- */
    async refreshAccessToken(): Promise<string | null> {
      if (!this.refresh) return null
      try {
        const { data } = await api.post<{ access: string }>(
          '/token/refresh/',
          { refresh: this.refresh }
        )
        this._saveTokens(data.access, this.refresh)   // 只换 access
        return data.access
      } catch (err) {
        // refresh 失效，强制登出
        this.clearAuth()
        router.replace({ name: 'Login' })
        return null
      }
    },

    /* ---------- 预刷新定时器 ---------- */
    _setupRefreshTimer() {
      // 清理旧计时器
      if (this._refreshTimer) {
        clearTimeout(this._refreshTimer)
        this._refreshTimer = null
      }
      const exp = decodeJwtExp(this.token)
      if (!exp) return

      // exp 是秒，Date.now() 是毫秒
      const msUntilExp = exp * 1000 - Date.now()
      // 提前 1 分钟刷新
      const msUntilRefresh = Math.max(msUntilExp - REFRESH_BUFFER_MS, 0)

      this._refreshTimer = window.setTimeout(() => {
        // 静默刷新即可，不阻塞 UI
        this.refreshAccessToken()
      }, msUntilRefresh)
    },

    /* ---------- 保存 & 清理 ---------- */
    _saveTokens(access: string, refresh: string | null) {
      this.token   = access
      this.refresh = refresh
      localStorage.setItem(TOKEN_KEY, access)
      if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
      this._setupRefreshTimer()
    },

    clearAuth() {
      this.token = null
      this.refresh = null
      this.user = this.couple = null
      this._lastProfileFetch = 0 // 🎯 清除缓存时间戳
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_KEY)
      if (this._refreshTimer) {
        clearTimeout(this._refreshTimer)
        this._refreshTimer = null
      }
    },
  },
})

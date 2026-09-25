// src/plugins/axios.ts
import axios, { AxiosError, InternalAxiosRequestConfig, AxiosRequestConfig } from 'axios'
import router from '@/router'

/* ─────────────── 本地存储键 ─────────────── */
export const TOKEN_KEY   = 'auth_token'     // access token
export const REFRESH_KEY = 'refresh_token'  // refresh token

/* ─────────────── 基础配置 ─────────────── */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL : BASE_URL,
  timeout : 72000,
  headers : { 'Content-Type': 'application/json' },
})

// 一个“干净”的实例，用来刷新 token（避免拦截器递归）
const raw = axios.create({ baseURL: BASE_URL })

/* ─────────────── 小工具 ─────────────── */
const getAccess  = () => localStorage.getItem(TOKEN_KEY)
const getRefresh = () => localStorage.getItem(REFRESH_KEY)
const setAccess  = (t: string) => localStorage.setItem(TOKEN_KEY, t)
const clearAll   = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

let refreshPromise: Promise<string | null> | null = null
async function refreshAccessToken(): Promise<string | null> {
  // 已在刷新流程中则复用
  if (refreshPromise) return refreshPromise

  const refreshToken = getRefresh()
  if (!refreshToken) return null

  refreshPromise = raw
    .post<{ access: string }>('/token/refresh/', { refresh: refreshToken })
    .then(({ data }) => {
      setAccess(data.access)
      return data.access
    })
    .catch(() => null)
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

/* ─────────────── 📊 API调用追踪器 ─────────────── */
const apiCallTracker = new Map<string, number>()
let requestCounter = 0

/* ─────────────── 请求拦截：自动带 Bearer + 调用追踪 ─────────────── */
api.interceptors.request.use((cfg: InternalAxiosRequestConfig) => {
  const token = getAccess()
  if (token && cfg.headers && !cfg.headers.Authorization) {
    cfg.headers.Authorization = `Bearer ${token}`
  }
  
  // 🎯 性能监控：追踪API调用
  requestCounter++
  const requestId = requestCounter
  const url = `${cfg.method?.toUpperCase()} ${cfg.url}`
  const count = (apiCallTracker.get(url) || 0) + 1
  apiCallTracker.set(url, count)
  
  // 🚨 检测重复调用
  if (count > 1) {
    console.warn(`🚨 [API] Duplicate call #${count}:`, url, 'RequestID:', requestId)
    console.trace('Call stack:')
  } else {
    console.log(`📡 [API] Request #${requestId}:`, url)
  }
  
  return cfg
})

/* ─────────────── 响应拦截：401 自动刷新一次 + 响应日志 ─────────────── */
api.interceptors.response.use(
  (res) => {
    const url = `${res.config.method?.toUpperCase()} ${res.config.url}`
    console.log(`✅ [API] Success:`, url, `(${res.status})`)
    return res
  },
  async (err: AxiosError) => {
    const original = err.config as AxiosRequestConfig & { _retry?: boolean }

    if (err.response?.status !== 401) {
      return Promise.reject(err)
    }

    // 避免死循环
    if (original._retry) {
      clearAll()
      if (router.currentRoute.value.name !== 'Login') router.replace({ name: 'Login' })
      return Promise.reject(err)
    }
    original._retry = true

    // 尝试刷新
    const newToken = await refreshAccessToken()
    if (!newToken) {
      clearAll()
      if (router.currentRoute.value.name !== 'Login') router.replace({ name: 'Login' })
      return Promise.reject(err)
    }

    // 更新并重试原请求
    original.headers = {
      ...original.headers,
      Authorization: `Bearer ${newToken}`,
    }
    return api(original)
  }
)

/* ─────────────── 📊 全局API统计工具 ─────────────── */
// 在控制台使用: window.showAPIStats()
if (typeof window !== 'undefined') {
  (window as any).showAPIStats = () => {
    console.group('📊 API Call Statistics')
    console.log('Total requests:', requestCounter)
    console.log('\nDuplicate calls detected:')
    
    const duplicates = Array.from(apiCallTracker.entries())
      .filter(([_, count]) => count > 1)
      .sort((a, b) => b[1] - a[1])
    
    if (duplicates.length === 0) {
      console.log('✅ No duplicate calls detected!')
    } else {
      duplicates.forEach(([url, count]) => {
        console.warn(`🚨 ${url}: ${count} calls`)
      })
    }
    
    console.log('\nAll calls:')
    Array.from(apiCallTracker.entries())
      .sort((a, b) => b[1] - a[1])
      .forEach(([url, count]) => {
        console.log(`  ${url}: ${count}x`)
      })
    console.groupEnd()
  }
  
  (window as any).resetAPIStats = () => {
    apiCallTracker.clear()
    requestCounter = 0
    console.log('✅ API stats reset')
  }
}

export default api

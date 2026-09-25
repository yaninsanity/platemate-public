import axios from '@/plugins/axios'

const FALLBACK_ORIGIN = typeof window !== 'undefined' ? window.location.origin : ''
const BASE_INPUT = import.meta.env.VITE_API_BASE_URL ?? axios.defaults.baseURL ?? ''

const API_ORIGIN = (() => {
  if (!BASE_INPUT) return FALLBACK_ORIGIN
  try {
    // Support relative API base paths like "/api"
    return new URL(BASE_INPUT, FALLBACK_ORIGIN || 'http://localhost').origin
  } catch {
    return FALLBACK_ORIGIN
  }
})()

const CONTAINER_HOST_PATTERN = /^https?:\/\/(web|localhost|127\.0\.0\.1|45\.79\.163\.242)(:\d+)?/i

export function resolveURL(raw?: string | null): string | undefined {
  if (!raw) return undefined
  if (raw.startsWith('data:')) return raw

  if (/^https?:\/\//i.test(raw)) {
    return raw.replace(CONTAINER_HOST_PATTERN, API_ORIGIN)
  }

  if (raw.startsWith('//')) {
    const apiUrl = new URL(API_ORIGIN || FALLBACK_ORIGIN || 'http://localhost')
    return `${apiUrl.protocol}${raw}`
  }

  const normalized = raw.startsWith('/') ? raw : `/${raw}`
  return `${API_ORIGIN}${normalized}`
}

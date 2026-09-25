import { defineStore } from 'pinia'
import api from '@/plugins/axios'

export const useAIStore = defineStore('ai', {
  state: () => ({
    loading: false,
    error:   null as string | null,
  }),

  actions: {
    async detect(imageUrl: string, target: string) {
      this.loading = true
      this.error   = null
      try {
        const { data } = await api.post('/cookai/detect/', {
          image: imageUrl,
          target,
        })
        return data as { detected: string[]; match: number }
      } catch (e: any) {
        this.error = e.response?.data?.detail || e.message
        throw e
      } finally {
        this.loading = false
      }
    },
  },
})

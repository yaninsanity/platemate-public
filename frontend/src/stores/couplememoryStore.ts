/* ────────────── couplememoryStore.ts (替换版) ────────────── */
import { defineStore }  from 'pinia'
import api              from '@/plugins/axios'
import type {
  CoupleMemory,
  MemoryEntry,
  MemoryComment,
  TopIngredients,
}                       from '@/models/couplememory'
import type { Recipe }  from '@/models/recipes'

/* ---------------- 新增：后端统一前缀 ---------------- */
const API_BASE = '/couplememory'  // ← 入口统一已加/api

/* ─────────── 扩展字段 ─────────── */
type CoupleMemoryEx = CoupleMemory & {
  recipes?: Recipe[]
  _loading?: boolean
  _error?: string
}

/* ─────────── endpoints ─────────── */
const MEM_BASE     = `${API_BASE}/memories`
const ENTRY_BASE   = `${API_BASE}/entries`
const COMMENT_BASE = `${API_BASE}/comments`
const MENU_BASE    = `${API_BASE}/family-menu`   // NEW

/* ─────────── tiny helpers ───────── */
function _log(msg: string, ...args: any[]) {
  console.debug('[CoupleMemory]', msg, ...args)
}
function _handleError(store: any, e: unknown, fallback: string) {
  const detail =
    (e as any)?.response?.data?.detail ??
    (e as any)?.message               ??
    fallback
  store.error = detail
  console.error('[CoupleMemory] ❌', detail)
}

/* ─────────── 聚合周内 recipe 的小工具 ─────────── */
function _collectRecipesFromEntries(entries: MemoryEntry[] = []): Recipe[] {
  const map: Record<number, Recipe> = {}
  entries.forEach(e => {
    if (e.recipe) map[(e.recipe as any).id] = e.recipe as unknown as Recipe
  })
  return Object.values(map)
}

export const useCoupleMemoryStore = defineStore('coupleMemory', {
  /* ─────────── state ─────────── */
  state: () => ({
    memories      : [] as CoupleMemoryEx[],
    current       : null as CoupleMemoryEx | null,
    topIngredients: {}  as TopIngredients,
    loading       : false,
    error         : ''  as string,
  }),

  /* ─────────── getters ─────────── */
  getters: {
    byId: (s) => (id: number) => s.memories.find(w => w.id === id) ?? null,
    roundByRecipe: (s) => (rid: number) =>
      s.memories.find(w => (w.recipes ?? []).some(r => r.id === rid)) ?? null,
  },

  /* ─────────── actions ─────────── */
  actions: {
    /* 1. paginated list */
    async fetchMemories(params?: {
      page?: number; page_size?: number; search?: string; ordering?: string
    }) {
      if (this.loading) return
      this.loading = true
      _log('fetchMemories →', params)
      try {
        const { data } = await api.get<{ results: CoupleMemory[] }>(
          `${MEM_BASE}/`, { params }
        )
        this.memories = data.results as CoupleMemoryEx[]
        
        _log(`✔ fetched ${data.results.length} round(s)`)
      } catch (e) {
        _handleError(this, e, 'Failed to load rounds')
      } finally {
        this.loading = false
      }
    },

    /* 2. current round */
    async fetchCurrent() {
      if (this.loading) return
      this.loading = true
      _log('fetchCurrent')
      try {
        const { data } = await api.get<CoupleMemory>(`${MEM_BASE}/current/`)
        this.current = data as CoupleMemoryEx
        _log('✔ current round id', data.id)
      } catch (e) {
        _handleError(this, e, 'Failed to load current round')
      } finally {
        this.loading = false
      }
    },

    /* 9. fetch by id (detail view) */
    async fetchRoundById(roundId: number, ignoreCache = false) {
      const cached = this.byId(roundId)
      if (cached && !ignoreCache) return cached

      this.loading = true
      _log(`fetchRoundById #${roundId}`)
      try {
        const { data } = await api.get<CoupleMemory>(`${MEM_BASE}/${roundId}/`)
        this.memories.push(data as CoupleMemoryEx)
        _log('✔ round fetched id', data.id)
        return data
      } catch (e) {
        _handleError(this, e, 'Failed to load this round')
        return null
      } finally {
        this.loading = false
      }
    },

    /* 10. lazy-load recipes for a round（先本地聚合，兜底远端） */
    async fetchRecipes(round: CoupleMemoryEx) {
      if (round.recipes) return

      /* ① 先用本地 entries 聚合 */
      const local = _collectRecipesFromEntries(round.entries)
      if (local.length) {
        round.recipes = local
        _log(`◎ round #${round.id} recipes (local)`, local.length)
        return
      }

      /* ② 兜底：调用原来的 memories/{id}/recipes/ */
      round._loading = true
      _log(`fetchRecipes → round #${round.id} (remote)`)
      try {
        const { data } = await api.get<Recipe[]>(`${MEM_BASE}/${round.id}/recipes/`)
        round.recipes = data                       // ← 这里就是纯数组
        _log(`✔ round #${round.id} recipes`, data.length)
      } catch (e) {
        round._error = (e as any)?.response?.data?.detail ?? 'Failed to load recipes'
        console.error('[CoupleMemory] ❌', round._error)
      } finally {
        round._loading = false
      }
    },


    /* 11. find round via recipeId (auto fetch if needed) */
    async findRoundByRecipe(rid: number): Promise<CoupleMemoryEx | null> {
      let hit = this.roundByRecipe(rid)
      if (hit) return hit

      for (const w of this.memories) {
        await this.fetchRecipes(w)
        if ((w.recipes ?? []).some(r => r.id === rid)) {
          hit = w
          break
        }
      }
      return hit ?? null
    },

    /* 3. patch summary */
    async updateSummary(roundId: number, summary: string) {
      this.loading = true
      _log(`updateSummary #${roundId}`)
      try {
        const { data } = await api.patch<CoupleMemory>(
          `${MEM_BASE}/${roundId}/summary/`, { summary }
        )
        if (this.current?.id === roundId) this.current = data as CoupleMemoryEx
        const idx = this.memories.findIndex(w => w.id === roundId)
        if (idx !== -1) this.memories[idx] = data as CoupleMemoryEx
        _log('✔ summary saved')
      } catch (e) {
        _handleError(this, e, 'Failed to update summary')
      } finally {
        this.loading = false
      }
    },

    /* 4. top-N ingredients */
    async fetchTopIngredients(roundId: number) {
      this.loading = true
      _log(`fetchTopIngredients #${roundId}`)
      try {
        const { data } = await api.get<TopIngredients>(
          `${MEM_BASE}/${roundId}/top_ingredients/`
        )
        this.topIngredients = data
        _log('✔ topIngredients', data)
      } catch (e) {
        _handleError(this, e, 'Failed to load top ingredients')
      } finally {
        this.loading = false
      }
    },

    /* 5. diary entry – create text first (tuning版) */
    async createEntry(recipeId: number, content: string, mood: string) {
      if (!this.current) {
        this.error = 'Current round not loaded'
        throw new Error('Current round not loaded')
      }
      
      this.loading = true
      _log('createEntry', { recipeId, content, mood })
      
      try {
        const { data } = await api.post<MemoryEntry>(`${ENTRY_BASE}/`, {
          recipe : recipeId,
          content, mood,
        })
        
        // 立即更新本地状态
        this.current.entries.unshift({ ...data, media: [], comments: [] })

        /* 立即把菜谱塞进当前周的 chip 列表 */
        if (!this.current.recipes) this.current.recipes = []
        if (recipeId && !this.current.recipes.some(r => r.id === recipeId) && data.recipe) {
          this.current.recipes.push(data.recipe as unknown as Recipe)
        }

        _log('✔ entry created id', data.id)
        return data
        
      } catch (e) {
        _handleError(this, e, 'Failed to create entry')
        throw e // 重新抛出错误，让调用方处理
      } finally {
        this.loading = false
      }
    },

    /* 6. add one picture (tuning版，支持重试) */
    async addMedia(entryId: number, file: File, isHighlight = false, retryCount = 0): Promise<MemoryEntry> {
      const maxRetries = 3
      this.loading = true
      _log(`addMedia → entry #${entryId}`, file, `(attempt ${retryCount + 1})`)
      
      try {
        const fd = new FormData()
        fd.append('media', file)
        fd.append('is_highlight', isHighlight ? 'true' : 'false')
        
        const { data } = await api.post<MemoryEntry>(
          `${ENTRY_BASE}/${entryId}/add_media/`, fd,
          { 
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 30000 // 30秒超时
          }
        )
        
        // 更新本地状态
        if (this.current) {
          const idx = this.current.entries.findIndex(e => e.id === entryId)
          if (idx !== -1) this.current.entries[idx] = data
        }
        
        _log('✔ media added')
        return data
        
      } catch (e) {
        // 如果是网络错误且还有重试次数，则重试
        if (retryCount < maxRetries && this._isRetryableError(e)) {
          _log(`⚠️ Media upload failed, retrying... (${retryCount + 1}/${maxRetries})`)
          await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1))) // 递增延迟
          return this.addMedia(entryId, file, isHighlight, retryCount + 1)
        }
        
        _handleError(this, e, 'Failed to upload media')
        throw e
      } finally {
        this.loading = false
      }
    },

    // 判断是否为可重试的错误
    _isRetryableError(error: any): boolean {
      const status = error?.response?.status
      const message = (error?.message || '').toLowerCase()
      // 仅对网络/超时重试；不对 4xx/5xx 重试
      return (
        !status ||
        status === 0 ||
        status === 408 ||
        message.includes('timeout') ||
        message.includes('network')
      )
    },

    /* 7. manual AI score override */
    async setAiScore(entryId: number, score: number) {
      this.loading = true
      _log(`setAiScore → entry #${entryId} = ${score}`)
      try {
        const { data } = await api.patch<MemoryEntry>(
          `${ENTRY_BASE}/${entryId}/set_ai_score/`, { ai_score: score }
        )
        if (this.current) {
          const idx = this.current.entries.findIndex(e => e.id === entryId)
          if (idx !== -1) this.current.entries[idx] = data
        }
        _log('✔ score set')
        return data
      } catch (e) {
        _handleError(this, e, 'Failed to set AI score')
        return null
      } finally {
        this.loading = false
      }
    },

    /* 7.5. trigger AI scoring manually (if auto-scoring failed) */
    async triggerAiScoring(entryId: number) {
      this.loading = true
      _log(`triggerAiScoring → entry #${entryId}`)
      try {
        const { data } = await api.post<MemoryEntry>(
          `${ENTRY_BASE}/${entryId}/trigger_ai_scoring/`
        )
        if (this.current) {
          const idx = this.current.entries.findIndex(e => e.id === entryId)
          if (idx !== -1) this.current.entries[idx] = data
        }
        _log('✔ AI scoring triggered')
        return data
      } catch (e) {
        _handleError(this, e, 'Failed to trigger AI scoring')
        return null
      } finally {
        this.loading = false
      }
    },

    /* 8. commenting - 禁止重试以避免重复 */
    async createComment(entryId: number, content: string, retryCount = 0): Promise<MemoryComment> {
      const maxRetries = 0
      this.loading = true
      _log(`createComment → entry #${entryId}`, content, `(attempt ${retryCount + 1})`)
      
      try {
        const { data } = await api.post<MemoryComment>(
          `${COMMENT_BASE}/`, 
          { entry: entryId, content },
          { timeout: 72000 } // 72秒超时
        )
        
        // 立即更新本地缓存（current + memories）
        const applyToRound = (round: CoupleMemoryEx | null | undefined) => {
          if (!round) return
          const ent = round.entries.find(e => e.id === entryId)
          if (ent && !ent.comments.some(c => c.id === data.id)) {
            ent.comments.push(data)
          }
        }
        applyToRound(this.current)
        for (const r of this.memories) applyToRound(r)
        
        _log('✔ comment added id', data.id)
        return data
        
      } catch (e) {
        if (retryCount < maxRetries && this._isRetryableError(e)) {
          _log(`⚠️ Comment posting failed, retrying... (${retryCount + 1}/${maxRetries})`)
          await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)))
          return this.createComment(entryId, content, retryCount + 1)
        }
        
        _handleError(this, e, 'Failed to post comment')
        throw e // 重新抛出错误，让调用方处理
        
      } finally {
        this.loading = false
      }
    },

    async deleteComment(commentId: number) {
      this.loading = true
      _log(`deleteComment #${commentId}`)
      try {
        await api.delete(`${COMMENT_BASE}/${commentId}/`)
        if (this.current) {
          this.current.entries.forEach(e => {
            e.comments = e.comments.filter(c => c.id !== commentId)
          })
        }
        _log('✔ comment deleted')
      } catch (e) {
        _handleError(this, e, 'Failed to delete comment')
      } finally {
        this.loading = false
      }
    },
  },
})
/* ────────────── END ────────────── */

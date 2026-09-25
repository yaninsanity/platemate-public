import { defineStore }  from 'pinia'
import api              from '@/plugins/axios'
import type {
  FamilyMenuEntry,
  RecipeLite,
}                       from '@/models/familymenu'

/* ───────── 工具 ───────── */
const ORIGIN = window.location.origin
const fixUrl = (u: string | null) =>
  u ? u.replace(/^https?:\/\/web:\d+/, ORIGIN) : u

const normalizeRecipes = (arr: RecipeLite[]): RecipeLite[] =>
  arr.map(r => ({ ...r, default_picture: fixUrl(r.default_picture) }))

/* ───────── Store ───────── */
export const useFamilyMenuStore = defineStore('familyMenu', {
  state: () => ({
    menus   : []   as FamilyMenuEntry[],
    loading : false,
    error   : null as string | null,
    pending : new Map<number, Promise<void>>(),  // menu.id → inflight promise
  }),

  getters: {
    byId: s => (id: number) => s.menus.find(m => m.id === id) || null,
  },

  actions: {
    /* ① 一次性拉总览 */
    async fetchMenus () {
      if (this.menus.length || this.loading) return
      this.loading = true
      this.error   = null
      console.debug('[familyMenu] fetchMenus …')

      try {
        const { data } = await api.get<FamilyMenuEntry[]>('/recipes/family-menus/')
        this.menus = data.map(fm => ({
          ...fm,
          unlocked_recipes:
            fm.unlocked_recipes ?? (fm.is_locked ? 0 : fm.menu.recipes_count),
        }))
        console.debug(`[familyMenu] ✔ got ${this.menus.length} menu(s)`)
      } catch (e: any) {
        this.error = e?.response?.data?.detail || e?.message || 'Failed to load menus'
        console.error('[familyMenu] ✖ fetchMenus', this.error)
      } finally {
        this.loading = false
      }
    },

    /* ② 懒加载具体菜谱 */
    async fetchRecipes (fm: FamilyMenuEntry) {
      if (fm.recipes || fm._loading) return

      /* 若已有并发请求 → 直接等待同一个 Promise */
      const inflight = this.pending.get(fm.menu.id)
      if (inflight) return inflight

      const p = (async () => {
        fm._loading = true
        fm._error   = null
        console.debug(`[familyMenu] fetchRecipes → menu#${fm.menu.id}`)

        try {
          const { data } = await api.get<{ recipes?: RecipeLite[] }>(
            `/recipes/menus/${fm.menu.id}/`
          )
          /* 兼容 MenuSerializer 无 wrapper & 有 wrapper 两种返回 */
          const list = (data as any).recipes ?? (data as any)
          fm.recipes = normalizeRecipes(list)
          /* if the backend omits unlocked_recipes, infer it from the lock state */
          if (fm.unlocked_recipes == null) {
            fm.unlocked_recipes = fm.is_locked ? 0 : fm.recipes.length
          }
          console.debug(`[familyMenu] ✔ menu#${fm.menu.id} : ${list.length} recipes`)
        } catch (e: any) {
          fm._error = e?.response?.data?.detail || e?.message || 'Load failed'
          console.warn(`[familyMenu] ✖ menu#${fm.menu.id}`, fm._error)
        } finally {
          fm._loading = false
          this.pending.delete(fm.menu.id)
        }
      })()

      this.pending.set(fm.menu.id, p)
      return p
    },
  },
})

import { defineStore } from 'pinia'
import api from '@/plugins/axios'
import type {
  Ingredient,
  Recipe,
  RoundBracket,
  DicePocket,
} from '@/models/recipes'

// 统一错误文案
const _err = (msg: string) => msg

export const useRecipesStore = defineStore('recipes', {
  state: () => ({
    loading: false as boolean,
    error:   null  as string | null,

    ingredients: [] as Ingredient[],
    recipes:     [] as Recipe[],

    brackets:       [] as RoundBracket[],
    currentBracket: null as RoundBracket | null,
    dice:           null as DicePocket   | null,
  }),

  getters: {
    hasDice: (s) => (s.dice?.balance ?? 0) > 0,
  },

  actions: {
    /* 通用 loading / error 包装器 */
    async _withLoading<T>(fn: () => Promise<T>, onError?: string) {
      this.loading = true
      this.error   = null
      try {
        return await fn()
      } catch (e: any) {
        this.error = e?.message || onError || _err('Request failed')
        throw e
      } finally {
        this.loading = false
      }
    },

    /* 初始化：基础数据 + Bracket */
    async init() {
      await this._withLoading(async () => {
        await Promise.all([this.loadBasics(), this.loadBrackets()])
      }, _err('Store initialization failed'))
    },

    /* Ingredients + Recipes */
    async loadBasics() {
      await this._withLoading(async () => {
        const [ingRes, recRes] = await Promise.all([
          api.get<Ingredient[]>('/recipes/ingredients/'),
          api.get<Recipe[]>    ('/recipes/recipes/'),
        ])
        this.ingredients = ingRes.data
        this.recipes     = recRes.data
      }, _err('Failed to load ingredients or recipes'))
    },

   /* store/recipeStore.ts */
    async loadBrackets() {
      await this._withLoading(async () => {
        await api.post('/recipes/brackets/check/', {})  // 确保有当前周的 bracket
        const { data } = await api.get<RoundBracket[]>('/recipes/brackets/')
        // ① 先按 round 降序排，最新在最前
        data.sort((a, b) => new Date(b.round).getTime() - new Date(a.round).getTime())
        // ② 如果仍可能有同周多条，优先拿有 recipe 的
        this.currentBracket = data.find(b => b.recipe) || data[0] || null
        this.brackets       = data
        await this.loadDice()
      }, _err('Failed to load roundly brackets'))
    },

    /* 第一轮 roll → 直接调用 loadBrackets（后端自动处理） */
    async firstRoll() {
      if (!this.currentBracket) await this.loadBrackets()
    },

    /* Reroll（48h 内 + 扣骰子） */
    async reroll() {
      if (!this.currentBracket) return
      await this._withLoading(async () => {
        // the refresh endpoint may reroll when conditions allow, and returns the newest bracket
        const { data } = await api.post<RoundBracket>('/recipes/brackets/refresh/', {})
        this.currentBracket = data
        await this.loadDice()
        await this.loadBrackets()          // 更新列表 & 进度
      }, _err('Bracket reroll failed'))
    },

    /* Dice 余额 */
    async loadDice() {
      try {
        const { data } = await api.get<DicePocket>('/recipes/dice-pocket/')
        this.dice = data
      } catch {
        /* ignore */
      }
    },
  },
})

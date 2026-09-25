// src/stores/taskStore.ts
import { defineStore } from 'pinia'
import api            from '@/plugins/axios'
import type { RecipeIngredientTask }  from '@/models/recipes'

/* ────────────────────────── ① 统一后端根地址 ──────────────────────────
   VITE_API_BASE_URL 在 docker-compose 里写的是 "http://localhost:911/api"
   这里把 service 名 'web' swap in the host the browser actually sees: localhost, an IP…）
   -------------------------------------------------------------------- */
function computeBackendRoot(): string {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  try {
    // 兼容只写了 /api 的场景
    const u = new URL(base, window.location.origin)
    if (u.hostname === 'web') {
      u.hostname = window.location.hostname         // ← 关键替换
    }
    return u.origin.replace(/\/$/, '')              // 去掉末尾 /
  } catch {
    // 最坏 fallback：跟随浏览器 origin
    return window.location.origin
  }
}
const backendRoot = computeBackendRoot()            // 例：http://localhost:911

/* ─────────────────────── ② 图片 URL correction工具 ──────────────────────── */
function normalizeImageURL(raw: string | null | undefined): string {
  if (!raw) return ''
  try {
    // 支持后端给的是相对路径 /media/… 也支持绝对 http://localhost:911/…
    const u = new URL(raw, backendRoot)

    // 后端若仍返回 localhost:911，再保险替换一次
    if (u.hostname === 'web') {
      u.hostname = window.location.hostname
    }
    return u.toString()
  } catch {
    console.warn('Invalid image URL:', raw)
    return ''
  }
}

/* ─────────────────────────── Pinia Store ─────────────────────────── */
export const useTaskStore = defineStore('tasks', {
  state: () => ({
    tasks   : [] as RecipeIngredientTask[],
    loading : false,
    error   : null as string | null,
    // Enhanced couple interaction features
    partnerProgress: null as Record<string, {
      user_id: number,
      completed_ingredients: Array<{
        ingredient_id: number,
        ingredient_name: string,
        verified_at: string | null,
        task_id?: number  // 添加可选的任务ID
      }>,
      total_tasks: number,
      completed_tasks: number
    }> | null,
    coupleId: null as number | null,
    
    // 🎯 精准改善：缓存机制（3分钟缓存）
    _taskCache: {} as Record<number, { data: any, timestamp: number }>,
    _currentRecipeId: null as number | null,
  }),

  getters: {
    doneCount      : s => s.tasks.filter(t => t.is_verified).length,
    allDone        : s => s.tasks.length > 0 && s.tasks.every(t => t.is_verified),
    verifiedTasks  : s => s.tasks.filter(t =>  t.is_verified),
    unverifiedTasks: s => s.tasks.filter(t => !t.is_verified),
    getTaskById    : s => (id: number) => s.tasks.find(t => t.id === id) || null,
    // 基于用户的验证状态检查
    userVerifiedTasks: s => s.tasks.filter(t => t.is_verified && t.user),
    userPendingTasks: s => s.tasks.filter(t => !t.is_verified && t.user),
    heatPercent    : s => {
      const done  = s.tasks.filter(t => t.is_verified).length
      return s.tasks.length === 0 ? 0 : Math.round((done / s.tasks.length) * 100)
    },
    // Enhanced couple interaction getters
    hasPartner: s => s.partnerProgress && Object.keys(s.partnerProgress).length > 0,
    partnerNames: s => s.partnerProgress ? Object.keys(s.partnerProgress) : [],
    getPartnerProgress: s => (partnerName: string) => s.partnerProgress?.[partnerName] || null,
    isIngredientCompletedByPartner: s => (ingredientId: number) => {
      if (!s.partnerProgress) return false
      return Object.values(s.partnerProgress).some(partner => 
        partner.completed_ingredients.some(ing => ing.ingredient_id === ingredientId)
      )
    },
    getPartnerWhoCompletedIngredient: s => (ingredientId: number) => {
      if (!s.partnerProgress) return null
      
      // 检查是否有伴侣完成了该ingredient的任务
      for (const [partnerName, progress] of Object.entries(s.partnerProgress)) {
        const completed = progress.completed_ingredients.find(ing => ing.ingredient_id === ingredientId)
        if (completed) {
          return { 
            partnerName, 
            completedAt: completed.verified_at,
            taskId: completed.task_id || null  // 添加任务ID用于精确匹配
          }
        }
      }
      return null
    },
    // the partner progress is visible only while the user has not finished
    shouldShowPartnerStatus: s => (taskId: number, ingredientId: number) => {
      const userTask = s.tasks.find(t => t.id === taskId)
      if (!userTask || userTask.is_verified) return false  // 用户已完成，不显示伴侣状态
      
      // has the partner finished the same ingredient?
      if (!s.partnerProgress) return false
      return Object.values(s.partnerProgress).some(partner => 
        partner.completed_ingredients.some(ing => ing.ingredient_id === ingredientId)
      )
    },
    isTaskCompletedByCurrentUser: s => (taskId: number) => {
      const task = s.tasks.find(t => t.id === taskId)
      return task ? task.is_verified : false
    },
    canCurrentUserVerifyTask: s => (taskId: number) => {
      const task = s.tasks.find(t => t.id === taskId)
      if (!task) return false
      // 用户只能验证自己的未完成任务
      return !task.is_verified && (!task.user || task.user === s.tasks[0]?.user)
    },
    overallCoupleProgress: s => {
      const userDoneCount = s.tasks.filter(t => t.is_verified).length
      if (!s.partnerProgress) return { completed: userDoneCount, total: s.tasks.length }
      
      const totalPartnerCompleted = Object.values(s.partnerProgress)
        .reduce((sum, partner) => sum + partner.completed_tasks, 0)
      const totalPartnerTasks = Object.values(s.partnerProgress)
        .reduce((sum, partner) => sum + partner.total_tasks, 0)
      
      return {
        user: { completed: userDoneCount, total: s.tasks.length },
        partners: { completed: totalPartnerCompleted, total: totalPartnerTasks },
        combined: { completed: userDoneCount + totalPartnerCompleted, total: s.tasks.length + totalPartnerTasks }
      }
    }
  },

  actions: {
    /* load the tasks for a recipe, including the partner progress, cached for three minutes */
    async fetchTasks(recipeId: number, forceRefresh = false) {
      if (recipeId === -1) return
      
      const now = Date.now()
      const CACHE_DURATION = 3 * 60 * 1000 // 3分钟缓存
      
      // 检查缓存是否有效
      const cached = this._taskCache[recipeId]
      if (!forceRefresh && cached && (now - cached.timestamp) < CACHE_DURATION) {
        console.log('[taskStore] 🚀 Using cached tasks for recipe', recipeId, '(age:', Math.round((now - cached.timestamp) / 1000), 'seconds)')
        
        // 使用缓存数据
        this.tasks = cached.data.user_tasks
        this.partnerProgress = cached.data.partner_progress
        this.coupleId = cached.data.couple_id
        this._currentRecipeId = recipeId
        return
      }
      
      this.loading = true
      this.error   = null
      try {
        console.log('[taskStore] 📡 Fetching fresh tasks for recipe', recipeId, 'from API')
        const { data } = await api.post<{
          user_tasks: RecipeIngredientTask[],
          partner_progress: Record<string, {
            user_id: number,
            completed_ingredients: Array<{
              ingredient_id: number,
              ingredient_name: string,
              verified_at: string | null,
              task_id?: number  // 添加可选的任务ID
            }>,
            total_tasks: number,
            completed_tasks: number
          }> | null,
          couple_id: number | null
        }>('/recipes/tasks/by-recipe-enhanced/', { recipe: recipeId })
        
        this.tasks = data.user_tasks.map(task => ({
          ...task,
          ingredient: {
            ...task.ingredient,
            default_picture: normalizeImageURL(task.ingredient.default_picture),
          },
        }))
        
        // Store partner progress for enhanced interaction
        this.partnerProgress = data.partner_progress
        this.coupleId = data.couple_id
        this._currentRecipeId = recipeId
        
        // 更新缓存
        this._taskCache[recipeId] = {
          data: {
            user_tasks: this.tasks,
            partner_progress: data.partner_progress,
            couple_id: data.couple_id
          },
          timestamp: now
        }
        console.log('[taskStore] ✅ Tasks cached for recipe', recipeId)
        
      } catch (err: any) {
        // Fallback to regular API if enhanced fails
        console.warn('Enhanced API failed, falling back to regular API:', err.message)
        try {
          const { data } = await api.post<RecipeIngredientTask[]>(
            '/recipes/tasks/by-recipe/', { recipe: recipeId }
          )
          this.tasks = data.map(task => ({
            ...task,
            ingredient: {
              ...task.ingredient,
              default_picture: normalizeImageURL(task.ingredient.default_picture),
            },
          }))
          this.partnerProgress = null
          this.coupleId = null
        } catch (fallbackErr: any) {
          this.error = fallbackErr?.response?.data?.detail || fallbackErr?.message || 'Failed to load tasks'
        }
      } finally {
        this.loading = false
      }
    },

    /* 标记任务已验证 */
    async verifyTask(taskId: number) {
      this.loading = true
      this.error   = null
      try {
        const { data: updatedTask } = await api.post('/recipes/tasks/verify/', { id: taskId })
        
        // 更新本地任务状态
        this.tasks = this.tasks.map(t =>
          t.id === taskId
            ? { ...updatedTask, 
                ingredient: {
                  ...updatedTask.ingredient,
                  default_picture: normalizeImageURL(updatedTask.ingredient.default_picture),
                }
              }
            : t
        )
        
        // 清除当前recipe的缓存，强制重新获取最新状态
        const currentRecipe = this.tasks[0]?.recipe
        if (currentRecipe && this._taskCache[currentRecipe]) {
          console.log('[taskStore] 🗑️ Clearing cache for recipe', currentRecipe, 'after verification')
          delete this._taskCache[currentRecipe]
        }
        
        // 重新获取最新的任务状态和伴侣进度以确保同步
        if (currentRecipe) {
          await this.fetchTasks(currentRecipe, true) // forceRefresh = true
        }
        
      } catch (err: any) {
        this.error = err?.response?.data?.detail || err?.message || '验证失败'
        throw err
      } finally {
        this.loading = false
      }
    },

    /* 切换 recipe 时清空本地状态 */
    clear() {
      this.tasks   = []
      this.error   = null
      this.loading = false
      this.partnerProgress = null
      this.coupleId = null
    },
  },
})

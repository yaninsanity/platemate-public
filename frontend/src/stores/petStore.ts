/* ──────────────────────────────────────────────
   src/stores/petStore.ts   ★2025‑01‑21 patch
   ────────────────────────────────────────────── */
import { defineStore } from 'pinia'
import api             from '@/plugins/axios'
import { playNotificationSound, playPetStatusSound, GameSounds, soundManager } from '@/utils/soundManager'
import { trackPlayGame } from '@/utils/analytics'
import type {
  Pet,
  RewardBox,
  Badge,
  PetMessage,
} from '@/models/pet'

/* ---------- 常量 ---------- */
const LS_KEY  = 'platemate_pet_cache'
const POLL_MS = 120_000   // 2分钟轮询

/* ---------- PetStore ---------- */
export const usePetStore = defineStore('pet', {
  state: () => ({
    pet     : (() => {
      try {
        const cached = localStorage.getItem(LS_KEY)
        return cached ? JSON.parse(cached) : null
      } catch {
        return null
      }
    })() as Pet | null,
    boxes   : []   as RewardBox[],
    badges  : []   as Badge[],
    messages: []   as PetMessage[],
    stateMessages: [] as String[],
    loading : false,
    _timer  : null as ReturnType<typeof setInterval> | null,
    _slotTimer: null as ReturnType<typeof setInterval> | null, // 🎰 老虎机定时器
    currentAnimation: 'idle' as string, // Add current animation state
    foodInventory: [] as Array<{
      food_type: string
      food_display: string
      quantity: number
      can_harvest: boolean
      last_harvest: string | null
    }>,
    totalFoodItems: 0,
    
    // 🎯 couple comparison is cached for five minutes
    _coupleComparisonCache: null as any,
    _lastCoupleComparisonFetch: 0,
    
    // 🎯 Checkin相关状态
    lastCheckinTime: null as Date | null,
    nextCheckinTime: null as Date | null,
    hasCheckedInToday: false,
    checkinReward: null as any,
    
    // 🎯 可harvest状态
    harvestableQuantities: {} as Record<string, number>,
    
    // 🎰 老虎机状态管理
    slotMachine: {
      isVisible: false,
      isSpinning: false,
      canSpin: true,
      lastSpinTime: null as Date | null,
      nextAvailableTime: null as Date | null,
      cooldownRemaining: '',
  result: null as any,
  slotResults: [] as any[],
  slotAnimation: null as any,
  slotPreview: null as any,
  totalSpins: 0
    }
  }),

  /* ---------- Getters ---------- */
  getters: {
    /* 基础 */
    level : s => s.pet?.level ?? 1,
    xp    : s => s.pet?.xp    ?? 0,

    /* accepts either field -------------------------- */
    health (s): number {
      return (
        s.pet?.health ??
        s.pet?.status?.hunger ??
        0
      )
    },
    energy (s): number {
      return (
        s.pet?.energy ??
        s.pet?.status?.happiness ??
        0
      )
    },
    hygiene (s): number {
      return (
        s.pet?.hygiene ??
        s.pet?.status?.hygiene ??
        0
      )
    },

    /* 进度 & currency --------------------------- */
    nextLv(): number {
      return this.pet?.next_level ??
             Math.ceil(((this.level) + 4) * 20)
    },
    xpPercent(): number {
      return Math.min(this.xp / this.nextLv, 1) * 100
    },
    coins(s): number {
      return s.pet ? s.pet.level * 50 + s.badges.length * 10 : 0
    },
    notifications(s): number {
      return s.messages.filter(m => !m.is_read).length
    },

    /* 供动画占位 */
    petStatus: (s) => s.currentAnimation,
  },

  /* ---------- Actions ---------- */
  actions: {
    /* —— 主动拉取宠物 —— */
    async fetchPet () {
      // 避免并发
      if (this.loading) return
      this.loading = true
      try {
        const { data, status } = await api.get<Pet[]>(
          '/petcare/pet/',
          {
            // 强制绕过任何代理/浏览器缓存
            headers        : { 'Cache-Control': 'no-cache' },
            params         : { _t: Date.now() },
            validateStatus : s => s === 200 || s === 304,
          },
        )
        this.fetchStateMessages()

        if (status === 200 && Array.isArray(data) && data.length) {
          this.pet = data[0]
          localStorage.setItem(LS_KEY, JSON.stringify(this.pet))
          console.debug('[petStore] fetch ok', this.pet)
        } else {
          console.debug('[petStore] 304 – 使用缓存，不更新 state')
          /* 如果第一次加载就 304，但本地没缓存，视为无宠物 */
          if (!this.pet) this.pet = null
        }
      } catch (e) {
        console.error('[petStore] fetchPet err', e)
      } finally {
        this.loading = false
      }
    },

    /* —— 🎯 精准改善：登录后初始化所有宠物数据 —— */
    async initializePetData() {
      console.debug('[petStore] Initializing pet data after login...')
      try {
        // 🎵 预加载游戏音效 - AAA级体验
        soundManager.preloadSounds()
        
        // 并行加载所有必要数据
        await Promise.all([
          this.fetchPet(),
          this.fetchFoodInventory(),
          this.fetchBadges(),
          this.fetchMessages()
        ])
        
        // 启动轮询
        this.startPolling()
        
        console.debug('[petStore] Pet data initialization complete. Hunger:', this.health)
      } catch (error) {
        console.error('[petStore] Failed to initialize pet data:', error)
      }
    },

    /* —— 示例：喂食 —— */
    async feed(points = 1) {
      if (!this.pet) return
      if (this.pet.status?.hunger !== undefined) {
        this.pet.status.hunger = Math.min(100, this.pet.status.hunger + points * 2)
      }
      await api.post('/petcare/pet/feed/', { points })
      await this.fetchPet()
    },

    /* —— 游戏API —— */
    async playGame(gameType: string, result: 'win' | 'lose' | 'draw', hungerCost: number = 8) {
      if (!this.pet) return null
      
      try {
        const response = await api.post('/petcare/pet/play_game/', {
          game_type: gameType,
          result: result,
          hunger_cost: hungerCost
        })
        
        // 🎯 精准改善：调用 analytics tracking
        trackPlayGame(
          gameType,
          result,
          hungerCost,
          response.data.food_reward ? [response.data.food_reward] : undefined
        )
        
        // Update local pet state with server response
        if (response.data.pet) {
          this.pet = response.data.pet
        }
        
        // If we got a food reward, refresh inventory
        if (response.data.food_reward) {
          await this.fetchFoodInventory()
        }
        
        return {
          success: true,
          finalHunger: response.data.final_hunger,
          hungerCost: response.data.hunger_cost,
          winReward: response.data.win_reward,
          result: response.data.result,
          foodReward: response.data.food_reward
        }
      } catch (error: any) {
        console.error('[petStore] Game API error:', error)
        
        // Return error info for UI handling
        if (error.response?.status === 400) {
          return {
            success: false,
            error: error.response.data.detail,
            currentHunger: error.response.data.current_hunger,
            requiredHunger: error.response.data.required_hunger
          }
        }
        
        return {
          success: false,
          error: 'Game API call failed'
        }
      }
    },

    /* —— 食物库存管理 —— */
    async fetchFoodInventory() {
      try {
        const response = await api.get('/petcare/food-inventory/')
        this.foodInventory = response.data.inventory
        this.totalFoodItems = response.data.total_items
        console.debug('[petStore] Food inventory loaded:', this.foodInventory)
      } catch (error) {
        console.error('[petStore] Failed to fetch food inventory:', error)
      }
    },

    /* —— 🎯 精准改善：获取情侣双方食物库存对比（带5分钟缓存） —— */
    async fetchCoupleInventoryComparison(forceRefresh = false) {
      const now = Date.now()
      const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存
      
      // 检查缓存是否有效
      if (!forceRefresh && this._coupleComparisonCache && (now - this._lastCoupleComparisonFetch) < CACHE_DURATION) {
        console.log('[petStore] 🚀 Using cached couple comparison (age:', Math.round((now - this._lastCoupleComparisonFetch) / 1000), 'seconds)')
        return this._coupleComparisonCache
      }
      
      try {
        console.log('[petStore] 📡 Fetching fresh couple inventory comparison from API')
        const response = await api.get('/petcare/food-inventory/couple_comparison/')
        
        // 更新缓存
        this._coupleComparisonCache = response.data
        this._lastCoupleComparisonFetch = now
        
        console.debug('[petStore] ✅ Couple inventory comparison loaded and cached:', response.data)
        return response.data
      } catch (error: any) {
        console.error('[petStore] ❌ Failed to fetch couple inventory comparison:', error)
        
        // 如果有缓存，返回缓存数据
        if (this._coupleComparisonCache) {
          console.warn('[petStore] ⚠️ Using stale cache due to API error')
          return this._coupleComparisonCache
        }
        
        // 返回默认空数据
        return {
          comparison: [],
          self: { inventory: [], total_items: 0 },
          partner: null,
          engagement_stats: {
            self_total: 0,
            partner_total: 0,
            combined_total: 0
          }
        }
      }
    },

    /* —— � the daily check-in is its own reward loop and costs no hunger —— */
    async performDailyCheckin() {
      try {
        console.log('� [Daily Reward] Starting daily reward collection...')
        
  const response = await api.post('/petcare/food-inventory/checkin/')
        
        if (response.data.success) {
          console.log('� [Daily Reward] SUCCESS! Collected:', response.data.amount, response.data.food_display)
          
          // � 每日奖励成功音效
          soundManager.playSound(GameSounds.REWARD_EARNED, { volume: 0.8, fadeIn: 200 })
          
          // �🎯 设置每日奖励状态
          this.hasCheckedInToday = true
          this.lastCheckinTime = new Date()
          if (response.data.next_checkin) {
            this.nextCheckinTime = new Date(response.data.next_checkin)
          }
          
          // � 设置奖励收集结果 - 精准动画数据
          this.slotMachine.result = {
            food_type: response.data.food_type,
            name: response.data.food_display,
            emoji: response.data.slot_animation?.winning_symbol || this.getFoodEmoji(response.data.food_type),
            amount: response.data.amount,
            effect: `+${response.data.amount} ${response.data.food_display}`,
            message: response.data.message || '🎁 Daily Reward Collected!'
          }

          // 🎰 传递转轮详细数据给前端组件
          this.slotMachine.slotResults = response.data.slot_results || []
          this.slotMachine.slotAnimation = response.data.slot_animation || null
          this.slotMachine.slotPreview = response.data.slot_preview || null
          
          // � 更新冷却状态
          this.slotMachine.lastSpinTime = new Date()
          this.slotMachine.nextAvailableTime = new Date(response.data.next_available)
          this.slotMachine.totalSpins = response.data.total_checkins || 0
          this.slotMachine.canSpin = false
          
          // � 显示奖励收集动画
          this.slotMachine.isVisible = true
          this.slotMachine.isSpinning = true
          
          // � 启动冷却倒计时
          this.startSlotCooldownTimer()
          
          // 刷新库存并清除couple comparison缓存
          await this.fetchFoodInventory()
          this._lastCoupleComparisonFetch = 0 // 清除缓存
          
          return response.data
        } else if (response.data.on_cooldown) {
          console.log('� [Daily Reward] ON COOLDOWN:', response.data.remaining_time)
          
          // � 设置冷却状态
          this.slotMachine.canSpin = false
          this.slotMachine.nextAvailableTime = new Date(response.data.next_available)
          this.slotMachine.cooldownRemaining = response.data.remaining_time
          
          // � 启动冷却倒计时
          this.startSlotCooldownTimer()
          
          return {
            success: false,
            on_cooldown: true,
            message: response.data.message,
            remaining_time: response.data.remaining_time,
            slot_preview: response.data.slot_preview // 🎯 精准改善：传递预览数据
          }
        }
        
        return { success: false, error: 'Daily reward collection failed' }
      } catch (error: any) {
        console.error('� [Daily Reward] ERROR:', error)
        
        // 检查是否是重复领取
        if (error.response?.status === 400) {
          this.hasCheckedInToday = true
        }
        
        return {
          success: false,
          error: error.response?.data?.detail || 'Daily reward collection failed'
        }
      }
    },
    
    // 🎯 Unified food emoji - always returns Kinny Food icon
    getFoodEmoji(foodType: string): string {
      return '�️' // All food types unified as Kinny Food
    },
    
    // 🎯 获取食物效果
    getFoodEffect(foodType: string): string {
      const effectMap: Record<string, string> = {
        apple: 'Restores hunger and boosts health',
        banana: 'High energy and happiness boost',
        orange: 'Vitamin C for immunity',
        strawberry: 'Sweet treat for mood',
        grapes: 'Antioxidants for longevity', 
        watermelon: 'Hydration and freshness',
        pineapple: 'Tropical energy boost',
        cherry: 'Delicious and lucky!'
      }
      return effectMap[foodType] || 'Nutritious and delicious!'
    },

    /* —— 🎯 精准改善：喂食功能 - 连接后端API —— */
    async feedPet(foodType: string, amount: number = 1) {
      try {
        const response = await api.post('/petcare/food-inventory/use/', {
          food_type: foodType,
          amount: amount
        })
        
        if (response.data.success) {
          // 🎯 更新宠物饥饿值
          if (this.pet?.status) {
            this.pet.status.hunger = response.data.new_hunger
          } else if (this.pet) {
            // 兼容不同的数据结构
            this.pet.health = response.data.new_hunger
          }
          
          // 🎯 喂食成功音效
          soundManager.playSound(GameSounds.FEED_SUCCESS, { volume: 0.7, fadeIn: 100 })
          
          // 🎯 refresh the inventory and drop the couple comparison cache
          await this.fetchFoodInventory()
          this._lastCoupleComparisonFetch = 0 // 清除缓存，强制下次重新获取
          
          return {
            success: true,
            new_hunger: response.data.new_hunger,
            food_used: response.data.food_used,
            hunger_gained: response.data.hunger_gained
          }
        }
        
        return { success: false, error: 'Feed failed' }
      } catch (error: any) {
        console.error('[petStore] Feed error:', error)
        return {
          success: false,
          error: error.response?.data?.detail || 'Feed failed'
        }
      }
    },

    /* —— � 奖励收集界面控制 —— */
    showSlotMachine() {
      console.log('� [Daily Reward] Showing reward collection interface')
      this.slotMachine.isVisible = true
      this.slotMachine.isSpinning = true
    },

    closeSlotMachine() {
      console.log('� [Daily Reward] Closing reward collection interface')
      this.slotMachine.isVisible = false
      this.slotMachine.isSpinning = false
  // 保留最近一次结果数据用于展示历史或调试（不清空）
  this.checkinReward = null // 🎯 兼容旧的checkin系统
    },

    /* —— � 冷却倒计时管理 —— */
    startSlotCooldownTimer() {
      // 清除现有定时器
      if (this._slotTimer) {
        clearInterval(this._slotTimer)
      }
      
      // 启动新的倒计时定时器
      this._slotTimer = setInterval(() => {
        this.updateSlotCooldown()
      }, 1000)
    },

    updateSlotCooldown() {
      if (!this.slotMachine.nextAvailableTime) {
        this.slotMachine.canSpin = true
        this.slotMachine.cooldownRemaining = ''
        if (this._slotTimer) {
          clearInterval(this._slotTimer)
          this._slotTimer = null
        }
        return
      }
      
      const now = new Date().getTime()
      const nextTime = new Date(this.slotMachine.nextAvailableTime).getTime()
      const distance = nextTime - now
      
      if (distance > 0) {
        const hours = Math.floor(distance / (1000 * 60 * 60))
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60))
        const seconds = Math.floor((distance % (1000 * 60)) / 1000)
        
        this.slotMachine.cooldownRemaining = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
        this.slotMachine.canSpin = false
      } else {
        this.slotMachine.canSpin = true
        this.slotMachine.cooldownRemaining = ''
        this.slotMachine.nextAvailableTime = null
        
        // 清除定时器
        if (this._slotTimer) {
          clearInterval(this._slotTimer)
          this._slotTimer = null
        }
        
        console.log('� [Daily Reward] Cooldown finished! Ready for next collection.')
      }
    },

    async harvestFood(foodType: string) {
      try {
        const response = await api.post('/petcare/food-inventory/harvest/', {
          food_type: foodType
        })
        
        if (response.data.success) {
          // Refresh inventory after successful harvest and clear couple comparison cache
          await this.fetchFoodInventory()
          this._lastCoupleComparisonFetch = 0 // 清除缓存
          return response.data
        }
        
        return { success: false, error: 'Harvest failed' }
      } catch (error: any) {
        console.error('[petStore] Harvest error:', error)
        return {
          success: false,
          error: error.response?.data?.detail || 'Harvest failed'
        }
      }
    },

    async useFoodItem(foodType: string, amount: number = 1) {
      try {
        const response = await api.post('/petcare/food-inventory/use_food/', {
          food_type: foodType,
          amount: amount
        })
        
        if (response.data.success) {
          // Update pet hunger locally
          if (this.pet?.status) {
            this.pet.status.hunger = response.data.new_hunger
          }
          
          // Refresh inventory after use and clear couple comparison cache
          await this.fetchFoodInventory()
          this._lastCoupleComparisonFetch = 0 // 清除缓存
          return response.data
        }
        
        return { success: false, error: 'Food use failed' }
      } catch (error: any) {
        console.error('[petStore] Use food error:', error)
        return {
          success: false,
          error: error.response?.data?.detail || 'Food use failed'
        }
      }
    },

    /**
     * 🎯 Unified Kinny Food: Auto-use any available food
     * Frontend doesn't need to specify type, backend auto-selects
     */
    async useAnyAvailableFood(amount: number = 1) {
      try {
        console.log('🍽️ [useAnyAvailableFood] Calling API with amount:', amount)
        
        const response = await api.post('/petcare/food-inventory/use-any/', {
          amount: amount
        })
        
        console.log('🍽️ [useAnyAvailableFood] API Response:', response.data)
        
        // Check if response has data and success flag
        if (response.data && (response.data.success || response.status === 200)) {
          // Update pet hunger locally
          if (this.pet?.status && response.data.new_hunger !== undefined) {
            this.pet.status.hunger = response.data.new_hunger
            console.log('✅ [useAnyAvailableFood] Updated local hunger to:', response.data.new_hunger)
          }
          
          // Refresh inventory and pet data
          await Promise.all([
            this.fetchFoodInventory(),
            this.fetchPet()
          ])
          
          // Return unified Kinny Food data (hide specific types from frontend)
          return {
            success: true,
            food_emoji: '🍽️',  // Always use plate emoji
            food_display: 'Kinny Food',
            hunger_gain: response.data.hunger_gain || response.data.hunger_increase || 10,
            new_hunger: response.data.new_hunger || response.data.final_hunger || 0,
            remaining_total: response.data.remaining_total || 0,
            message: 'Fed Kinny successfully!'
          }
        }
        
        // Handle failure response
        const errorMsg = response.data?.message || response.data?.error || 'No food available'
        console.warn('⚠️ [useAnyAvailableFood] Failed:', errorMsg)
        
        return { 
          success: false, 
          error: errorMsg
        }
      } catch (error: any) {
        console.error('❌ [useAnyAvailableFood] Exception:', error)
        console.error('❌ Response data:', error.response?.data)
        
        // Parse error message
        let errorMsg = 'Unable to feed Kinny'
        
        if (error.response?.data) {
          if (typeof error.response.data === 'string') {
            errorMsg = error.response.data
          } else if (error.response.data.detail) {
            errorMsg = error.response.data.detail
          } else if (error.response.data.message) {
            errorMsg = error.response.data.message
          } else if (error.response.data.error) {
            errorMsg = error.response.data.error
          }
        } else if (error.message) {
          errorMsg = error.message
        }
        
        return {
          success: false,
          error: errorMsg
        }
      }
    },

    async perform(action: string) {
      switch (action) {
        case 'feed': return this.feed(2)
        default:     console.warn('[petStore] unknown action', action)
      }
    },

    /* —— 轮询（可在标签页隐藏时暂停） —— */
    startPolling() {
      if (this._timer) return
      /* 可见性切换时暂停/恢复轮询 */
      const visCb = () => {
        if (document.hidden) this.stopPolling()
        else                 this.startPolling()
      }
      document.addEventListener('visibilitychange', visCb, { once:true })

      this._timer = setInterval(() => this.fetchPet(), POLL_MS)
    },
    stopPolling() {
      if (this._timer) clearInterval(this._timer)
      this._timer = null
    },

    /* the remaining endpoints are unchanged ----------------------- */
    async fetchBoxes(opened = false) {
      this.boxes = (await api.get<RewardBox[]>(
        `/petcare/boxes/?opened=${opened}`)).data
    },
    async openBox(id:number) {
      await api.post(`/petcare/boxes/${id}/open/`)
      await this.fetchBoxes(false)
    },
    async fetchBadges()   { this.badges   = (await api.get<Badge[]>('/petcare/badges/')).data },
    async fetchMessages() { 
      try {
        this.messages = (await api.get<PetMessage[]>('/petcare/pet-messages/')).data 
      } catch (error) {
        console.warn('[petStore] Failed to fetch messages:', error)
        this.messages = []
      }
    },
    
    /* —— 🎵 Animation Control with Sound Effects —— */
    setAnimation(animation: string) {
      const previousAnimation = this.currentAnimation
      this.currentAnimation = animation
      
      // 🎵 状态变化音效 - AAA级游戏体验
      if (previousAnimation !== animation) {
        this.playAnimationSound(animation, previousAnimation)
      }
    },
    
    resetAnimation() {
      this.currentAnimation = 'idle'
    },

    /* —— 🎵 宠物状态音效系统 —— */
    playAnimationSound(newAnimation: string, previousAnimation?: string) {
      // 🎯 根据动画状态播放对应音效
      const soundConfig = { volume: 0.5, fadeIn: 100 }
      
      switch (newAnimation) {
        case 'hungry':
          playPetStatusSound('hungry', soundConfig)
          console.log('🎵 Playing hungry sound effect')
          break
          
        case 'excited':
        case 'eating':
          playPetStatusSound('excited', soundConfig)
          console.log('🎵 Playing excited sound effect')
          break
          
        case 'satisfied':
        case 'happy':
          playPetStatusSound('satisfied', { ...soundConfig, volume: 0.6 })
          console.log('🎵 Playing satisfied sound effect')
          break
          
        case 'levelup':
          soundManager.playSound(GameSounds.LEVEL_UP, { volume: 0.8, fadeIn: 200 })
          console.log('🎵 Playing level up sound effect')
          break
          
        default:
          // 默认轻微状态变化音效
          if (previousAnimation && previousAnimation !== 'idle') {
            playNotificationSound({ volume: 0.3, fadeIn: 150 })
          }
          break
      }
    },

    async fetchStateMessages() {
      try {
        const res = await api.post('/petcare/pet-message-state/refresh/')
        // console.log('[petStore] Refreshed pet message state from server.', res.data.success)
        const { data } = await api.get('/petcare/pet-message-state/')
        
        // 🎯 精准检测：后端返回的消息状态与当前状态对比
        const newMessages = Object.values(data.available_messages).flatMap(
          state => (state as { messages: string[] }).messages
        );
        
        // 🎵 状态变化音效：仅当有真实变化时播放
        if (this.stateMessages.length > 0 && JSON.stringify(this.stateMessages) !== JSON.stringify(newMessages)) {
          playNotificationSound({ volume: 0.6, fadeIn: 200 })
        }
        
        this.stateMessages = newMessages
        console.log('[petStore] Fetched pet messages:', this.stateMessages)
        return data
      } catch (error) {
        console.error('[petStore] Failed to fetch pet message state:', error)
        // Return default state on error
        return {
          currentStates: [],
          availableMessages: {
            default: {
              name: '',
              messages: ['Welcome to the game! Start your cooking journey!']
            }
          },
          lastUpdated: null
        }
      }
    },
  },
})

export default usePetStore   // 仅导出 store 定义

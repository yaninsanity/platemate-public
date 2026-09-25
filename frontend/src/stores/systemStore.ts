// stores/systemStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/plugins/axios'

/**
 * 🎯 Single Source of Truth: 后端SystemConfig接口
 * the frontend declares types only, never defaults, so there is one source of truth
 */
interface SystemConfig {
  ai_verification_enabled: boolean
  nice_guy_card_mode: boolean
  enable_reward_cooldown: boolean
  reward_cooldown_hours: number
  pet_prompt_display_seconds: number
}

export const useSystemStore = defineStore('system', () => {
  // 🎯 State: null = 未加载，SystemConfig = 已加载（后端是唯一数据源）
  const config = ref<SystemConfig | null>(null)
  const isLoading = ref<boolean>(false)
  const lastChecked = ref<number>(0)
  
  // 缓存时间：5分钟
  const CACHE_DURATION = 5 * 60 * 1000

  /**
   * 🎯 read the system configuration, the single source of truth
   * @param forceRefresh 强制刷新，忽略缓存
   */
  async function fetchSystemConfig(forceRefresh = false) {
    const now = Date.now()
    
    // 缓存策略：5分钟内复用已有数据
    if (!forceRefresh && config.value && (now - lastChecked.value) < CACHE_DURATION) {
      return config.value
    }

    isLoading.value = true
    try {
      const response = await api.get<SystemConfig>('/system/config/')
      
      // 🎯 use the backend data directly; the backend is the single source of truth
      config.value = response.data
      lastChecked.value = now
      
      // 🎯 结构化日志输出
      console.group('🔧 System Config Loaded from Backend')
      console.log(`AI Verification: ${config.value.ai_verification_enabled ? '✅ ENABLED' : '❌ DISABLED'}`)
      console.log(`Nice Guy Card Mode: ${config.value.nice_guy_card_mode ? '✅ ENABLED (80-100)' : '❌ DISABLED (0-100)'}`)
      console.log(`Reward Cooldown: ${config.value.enable_reward_cooldown ? `✅ ${config.value.reward_cooldown_hours}h` : '❌ DISABLED (∞)'}`)
      console.log(`Pet Prompt Display: ${config.value.pet_prompt_display_seconds}s`)
      console.groupEnd()
      
      return config.value
    } catch (error) {
      console.error('❌ Failed to fetch system config:', error)
      
      // 🎯 失败时保持null，强制组件处理未加载状态
      // 不提供fallback默认值 - 避免前端假数据
      console.error('⚠️ Config unavailable - components must handle null state')
      throw error  // 让调用方处理错误
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 🎯 清除缓存，强制下次重新获取
   */
  function clearCache() {
    lastChecked.value = 0
  }

  /**
   * 🎯 类型安全的Computed Getters
   * 返回undefined表示"未加载" - 组件需要处理这个状态
   */
  const aiVerificationEnabled = computed(() => config.value?.ai_verification_enabled)
  const niceGuyCardMode = computed(() => config.value?.nice_guy_card_mode)
  const enableRewardCooldown = computed(() => config.value?.enable_reward_cooldown)
  const rewardCooldownHours = computed(() => config.value?.reward_cooldown_hours)
  const petPromptDisplaySeconds = computed(() => config.value?.pet_prompt_display_seconds)

  return {
    // 🎯 expose computed getters only, never the raw config, so callers cannot mutate it
    // these can be undefined while loading; callers must handle it
    aiVerificationEnabled,
    niceGuyCardMode,
    enableRewardCooldown,
    rewardCooldownHours,
    petPromptDisplaySeconds,
    
    // 状态和方法
    isLoading,
    fetchSystemConfig,
    clearCache,
  }
})

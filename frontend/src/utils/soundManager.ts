/* ──────────────────────────────────────────────
   🎵 Sound Manager - AAA级游戏音效系统
   ────────────────────────────────────────────── */

interface SoundConfig {
  volume?: number
  loop?: boolean
  fadeIn?: number
  fadeOut?: number
}

class SoundManager {
  private audioCache = new Map<string, HTMLAudioElement>()
  private masterVolume = 0.7
  private soundEnabled = true
  private bgmOriginalVolume = 0.3 // BGM默认音量
  private isBgmDucked = false // BGM是否已降低

  constructor() {
    // 🎯 检查用户音频偏好
    const savedVolume = localStorage.getItem('platemate_sound_volume')
    const soundEnabled = localStorage.getItem('platemate_sound_enabled')
    
    if (savedVolume) this.masterVolume = parseFloat(savedVolume)
    if (soundEnabled !== null) this.soundEnabled = soundEnabled === 'true'
    
    console.log('🎵 Sound Manager initialized:', { 
      volume: this.masterVolume, 
      enabled: this.soundEnabled 
    })
  }

  /* ─── 🎯 核心播放功能 ─── */
  async playSound(soundPath: string, config: SoundConfig = {}): Promise<void> {
    if (!this.soundEnabled) return

    try {
      const audio = await this.getAudio(soundPath)
      if (!audio) return

      // 🎯 高优先级音效时降低BGM音量
      const isHighPrioritySound = this.isHighPrioritySound(soundPath)
      if (isHighPrioritySound) {
        await this.duckBGM()
      }

      // 🎯 配置音频属性
      audio.volume = (config.volume ?? 1) * this.masterVolume
      audio.loop = config.loop ?? false
      audio.currentTime = 0

      // 🎯 淡入效果
      if (config.fadeIn) {
        audio.volume = 0
        audio.play()
        this.fadeVolume(audio, (config.volume ?? 1) * this.masterVolume, config.fadeIn)
      } else {
        await audio.play()
      }

      console.log(`🎵 Playing sound: ${soundPath}`)
    } catch (error) {
      console.warn(`🎵 Failed to play sound ${soundPath}:`, error)
    }
  }

  /* ─── 🎯 停止音效播放 ─── */
  stopSound(soundPath: string): void {
    try {
      const audio = this.audioCache.get(soundPath)
      if (audio && !audio.paused) {
        audio.pause()
        audio.currentTime = 0
        console.log(`🔇 Stopped sound: ${soundPath}`)
        
        // 🎯 如果停止的是高优先级音效，恢复BGM音量
        if (this.isHighPrioritySound(soundPath)) {
          this.restoreBGM()
        }
      }
    } catch (error) {
      console.warn(`🔇 Failed to stop sound ${soundPath}:`, error)
    }
  }

  /* ─── 🎯 BGM淡出/恢复系统 ─── */
  private isHighPrioritySound(soundPath: string): boolean {
    const highPrioritySounds = [
      '/assets/sounds/bite.mp3',
      '/assets/sounds/notification.mp3'
    ]
    return highPrioritySounds.some(prioritySound => soundPath.includes(prioritySound))
  }

  private async duckBGM(): Promise<void> {
    if (this.isBgmDucked) return
    
    const bgmAudio = this.audioCache.get('/assets/sounds/bgm.mp3')
    if (bgmAudio && !bgmAudio.paused) {
      console.log('🎵 Ducking BGM for high-priority sound')
      this.isBgmDucked = true
      this.fadeVolume(bgmAudio, this.bgmOriginalVolume * 0.2, 300) // 降到20%音量
    }
  }

  private restoreBGM(): void {
    if (!this.isBgmDucked) return
    
    const bgmAudio = this.audioCache.get('/assets/sounds/bgm.mp3')
    if (bgmAudio && !bgmAudio.paused) {
      console.log('🎵 Restoring BGM volume')
      this.isBgmDucked = false
      this.fadeVolume(bgmAudio, this.bgmOriginalVolume * this.masterVolume, 500)
    }
  }

  /* ─── 🎯 音频缓存管理 ─── */
  private async getAudio(soundPath: string): Promise<HTMLAudioElement | null> {
    if (this.audioCache.has(soundPath)) {
      return this.audioCache.get(soundPath)!
    }

    try {
      const audio = new Audio(soundPath)
      audio.preload = 'auto'
      
      // 🎯 等待音频加载完成
      await new Promise((resolve, reject) => {
        audio.addEventListener('canplaythrough', resolve, { once: true })
        audio.addEventListener('error', reject, { once: true })
        audio.load()
      })

      this.audioCache.set(soundPath, audio)
      return audio
    } catch (error) {
      console.warn(`🎵 Failed to load audio ${soundPath}:`, error)
      return null
    }
  }

  /* ─── 🎯 音量控制 ─── */
  private fadeVolume(audio: HTMLAudioElement, targetVolume: number, duration: number) {
    const startVolume = audio.volume
    const volumeDiff = targetVolume - startVolume
    const steps = duration / 16 // 60fps
    const volumeStep = volumeDiff / steps

    let currentStep = 0
    const fadeInterval = setInterval(() => {
      currentStep++
      audio.volume = Math.max(0, Math.min(1, startVolume + (volumeStep * currentStep)))
      
      if (currentStep >= steps) {
        audio.volume = targetVolume
        clearInterval(fadeInterval)
      }
    }, 16)
  }

  /* ─── 🎯 系统控制 ─── */
  setMasterVolume(volume: number) {
    this.masterVolume = Math.max(0, Math.min(1, volume))
    localStorage.setItem('platemate_sound_volume', this.masterVolume.toString())
  }

  toggleSound() {
    this.soundEnabled = !this.soundEnabled
    localStorage.setItem('platemate_sound_enabled', this.soundEnabled.toString())
    return this.soundEnabled
  }

  /* ─── 🎯 预加载常用音效 ─── */
  async preloadSounds() {
    const commonSounds = [
      '/assets/sounds/notification.mp3',
      '/assets/sounds/bgm.mp3'
    ]

    await Promise.all(
      commonSounds.map(sound => this.getAudio(sound))
    )
    console.log('🎵 Common sounds preloaded')
  }
}

// 🎯 游戏专用音效枚举
export const GameSounds = {
  // 状态变化音效
  NOTIFICATION: '/assets/sounds/notification.mp3',
  BGM: '/assets/sounds/bgm.mp3',
  
  // AI分析音效
  BITE: '/assets/sounds/bite.mp3',
  
  // 宠物状态音效
  PET_HUNGRY: '/assets/sounds/notification.mp3',
  PET_SATISFIED: '/assets/sounds/notification.mp3',
  PET_EXCITED: '/assets/sounds/notification.mp3',
  
  // 游戏交互音效
  FEED_SUCCESS: '/assets/sounds/notification.mp3',
  LEVEL_UP: '/assets/sounds/notification.mp3',
  REWARD_EARNED: '/assets/sounds/notification.mp3',
} as const

// 🎯 单例模式 - 全局音效管理器
export const soundManager = new SoundManager()

// 🎯 便捷播放函数
export const playNotificationSound = (config?: SoundConfig) => 
  soundManager.playSound(GameSounds.NOTIFICATION, { volume: 0.6, ...config })

export const playPetStatusSound = (status: string, config?: SoundConfig) => {
  const soundMap: Record<string, string> = {
    'hungry': GameSounds.PET_HUNGRY,
    'satisfied': GameSounds.PET_SATISFIED,
    'excited': GameSounds.PET_EXCITED
  }
  
  const sound = soundMap[status] || GameSounds.NOTIFICATION
  return soundManager.playSound(sound, { volume: 0.5, ...config })
}

export default soundManager

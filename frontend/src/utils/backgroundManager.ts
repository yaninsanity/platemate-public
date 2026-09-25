/**
 * 🎮 统一背景管理系统
 * 为 HomeView, RoundlyBattleHistoryView, DanmakuCommentWall 提供统一的随机背景
 */

import { ref, computed } from 'vue'

// 🎨 背景图库 - 统一管理所有游戏背景
// 🎯 paths: files under public/ use /, files under assets/ must be imported
export const GAME_BACKGROUNDS = [
  '/wallpaper1.png',      // ✅ public/wallpaper1.png
  '/wallpaper2.png',      // ✅ public/wallpaper2.png
  '/wallpaper3.png',      // ✅ public/wallpaper3.png
  '/wallpaper4.png',      // ✅ public/wallpaper4.png
  // 🎯 assets/ entries removed for now; only the dependable public/ files are used
] as const

// 🎯 系统主色调渐变
export const PRIMARY_GRADIENT = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'

// 📦 随机背景管理器
export class BackgroundManager {
  private currentBackground = ref<string>('')
  
  constructor() {
    // 🎯 确保初始化时有背景
    this.currentBackground.value = GAME_BACKGROUNDS[0]
    this.randomize()
  }
  
  /**
   * 随机选择一个背景
   */
  randomize(): void {
    const randomIndex = Math.floor(Math.random() * GAME_BACKGROUNDS.length)
    const newBg = GAME_BACKGROUNDS[randomIndex]
    this.currentBackground.value = newBg
    console.log('🎨 Random background selected:', newBg)
    console.log('🎨 Available backgrounds:', GAME_BACKGROUNDS)
  }
  
  /**
   * 获取当前背景 URL（响应式）
   */
  getCurrent(): string {
    // 🎯 确保返回值不为空
    if (!this.currentBackground.value) {
      console.warn('⚠️ No background set, using fallback')
      this.currentBackground.value = GAME_BACKGROUNDS[0]
    }
    return this.currentBackground.value
  }
  
  /**
   * 获取响应式 Ref（用于 computed）
   */
  getCurrentRef() {
    return this.currentBackground
  }
  
  /**
   * 生成完整背景样式（带渐变叠加）
   * @param gradientOpacity 渐变叠加透明度 (0-1)
   */
  getStyle(gradientOpacity: number = 0.3): Record<string, string> {
    const bg = this.currentBackground.value
    if (!bg) {
      console.warn('⚠️ No background selected, using default')
      this.randomize()
    }
    
    const gradient = `linear-gradient(135deg, 
      rgba(102, 126, 234, ${gradientOpacity}) 0%, 
      rgba(118, 75, 162, ${gradientOpacity}) 100%
    )`
    
    const finalBg = this.currentBackground.value || GAME_BACKGROUNDS[0]
    console.log('🎨 Generating style for background:', finalBg)
    
    // 🎯 mobile uses scroll rather than fixed, for iOS compatibility
    const isMobile = typeof window !== 'undefined' && window.innerWidth <= 768
    
    return {
      backgroundImage: `${gradient}, url('${finalBg}')`,
      backgroundSize: 'cover',  /* 🎯 确保图片完全覆盖容器，自动缩放 */
      backgroundPosition: 'center center',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: isMobile ? 'scroll' : 'fixed',  /* 🎯 移动端用 scroll，桌面用 fixed */
      minHeight: '100vh',
      width: '100%',  /* 🎯 确保宽度填满父容器 */
    }
  }
  
  /**
   * 生成纯 CSS 字符串（用于内联样式）
   */
  getStyleString(gradientOpacity: number = 0.3): string {
    const style = this.getStyle(gradientOpacity)
    return `
      background-image: ${style.backgroundImage};
      background-size: ${style.backgroundSize};
      background-position: ${style.backgroundPosition};
      background-repeat: ${style.backgroundRepeat};
    `.trim()
  }
}

// 🌟 全局单例实例（所有页面共享同一个随机背景）
export const globalBackgroundManager = new BackgroundManager()

// 🔄 页面级别独立实例工厂（每个页面有自己的随机背景）
export function createBackgroundManager(): BackgroundManager {
  return new BackgroundManager()
}

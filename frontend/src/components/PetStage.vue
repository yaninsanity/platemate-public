<!-- PetStage.vue ─ 渲染蛋 / 宠物动画（最终版） -->
<template>
  <div :style="wrapperStyle" class="wrapper">
    <PetRenderer
      ref="renderer"
      :base="ASSET_DIR"
      :initial-anim="fileFor(status)"
      :bg="bg"
      class="stage"
      @error="handleLoadError"       
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import PetRenderer from '@/components/PetRenderer.vue'

/* ───────────── iOS原生级performance tuning ───────────── */
const isMobile = ref(false)
const isLowPerformance = ref(false)
const isIOS = ref(false)
const devicePixelRatio = ref(1)
const isRetina = ref(false)

/* ───────────── Props ───────────── */
const props = defineProps<{
  status : string | null | undefined  /* API 可能返回 null / undefined */
  size?  : number
  bg?    : string
  loop?  : boolean
}>()

/* ─────────── 常量 ─────────── */
const ASSET_DIR = '/biped/'
const EGG_FILE  = 'egg.glb'

/* 状态 ↔︎ 文件映射 */
const statusMap: Record<string, string> = {
  egg    : EGG_FILE,
  idle   : 'Animation_You_Groove_withSkin.glb',
  walk   : 'Animation_Walking_withSkin.glb',
  run    : 'Animation_RunFast_withSkin.glb',
  running: 'Animation_Running_withSkin.glb',
  dance  : 'Animation_Boom_Dance_withSkin.glb',
  hype   : 'Animation_All_Night_Dance_withSkin.glb',
  skill  : 'Animation_Skill_01_withSkin.glb',
  gesture: 'Animation_Agree_Gesture_withSkin.glb',
  tired  : 'Animation_Slow_Orc_Walk_withSkin.glb',
  dizzy  : 'Animation_Unsteady_Walk_withSkin.glb',
  woman  : 'Animation_Walking_Woman_withSkin.glb',
  boxing : 'Animation_Boxing_Practice_withSkin.glb',
  arise  : 'Animation_Arise_withSkin.glb',
  dead   : 'Animation_Dead_withSkin.glb',
}

/* 根据状态拿 glb；任何未知 / 空值 → 蛋 */
function fileFor(s: string | null | undefined): string {
  return s && statusMap[s] ? statusMap[s] : EGG_FILE
}

/* ─────────── Renderer 控制 ─────────── */
const renderer = ref<InstanceType<typeof PetRenderer>>()

/* 🎯 iOSperformance tuning that switches animation strategy */
function optimizedPlay(file: string) {
  if (!renderer.value) return
  
  // 🎯 iOS专用tuning：利用Safari特性
  if (isIOS.value) {
    // iOS设备使用原生动画时机tuning
    if (isRetina.value && !isLowPerformance.value) {
      // Retina设备：利用硬件加速
      renderer.value?.play(file)
    } else {
      // 普通iOS设备：使用RAFtuning
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          renderer.value?.play(file)
        })
      })
    }
  } else if (isLowPerformance.value) {
    // 非iOS低性能设备：微延迟渲染
    requestAnimationFrame(() => {
      renderer.value?.play(file)
    })
  } else {
    // 桌面和高性能设备：直接播放
    renderer.value.play(file)
  }
}

/* 自动切换动画 */
watch(
  () => props.status,
  s => optimizedPlay(fileFor(s)),
  { flush: 'post' }
)

/* loop=true 时，每次都重播整个动画 */
if (props.loop !== false) {
  watch(renderer, r => r && optimizedPlay(fileFor(props.status)))
}

/* 加载出错 → 播放蛋动画 */
function handleLoadError() {
  console.warn('🎮 3D模型加载失败，切换到备用蛋动画')
  // 🎯 iOStuning：错误处理时也使用tuning的播放方式
  optimizedPlay(EGG_FILE)
}

/* ─────────── iOS原生级尺寸tuning ─────────── */
const wrapperStyle = computed(() => {
  let baseSize = props.size ?? 144
  
  // 🎯 iOS设备智能尺寸调整
  if (isIOS.value) {
    // iPhone适配：根据屏幕尺寸智能调整
    if (window.innerWidth <= 414) { // iPhone Pro Max及以下
      baseSize = Math.max(baseSize * 0.88, 110)
    } else if (window.innerWidth <= 375) { // iPhone标准尺寸
      baseSize = Math.max(baseSize * 0.85, 105)
    }
    
    // Retina显示屏tuning：利用高分辨率
    if (isRetina.value && !isLowPerformance.value) {
      // Retina设备可以保持较大尺寸，硬件加速处理
      baseSize = Math.max(baseSize, 120)
    }
  } else if (isMobile.value && baseSize > 150) {
    // 非iOS移动设备：温和调整
    baseSize = Math.max(baseSize * 0.9, 120)
  }
  
  // 🎯 极低性能设备：最小影响调整
  if (isLowPerformance.value && window.innerWidth <= 360) {
    baseSize = Math.max(baseSize * 0.82, 95)
  }
  
  const px = String(Math.round(baseSize)) + 'px'
  return { 
    width: px, 
    height: px,
    // 🎯 iOS专用CSS变量
    '--pet-size': px,
    '--device-pixel-ratio': String(devicePixelRatio.value),
    '--is-ios': isIOS.value ? '1' : '0',
    '--is-retina': isRetina.value ? '1' : '0'
  }
})

/* ─────────── iOS原生级设备检测 ─────────── */
onMounted(() => {
  // 🎯 精准iOS设备检测
  const detectDevice = () => {
    // 基础移动设备检测
    isMobile.value = window.innerWidth <= 768 || ('ontouchstart' in window)
    
    // 🎯 iOSdevice detection
    const isIOSDevice = /iPad|iPhone|iPod/.test(navigator.userAgent) || 
                       (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
    isIOS.value = isIOSDevice
    
    // 🎯 Retina显示屏检测
    devicePixelRatio.value = window.devicePixelRatio || 1
    isRetina.value = devicePixelRatio.value >= 2
    
    // 🎯 iOS性能分级检测
    if (isIOSDevice) {
      const userAgent = navigator.userAgent
      
      // iOS版本检测
      const iOSVersion = userAgent.match(/OS (\d+)_/)?.[1]
      const version = iOSVersion ? parseInt(iOSVersion) : 15
      
      // 设备型号判断
      const isOldDevice = /iPhone.*OS [0-9]_|iPad.*OS [0-9]_/.test(userAgent) ||
                         version < 13
      
      const isLowMemoryDevice = window.innerWidth <= 375 && window.innerHeight <= 667 // iPhone SE等
      
      // Safarispecific tuning
      const isSafari = /Safari/.test(userAgent) && !/Chrome|CriOS|FxiOS/.test(userAgent)
      
      // 综合性能评估
      isLowPerformance.value = isOldDevice || 
                              isLowMemoryDevice || 
                              (devicePixelRatio.value >= 3 && window.innerWidth <= 414) || // 高分辨率小屏
                              navigator.hardwareConcurrency < 4
      
      console.log('🍎 iOS设备检测:', {
        isIOS: isIOS.value,
        isRetina: isRetina.value,
        devicePixelRatio: devicePixelRatio.value,
        isLowPerformance: isLowPerformance.value,
        isSafari,
        version
      })
    } else {
      // 非iOS设备性能检测
      const cpuCores = navigator.hardwareConcurrency || 2
      const isSlowDevice = /Android.*Chrome\/[0-5]/.test(navigator.userAgent)
      const isSmallScreen = window.innerWidth <= 480
      const isSlowConnection = (navigator as any).connection?.effectiveType === 'slow-2g' || 
                              (navigator as any).connection?.effectiveType === '2g'
      
      isLowPerformance.value = (cpuCores < 4 && isSmallScreen) || isSlowDevice || isSlowConnection
    }
  }
  
  detectDevice()
  
  // 🎯 iOSdedicated event-listener tuning
  let resizeTimer: NodeJS.Timeout
  const throttledResize = () => {
    clearTimeout(resizeTimer)
    // iOSdevices use a shorter delay so rotation feels responsive
    const delay = isIOS.value ? 150 : 200
    resizeTimer = setTimeout(detectDevice, delay)
  }
  
  window.addEventListener('resize', throttledResize, { passive: true })
  
  // iOS设备方向变化监听
  if (isIOS.value) {
    window.addEventListener('orientationchange', () => {
      setTimeout(detectDevice, 100) // iOSa delay is needed before the size is correct
    }, { passive: true })
  }
})
</script>

<style scoped>
/* 🍎 iOS原生级3D渲染tuning */
.wrapper{
  overflow:hidden;
  border-radius:18px;
  box-shadow:0 6px 18px rgba(0,0,0,.15);
  
  /* 🎯 iOS Safari专用tuning */
  transform: translateZ(0);
  will-change: transform;
  backface-visibility: hidden;
  
  /* 🎯 关键：iOS抗锯齿tuning */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-transform: translateZ(0);
  
  /* 🎯 iOS原生级触摸tuning */
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  user-select: none;
  touch-action: manipulation;
}

.stage{
  width:100%;
  height:100%;
  
  /* 🎯 iOS Safari 3D渲染最佳实践 */
  transform: translateZ(0);
  image-rendering: auto;
  
  /* 🎯 WebGL在iOS上的tuning */
  perspective: 1000px;
  transform-style: preserve-3d;
  
  /* 🎯 iOS硬件加速tuning */
  -webkit-transform: translateZ(0);
  -webkit-perspective: 1000px;
  -webkit-transform-style: preserve-3d;
}

/* � iOSdevice-specific tuning */
@supports (-webkit-touch-callout: none) {
  .wrapper {
    /* iOS Safarispecific tuning */
    -webkit-overflow-scrolling: touch;
    isolation: isolate;
  }
  
  .stage {
    /* WebGL在iOS Safari中的最佳配置 */
    image-rendering: -webkit-optimize-contrast;
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
  }
}

/* �🎯 Retina显示屏tuning */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
  .wrapper {
    /* Retina设备：增强视觉效果 */
    box-shadow: 0 8px 24px rgba(0,0,0,.18);
    border-radius: 20px;
  }
  
  .stage {
    /* Retina专用：利用高分辨率优势 */
    image-rendering: -webkit-optimize-contrast;
  }
}

/* 🎯 iPhone Portraittuning */
@media (max-width: 414px) and (orientation: portrait) {
  .wrapper {
    /* iPhone竖屏：tuning阴影性能 */
    box-shadow: 0 4px 16px rgba(0,0,0,.14);
    border-radius: 16px;
  }
  
  .stage {
    /* iPhone WebGLtuning */
    image-rendering: optimizeSpeed;
    -webkit-transform: translateZ(0) scale3d(1, 1, 1);
    transform: translateZ(0) scale3d(1, 1, 1);
  }
}

/* 🎯 iPhone Landscapetuning */
@media (max-width: 896px) and (orientation: landscape) {
  .wrapper {
    /* iPhone横屏：保持性能 */
    box-shadow: 0 3px 14px rgba(0,0,0,.12);
    border-radius: 14px;
  }
}

/* 🎯 iPadtuning */
@media (min-width: 768px) and (max-width: 1024px) {
  .wrapper {
    /* iPad：利用更强性能 */
    box-shadow: 0 8px 24px rgba(0,0,0,.16);
    border-radius: 22px;
  }
  
  .stage {
    /* iPad WebGL：更高质量 */
    image-rendering: auto;
    perspective: 1200px;
  }
}

/* 🎯 iOS低性能设备保护 */
@media (max-width: 375px) and (-webkit-max-device-pixel-ratio: 2) {
  .stage {
    /* 老款iPhone：性能优先 */
    image-rendering: optimizeSpeed;
    perspective: 800px;
    -webkit-transform: translateZ(0) scale3d(1, 1, 1);
    transform: translateZ(0) scale3d(1, 1, 1);
  }
  
  .wrapper {
    /* 简化视觉效果保持流畅 */
    box-shadow: 0 2px 12px rgba(0,0,0,.1);
    border-radius: 12px;
  }
}

/* 🎯 iOS Safari深色模式适配 */
@media (prefers-color-scheme: dark) {
  .wrapper {
    /* 深色模式：调整阴影 */
    box-shadow: 0 6px 18px rgba(0,0,0,.25);
    border: 1px solid rgba(255,255,255,.1);
  }
}

/* 🎯 iOS用户偏好：减少动画 */
@media (prefers-reduced-motion: reduce) {
  .wrapper,
  .stage {
    will-change: auto;
    animation: none;
    transition: none;
    -webkit-transform: none;
    transform: none;
  }
}

/* 🎯 iOS安全区域适配 */
@supports (padding: max(0px)) {
  .wrapper {
    /* 避免刘海屏遮挡 */
    margin-left: max(env(safe-area-inset-left), 0px);
    margin-right: max(env(safe-area-inset-right), 0px);
  }
}

/* 🎯 CSS变量驱动的动态tuning */
.wrapper[style*="--is-ios: 1"] {
  /* iOS设备特定样式 */
  isolation: isolate;
  contain: layout style paint;
}

.wrapper[style*="--is-retina: 1"] {
  /* Retina显示屏增强 */
  image-rendering: -webkit-optimize-contrast;
}

.wrapper[style*="--device-pixel-ratio: 3"] {
  /* 超高分辨率设备 */
  transform: translateZ(0) scale3d(1, 1, 1);
}

/* 🎯 桌面设备：完整特效 */
@media (min-width: 1025px) {
  .wrapper {
    /* 桌面：完整视觉效果 */
    box-shadow: 0 10px 30px rgba(0,0,0,.2);
    border-radius: 24px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }
  
  .wrapper:hover {
    transform: translateY(-2px) translateZ(0);
    box-shadow: 0 15px 40px rgba(0,0,0,.25);
  }
  
  .stage {
    image-rendering: auto;
    perspective: 1500px;
  }
}
</style>

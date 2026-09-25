<template>
    <div class="screenshot-wrapper" ref="wrapperRef">
        <!-- Game content slot -->
        <slot></slot>

                <!-- Screenshot Button with Game UI -->
        <div class="screenshot-controls">
            <button class="screenshot-btn" @click="captureAndShare" :disabled="isCapturing">
                <div class="btn-content">
                    <div class="camera-icon">{{ buttonIcon }}</div>
                    <span class="btn-text">{{ isCapturing ? loadingText : (dynamicButtonText || buttonText) }}</span>
                    <div class="sparkles">
                        <div class="sparkle"></div>
                        <div class="sparkle"></div>
                        <div class="sparkle"></div>
                        <div class="sparkle"></div>
                        <div class="sparkle"></div>
                        <div class="sparkle"></div>
                    </div>
                </div>
                <div class="btn-glow"></div>
            </button>
        </div>

        <!-- Success Animation Modal -->
        <div v-if="showSuccess" class="success-modal">
            <div class="success-content">
                <div class="success-icon">{{ successIcon }}</div>
                <h3>{{ dynamicSuccessTitle || successTitle }}</h3>
                <p>{{ dynamicSuccessMessage || successMessage }}</p>
            </div>
        </div>

        <!-- Screenshot Preview with Game UI -->
        <div v-if="imgSrc" class="screenshot-preview-container">
            <div class="preview-header">
                <h3>{{ dynamicPreviewTitle || previewTitle }}</h3>
                <button class="close-btn" @click="imgSrc = null">×</button>
            </div>
            <div class="preview-frame">
                <img :src="imgSrc" alt="Screenshot Preview" class="screenshot-preview" />
                <div class="preview-overlay">
                    <div class="share-buttons">
                        <button class="share-btn primary" @click="shareAgain">
                            <span>{{ shareButtonText }}</span>
                        </button>
                        <button class="share-btn secondary" @click="downloadImage">
                            <span>{{ downloadButtonText }}</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted } from 'vue'
import html2canvas from 'html2canvas'

/* ───────────── iOS原生级移动端检测 ───────────── */
const isMobile = ref(false)
const isIOS = ref(false)
const isAndroid = ref(false)
const isLowPerformance = ref(false)
const devicePixelRatio = ref(1)

// Props for customization
const props = defineProps({
    // Button text customization
    buttonText: {
        type: String,
        default: 'Share Our Story'
    },
    loadingText: {
        type: String,
        default: 'Capturing...'
    },
    buttonIcon: {
        type: String,
        default: '📸'
    },
    
    // Success modal customization
    successTitle: {
        type: String,
        default: 'Screenshot Captured!'
    },
    successMessage: {
        type: String,
        default: 'Your PlateMate progress is ready to share!'
    },
    successIcon: {
        type: String,
        default: '🎉'
    },
    
    // Preview customization
    previewTitle: {
        type: String,
        default: '🏆 Your PlateMate Achievement!'
    },
    shareButtonText: {
        type: String,
        default: '🚀 Share Now'
    },
    downloadButtonText: {
        type: String,
        default: '💾 Save Image'
    },
    
    // Share content customization
    shareTitle: {
        type: String,
        default: '🍽️ My PlateMate Achievement!'
    },
    shareText: {
        type: String,
        default: 'Check out my cooking progress in PlateMate! 👨‍🍳✨'
    },
    fileName: {
        type: String,
        default: 'platemate-achievement.png'
    },
    
    // Error message customization
    errorMessage: {
        type: String,
        default: 'Screenshot failed! Please try again 🎮'
    },
    
    // Context-specific defaults
    context: {
        type: String,
        default: 'default',
        validator: (value) => ['default', 'about', 'game', 'profile', 'recipe'].includes(value)
    }
})

// Context-specific text configurations
const contextTexts = {
    default: {
        buttonText: 'Share Our Story',
        successTitle: 'Screenshot Captured!',
        successMessage: 'Your PlateMate progress is ready to share!',
        previewTitle: '🏆 Your PlateMate Achievement!',
        shareTitle: '🍽️ My PlateMate Achievement!',
        shareText: 'Check out my cooking progress in PlateMate! 👨‍🍳✨'
    },
    about: {
        buttonText: 'Share PlateMate Story',
        successTitle: 'Story Captured!',
        successMessage: 'Your PlateMate story is ready to inspire others!',
        previewTitle: '📖 Share Our PlateMate Story',
        shareTitle: '🌟 Discover PlateMate with me!',
        shareText: 'Join me on this amazing culinary journey with PlateMate! 🍽️✨'
    },
    game: {
        buttonText: 'Share Victory',
        successTitle: 'Victory Captured!',
        successMessage: 'Your gaming achievement is ready to share!',
        previewTitle: '🎮 Gaming Achievement Unlocked!',
        shareTitle: '🏆 PlateMate Victory!',
        shareText: 'Just achieved something awesome in PlateMate! 🎮🔥'
    },
    profile: {
        buttonText: 'Share Profile',
        successTitle: 'Profile Captured!',
        successMessage: 'Your profile showcase is ready to share!',
        previewTitle: '👤 My PlateMate Profile',
        shareTitle: '👨‍🍳 My PlateMate Profile',
        shareText: 'Check out my culinary profile and achievements! 🍽️⭐'
    },
    recipe: {
        buttonText: 'Share Recipe',
        successTitle: 'Recipe Captured!',
        successMessage: 'Your delicious recipe is ready to share!',
        previewTitle: '🍳 Recipe to Share',
        shareTitle: '🍽️ Delicious Recipe from PlateMate',
        shareText: 'Found this amazing recipe on PlateMate! Try it out! 👨‍🍳✨'
    }
}

// Computed properties for dynamic text
const dynamicButtonText = computed(() => props.buttonText || contextTexts[props.context].buttonText)
const dynamicSuccessTitle = computed(() => props.successTitle || contextTexts[props.context].successTitle)
const dynamicSuccessMessage = computed(() => props.successMessage || contextTexts[props.context].successMessage)
const dynamicPreviewTitle = computed(() => props.previewTitle || contextTexts[props.context].previewTitle)
const dynamicShareTitle = computed(() => props.shareTitle || contextTexts[props.context].shareTitle)
const dynamicShareText = computed(() => props.shareText || contextTexts[props.context].shareText)

// Reactive state
const wrapperRef = ref(null)
const imgSrc = ref(null)
const isCapturing = ref(false)
const showSuccess = ref(false)
let currentBlob = null

// Emits for parent component communication
const emit = defineEmits(['capture-start', 'capture-success', 'capture-error', 'share-success', 'share-error'])

/* ───────────── iOS原生级设备检测初始化 ───────────── */
onMounted(() => {
    // 🎯 精准移动设备检测
    const detectDevice = () => {
        // 基础移动设备检测
        isMobile.value = window.innerWidth <= 768 || ('ontouchstart' in window)
        
        // 🎯 iOSdevice detection
        const isIOSDevice = /iPad|iPhone|iPod/.test(navigator.userAgent) || 
                           (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
        isIOS.value = isIOSDevice
        
        // 🎯 Androiddevice detection
        const isAndroidDevice = /Android/.test(navigator.userAgent) && !isIOSDevice
        isAndroid.value = isAndroidDevice
        
        // 🎯 设备性能评估
        devicePixelRatio.value = window.devicePixelRatio || 1
        
        // 🎯 iOS/Android性能分级检测
        if (isIOSDevice) {
            // iPhoneperformance probe based on screen size and pixel ratio
            const screenArea = window.screen.width * window.screen.height
            const pixelRatio = window.devicePixelRatio || 1
            
            // detects older iPhones and low-end devices
            isLowPerformance.value = (
                screenArea < 750 * 1334 || // iPhone 6以下
                pixelRatio < 2 || // 非Retina
                window.innerWidth <= 320 // iPhone SE第一代
            )
        } else if (isAndroidDevice) {
            // Android设备性能检测
            const screenArea = window.screen.width * window.screen.height
            const pixelRatio = window.devicePixelRatio || 1
            const cores = navigator.hardwareConcurrency || 2
            
            // Android低端设备检测
            isLowPerformance.value = (
                screenArea < 720 * 1280 || // 低分辨率Android
                pixelRatio < 2 || // 低像素密度
                cores <= 4 || // 低核心数
                window.innerWidth <= 360 // 小屏设备
            )
        } else {
            // 非移动设备性能检测
            isLowPerformance.value = (
                window.innerWidth <= 480 &&
                window.devicePixelRatio <= 1.5 &&
                navigator.hardwareConcurrency <= 2
            )
        }
    }
    
    detectDevice()
    
    // 🎯 iOSdedicated event-listener tuning
    let resizeTimer
    const throttledResize = () => {
        clearTimeout(resizeTimer)
        // iOSdevices use a shorter delay so rotation feels responsive
        const delay = isIOS.value ? 150 : 200
        resizeTimer = setTimeout(detectDevice, delay)
    }
    
    window.addEventListener('resize', throttledResize, { passive: true })
    
    // iOS设备方向变化监听
    if (window.screen?.orientation) {
        window.screen.orientation.addEventListener('change', () => {
            setTimeout(detectDevice, 100) // iOSa delay is needed before the size is correct
        })
    }
})

async function captureAndShare() {
    if (!wrapperRef.value || isCapturing.value) return

    isCapturing.value = true
    emit('capture-start')
    
    try {
        console.log('🎮 Starting screenshot capture...')

        await nextTick()
        
        // 🎯 iOStuning：根据设备性能调整等待时间
        const waitTime = isIOS.value ? (isLowPerformance.value ? 500 : 200) : 300
        await new Promise(resolve => setTimeout(resolve, waitTime))

        let canvas
        
        // 🎯 移动设备专用截图策略
        if (isIOS.value || isAndroid.value) {
            console.log(`� Using mobile-optimized capture for ${isIOS.value ? 'iOS' : 'Android'}`)
            canvas = await captureWithHtml2CanvasIOS()
        } else if (window.navigator.mediaDevices && window.navigator.mediaDevices.getDisplayMedia) {
            console.log('📺 Using Screen Capture API for desktop')
            canvas = await captureWithScreenAPI()
        }
        
        if (!canvas) {
            canvas = await captureWithHtml2Canvas()
        }

        if (!canvas) {
            throw new Error('Screenshot capture failed - no canvas generated')
        }

        // 🎯 iOStuning：根据设备能力调整图像质量
        const quality = isLowPerformance.value ? 0.8 : 0.95
        imgSrc.value = canvas.toDataURL('image/png', quality)
        
        // Show success animation
        showSuccess.value = true
        setTimeout(() => {
            showSuccess.value = false
        }, 2000)

        // Convert to blob for sharing
        currentBlob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png', quality))
        const file = new File([currentBlob], props.fileName, { type: 'image/png' })

        emit('capture-success', { canvas, blob: currentBlob, file })

        // Try to share immediately
        await attemptShare(file)

    } catch (error) {
        console.error('❌ Screenshot capture failed:', error)
        emit('capture-error', error)
        showGameAlert(props.errorMessage)
    } finally {
        isCapturing.value = false
    }
}

/* ───────────── iOS/Android移动端专用截图tuning ───────────── */
async function captureWithHtml2CanvasIOS() {
    try {
        await waitForImages()
        
        const element = wrapperRef.value
        const rect = element.getBoundingClientRect()
        
        // 🎯 移动device-specific tuning配置
        const mobileConfig = {
            scale: isLowPerformance.value ? 1 : Math.min(devicePixelRatio.value, 2),
            width: rect.width,
            height: rect.height,
            scrollX: 0,
            scrollY: 0,
            x: rect.left,
            y: rect.top,
            useCORS: true,
            allowTaint: true,
            logging: false,
            backgroundColor: '#f8f9fa',
            removeContainer: true,
            foreignObjectRendering: false, // 移动设备兼容性
            imageTimeout: isLowPerformance.value ? 10000 : 6000,
            // 🎯 移动device-specific tuning
            ignoreElements: (element) => {
                // 忽略可能导致移动设备崩溃的元素
                return element.tagName === 'IFRAME' || 
                       element.tagName === 'VIDEO' ||
                       element.classList.contains('screenshot-controls') ||
                       element.classList.contains('screenshot-preview-container') ||
                       element.classList.contains('success-modal') ||
                       element.style.position === 'fixed' ||
                       element.style.position === 'sticky'
            },
            onclone: (clonedDoc) => {
                // 🎯 移动设备渲染tuning
                const clonedElement = clonedDoc.querySelector('.screenshot-wrapper')
                if (clonedElement) {
                    // 清除可能影响截图的变换
                    clonedElement.style.transform = 'none'
                    clonedElement.style.webkitTransform = 'none'
                    clonedElement.style.perspective = 'none'
                    clonedElement.style.overflow = 'visible'
                    clonedElement.style.position = 'static'
                    
                    // iOS/Android专用样式tuning
                    if (isIOS.value) {
                        clonedElement.style.webkitBackfaceVisibility = 'visible'
                        clonedElement.style.isolation = 'auto'
                    } else {
                        // Android专用tuning
                        clonedElement.style.backfaceVisibility = 'visible'
                    }
                }
                
                // 🎯 移除UI控制元素
                const elementsToRemove = [
                    '.screenshot-controls',
                    '.screenshot-preview-container', 
                    '.success-modal',
                    '.game-alert',
                    '[style*="position: fixed"]',
                    '[style*="z-index"]'
                ]
                
                elementsToRemove.forEach(selector => {
                    const elements = clonedDoc.querySelectorAll(selector)
                    elements.forEach(el => el.remove())
                })
                
                // 🎯 确保所有图片可见
                const images = clonedDoc.querySelectorAll('img')
                images.forEach(img => {
                    if (img.style.display === 'none') {
                        img.style.display = 'block'
                    }
                    // 移动设备图片渲染tuning
                    img.style.imageRendering = 'auto'
                })
                
                // 🎯 font rendering tuned for mobile
                const textElements = clonedDoc.querySelectorAll('*')
                textElements.forEach(el => {
                    if (el.style) {
                        el.style.webkitFontSmoothing = 'antialiased'
                        el.style.mozOsxFontSmoothing = 'grayscale'
                    }
                })
            }
        }

        const canvas = await html2canvas(element, mobileConfig)
        return canvas
        
    } catch (error) {
        console.error('Mobile html2canvas failed:', error)
        return null
    }
}

async function captureWithScreenAPI() {
    try {
        if (!navigator.mediaDevices?.getDisplayMedia) {
            return null
        }

        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: {
                mediaSource: 'screen',
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            }
        })

        const video = document.createElement('video')
        video.srcObject = stream
        video.play()

        return new Promise((resolve) => {
            video.addEventListener('loadedmetadata', () => {
                const canvas = document.createElement('canvas')
                canvas.width = video.videoWidth
                canvas.height = video.videoHeight
                
                const ctx = canvas.getContext('2d')
                ctx.drawImage(video, 0, 0)
                
                stream.getTracks().forEach(track => track.stop())
                resolve(canvas)
            })
        })
    } catch (error) {
        console.log('Screen Capture API not available or denied:', error)
        return null
    }
}

async function captureWithHtml2Canvas() {
    try {
        await waitForImages()
        
        const element = wrapperRef.value
        const rect = element.getBoundingClientRect()
        
        // 🎯 通用tuning配置，考虑移动设备性能
        const canvas = await html2canvas(element, {
            scale: isMobile.value ? (isLowPerformance.value ? 1 : 1.5) : Math.min(window.devicePixelRatio || 2, 2),
            width: rect.width,
            height: rect.height,
            scrollX: 0,
            scrollY: 0,
            x: rect.left,
            y: rect.top,
            useCORS: true,
            allowTaint: true,
            logging: false,
            backgroundColor: '#f8f9fa',
            removeContainer: true,
            foreignObjectRendering: !isMobile.value, // 移动设备禁用以提高兼容性
            imageTimeout: isLowPerformance.value ? 8000 : 5000,
            onclone: (clonedDoc) => {
                const clonedElement = clonedDoc.querySelector('.screenshot-wrapper')
                if (clonedElement) {
                    clonedElement.style.transform = 'none'
                    clonedElement.style.position = 'static'
                    
                    // 🎯 移动设备CSStuning
                    if (isMobile.value) {
                        clonedElement.style.webkitTransform = 'translateZ(0)'
                        clonedElement.style.webkitBackfaceVisibility = 'hidden'
                        clonedElement.style.backfaceVisibility = 'hidden'
                    }
                }
            }
        })

        return canvas
    } catch (error) {
        console.error('html2canvas failed:', error)
        return null
    }
}

async function waitForImages() {
    const images = wrapperRef.value.querySelectorAll('img')
    const promises = Array.from(images).map(img => {
        if (img.complete) return Promise.resolve()
        
        return new Promise((resolve) => {
            img.onload = resolve
            img.onerror = resolve
            // 🎯 iOS设备使用更长的超时时间
            const timeout = isIOS.value ? 5000 : 3000
            setTimeout(resolve, timeout)
        })
    })
    
    await Promise.all(promises)
}

async function attemptShare(file) {
    // 🎯 移动设备原生分享tuning
    if ((isIOS.value || isAndroid.value) && navigator.share) {
        try {
            // 检查设备是否支持文件分享
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({
                    files: [file],
                    title: dynamicShareTitle.value,
                    text: dynamicShareText.value
                })
                console.log(`📤 ${isIOS.value ? 'iOS' : 'Android'} native share successful!`)
                emit('share-success', { file })
                return
            } else {
                // 移动设备不支持文件分享，尝试其他方式
                console.log('📱 File sharing not supported, trying alternative methods')
                if (isAndroid.value) {
                    // Android设备特殊处理
                    await attemptAndroidShare(file)
                    return
                }
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.log(`${isIOS.value ? 'iOS' : 'Android'} share cancelled or failed, showing preview instead`)
                emit('share-error', error)
            }
            return
        }
    }
    
    // 🎯 桌面端或不支持原生分享的设备
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
        try {
            await navigator.share({
                files: [file],
                title: dynamicShareTitle.value,
                text: dynamicShareText.value
            })
            console.log('📤 Screenshot shared successfully!')
            emit('share-success', { file })
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.log('Share cancelled or failed, showing preview instead')
                emit('share-error', error)
            }
        }
    } else {
        console.log('💡 Web Share API not supported, showing preview')
    }
}

// 🎯 Android设备专用分享处理
async function attemptAndroidShare(file) {
    try {
        // Android Chrome支持的分享方式
        if ('share' in navigator) {
            // 尝试分享URL而不是文件（更好的Android兼容性）
            const dataUrl = URL.createObjectURL(file)
            
            // 如果支持，直接分享文件
            if (navigator.canShare({ files: [file] })) {
                await navigator.share({
                    files: [file],
                    title: dynamicShareTitle.value,
                    text: dynamicShareText.value
                })
            } else {
                // 否则分享文本和链接
                await navigator.share({
                    title: dynamicShareTitle.value,
                    text: `${dynamicShareText.value} - Screenshot: ${dataUrl}`,
                    url: window.location.href
                })
            }
            
            console.log('📤 Android share successful!')
            emit('share-success', { file })
            
            // 清理临时URL
            setTimeout(() => URL.revokeObjectURL(dataUrl), 1000)
        }
    } catch (error) {
        console.log('Android share failed:', error)
        // 回退到下载
        downloadImage()
        emit('share-error', error)
    }
}

async function shareAgain() {
    if (currentBlob) {
        const file = new File([currentBlob], props.fileName, { type: 'image/png' })
        await attemptShare(file)
    }
}

function downloadImage() {
    if (imgSrc.value) {
        const link = document.createElement('a')
        link.download = props.fileName
        link.href = imgSrc.value
        link.click()
    }
}

function showGameAlert(message) {
    const alertEl = document.createElement('div')
    alertEl.className = 'game-alert'
    alertEl.textContent = message
    
    // 🎯 iOS专用样式tuning
    if (isIOS.value) {
        alertEl.style.webkitTransform = 'translateZ(0)'
        alertEl.style.webkitBackfaceVisibility = 'hidden'
    }
    
    document.body.appendChild(alertEl)
    
    setTimeout(() => {
        alertEl.remove()
    }, 3000)
}

// Expose for parent components
defineExpose({
    captureAndShare,
    isCapturing,
    // 🎯 移动设备状态暴露
    isMobile,
    isIOS,
    isAndroid,
    isLowPerformance,
    setCustomText: (textOverrides) => {
        Object.assign(contextTexts[props.context], textOverrides)
    },
    // 🎯 通用截图API - 供其他组件使用
    captureScreenshot: async (targetElement = null) => {
        try {
            const element = targetElement || wrapperRef.value
            if (!element) throw new Error('No target element found')
            
            // 临时设置目标元素
            const originalRef = wrapperRef.value
            if (targetElement) {
                wrapperRef.value = targetElement
            }
            
            // 执行截图
            await waitForImages()
            let canvas
            
            if (isIOS.value || isAndroid.value) {
                canvas = await captureWithHtml2CanvasIOS()
            } else {
                canvas = await captureWithHtml2Canvas()
            }
            
            // 恢复原始引用
            wrapperRef.value = originalRef
            
            if (!canvas) throw new Error('Screenshot capture failed')
            
            // 生成图片
            const quality = isLowPerformance.value ? 0.8 : 0.95
            const dataUrl = canvas.toDataURL('image/png', quality)
            const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png', quality))
            const file = new File([blob], props.fileName, { type: 'image/png' })
            
            return {
                canvas,
                dataUrl,
                blob,
                file,
                share: async () => await attemptShare(file)
            }
        } catch (error) {
            console.error('Screenshot API failed:', error)
            throw error
        }
    }
})
</script>

<style scoped>
.screenshot-wrapper {
    position: relative;
    min-height: 100vh;
    overflow: visible;
    
    /* 🎯 iOS Safari专用tuning */
    -webkit-overflow-scrolling: touch;
    -webkit-transform: translateZ(0);
    transform: translateZ(0);
    will-change: transform;
    
    /* 🎯 iOSperformance tuning */
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
}

.screenshot-controls {
    position: fixed;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    
    /* 🎯 iOS安全区域适配 */
    padding-bottom: env(safe-area-inset-bottom, 0);
    
    /* 🎯 iOS触摸tuning */
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    user-select: none;
}

.screenshot-btn {
    background: linear-gradient(135deg, #ff6b9d, #ffc3a0, #ff9a9e);
    border: none;
    border-radius: 50px;
    color: white;
    font-weight: 800;
    padding: 16px 32px;
    font-size: 1.1rem;
    cursor: pointer;
    position: relative;
    overflow: visible;
    box-shadow: 0 8px 30px rgba(255, 107, 157, 0.4);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    transform: translateY(0);
    min-width: 220px;
    max-width: 90vw;
    text-align: center;
    white-space: nowrap;
    display: flex;
    align-items: center;
    justify-content: center;
    
    /* 🎯 iOS原生触摸tuning */
    -webkit-tap-highlight-color: transparent;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    user-select: none;
    touch-action: manipulation;
    
    /* 🎯 iOS Safariperformance tuning */
    -webkit-transform: translateY(0) translateZ(0);
    will-change: transform;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
}

.screenshot-btn:hover:not(:disabled) {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(255, 107, 157, 0.6);
    
    /* 🎯 iOS Safari硬件加速 */
    -webkit-transform: translateY(-4px) translateZ(0);
}

/* 🎯 iOS设备触摸状态tuning */
.screenshot-btn:active {
    transform: translateY(-2px) scale(0.98);
    -webkit-transform: translateY(-2px) scale(0.98) translateZ(0);
    transition: all 0.1s ease;
}

.screenshot-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    transform: translateY(0);
    -webkit-transform: translateY(0) translateZ(0);
}

.btn-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    position: relative;
    z-index: 2;
    width: 100%;
}

.camera-icon {
    font-size: 1.2em;
    animation: bounce 2s infinite;
    flex-shrink: 0;
}

.btn-text {
    font-family: 'Comic Sans MS', cursive, sans-serif;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    flex: 1;
    min-width: 0;
    text-align: center;
    font-size: 1em;
    line-height: 1.2;
}

.btn-glow {
    position: absolute;
    top: -10px;
    left: -10px;
    right: -10px;
    bottom: -10px;
    background: linear-gradient(135deg, #ff6b9d, #ffc3a0, #ff9a9e);
    border-radius: 60px;
    opacity: 0.3;
    animation: pulse 3s infinite;
    z-index: 0;
}

.sparkles {
    position: absolute;
    top: -20px;
    left: -20px;
    right: -20px;
    bottom: -20px;
    pointer-events: none;
    z-index: 3;
}

.sparkle {
    position: absolute;
    width: 4px;
    height: 4px;
    background: white;
    border-radius: 50%;
    animation: sparkle 2s infinite;
}

.sparkle:nth-child(1) { top: 10%; left: 15%; animation-delay: 0s; }
.sparkle:nth-child(2) { top: 20%; right: 20%; animation-delay: 0.3s; }
.sparkle:nth-child(3) { bottom: 15%; left: 25%; animation-delay: 0.6s; }
.sparkle:nth-child(4) { bottom: 25%; right: 15%; animation-delay: 0.9s; }
.sparkle:nth-child(5) { top: 50%; left: 10%; animation-delay: 1.2s; }
.sparkle:nth-child(6) { top: 60%; right: 10%; animation-delay: 1.5s; }

.success-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    animation: fadeIn 0.3s ease;
}

.success-content {
    background: white;
    padding: 2rem;
    border-radius: 20px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
    animation: popIn 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    max-width: 400px;
    margin: 0 1rem;
}

.success-content h3 {
    margin: 1rem 0 0.5rem 0;
    font-family: 'Comic Sans MS', cursive, sans-serif;
    color: #333;
}

.success-content p {
    margin: 0;
    color: #666;
    line-height: 1.5;
}

.success-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    animation: rotate 0.8s ease-in-out;
}

.screenshot-preview-container {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 1500;
    max-width: 90vw;
    max-height: 90vh;
    background: white;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    overflow: hidden;
    animation: slideUp 0.5s ease;
}

.preview-header {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 1rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.preview-header h3 {
    margin: 0;
    font-family: 'Comic Sans MS', cursive, sans-serif;
    font-size: 1.2rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.close-btn {
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s ease;
    flex-shrink: 0;
}

.close-btn:hover {
    background: rgba(255, 255, 255, 0.2);
}

.preview-frame {
    position: relative;
    max-height: 60vh;
    overflow: hidden;
}

.screenshot-preview {
    width: 100%;
    height: auto;
    display: block;
}

.preview-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
    padding: 2rem 1rem 1rem;
}

.share-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
}

.share-btn {
    border: none;
    border-radius: 25px;
    padding: 12px 24px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease;
    font-family: 'Comic Sans MS', cursive, sans-serif;
    min-width: 120px;
    text-align: center;
}

.share-btn span {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: block;
}

.share-btn.primary {
    background: linear-gradient(135deg, #ff6b9d, #ff9a9e);
    color: white;
    box-shadow: 0 4px 15px rgba(255, 107, 157, 0.4);
}

.share-btn.secondary {
    background: linear-gradient(135deg, #a8edea, #fed6e3);
    color: #333;
    box-shadow: 0 4px 15px rgba(168, 237, 234, 0.4);
}

.share-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

:global(.game-alert) {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #ff6b9d, #ff9a9e);
    color: white;
    padding: 1rem 2rem;
    border-radius: 50px;
    font-weight: 700;
    z-index: 3000;
    animation: slideDown 0.5s ease, fadeOut 0.5s ease 2.5s;
    box-shadow: 0 8px 30px rgba(255, 107, 157, 0.4);
    max-width: 80vw;
    text-align: center;
}

@keyframes bounce {
    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
    40% { transform: translateY(-6px); }
    60% { transform: translateY(-3px); }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.3; }
    50% { transform: scale(1.05); opacity: 0.5; }
}

@keyframes sparkle {
    0%, 100% { opacity: 0; transform: scale(0) rotate(0deg); }
    50% { opacity: 1; transform: scale(1) rotate(180deg); }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes popIn {
    from { opacity: 0; transform: scale(0.8); }
    to { opacity: 1; transform: scale(1); }
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes slideUp {
    from { opacity: 0; transform: translate(-50%, -40%); }
    to { opacity: 1; transform: translate(-50%, -50%); }
}

@keyframes slideDown {
    from { opacity: 0; transform: translate(-50%, -100%); }
    to { opacity: 1; transform: translate(-50%, 0); }
}

@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}

@media (max-width: 768px) {
    .screenshot-btn {
        padding: 14px 24px;
        font-size: 1rem;
        min-width: 200px;
        max-width: 85vw;
        
        /* 🎯 touch tuning for mobile */
        min-height: 48px; /* iOS推荐最小触摸目标 */
    }
    
    .btn-text {
        font-size: 0.9rem;
    }
    
    .screenshot-preview-container {
        max-width: 95vw;
        max-height: 95vh;
        
        /* 🎯 iOS安全区域适配 */
        margin-top: env(safe-area-inset-top, 0);
        margin-bottom: env(safe-area-inset-bottom, 0);
    }
    
    .share-buttons {
        flex-direction: column;
        align-items: center;
        gap: 0.8rem; /* 移动设备增加间距 */
    }
    
    .share-btn {
        width: 100%;
        max-width: 200px;
        min-height: 44px; /* iOS推荐触摸目标 */
        
        /* 🎯 touch tuning for mobile */
        -webkit-tap-highlight-color: transparent;
        touch-action: manipulation;
    }
    
    .preview-header h3 {
        font-size: 1rem;
    }
    
    /* 🎯 iOS专用控制区域适配 */
    .screenshot-controls {
        bottom: max(30px, env(safe-area-inset-bottom));
        padding-left: env(safe-area-inset-left, 0);
        padding-right: env(safe-area-inset-right, 0);
    }
}

@media (max-width: 480px) {
    .screenshot-btn {
        padding: 12px 20px;
        font-size: 0.9rem;
        min-width: 180px;
        min-height: 46px; /* 小屏设备确保触摸目标 */
    }
    
    .btn-text {
        font-size: 0.85rem;
    }
    
    .camera-icon {
        font-size: 1.1em;
    }
    
    /* 🎯 小屏iOS设备tuning */
    .screenshot-preview-container {
        max-width: 98vw;
        max-height: 90vh;
        border-radius: 12px; /* 减小圆角以适应小屏 */
    }
}

/* 🎯 iOSdevice-specific tuning */
@supports (-webkit-touch-callout: none) {
    .screenshot-wrapper {
        /* iOS Safarispecific tuning */
        -webkit-overflow-scrolling: touch;
        isolation: isolate;
    }
    
    .screenshot-btn {
        /* iOS原生按钮感觉 */
        -webkit-appearance: none;
        appearance: none;
    }
    
    .share-btn {
        -webkit-appearance: none;
        appearance: none;
        -webkit-tap-highlight-color: transparent;
    }
}

/* 🎯 iOS深色模式适配 */
@media (prefers-color-scheme: dark) {
    .screenshot-preview-container {
        background: #2a2a3e;
        color: white;
    }
    
    .preview-header {
        background: linear-gradient(135deg, #4a5568, #2d3748);
    }
}

/* 🎯 iOS用户偏好：减少动画 */
@media (prefers-reduced-motion: reduce) {
    .screenshot-btn,
    .btn-glow,
    .sparkle,
    .success-modal,
    .screenshot-preview-container {
        animation: none !important;
        transition: none !important;
    }
    
    .camera-icon {
        animation: none !important;
    }
}
</style>
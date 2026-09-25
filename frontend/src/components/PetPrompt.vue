<template>
  <!-- 固定在视口上 1/3，高度随内容 -->
  <section class="hud-zone">
    <transition name="pop" mode="out-in"
      @before-enter="resetTyped"
      @enter="typeIt"
    >
      <div
        v-if="msg"
        :key="msg"
        class="bubble"
        :class="{ glass, 'has-progress': countdown }"
        :style="bubbleStyle"
      >
        <img v-if="avatar" :src="avatar" class="avatar" />

        <span ref="txt" class="text"/>

        <!-- 倒计进度条 -->
        <div
          v-if="countdown"
          class="progress"
          :style="{ animationDuration: countdown + 'ms' }"
        />
      </div>
    </transition>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { playNotificationSound } from '@/utils/soundManager'

/* ─ props ─ */
const props = withDefaults(defineProps<{
  msg        : string
  /* 色彩相关 */
  gradient?  : string
  bgColor?   : string
  textColor? : string
  glass?     : boolean
  /* 尺寸 & 间距 */
  min?       : number
  max?       : number
  gap?       : number     /* 与宠物垂直间隙，HomeView 控制 */
  /* 其他 */
  avatar?    : string
  countdown? : number     /* ms，自动隐藏并 emit */
  typeSpeed? : number     /* 0 = 不打字 */
}>(), {
  gradient : '',
  bgColor  : 'rgba(255,255,255,.92)',
  textColor: '',
  glass    : false,
  min      : 260,
  max      : 420,
  gap      : 24,
  typeSpeed: 35,
  countdown: 0,
})

/* ─ 颜色处理：若 textColor 未给，自动判断深/浅 ─ */
function luminance (hex:string) {
  const c = hex.replace('#','')
  const rgb = c.length === 3
      ? c.split('').map(s=>parseInt(s+s,16))
      : [0,1,2].map(i=>parseInt(c.substr(i*2,2),16))
  return (0.299*rgb[0]+0.587*rgb[1]+0.114*rgb[2]) / 255
}
const autoTxt = computed(() => {
  if (props.textColor) return props.textColor
  // take the first gradient stop when there is one, otherwise bgColor
  const sample = props.gradient?.split(',')[1] || props.bgColor
  return luminance(sample) > .6 ? '#222' : '#fff'
})

/* ─ style ─ */
const bubbleStyle = computed(() => ({
  background : props.gradient
    ? `linear-gradient(${props.gradient})`
    : props.bgColor,
  color      : autoTxt.value,
  minWidth   : props.min + 'px',
  maxWidth   : `min(${props.max}px, 90vw)`,
  textShadow : '0 1px 2px rgba(0,0,0,.35)',
}))

/* ─ 打字机 ─ */
const txt = ref<HTMLSpanElement>()
function resetTyped(){ if(txt.value) txt.value.textContent='' }
function typeIt () {
  if (!txt.value) return
  if (!props.typeSpeed) { txt.value.textContent = props.msg; return }
  let i = 0; const ch = [...props.msg]
  const timer = setInterval(()=>{
    txt.value!.textContent += ch[i++] ?? ''
    if (i >= ch.length) clearInterval(timer)
  }, props.typeSpeed)
}
watch(()=>props.msg,()=>{ 
  resetTyped(); 
  typeIt(); 
  restart();
  
  // 🎵 new-message sound, tuned for mobile
  if (props.msg) {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
    const volumeConfig = isMobile ? 0.25 : 0.4  // 移动端降低音量避免干扰其他音效
    const fadeInTime = isMobile ? 150 : 200     // 移动端更快淡入
    
    playNotificationSound({ 
      volume: volumeConfig, 
      fadeIn: fadeInTime 
    })
  }
})

/* ─ 自动隐藏 ─ */
const emit = defineEmits<{ (e:'hide'):void }>()
let t:ReturnType<typeof setTimeout>|null=null
function restart(){
  t && clearTimeout(t)
  if (props.countdown) t = setTimeout(()=>emit('hide'), props.countdown)
}
onMounted(() => { typeIt(); restart() })
onBeforeUnmount(()=> t && clearTimeout(t))
</script>

<style scoped>
/* 🎮 AAA HUD zone：扩展到头像上方 */
.hud-zone{
  position:fixed; 
  inset:0 0 auto 0; 
  height:40vh; /* 🎯 33vh→40vh，更大空间 */
  display:flex; 
  justify-content:center; 
  align-items:center; /* 🎯 flex-start→center，垂直居中 */
  padding-top: 2vh; /* 🎯 向下偏移，避免贴顶 */
  pointer-events:none; 
  z-index:900;
}

/* 🎮 AAA bubble：终极超大游戏化对话框 */
.bubble{
  position:relative;
  padding: 32px 48px; /* 🎯 24px→32px, 36px→48px，+33%内边距 */
  border-radius: 40px; /* 🎯 32px→40px，极致圆润 */
  display:flex; 
  align-items:center; 
  gap:24px; /* 🎯 18px→24px，+33% */
  box-shadow:0 20px 50px rgba(0,0,0,.3), 
             0 0 30px rgba(255,255,255,.25),
             0 0 60px rgba(255,182,193,.2); /* 🎯 三层阴影+超强发光 */
  backdrop-filter:blur(28px);
  transform: scale(1.2); /* 🎯 1.1→1.2，整体放大20% */
  animation: bubbleFloat 4s ease-in-out infinite;
}

@keyframes bubbleFloat {
  0%, 100% { transform: scale(1.2) translateY(0); }
  50% { transform: scale(1.2) translateY(-10px); }
}

.glass{
  background:rgba(255,255,255,.4); /* 🎯 增强背景透明度 */
  border:3px solid rgba(255,255,255,.6); /* 🎯 2px→3px，更粗边框 */
  box-shadow:0 16px 40px rgba(0,0,0,.18), 
             inset 0 0 12px rgba(255,255,255,.95),
             0 0 30px rgba(255,182,193,.3); /* 🎯 粉色外发光 */
}

.avatar{
  width:56px;
  height:56px; /* 🎯 48px→56px，+17% */
  border-radius:50%;
  flex:none;
  object-fit:cover;
  box-shadow:0 0 0 5px rgba(255,255,255,1), 
             0 0 20px rgba(255,182,193,.6); /* 🎯 5px边框+更强粉色发光 */
}

.text{
  white-space:pre-line;
  font-size: 36px; /* 🎯 28px → 36px，+29% 终极放大 */
  line-height: 1.6;
  font-family: 'Comic Sans MS', 'Chalkboard SE', 'Comic Neue', 'Marker Felt', 'Bradley Hand', cursive, sans-serif;
  font-weight: 900; /* 🎯 800→900，最粗游戏化 */
  letter-spacing: 1px; /* 🎯 0.8px→1px，更大字间距 */
  text-shadow: 0 4px 8px rgba(0,0,0,.25), 
               0 0 30px rgba(255,255,255,.5),
               0 0 60px rgba(255,182,193,.4),
               0 0 100px rgba(255,215,0,.2); /* 🎯 四层阴影+金色光晕 */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #1a1a1a; /* 🎯 更深色文字，最高对比度 */
}

/* 🎮 AAA progress bar */
.has-progress{ padding-bottom:32px; } /* 🎯 26px→32px */
.progress{
  position:absolute;
  inset:auto 14px 10px 14px; /* 🎯 更大边距 */
  height:5px; /* 🎯 3px→5px，更粗更可见 */
  background:rgba(0,0,0,.25);
  border-radius:5px;
  overflow:hidden;
  box-shadow: inset 0 1px 3px rgba(0,0,0,.3); /* 🎯 内阴影 */
}
.progress::before{
  content:'';
  position:absolute;
  inset:0;
  background: linear-gradient(90deg, #ff6b9d, #ffa07a, #ffd700); /* 🎯 渐变彩色 */
  transform-origin:left;
  animation:fill var(--dur,3s) linear forwards;
  box-shadow: 0 0 10px rgba(255,107,157,.6); /* 🎯 发光效果 */
}
.progress[style]::before{ animation-duration:inherit }

/* pop motion */
.pop-enter-active,.pop-leave-active{
  transition:opacity .4s ease, transform .4s cubic-bezier(.25,1,.3,1);
}
.pop-enter-from,.pop-leave-to{
  opacity:0; transform:translateY(-16px) scale(.8);
}
</style>

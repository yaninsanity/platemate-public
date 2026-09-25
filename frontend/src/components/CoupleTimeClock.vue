<template>
  <div class="couple-time-clock" @click="$emit('click')">
    <div class="clock-glow"></div>
    <div class="clock-container clock-clickable">
      <!-- 🎯 真实时钟表盘 -->
      <div class="clock-dial">
        <div class="clock-center"></div>
        <!-- 12个刻度点 -->
        <div v-for="i in 12" :key="i" class="clock-tick" :style="getTickStyle(i)"></div>
        <!-- 时针 -->
        <div class="clock-hand hour-hand" :style="{ transform: `rotate(${hourRotation}deg)` }"></div>
        <!-- 分针 -->
        <div class="clock-hand minute-hand" :style="{ transform: `rotate(${minuteRotation}deg)` }"></div>
      </div>
      <!-- 时区标签 -->
      <div class="timezone-label">{{ timezoneLabel }}</div>
      <!-- 🎯 日期显示（MM-DD-YYYY） -->
      <div class="date-label">{{ formattedDate }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  timezone: string  // e.g. 'America/New_York', 'Asia/Shanghai', 'UTC'
  label?: string    // e.g. 'Partner', 'You'
}

const props = withDefaults(defineProps<Props>(), {
  label: ''
})

// 🎯 发出点击事件，用于打开Modal
defineEmits<{
  (e: 'click'): void
}>()

// 当前时间（每秒更新）
const currentTime = ref(new Date())
let intervalId: number | null = null

// 🎯 计算时针分针角度
const hourRotation = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.timezone }))
    const hours = date.getHours() % 12
    const minutes = date.getMinutes()
    // 时针：每小时30度，每分钟0.5度
    return (hours * 30) + (minutes * 0.5)
  } catch (e) {
    return 0
  }
})

const minuteRotation = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.timezone }))
    const minutes = date.getMinutes()
    // 分针：每分钟6度
    return minutes * 6
  } catch (e) {
    return 0
  }
})

// 🎯 时区标签显示 - 精准改善：显示完整时区路径
const timezoneLabel = computed(() => {
  if (props.label) return props.label
  
  // 🎯 show the full timezone path, for example America/New_York, Asia/Shanghai, America/Phoenix）
  // underscores become spaces for readability, for example America/Los_Angeles → America/Los Angeles）
  return props.timezone.replace(/_/g, ' ')
})

// 🎯 格式化日期（MM-DD-YYYY）
const formattedDate = computed(() => {
  try {
    const date = new Date(currentTime.value.toLocaleString('en-US', { timeZone: props.timezone }))
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const year = date.getFullYear()
    return `${month}-${day}-${year}`
  } catch (e) {
    return 'N/A'
  }
})

// 🎯 刻度位置计算
const getTickStyle = (index: number) => {
  const angle = (index * 30) - 90 // 12点为0度，向右为正
  const radius = 42 // 表盘半径的百分比
  const x = 50 + radius * Math.cos(angle * Math.PI / 180)
  const y = 50 + radius * Math.sin(angle * Math.PI / 180)
  return {
    left: `${x}%`,
    top: `${y}%`
  }
}

// 生命周期：启动时钟
onMounted(() => {
  intervalId = window.setInterval(() => {
    currentTime.value = new Date()
  }, 1000)
})

// 生命周期：清理定时器
onUnmounted(() => {
  if (intervalId !== null) {
    clearInterval(intervalId)
  }
})
</script>

<style scoped lang="scss">
// 🎮 AAA工业级时钟组件 - 情侣时区实时显示
.couple-time-clock {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  z-index: 300; /* 高于按钮 */
}

// 🎨 发光效果
.clock-glow {
  position: absolute;
  inset: -10px;
  background: radial-gradient(circle, rgba(255, 182, 193, 0.5) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(15px);
  opacity: 0.6;
  animation: clockGlow 3s ease-in-out infinite;
  pointer-events: none;
}

@keyframes clockGlow {
  0%, 100% { opacity: 0.5; transform: scale(0.95); }
  50% { opacity: 0.8; transform: scale(1.08); }
}

// 🎮 时钟容器 - 精准改善：固定尺寸确保一致性
.clock-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px;
  
  /* 🎯 固定宽度，防止时区文字长度导致尺寸不一致 */
  width: 160px;
  min-width: 160px;
  max-width: 160px;
  
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.18) 0%, 
    rgba(255, 182, 193, 0.12) 100%
  );
  border-radius: 18px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(28px) saturate(200%);
  box-shadow: 
    0 12px 45px rgba(0, 0, 0, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.4),
    0 0 30px rgba(255, 182, 193, 0.25);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  
  &:hover {
    transform: translateY(-4px) scale(1.04);
    border-color: rgba(255, 182, 193, 0.65);
    box-shadow: 
      0 18px 60px rgba(0, 0, 0, 0.35),
      inset 0 2px 0 rgba(255, 255, 255, 0.5),
      0 0 40px rgba(255, 182, 193, 0.35);
  }
  
  /* 🎯 响应式尺寸 - 保持固定宽度 */
  @media (min-width: 1200px) {
    width: 180px;
    min-width: 180px;
    max-width: 180px;
    padding: clamp(12px, 1.4vh, 16px);
    gap: clamp(6px, 0.7vh, 10px);
  }
  
  @media (min-width: 769px) and (max-width: 1199px) {
    width: 160px;
    min-width: 160px;
    max-width: 160px;
    padding: 10px;
    gap: 6px;
  }
  
  @media (max-width: 768px) {
    width: 140px;
    min-width: 140px;
    max-width: 140px;
    padding: 8px;
    gap: 4px;
  }
}

// 🕐 时钟表盘
.clock-dial {
  position: relative;
  width: clamp(70px, 8vw, 90px);
  height: clamp(70px, 8vw, 90px);
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, 
    rgba(255, 255, 255, 0.25) 0%, 
    rgba(255, 182, 193, 0.15) 100%
  );
  border: 3px solid rgba(255, 255, 255, 0.4);
  box-shadow: 
    inset 0 2px 8px rgba(0, 0, 0, 0.2),
    inset 0 -2px 4px rgba(255, 255, 255, 0.3),
    0 4px 12px rgba(0, 0, 0, 0.15);
  
  @media (max-width: 768px) {
    width: 60px;
    height: 60px;
    border-width: 2px;
  }
}

// 🎯 中心点
.clock-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b9d, #ffa07a);
  box-shadow: 
    0 0 8px rgba(255, 107, 157, 0.6),
    inset 0 1px 2px rgba(255, 255, 255, 0.5);
  z-index: 10;
  
  @media (max-width: 768px) {
    width: 6px;
    height: 6px;
  }
}

// 🎯 刻度点 - 精准改善：增强可见性
.clock-tick {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.95); /* 🎯 提高不透明度 */
  transform: translate(-50%, -50%);
  box-shadow: 
    0 1px 3px rgba(0, 0, 0, 0.5),  /* 🎯 加深阴影 */
    0 0 4px rgba(255, 255, 255, 0.6); /* 🎯 白色外发光 */
  border: 0.5px solid rgba(0, 0, 0, 0.3); /* 🎯 添加深色边框 */
  
  @media (max-width: 768px) {
    width: 3px;
    height: 3px;
  }
}

// 🕐 指针基础样式
.clock-hand {
  position: absolute;
  bottom: 50%;
  left: 50%;
  transform-origin: bottom center;
  border-radius: 999px;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

// ⏰ 时针
.hour-hand {
  width: 4px;
  height: 28%;
  background: linear-gradient(to top, 
    rgba(255, 107, 157, 0.9), 
    rgba(255, 107, 157, 0.7)
  );
  margin-left: -2px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  
  @media (max-width: 768px) {
    width: 3px;
    height: 26%;
    margin-left: -1.5px;
  }
}

// ⏰ 分针
.minute-hand {
  width: 3px;
  height: 38%;
  background: linear-gradient(to top, 
    rgba(255, 160, 122, 0.95), 
    rgba(255, 160, 122, 0.75)
  );
  margin-left: -1.5px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
  
  @media (max-width: 768px) {
    width: 2px;
    height: 36%;
    margin-left: -1px;
  }
}

// 🕐 时间显示 - 精准改善：增强对比度
.time-display {
  font-size: clamp(18px, 2.2vw, 24px);
  font-weight: 900;
  font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
  color: #ffffff; /* 🎯 纯白色 */
  text-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.8), /* 🎯 加深阴影，增强对比 */
    0 0 12px rgba(0, 0, 0, 0.6),   /* 🎯 外发光深色背景 */
    0 0 2px rgba(0, 0, 0, 1);       /* 🎯 描边效果 */
  letter-spacing: 1px;
  line-height: 1;
  -webkit-font-smoothing: antialiased;
  -webkit-text-stroke: 0.5px rgba(0, 0, 0, 0.3); /* 🎯 文字描边 */
  
  @media (max-width: 768px) {
    font-size: 16px;
  }
}

// 🏷️ 时区标签 - 精准改善：固定容器，文字自适应
.timezone-label {
  /* 🎯 固定宽度，确保容器统一 */
  width: 100%;
  max-width: 140px;
  
  font-size: clamp(10px, 1.2vw, 12px); /* 🎯 稍微减小避免溢出 */
  font-weight: 800;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: #ffffff;
  text-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.95),
    0 0 10px rgba(0, 0, 0, 0.8),
    0 0 3px rgba(0, 0, 0, 1);
  letter-spacing: 0.5px; /* 🎯 减小字间距避免溢出 */
  line-height: 1.3;
  text-transform: uppercase;
  -webkit-font-smoothing: antialiased;
  -webkit-text-stroke: 0.4px rgba(0, 0, 0, 0.5);
  
  /* 🎯 文字溢出处理 - 自动换行 */
  word-break: break-word;
  overflow-wrap: break-word;
  text-align: center;
  
  /* 🎯 添加背景高光 */
  padding: 4px 8px;
  background: linear-gradient(135deg, 
    rgba(255, 182, 193, 0.25) 0%, 
    rgba(255, 107, 157, 0.2) 100%
  );
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  
  @media (max-width: 768px) {
    max-width: 120px;
    font-size: 9px;
    padding: 3px 6px;
    letter-spacing: 0.3px;
  }
}

// 🗓️ date label in MM-DD-YYYY, fixed width
.date-label {
  /* 🎯 固定宽度，确保统一 */
  width: 100%;
  max-width: 140px;
  text-align: center;
  
  font-size: clamp(10px, 1.1vw, 12px);
  font-weight: 700;
  font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 
    0 1px 3px rgba(0, 0, 0, 0.9),
    0 0 6px rgba(0, 0, 0, 0.7);
  letter-spacing: 0.3px; /* 🎯 减小避免溢出 */
  line-height: 1;
  -webkit-font-smoothing: antialiased;
  -webkit-text-stroke: 0.2px rgba(0, 0, 0, 0.3);
  opacity: 0.9;
  
  /* 🎯 防止文字溢出 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  
  @media (max-width: 768px) {
    max-width: 120px;
    font-size: 9px;
    letter-spacing: 0.2px;
  }
}
</style>

<template>
  <div
    ref="root"
    class="hunger-display-aaa"
    :class="hungerStatusClass"
    role="button"
    tabindex="0"
    :aria-label="`Hunger ${Math.round(hunger * 10) / 10} percent. ${hungerText}`"
    @click="handleOpen"
    @keyup.enter="handleOpen"
  >
    <div class="hunger-glow" :style="hungerGlowStyle"></div>

  <!-- 左侧：状态图标 -->
  <div class="hunger-icon-section">
    <div class="status-icon-glow" :class="hungerStatusClass">
      <v-icon size="20" color="white">{{ hunger < 30 ? 'mdi-heart-pulse' : 'mdi-food-drumstick' }}</v-icon>
    </div>
  </div>

    <!-- 中间信息区 -->
    <div class="hunger-info-aaa">
      <div class="hunger-status-row">
        <span class="hunger-label">HUNGER</span>
        <span class="hunger-status">{{ hungerText.toUpperCase() }}</span>
      </div>
      <div class="hunger-bar-aaa">
        <div class="hunger-track">
          <div class="hunger-fill-aaa" :style="hungerBarStyle">
            <div class="fill-shine"></div>
            <div class="fill-particles"></div>
          </div>
        </div>
        <div class="hunger-percentage">{{ Math.round(hunger * 10) / 10 }}%</div>
      </div>
    </div>

    <!-- 右侧交互提示：精简CTA -->
    <div class="hunger-action-aaa">
      <div class="action-glow" :class="{ pulse: hunger < 50, critical: hunger < 20 }">
        <v-icon size="18" color="white">mdi-plus-circle</v-icon>
      </div>
      <div class="feed-hint" v-if="hunger < 80">
        {{ hunger < 20 ? 'URGENT' : hunger < 50 ? 'FEED' : 'ADD' }}
      </div>
    </div>

    <!-- 装饰粒子 -->
    <div class="hunger-particles" v-if="hunger < 30">
      <div v-for="i in 6" :key="i" class="hunger-particle" :style="getHungerParticleStyle(i)"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{ hunger: number }>()
const emit = defineEmits<{ (e: 'open-feed'): void }>()

const hunger = computed(() => Math.max(0, Math.min(100, props.hunger ?? 0)))

const hungerStatusClass = computed(() => {
  if (hunger.value < 20) return 'critical'
  if (hunger.value < 40) return 'low'
  if (hunger.value < 70) return 'medium'
  return 'good'
})

const hungerText = computed(() => {
  if (hunger.value < 20) return 'Starving'
  if (hunger.value < 40) return 'Hungry'
  if (hunger.value < 70) return 'Okay'
  return 'Full'
})

const hungerFillColor = computed(() => {
  if (hunger.value >= 80) return 'linear-gradient(90deg, #00e676, #4caf50, #66bb6a)'
  if (hunger.value >= 60) return 'linear-gradient(90deg, #76ff03, #8bc34a, #aed581)'
  if (hunger.value >= 40) return 'linear-gradient(90deg, #ffeb3b, #ffc107, #ffb74d)'
  if (hunger.value >= 20) return 'linear-gradient(90deg, #ff9800, #ff5722, #ff7043)'
  return 'linear-gradient(90deg, #f44336, #e91e63, #ff1744)'
})

const hungerBarStyle = computed(() => ({
  width: `${hunger.value}%`,
  background: hungerFillColor.value
}))

const hungerGlowColor = computed(() => {
  if (hunger.value >= 70) return 'rgba(76, 175, 80, 0.6)'
  if (hunger.value >= 50) return 'rgba(255, 152, 0, 0.6)'
  if (hunger.value >= 30) return 'rgba(255, 87, 34, 0.7)'
  return 'rgba(244, 67, 54, 0.8)'
})

const hungerGlowStyle = computed(() => ({
  background: `radial-gradient(ellipse at center, ${hungerGlowColor.value} 0%, transparent 70%)`,
  opacity: hunger.value < 50 ? '1' : '0.6'
}))

function getHungerParticleStyle(index: number) {
  const angle = (index * 60) % 360
  const delay = (index * 0.3) % 2
  const size = Math.random() * 3 + 2
  return { '--angle': `${angle}deg`, '--delay': `${delay}s`, '--size': `${size}px` }
}

const root = ref<HTMLElement | null>(null)
function handleOpen() {
  emit('open-feed')
  const el = root.value
  if (el) {
    el.classList.add('clicked')
    setTimeout(() => el.classList.remove('clicked'), 300)
  }
  if (navigator.vibrate) navigator.vibrate([50, 25, 50])
}
</script>

<style scoped>
/* Dynamic Island 风格的饥饿显示组件 */
.hunger-display-aaa {
  display: flex;
  align-items: center;
  --island-bg: linear-gradient(145deg, rgba(15,15,20,0.92), rgba(8,8,12,0.88));
  --action-width: 56px; /* keep center balanced: left spacer width matches right CTA width */
  background: var(--island-bg);
  backdrop-filter: blur(20px) saturate(1.8);
  border-radius: 40px;
  border: 2px solid rgba(255,255,255,0.18);
  box-shadow:
    inset 0 2px 0 rgba(255,255,255,0.25),
    inset 0 -2px 0 rgba(0,0,0,0.4),
    0 8px 32px rgba(0,0,0,0.35),
    0 4px 16px rgba(0,0,0,0.2);
  cursor: pointer;
  transition: all 350ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
  min-width: 380px;
  width: clamp(380px, 52vw, 720px); /* 拉长到最右边 */
  height: 58px;
  position: relative;
  overflow: hidden;
  padding: 0;
  margin: 0 auto;
}

.hunger-display-aaa::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25) 30%, rgba(255,255,255,0.4) 50%, rgba(255,255,255,0.25) 70%, transparent);
  transition: left 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 1;
}
.hunger-display-aaa:hover::before { left: 100%; }

.hunger-display-aaa:hover {
  background: linear-gradient(145deg, rgba(20,20,28,0.95), rgba(12,12,18,0.92));
  border-color: rgba(255,255,255,0.35);
  transform: translateY(-3px) scale(1.02);
  box-shadow: 
    0 16px 40px rgba(0,0,0,0.4),
    0 8px 24px rgba(0,0,0,0.25),
    inset 0 2px 0 rgba(255,255,255,0.3);
}

.hunger-display-aaa:active {
  transform: translateY(-1px) scale(0.99);
  box-shadow: 0 8px 20px rgba(0,0,0,0.3);
}

.hunger-display-aaa.good { border-color: rgba(76,175,80,0.45); box-shadow: 0 0 20px rgba(76,175,80,0.3), 0 6px 18px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.2); }
.hunger-display-aaa.medium { border-color: rgba(255,152,0,0.45); box-shadow: 0 0 25px rgba(255,152,0,0.35), 0 6px 18px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.2); }
.hunger-display-aaa.low { border-color: rgba(255,87,34,0.55); box-shadow: 0 0 35px rgba(255,87,34,0.5), 0 6px 18px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.2); animation: lowHungerAAA 2s infinite; }
.hunger-display-aaa.critical { border-color: rgba(244,67,54,0.6); box-shadow: 0 0 50px rgba(244,67,54,0.7), 0 6px 18px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.2); animation: criticalHungerAAA 1.5s infinite; }

@keyframes lowHungerAAA { 
  0%, 100% { 
    opacity: 1; 
    box-shadow: 0 0 35px rgba(255,87,34,0.5), 0 0 60px rgba(255,87,34,0.3);
  } 
  50% { 
    opacity: 0.9; 
    box-shadow: 0 0 50px rgba(255,87,34,0.8), 0 0 80px rgba(255,87,34,0.5);
  } 
}
@keyframes criticalHungerAAA { 
  0%, 100% { 
    box-shadow: 0 0 50px rgba(244,67,54,0.7), 0 0 80px rgba(244,67,54,0.4), 0 0 0 0 rgba(244,67,54,0.8); 
    transform: translateY(-3px) scale(1);
  } 
  50% { 
    box-shadow: 0 0 70px rgba(244,67,54,1), 0 0 120px rgba(244,67,54,0.6), 0 0 0 15px rgba(244,67,54,0); 
    transform: translateY(-3px) scale(1.05);
  } 
}

.hunger-glow { 
  position: absolute; 
  top: -20px; 
  left: -20px; 
  right: -20px; 
  bottom: -20px; 
  border-radius: 50px; 
  transition: all 0.4s ease;
  /* 移除椭圆效果 - 简化渲染 */
}

/* 移除椭圆动画 - 精准改善渲染性能 */

/* 左侧状态图标区域 */
.hunger-icon-section { 
  width: var(--action-width); 
  height: 56px; 
  flex-shrink: 0; 
  display: flex;
  align-items: center;
  justify-content: center;
}
.status-icon-glow {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(255,255,255,0.3);
  transition: all 300ms ease;
  position: relative;
  overflow: hidden;
}
.status-icon-glow.good {
  background: linear-gradient(145deg, rgba(76,175,80,0.7), rgba(56,142,60,0.8));
  box-shadow: 0 4px 12px rgba(76,175,80,0.3);
}
.status-icon-glow.medium {
  background: linear-gradient(145deg, rgba(139,195,74,0.7), rgba(104,159,56,0.8));
  box-shadow: 0 4px 12px rgba(139,195,74,0.3);
}
.status-icon-glow.low {
  background: linear-gradient(145deg, rgba(255,152,0,0.7), rgba(245,124,0,0.8));
  box-shadow: 0 4px 12px rgba(255,152,0,0.3);
  animation: lowIconPulse 2s ease-in-out infinite;
}
.status-icon-glow.critical {
  background: linear-gradient(145deg, rgba(244,67,54,0.8), rgba(211,47,47,0.9));
  box-shadow: 0 4px 16px rgba(244,67,54,0.5);
  animation: criticalIconPulse 1.2s ease-in-out infinite;
}

@keyframes lowIconPulse {
  0%, 100% { transform: scale(1); box-shadow: 0 4px 12px rgba(255,152,0,0.3); }
  50% { transform: scale(1.05); box-shadow: 0 6px 18px rgba(255,152,0,0.5); }
}

@keyframes criticalIconPulse {
  0%, 100% { transform: scale(1); box-shadow: 0 4px 16px rgba(244,67,54,0.5); }
  50% { transform: scale(1.08); box-shadow: 0 8px 24px rgba(244,67,54,0.7); }
}

/* 信息区域 - 精准布局控制 */
.hunger-info-aaa { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  gap: 4px; 
  padding: 0 12px;
  min-width: 0; /* 允许flex收缩 */
  max-width: calc(100% - 112px); /* 减去左右spacer宽度 */
}

.hunger-status-label {
  font-size: 10px;
  font-weight: 900;
  color: rgba(255,255,255,0.9);
  text-transform: uppercase;
  letter-spacing: 1.2px;
  text-align: center;
  text-shadow: 0 1px 2px rgba(0,0,0,0.8);
  line-height: 1;
  margin: 0;
}

.hunger-status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1px;
  padding-top: 2px; /* 精准下移 */
}

.hunger-label {
  font-size: 9px; /* 精准调整大小 */
  font-weight: 900;
  color: rgba(255,255,255,0.85);
  text-transform: uppercase;
  letter-spacing: 1.8px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.8);
  min-width: 58px;
  line-height: 1.1; /* 精准控制行高 */
  transform: translateY(1px); /* 微调位置 */
}

.hunger-status {
  font-size: 9px; /* 匹配label大小 */
  font-weight: 900;
  color: rgba(255,255,255,0.95);
  text-transform: uppercase;
  letter-spacing: 1.2px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.8);
  min-width: 48px;
  line-height: 1.1; /* 精准控制行高 */
  transform: translateY(1px); /* 微调位置保持对齐 */
}
.hunger-info-aaa { position: relative; z-index: 1; }
.hunger-info-aaa::before { content: ''; position: absolute; inset: -2px 0px -2px 0px; background: linear-gradient(180deg, rgba(0,0,0,0.32), rgba(0,0,0,0.24)); border-radius: 12px; pointer-events: none; z-index: 0; }
.hunger-label-aaa { position: relative; z-index: 1; display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 900; color: #ffffff; text-transform: uppercase; letter-spacing: 1.5px; -webkit-text-stroke: 0.2px rgba(0,0,0,0.6); text-shadow: 0 1px 2px rgba(0,0,0,0.85), 0 2px 6px rgba(0,0,0,0.65); mix-blend-mode: normal; line-height: 1.05; margin: 0; }
.status-indicator { width: 8px; height: 8px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.3); }
.status-indicator.good { background: #4caf50; box-shadow: 0 0 8px rgba(76,175,80,0.6); }
.status-indicator.medium { background: #ff9800; box-shadow: 0 0 8px rgba(255,152,0,0.6); }
.status-indicator.low { background: #ff5722; box-shadow: 0 0 8px rgba(255,87,34,0.6); animation: statusBlink 1.5s infinite; }
.status-indicator.critical { background: #f44336; box-shadow: 0 0 12px rgba(244,67,54,0.8); animation: statusBlink 1s infinite; }
@keyframes statusBlink { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.hunger-bar-aaa { 
  display: flex; 
  align-items: center; 
  gap: 8px; 
  justify-content: space-between;
  max-width: 100%;
  overflow: hidden;
}
.hunger-track { 
  flex: 1; 
  max-width: calc(100% - 68px); /* 预留percentage空间 */
  height: 13px; 
  background: linear-gradient(145deg, rgba(0,0,0,0.6), rgba(0,0,0,0.4)); 
  border-radius: 8px; 
  overflow: hidden; 
  border: 1px solid rgba(255,255,255,0.12); 
  box-shadow: 
    inset 0 3px 6px rgba(0,0,0,0.5),
    inset 0 1px 0 rgba(255,255,255,0.05);
  position: relative; 
}
.hunger-fill-aaa { 
  height: 100%; 
  border-radius: 6px; 
  transition: width 600ms cubic-bezier(0.25, 0.46, 0.45, 0.94), background 400ms ease; 
  position: relative; 
  overflow: hidden; 
  box-shadow: 
    inset 0 2px 0 rgba(255,255,255,0.4),
    inset 0 -1px 0 rgba(0,0,0,0.3),
    0 2px 8px rgba(0,0,0,0.2);
}
.fill-shine { 
  position: absolute; 
  top: 0; 
  left: 0; 
  right: 0; 
  height: 60%; 
  background: linear-gradient(to bottom, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0.2) 50%, transparent 100%); 
  border-radius: 6px 6px 0 0; 
}
.fill-particles { 
  position: absolute; 
  top: 0; 
  left: 0; 
  right: 0; 
  bottom: 0; 
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 40%, rgba(255,255,255,0.5) 50%, rgba(255,255,255,0.3) 60%, transparent 100%); 
  animation: fillParticles 2.5s ease-in-out infinite; 
}
@keyframes fillParticles { 0% { transform: translateX(-120%);} 100% { transform: translateX(120%);} }

.hunger-percentage { 
  position: relative; 
  z-index: 2; 
  font-size: 15px; 
  font-weight: 900; 
  color: #ffffff; 
  text-shadow: 
    0 2px 4px rgba(0,0,0,0.9),
    0 1px 0 rgba(255,255,255,0.4),
    0 0 12px rgba(0,0,0,0.6); 
  min-width: 50px;
  max-width: 50px;
  text-align: center; 
  letter-spacing: 0.2px;
  background: linear-gradient(145deg, rgba(0,0,0,0.5), rgba(0,0,0,0.3));
  border-radius: 12px;
  padding: 4px 8px;
  border: 1px solid rgba(255,255,255,0.22);
  flex-shrink: 0;
}
.hunger-status-text { position: relative; z-index: 1; font-size: 11px; font-weight: 700; color: #ffffff; -webkit-text-stroke: 0.3px rgba(0,0,0,0.6); text-transform: uppercase; letter-spacing: 0.6px; text-shadow: 0 1px 2px rgba(0,0,0,0.9), 0 2px 6px rgba(0,0,0,0.65); mix-blend-mode: normal; line-height: 1.05; margin-top: 0; }

/* 操作区域 - AAA游戏级交互，紧凑布局 */
.hunger-action-aaa { 
  width: 56px; 
  height: 56px; 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  justify-content: center; 
  gap: 2px; 
  flex-shrink: 0; 
  padding: 2px;
}
.action-glow { 
  width: 32px; 
  height: 32px; 
  background: linear-gradient(145deg, rgba(96,125,139,0.7), rgba(69,90,100,0.8)); 
  border-radius: 50%; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  border: 2px solid rgba(255,255,255,0.4); 
  box-shadow: 
    0 3px 8px rgba(96,125,139,0.3), 
    inset 0 1px 0 rgba(255,255,255,0.25),
    inset 0 -1px 0 rgba(0,0,0,0.2); 
  transition: all 300ms cubic-bezier(0.25, 0.46, 0.45, 0.94); 
  position: relative;
  overflow: hidden;
}

.action-glow::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: conic-gradient(from 0deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: actionRotate 3s linear infinite;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.action-glow:hover::before {
  opacity: 1;
}

@keyframes actionRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.action-glow.pulse { 
  animation: actionGlowPulse 2s ease-in-out infinite; 
}

.action-glow.critical {
  background: linear-gradient(145deg, rgba(255,152,0,0.8), rgba(245,124,0,0.9));
  border-color: rgba(255,255,255,0.6);
  box-shadow: 
    0 6px 16px rgba(255,152,0,0.5),
    inset 0 2px 0 rgba(255,255,255,0.4);
  animation: criticalActionPulse 1.2s ease-in-out infinite;
}

@keyframes actionGlowPulse { 
  0%, 100% { 
    transform: scale(1); 
    box-shadow: 0 3px 8px rgba(96,125,139,0.3);
  } 
  50% { 
    transform: scale(1.05); 
    box-shadow: 0 5px 12px rgba(96,125,139,0.5);
  } 
}

@keyframes criticalActionPulse {
  0%, 100% { 
    transform: scale(1); 
    box-shadow: 0 6px 16px rgba(255,152,0,0.5);
  }
  50% { 
    transform: scale(1.08); 
    box-shadow: 0 8px 20px rgba(255,152,0,0.7);
  }
}

.feed-hint { 
  font-size: 8px; 
  font-weight: 900; 
  color: rgba(255,255,255,0.95); 
  text-transform: uppercase; 
  letter-spacing: 0.8px; 
  text-shadow: 0 1px 3px rgba(0,0,0,0.8); 
  background: linear-gradient(145deg, rgba(0,0,0,0.5), rgba(0,0,0,0.3));
  border-radius: 6px;
  padding: 1px 4px;
  border: 1px solid rgba(255,255,255,0.25);
  animation: hintPulse 2s ease-in-out infinite;
  white-space: nowrap;
  max-width: 48px;
  text-align: center;
  overflow: hidden;
}

@keyframes hintPulse {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}

.hunger-display-aaa.good .action-glow { 
  background: linear-gradient(145deg, #4caf50, #388e3c); 
  box-shadow: 0 4px 12px rgba(76,175,80,0.3), inset 0 1px 0 rgba(255,255,255,0.25); 
}
.hunger-display-aaa.medium .action-glow { 
  background: linear-gradient(145deg, #8bc34a, #689f38); 
  box-shadow: 0 4px 12px rgba(139,195,74,0.3), inset 0 1px 0 rgba(255,255,255,0.25); 
}
.hunger-display-aaa.low .action-glow { 
  background: linear-gradient(145deg, #ff9800, #f57c00); 
  box-shadow: 0 4px 14px rgba(255,152,0,0.4), inset 0 1px 0 rgba(255,255,255,0.25); 
}
.hunger-display-aaa.critical .action-glow { 
  background: linear-gradient(145deg, #ff5722, #d84315); 
  box-shadow: 0 6px 16px rgba(255,87,34,0.5), inset 0 1px 0 rgba(255,255,255,0.3); 
}
.hunger-display-aaa .action-glow:hover { 
  transform: translateY(-1px) scale(1.08); 
  box-shadow: 0 8px 20px rgba(0,0,0,0.2), inset 0 2px 0 rgba(255,255,255,0.4); 
}
.hunger-display-aaa.good .feed-hint { color: #b2ffb5; background: linear-gradient(145deg, rgba(76,175,80,0.2), rgba(76,175,80,0.1)); }
.hunger-display-aaa.medium .feed-hint { color: #c5e1a5; background: linear-gradient(145deg, rgba(139,195,74,0.2), rgba(139,195,74,0.1)); }
.hunger-display-aaa.low .feed-hint { color: #ffe0b2; background: linear-gradient(145deg, rgba(255,152,0,0.2), rgba(255,152,0,0.1)); }
.hunger-display-aaa.critical .feed-hint { color: #ffccbc; background: linear-gradient(145deg, rgba(255,87,34,0.3), rgba(255,87,34,0.1)); }

/* 粒子效果 */
.hunger-particles { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; overflow: visible; }
.hunger-particle { position: absolute; width: var(--size); height: var(--size); background: radial-gradient(circle, rgba(255,87,34,0.8), transparent); border-radius: 50%; top: 50%; left: 20%; transform-origin: 0 0; animation: hungerParticleFloat 3s linear infinite; animation-delay: var(--delay); }
@keyframes hungerParticleFloat { 0% { transform: translate(0, 0) rotate(var(--angle)) translateX(0); opacity: 0;} 10% { opacity: 1;} 90% { opacity: 1;} 100% { transform: translate(0, 0) rotate(var(--angle)) translateX(200px); opacity: 0;} }

/* 📱 移动端适配（仅作用于本组件） - 大幅提升可读性 */
@media (max-width: 768px) {
  .hunger-display-aaa { min-width: 280px; width: clamp(280px, 95vw, 480px); height: 52px; --action-width: 48px; }
  .hunger-info-aaa { padding: 0 8px; max-width: calc(100% - 96px); gap: 3px; }
  /* 大幅放大hunger文字让mobile用户看得清楚 */
  .hunger-label { 
    font-size: 14px !important; /* 从9px大幅提升到14px */
    letter-spacing: 2.5px; 
    min-width: 65px; 
    font-weight: 900;
    text-shadow: 0 2px 4px rgba(0,0,0,0.9), 0 1px 0 rgba(255,255,255,0.3);
  }
  .hunger-status { 
    font-size: 14px !important; /* 从9px大幅提升到14px */
    letter-spacing: 2px; 
    min-width: 55px; 
    font-weight: 900;
    text-shadow: 0 2px 4px rgba(0,0,0,0.9), 0 1px 0 rgba(255,255,255,0.3);
  }
  .hunger-track { max-width: calc(100% - 55px); height: 12px; }
  .hunger-percentage { font-size: 14px; min-width: 42px; max-width: 42px; padding: 3px 6px; }
  .hunger-action-aaa { width: 48px; height: 52px; gap: 1px; }
  .action-glow { width: 28px; height: 28px; }
  .status-icon-glow { width: 32px; height: 32px; }
  .feed-hint { font-size: 8px; padding: 1px 3px; max-width: 40px; }
}
@media (max-width: 480px) {
  .hunger-display-aaa { min-width: 240px; width: 100%; height: 48px; --action-width: 40px; }
  .hunger-icon-section { width: var(--action-width); height: 48px; }
  .hunger-info-aaa { padding: 0 6px; gap: 3px; max-width: calc(100% - 80px); }
  /* 小屏也要保持清晰可读 */
  .hunger-label { 
    font-size: 12px !important; /* 从8px提升到12px */
    letter-spacing: 2px; 
    min-width: 55px; 
    font-weight: 900;
    text-shadow: 0 2px 4px rgba(0,0,0,0.9), 0 1px 0 rgba(255,255,255,0.3);
  }
  .hunger-status { 
    font-size: 12px !important; /* 从8px提升到12px */
    letter-spacing: 1.5px; 
    min-width: 48px; 
    font-weight: 900;
    text-shadow: 0 2px 4px rgba(0,0,0,0.9), 0 1px 0 rgba(255,255,255,0.3);
  }
  .hunger-track { max-width: calc(100% - 50px); height: 10px; }
  .hunger-percentage { font-size: 12px; min-width: 36px; max-width: 36px; padding: 2px 4px; }
  .hunger-action-aaa { width: 40px; height: 48px; gap: 1px; }
  .action-glow { width: 24px; height: 24px; }
  .status-icon-glow { width: 28px; height: 28px; }
  .feed-hint { font-size: 7px; padding: 0px 2px; max-width: 32px; letter-spacing: 0.4px; }
}

/* 动画/可访问性：减少动画时禁用粒子与脉冲，仍保留可读性 */
@media (prefers-reduced-motion: reduce) {
  .fill-particles,
  .hunger-particles,
  .icon-pulse,
  .action-glow.pulse { animation: none !important; }
  .hunger-display-aaa { transition-duration: 0.2s !important; }
}

/* 字体渲染tuning（WebKit 常用） */
:where(.hunger-label-aaa, .hunger-percentage, .hunger-status-text) {
  -webkit-font-smoothing: antialiased;
  text-rendering: geometricPrecision;
}
</style>

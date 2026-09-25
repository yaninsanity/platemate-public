<template>
  <div class="ai-detection-loader">
    <div class="scanner-container">
      <div class="scanner-frame">
        <div class="scanner-line"></div>
        <div class="corner corner-tl"></div>
        <div class="corner corner-tr"></div>
        <div class="corner corner-bl"></div>
        <div class="corner corner-br"></div>
      </div>
      
      <div class="ai-brain">
        <div class="brain-pulse"></div>
        <div class="neural-network">
          <div class="node" v-for="i in 6" :key="i" :style="{ animationDelay: i * 0.2 + 's' }"></div>
        </div>
      </div>
      
      <div class="detection-text">
        <h3 class="scanning-title">🤖 AI ANALYZING...</h3>
        <p class="scanning-subtitle">{{ currentMessage }}</p>
        <div class="progress-dots">
          <span v-for="i in 3" :key="i" class="dot" :class="{ active: activeDot === i }"></span>
        </div>
      </div>
    </div>
    
    <div class="food-particles">
      <div 
        v-for="i in 8" 
        :key="i" 
        class="particle"
        :style="{ 
          left: Math.random() * 100 + '%',
          animationDelay: Math.random() * 2 + 's',
          animationDuration: (2 + Math.random() * 2) + 's'
        }"
      >
        {{ ['🍅', '🥬', '🧀', '🥕', '🌶️', '🥒', '🍄', '🧄'][i] }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const messages = [
  "Scanning ingredients with AI vision...",
  "Analyzing texture and color patterns...", 
  "Cross-referencing food database...",
  "Calculating ingredient confidence...",
  "Running final verification checks..."
]

const currentMessage = ref(messages[0])
const activeDot = ref(1)

let messageInterval: NodeJS.Timeout
let dotInterval: NodeJS.Timeout

onMounted(() => {
  // Cycle through messages
  messageInterval = setInterval(() => {
    const currentIndex = messages.indexOf(currentMessage.value)
    const nextIndex = (currentIndex + 1) % messages.length
    currentMessage.value = messages[nextIndex]
  }, 1500)
  
  // Animate dots
  dotInterval = setInterval(() => {
    activeDot.value = activeDot.value === 3 ? 1 : activeDot.value + 1
  }, 500)
})

onUnmounted(() => {
  if (messageInterval) clearInterval(messageInterval)
  if (dotInterval) clearInterval(dotInterval)
})
</script>

<style scoped>
.ai-detection-loader {
  position: relative;
  width: 100%;
  height: 300px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.scanner-container {
  position: relative;
  z-index: 2;
}

.scanner-frame {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 20px;
}

.scanner-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00ff88, transparent);
  animation: scanMove 2s ease-in-out infinite;
}

@keyframes scanMove {
  0%, 100% { transform: translateY(0); opacity: 0; }
  50% { transform: translateY(116px); opacity: 1; }
}

.corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid #00ff88;
}

.corner-tl { top: 0; left: 0; border-right: none; border-bottom: none; }
.corner-tr { top: 0; right: 0; border-left: none; border-bottom: none; }
.corner-bl { bottom: 0; left: 0; border-right: none; border-top: none; }
.corner-br { bottom: 0; right: 0; border-left: none; border-top: none; }

.ai-brain {
  position: relative;
  width: 60px;
  height: 60px;
  margin: 0 auto;
  margin-top: -90px;
}

.brain-pulse {
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, #ff6b6b, #4ecdc4);
  border-radius: 50%;
  animation: brainPulse 1.5s ease-in-out infinite;
}

@keyframes brainPulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.2); opacity: 1; }
}

.neural-network {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.node {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #fff;
  border-radius: 50%;
  animation: nodeFlicker 1s ease-in-out infinite;
}

.node:nth-child(1) { top: -30px; left: -2px; }
.node:nth-child(2) { top: -20px; left: 15px; }
.node:nth-child(3) { top: 5px; left: 20px; }
.node:nth-child(4) { top: 25px; left: 5px; }
.node:nth-child(5) { top: 15px; left: -15px; }
.node:nth-child(6) { top: -5px; left: -25px; }

@keyframes nodeFlicker {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.detection-text {
  text-align: center;
  color: white;
  margin-top: 40px;
}

.scanning-title {
  font-size: 1.4rem;
  font-weight: bold;
  margin-bottom: 8px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.scanning-subtitle {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-bottom: 16px;
  min-height: 20px;
  transition: all 0.3s ease;
}

.progress-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.4);
  transition: all 0.3s ease;
}

.dot.active {
  background: #00ff88;
  transform: scale(1.3);
  box-shadow: 0 0 10px #00ff88;
}

.food-particles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  font-size: 20px;
  animation: float infinite linear;
  opacity: 0.6;
}

@keyframes float {
  0% { 
    transform: translateY(100%) rotate(0deg);
    opacity: 0;
  }
  10% { opacity: 0.6; }
  90% { opacity: 0.6; }
  100% { 
    transform: translateY(-100%) rotate(360deg);
    opacity: 0;
  }
}
</style>

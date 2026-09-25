<!-- 🎵 Sound Control Panel - 用户音效设置 -->
<template>
  <div class="sound-control" :class="{ 'expanded': showPanel }">
    <!-- 音效按钮 -->
    <button 
      @click="toggleSound" 
      class="sound-toggle"
      :class="{ 'muted': !soundEnabled }"
      :title="soundEnabled ? 'Disable sound effects' : 'Enable sound effects'"
    >
      <v-icon>{{ soundEnabled ? 'mdi-volume-high' : 'mdi-volume-off' }}</v-icon>
    </button>
    
    <!-- 详细设置面板 -->
    <transition name="slide-fade">
      <div v-if="showPanel" class="sound-panel">
        <div class="volume-control">
          <label>Master Volume</label>
          <v-slider
            v-model="volume"
            :min="0"
            :max="100"
            :step="5"
            hide-details
            color="primary"
            track-color="rgba(255,255,255,0.2)"
            @update:model-value="updateVolume"
          >
            <template #append>
              <span class="volume-text">{{ volume }}%</span>
            </template>
          </v-slider>
        </div>
        
        <!-- 测试音效 -->
        <div class="test-sounds">
          <button @click="testNotification" class="test-btn">
            <v-icon>mdi-bell</v-icon>
            Test Notification
          </button>
          <button @click="testPetSound" class="test-btn">
            <v-icon>mdi-heart</v-icon>
            Test Pet Sound
          </button>
          <button @click="testBiteEffect" class="test-btn">
            <v-icon>mdi-food-apple</v-icon>
            Test AI Analysis
          </button>
        </div>
        
        <!-- BGM控制 -->
        <div class="bgm-control">
          <label>Background Music</label>
          <div class="bgm-buttons">
            <button @click="playBGM" class="bgm-btn" :disabled="isBGMPlaying">
              <v-icon>mdi-play</v-icon>
              Play BGM
            </button>
            <button @click="stopBGM" class="bgm-btn" :disabled="!isBGMPlaying">
              <v-icon>mdi-stop</v-icon>
              Stop BGM
            </button>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- 设置按钮 -->
    <button 
      @click="showPanel = !showPanel" 
      class="settings-btn"
      title="Sound settings"
    >
      <v-icon>mdi-cog</v-icon>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { soundManager, playNotificationSound, playPetStatusSound, GameSounds } from '@/utils/soundManager'

const showPanel = ref(false)
const soundEnabled = ref(true)
const volume = ref(70)
const isBGMPlaying = ref(false)

onMounted(() => {
  // 从 localStorage 加载设置
  const savedVolume = localStorage.getItem('platemate_sound_volume')
  const savedEnabled = localStorage.getItem('platemate_sound_enabled')
  
  if (savedVolume) volume.value = Math.round(parseFloat(savedVolume) * 100)
  if (savedEnabled !== null) soundEnabled.value = savedEnabled === 'true'
})

function toggleSound() {
  soundEnabled.value = soundManager.toggleSound()
}

function updateVolume(newVolume: number) {
  soundManager.setMasterVolume(newVolume / 100)
}

function testNotification() {
  playNotificationSound({ volume: 0.7 })
}

function testPetSound() {
  playPetStatusSound('excited', { volume: 0.7 })
}

function testBiteEffect() {
  // 🎵 测试AI分析音效 - 模拟bite循环播放
  soundManager.playSound(GameSounds.BITE, { volume: 0.4, loop: true })
  
  // 3秒后自动停止
  setTimeout(() => {
    soundManager.stopSound(GameSounds.BITE)
  }, 3000)
}

function playBGM() {
  soundManager.playSound(GameSounds.BGM, { volume: 0.3, loop: true })
  isBGMPlaying.value = true
}

function stopBGM() {
  soundManager.stopSound(GameSounds.BGM)
  isBGMPlaying.value = false
}
</script>

<style scoped>
.sound-control {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.sound-toggle, .settings-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.sound-toggle:hover, .settings-btn:hover {
  background: rgba(255, 255, 255, 1);
  transform: scale(1.05);
}

.sound-toggle.muted {
  background: rgba(255, 100, 100, 0.9);
}

.sound-panel {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(15px);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  min-width: 250px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.volume-control {
  margin-bottom: 16px;
}

.volume-control label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #555;
  margin-bottom: 8px;
}

.volume-text {
  font-size: 12px;
  color: #666;
  min-width: 32px;
  text-align: center;
}

.test-sounds {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.test-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.2s ease;
}

.test-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.bgm-control {
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 12px;
}

.bgm-control label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #555;
  margin-bottom: 8px;
}

.bgm-buttons {
  display: flex;
  gap: 6px;
}

.bgm-btn {
  flex: 1;
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  transition: all 0.2s ease;
}

.bgm-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.2);
}

.bgm-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
}

.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 1, 0.3, 1);
}

.slide-fade-enter-from, .slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .sound-control {
    top: 10px;
    right: 10px;
  }
  
  .sound-toggle, .settings-btn {
    width: 40px;
    height: 40px;
  }
  
  .sound-panel {
    min-width: 200px;
    padding: 12px;
  }
  
  .test-btn {
    font-size: 10px;
    padding: 6px 8px;
  }
}
</style>

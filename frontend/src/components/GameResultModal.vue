<template>
  <div class="game-result-overlay" v-if="isVisible" @click="handleOverlayClick">
    <div class="result-modal" @click.stop>
      <!-- 3D可爱PNG角色渲染 -->
      <div class="character-showcase">
        <img 
          v-if="result === 'win'" 
          src="/assets/win.png"
          alt="Victory Character"
          class="result-character win-character"
        />
        <img 
          v-else-if="result === 'lose'" 
          src="/assets/lose.png"
          alt="Defeat Character" 
          class="result-character lose-character"
        />
        <img 
          v-else-if="result === 'draw'" 
          src="/assets/tie.png"
          alt="Tie Character"
          class="result-character tie-character" 
        />
      </div>

      <!-- 结果标题与鼓励话语 -->
      <div class="result-title" :class="`result-${result}`">
        <div class="title-main">
          <span v-if="result === 'win'">🏆 VICTORY!</span>
          <span v-else-if="result === 'lose'">💪 TRY AGAIN!</span>
          <span v-else>🤝 TIE GAME!</span>
        </div>
        <div class="encouragement-text">
          {{ currentEncouragement }}
        </div>
      </div>

      <!-- 战斗回顾 -->
      <div class="battle-recap">
        <div class="player-move">
          <span class="move-label">You</span>
          <div class="move-choice">{{ playerChoice }}</div>
        </div>
        <div class="vs-separator">VS</div>
        <div class="kinny-move">
          <span class="move-label">Kinny</span>
          <div class="move-choice">{{ kinnyChoice }}</div>
        </div>
      </div>

      <!-- 奖励信息 -->
      <div class="rewards-section">
        <div class="hunger-cost">
          <span class="cost-icon">⚡</span>
          <span>Energy Cost: -{{ hungerCost }}</span>
        </div>
        
        <!-- 🎁 Unified Kinny Food reward display -->
        <div v-if="result === 'win' && foodReward" class="food-reward-container">
          <div class="reward-header">
            <span class="reward-icon">🎁</span>
            <span class="reward-title">Victory Reward!</span>
          </div>
          <div class="food-reward-details">
            <div class="food-icon">🍽️</div>
            <div class="food-info">
              <div class="food-name">Kinny Food</div>
              <div class="food-amount">+{{ foodReward.amount }} Added to Inventory!</div>
            </div>
          </div>
        </div>

        <!-- 平局时的鼓励 -->
        <div v-if="result === 'draw'" class="draw-message">
          <span class="draw-icon">🤝</span>
          <span>No rewards, but great effort!</span>
        </div>
      </div>

      <!-- 游戏化按钮组 -->
      <div class="action-bar">
        <button 
          class="game-btn play-again-btn"
          @click="$emit('playAgain')"
          :disabled="!canPlayAgain"
          v-if="canPlayAgain"
        >
          <span class="btn-icon">🎮</span>
          <span>PLAY AGAIN</span>
        </button>
        
        <button 
          class="game-btn need-food-btn"
          @click="$emit('needFood')"
          v-if="!canPlayAgain"
        >
          <span class="btn-icon">🍽️</span>
          <span>NEED FOOD</span>
        </button>
        
        <button 
          class="game-btn home-btn"
          @click="$emit('close')"
        >
          <span class="btn-icon">🏠</span>
          <span>HOME</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

interface FoodReward {
  type: string
  display: string
  amount: number
}

interface Props {
  isVisible: boolean
  result: 'win' | 'lose' | 'draw'
  playerChoice: string
  kinnyChoice: string
  hungerCost: number
  foodReward?: FoodReward | null
  canPlayAgain: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  playAgain: []
  needFood: []
}>()

// 随机鼓励话语库
const encouragementMessages = {
  win: [
    "Amazing strategy! You're a true champion!",
    "Fantastic win! Kinny is impressed!",
    "Outstanding! Your skills are growing stronger!",
    "Incredible victory! You've mastered the game!",
    "Brilliant play! Keep up the excellent work!",
    "Superb! You've earned this victory!",
    "Magnificent! Your timing was perfect!",
    "Exceptional! You're becoming unstoppable!",
    "Wonderful! That was a masterful move!",
    "Spectacular! Your instincts are spot-on!",
    "Marvelous! You've got the winning touch!",
    "Impressive! Your technique is improving!",
    "Excellent! You read Kinny's move perfectly!",
    "Outstanding performance! You're on fire!",
    "Phenomenal! Your skills are unmatched!"
  ],
  lose: [
    "Don't give up! Every loss is a lesson learned!",
    "Keep trying! Victory is just around the corner!",
    "Stay strong! You're getting better each round!",
    "Never quit! Champions are made through practice!",
    "Keep going! Your determination will pay off!",
    "Stay positive! Great players learn from defeat!",
    "Keep pushing! Success comes to those who persist!",
    "Don't stop! Your breakthrough is coming soon!",
    "Stay focused! Every attempt makes you stronger!",
    "Keep believing! Your skills are developing fast!",
    "Stay motivated! Winners never give up!",
    "Keep fighting! Your next win is closer than you think!",
    "Stay determined! Challenges make champions!",
    "Keep practicing! You're improving with each game!",
    "Stay hopeful! Your victory moment will come!"
  ],
  draw: [
    "Perfect balance! You matched Kinny's strategy!",
    "Great minds think alike! Excellent timing!",
    "Well played! You're evenly matched with Kinny!",
    "Impressive! You predicted Kinny's move!",
    "Smart play! That was a strategic tie!",
    "Clever! You're reading the game perfectly!",
    "Excellent! Your instincts are sharp!",
    "Well done! You're thinking like a champion!",
    "Great job! That was tactical brilliance!",
    "Nice work! You're mastering the patterns!",
    "Solid play! Your timing is getting better!",
    "Good thinking! You're learning Kinny's style!",
    "Smart move! You're becoming predictive!",
    "Well played! Your strategy is evolving!",
    "Great effort! You're matching expert level!"
  ]
}

// Unified food emoji (all food types now display as Kinny Food)
function getFoodEmoji(foodType: string): string {
  return '🍽️' // Always return unified Kinny Food emoji
}

// Unified food name (no longer needed but kept for compatibility)
function getFoodName(foodType: string): string {
  return 'Kinny Food' // Always return unified name
}

// 获取随机鼓励话语
function getRandomEncouragement(result: 'win' | 'lose' | 'draw'): string {
  const messages = encouragementMessages[result]
  return messages[Math.floor(Math.random() * messages.length)]
}

function handleOverlayClick() {
  emit('close')
}

const currentEncouragement = computed(() => {
  if (props.isVisible && props.result) {
    return getRandomEncouragement(props.result)
  }
  return ''
})
</script>

<style scoped>
.game-result-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: overlayFadeIn 0.3s ease-out;
}

@keyframes overlayFadeIn {
  from { 
    opacity: 0;
    backdrop-filter: blur(0px);
  }
  to { 
    opacity: 1;
    backdrop-filter: blur(8px);
  }
}

.result-modal {
  background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 24px;
  padding: 32px;
  max-width: 400px;
  width: 90%;
  text-align: center;
  box-shadow: 
    0 25px 60px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  animation: modalSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}

.result-modal::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, 
    rgba(255, 255, 255, 0.03) 0%, 
    transparent 50%, 
    rgba(255, 255, 255, 0.03) 100%);
  pointer-events: none;
}

@keyframes modalSlideIn {
  from { 
    opacity: 0;
    transform: translateY(-50px) scale(0.9);
  }
  to { 
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 角色展示区域 - 增大PNG尺寸提供AAA体验 */
.character-showcase {
  width: 220px;
  height: 220px;
  margin: 0 auto 28px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.05), transparent);
  border-radius: 50%;
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.3);
}

.result-character {
  width: 200px;
  height: 200px;
  object-fit: contain;
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
  background-color: transparent;
  transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
  filter: drop-shadow(0 8px 25px rgba(0, 0, 0, 0.4));
}

.win-character {
  animation: victoryBounce 2s ease-in-out infinite;
  filter: 
    drop-shadow(0 12px 30px rgba(76, 175, 80, 0.5))
    brightness(1.15)
    saturate(1.3);
}

.lose-character {
  animation: defeatShake 1.5s ease-in-out infinite;
  filter: 
    drop-shadow(0 8px 20px rgba(244, 67, 54, 0.4))
    brightness(0.9)
    sepia(0.2);
}

.tie-character {
  animation: drawPulse 2s ease-in-out infinite;
  filter: 
    drop-shadow(0 8px 20px rgba(255, 193, 7, 0.4))
    brightness(1.05)
    hue-rotate(10deg);
}

@keyframes victoryBounce {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-8px) scale(1.05); }
}

@keyframes defeatShake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-3px); }
  75% { transform: translateX(3px); }
}

@keyframes drawPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}

/* 结果标题 */
.result-title {
  margin-bottom: 20px;
  text-align: center;
}

.title-main {
  font-size: 28px;
  font-weight: 900;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
  background: linear-gradient(45deg, #fff, #e0e0e0);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.encouragement-text {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  font-style: italic;
  line-height: 1.4;
  max-width: 280px;
  margin: 0 auto;
}

.result-title.result-win .title-main {
  background: linear-gradient(45deg, #4caf50, #81c784);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: winGlow 2s ease-in-out infinite;
}

.result-title.result-lose .title-main {
  background: linear-gradient(45deg, #f44336, #e57373);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.result-title.result-draw .title-main {
  background: linear-gradient(45deg, #ff9800, #ffb74d);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

@keyframes winGlow {
  0%, 100% { filter: brightness(1); }
  50% { filter: brightness(1.2); }
}

/* 战斗回顾 */
.battle-recap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.player-move, .kinny-move {
  text-align: center;
  flex: 1;
}

.move-label {
  display: block;
  font-size: 12px;
  color: #a0a0a0;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.move-choice {
  font-size: 32px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.vs-separator {
  font-size: 14px;
  font-weight: bold;
  color: #666;
  margin: 0 16px;
  opacity: 0.7;
}

/* 奖励信息 */
.rewards-section {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hunger-cost {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #ff7043;
  font-weight: 600;
  background: rgba(255, 112, 67, 0.1);
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255, 112, 67, 0.2);
}

/* 🎁 精准食物奖励展示 - AAA级视觉效果 */
.food-reward-container {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(76, 175, 80, 0.08));
  border: 2px solid rgba(76, 175, 80, 0.4);
  border-radius: 20px;
  padding: 20px;
  animation: rewardGlow 2s ease-in-out infinite;
  position: relative;
  overflow: hidden;
}

.food-reward-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  animation: shimmer 3s infinite;
}

.reward-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
  color: #4caf50;
  font-weight: 800;
  font-size: 18px;
  text-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}

.reward-icon {
  font-size: 22px;
  animation: rewardBounce 1.5s ease-in-out infinite;
}

.food-reward-details {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 16px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.1);
}

.food-icon {
  font-size: 42px;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3));
  animation: foodBounce 2s ease-in-out infinite;
  transform-origin: center;
}

.food-info {
  text-align: left;
  color: white;
}

.food-name {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 6px;
  color: #ffffff;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.food-amount {
  font-size: 16px;
  color: #4caf50;
  font-weight: 800;
  background: rgba(76, 175, 80, 0.2);
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.draw-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #ff9800;
  font-weight: 600;
  background: rgba(255, 152, 0, 0.1);
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255, 152, 0, 0.2);
}

@keyframes foodBounce {
  0%, 100% { transform: translateY(0) scale(1) rotate(0deg); }
  25% { transform: translateY(-6px) scale(1.08) rotate(-2deg); }
  50% { transform: translateY(-3px) scale(1.12) rotate(0deg); }
  75% { transform: translateY(-8px) scale(1.05) rotate(2deg); }
}

@keyframes rewardBounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

@keyframes rewardGlow {
  0%, 100% { 
    box-shadow: 0 0 0 rgba(76, 175, 80, 0.2);
    border-color: rgba(76, 175, 80, 0.4);
  }
  50% { 
    box-shadow: 0 0 30px rgba(76, 175, 80, 0.5);
    border-color: rgba(76, 175, 80, 0.6);
  }
}

.food-reward {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #4caf50;
  font-weight: 600;
  background: rgba(76, 175, 80, 0.1);
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid rgba(76, 175, 80, 0.2);
  animation: rewardGlow 2s ease-in-out infinite;
}

.cost-icon, .reward-icon {
  font-size: 18px;
}

/* AAA级按钮设计 */
.action-bar {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.game-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: relative;
  overflow: hidden;
}

.game-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}

.game-btn:hover::before {
  left: 100%;
}

.play-again-btn {
  background: linear-gradient(135deg, #4caf50, #45a049);
  color: white;
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
}

.play-again-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
}

.need-food-btn {
  background: linear-gradient(135deg, #ff9800, #f57c00);
  color: white;
  box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
}

.need-food-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 152, 0, 0.4);
}

.home-btn {
  background: linear-gradient(135deg, #607d8b, #546e7a);
  color: white;
  box-shadow: 0 4px 15px rgba(96, 125, 139, 0.3);
}

.home-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(96, 125, 139, 0.4);
}

.game-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.btn-icon {
  font-size: 16px;
}

/* mobile tuning */
@media (max-width: 480px) {
  .result-modal {
    padding: 24px;
    margin: 16px;
  }
  
  .character-showcase {
    width: 120px;
    height: 120px;
  }
  
  .result-title {
    font-size: 24px;
  }
  
  .battle-recap {
    padding: 12px;
  }
  
  .move-choice {
    font-size: 24px;
    padding: 6px;
  }
  
  .action-bar {
    flex-direction: column;
  }
  
  .game-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>

<template>
  <ScreenshotShare>
    <main class="about-screen" aria-labelledby="main-title">
      <!-- Language Toggle -->
      <div class="language-toggle">
        <button 
          @click="currentLang = 'en'"
          :class="{ active: currentLang === 'en' }"
          class="lang-btn"
        >
          EN
        </button>
        <button 
          @click="currentLang = 'zh'"
          :class="{ active: currentLang === 'zh' }"
          class="lang-btn"
        >
          中文
        </button>
      </div>

      <!-- Animated Background -->
      <div class="cosmic-bg">
        <div class="star-field">
          <div class="star" v-for="i in 50" :key="i" 
               :style="{ 
                 left: Math.random() * 100 + '%',
                 top: Math.random() * 100 + '%',
                 animationDelay: Math.random() * 3 + 's',
                 animationDuration: (Math.random() * 3 + 2) + 's'
               }"></div>
        </div>
        <div class="nebula nebula-1"></div>
        <div class="nebula nebula-2"></div>
        <div class="nebula nebula-3"></div>
      </div>

      <article class="panel">
        <!-- Enhanced Logo Section -->
        <div class="logo-container">
          <div class="logo-aura">
            <div class="aura-ring ring-1"></div>
            <div class="aura-ring ring-2"></div>
            <div class="aura-ring ring-3"></div>
          </div>
          <div class="logo-wrapper">
            <v-img
              src="assets/logo2.png"
              alt="PlateMate Logo"
              contain
              class="logo-img"
            />
            <div class="logo-glow"></div>
          </div>
        </div>

        <!-- Epic Hero Section -->
        <header class="hero">
          <h1 id="main-title" class="title">
            <span class="title-main">PlateMate</span>
            <span class="title-sub">{{ content[currentLang].subtitle }}</span>
          </h1>
          <div class="hero-tagline">
            <span class="tagline-text">{{ content[currentLang].tagline }}</span>
          </div>
        </header>

        <!-- Epic Story Section -->
        <section class="section story-section">
          <div class="story-header">
            <h2 class="section-title">{{ content[currentLang].storyTitle }}</h2>
            <div class="title-ornament">
              <div class="ornament-line"></div>
              <div class="ornament-gem">💎</div>
              <div class="ornament-line"></div>
            </div>
          </div>
          
          <div class="story-content">
            <div class="story-paragraph" v-for="(paragraph, index) in content[currentLang].story" :key="index">
              <p class="story-text">{{ paragraph }}</p>
            </div>
          </div>
        </section>

        <!-- Game Features Section -->
        <section class="section features-section">
          <h3 class="section-title">{{ content[currentLang].featuresTitle }}</h3>
          <div class="features-grid">
            <div class="feature-card" v-for="(feature, index) in content[currentLang].features" :key="index">
              <div class="feature-icon">{{ feature.icon }}</div>
              <div class="feature-content">
                <h4 class="feature-title">{{ feature.title }}</h4>
                <p class="feature-desc">{{ feature.desc }}</p>
              </div>
              <div class="feature-glow"></div>
            </div>
          </div>
        </section>

        <!-- Quest Rules Section -->
        <section class="section quest-section">
          <h3 class="section-title">{{ content[currentLang].questTitle }}</h3>
          <div class="quest-steps">
            <div class="quest-step" v-for="(step, index) in content[currentLang].questSteps" :key="index">
              <div class="step-number">{{ index + 1 }}</div>
              <div class="step-content">
                <div class="step-icon">{{ step.icon }}</div>
                <div class="step-text">
                  <h4 class="step-title">{{ step.title }}</h4>
                  <p class="step-desc">{{ step.desc }}</p>
                </div>
              </div>
              <div class="step-connector" v-if="index < content[currentLang].questSteps.length - 1"></div>
            </div>
          </div>
          <div class="quest-warning">
            <div class="warning-icon">⚠️</div>
            <p class="warning-text">{{ content[currentLang].questWarning }}</p>
          </div>
        </section>

        <!-- Team Section -->
        <section class="section team-section">
          <h3 class="section-title">{{ content[currentLang].teamTitle }}</h3>
          <div class="team-card">
            <div class="team-avatar">
              <div class="avatar-bg"></div>
              <div class="avatar-icon">👨‍🍳👩‍🍳</div>
            </div>
            <div class="team-content">
              <p class="team-text">{{ content[currentLang].teamDesc }}</p>
            </div>
          </div>
        </section>

        <!-- Enhanced CTA Section -->
        <nav class="actions" aria-label="Page actions">
          <button class="action-btn primary-btn" @click="$router.push('/memories')">
            <div class="btn-bg"></div>
            <div class="btn-glow"></div>
            <div class="btn-content">
              <span class="btn-icon">🌟</span>
              <span class="btn-text">{{ content[currentLang].viewMemories }}</span>
            </div>
          </button>
          <button class="action-btn secondary-btn" @click="$router.push('/')">
            <div class="btn-bg"></div>
            <div class="btn-glow"></div>
            <div class="btn-content">
              <span class="btn-icon">🏠</span>
              <span class="btn-text">{{ content[currentLang].backHome }}</span>
            </div>
          </button>
        </nav>
      </article>
    </main>
  </ScreenshotShare>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ScreenshotShare from '@/components/ScreenshotShare.vue'

const router = useRouter()
const currentLang = ref<'en' | 'zh'>((localStorage.getItem('preferredLang') as 'en' | 'zh') || 'en')

const content = {
  en: {
    subtitle: 'Guardian of PlateStar',
    tagline: 'Taste is the oldest memory folded within time',
    storyTitle: 'The Legend of PlateStar',
    story: [
      'Taste is the oldest memory folded within time. It carries not just nourishment, but connection—life\'s very code.',
      'PlateStar—a planet forged from pure flavor and emotion, shaped through eons of civilization, gave birth to unique lifeforms—PlateMate. Guardians of taste, messengers of feeling.',
      'But balance is fragile. When the invisible "Flavorless Storm" consumed the planet\'s core, PlateStar plunged into a dark vortex of lost taste and fading emotion, civilizations crumbled, life withered.',
      'Amidst the crisis, a faint light pierced the darkness—PlateMate descended from stardust to Earth. It chose you—or perhaps, you were destined to become its guardian.',
      'This is not just a pet-raising game. It is a quest for time, memory, and connection. Every chop, every sizzle, calls forth the lost flavors and awakens warmth buried deep inside you.',
      'PlateMate is more than a virtual companion—it embodies your unspoken harmony with your partner, carrying the story of your shared history. Its heartbeat syncs with your rhythm, life\'s pulse dances in the kitchen, composing a delicious poem only you two can tell.',
      'Are you ready? Embark on a culinary journey beyond reality, to become the one who changes not only taste but each other\'s lives. Become a guardian of PlateStar, lighting up the cosmos of flavor.'
    ],
    featuresTitle: 'Cosmic Cooking Features',
    features: [
      {
        icon: '🌟',
        title: 'Stellar Recipes',
        desc: 'Unlock recipes from across the galaxy, each carrying ancient flavor memories'
      },
      {
        icon: '💫',
        title: 'Harmony Sync',
        desc: 'Cook together in perfect synchronization, building your cosmic connection'
      },
      {
        icon: '🎵',
        title: 'PlateMate\'s Song',
        desc: 'Hear delightful melodies as your companion celebrates every culinary victory'
      },
      {
        icon: '🔮',
        title: 'Memory Crystals',
        desc: 'Capture and preserve your precious cooking moments in crystalline form'
      },
      {
        icon: '🌌',
        title: 'Flavor Universe',
        desc: 'Explore infinite taste combinations and discover new dimensions of flavor'
      },
      {
        icon: '✨',
        title: 'Stardust Evolution',
        desc: 'Watch your PlateMate evolve and grow stronger with each shared meal'
      }
    ],
    questTitle: 'Roundly Cosmic Quest',
    questSteps: [
      {
        icon: '📜',
        title: 'Receive Transmission',
        desc: 'PlateMate channels a recipe from the cosmic cookbook'
      },
      {
        icon: '🔥',
        title: 'Cook in Harmony',
        desc: 'Synchronize your cooking with live timers and celestial guidance'
      },
      {
        icon: '💎',
        title: 'Earn Stardust',
        desc: 'Collect cosmic rewards and strengthen your bond with PlateMate'
      },
      {
        icon: '🎁',
        title: 'Unlock Mysteries',
        desc: 'Discover new recipes, skins, and abilities for your companion'
      }
    ],
    questWarning: 'Skip a round and PlateMate\'s glow dims. Miss two, and it drifts into cosmic slumber...',
    teamTitle: 'Created by Cosmic Chefs',
    teamDesc: 'Two passionate developers transformed their long-distance cooking dates into PlateMate\'s magic. Join us in this journey of taste, connection, and cosmic wonder.',
    viewMemories: 'View Memory Crystals',
    backHome: 'Return to PlateStar'
  },
  zh: {
    subtitle: 'PlateStar 守护者',
    tagline: '味觉是时间褶皱中最古老的记忆',
    storyTitle: 'PlateStar 传说',
    story: [
      'In the folds of time, taste is the oldest memory. It carries not only nourishment but connection: the code of life itself.',
      'PlateStar——A planet built from pure taste and feeling, where aeons of civilisation settled and evolved into a life form all of its own——PlateMate。它们是味道的守护者，也是情感的传递者。',
      '然而，平衡是脆弱的。当无形的"失味风暴"devoured the core of the planet. PlateStar fell into a dark spiral of taste and feeling; its civilisation began to collapse and life began to wither.',
      'Through that crisis a thread of light crossed space and time, and PlateMate fell from stardust to Earth. They chose you——或者说，你注定成为它们的守护者。',
      'This is not merely a raising game. It is a search for time, memory and connection. Every chop and every stir calls back a lost taste, and calls on what is inside心深处温暖的唤醒。',
      'PlateMateis more than a virtual pet: it embodies the unspoken understanding between you and your partner, and carries your shared history. Its heartbeat keeps time with yours, and its pulse lives in the kitchen跳跃，谱写一段专属于你们的美味诗篇。',
      'Ready? Begin a cooking journey beyond the ordinary and become someone who changes not just taste but the lives you share. Become a PlateStar 守护者，点亮味觉宇宙的星辰。'
    ],
    featuresTitle: '宇宙烹饪特色',
    features: [
      {
        icon: '🌟',
        title: '星际食谱',
        desc: '解锁来自银河系各处的食谱，每一道都承载着古老的味觉记忆'
      },
      {
        icon: '💫',
        title: '和谐同步',
        desc: '完美同步烹饪，建立你们的宇宙连接'
      },
      {
        icon: '🎵',
        title: 'PlateMate之歌',
        desc: '聆听伙伴为每一次烹饪胜利献上的美妙旋律'
      },
      {
        icon: '🔮',
        title: '记忆水晶',
        desc: '将珍贵的烹饪时光凝结成水晶形态永久保存'
      },
      {
        icon: '🌌',
        title: '味觉宇宙',
        desc: '探索无限的味道组合，发现全新的味觉维度'
      },
      {
        icon: '✨',
        title: '星尘进化',
        desc: '看着你的PlateMate在每一次共享美食中成长强大'
      }
    ],
    questTitle: '每周宇宙任务',
    questSteps: [
      {
        icon: '📜',
        title: '接收传输',
        desc: 'PlateMate从宇宙食谱中传送一道料理'
      },
      {
        icon: '🔥',
        title: '和谐烹饪',
        desc: '通过实时计时器和天体指导同步你们的烹饪'
      },
      {
        icon: '💎',
        title: '赚取星尘',
        desc: '收集宇宙奖励，加强与PlateMate的羁绊'
      },
      {
        icon: '🎁',
        title: '解锁奥秘',
        desc: '发现新食谱、皮肤和伙伴的全新能力'
      }
    ],
    questWarning: 'Skip a week and PlateMate dims. Miss two and it falls into a cosmic sleep...',
    teamTitle: '宇宙厨师创作',
    teamDesc: 'Two devoted developers turned their long-distance cooking dates into PlateMate. Join us on a journey of taste, connection and small cosmic wonders.',
    viewMemories: '查看记忆水晶',
    backHome: '返回PlateStar'
  }
}
</script>

<style scoped lang="scss">
// Import fonts
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

// Enhanced cosmic theme variables
$cosmic-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
$cosmic-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
$cosmic-accent: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
$cosmic-gold: linear-gradient(135deg, #ffd700 0%, #ffb347 100%);
$cosmic-purple: linear-gradient(135deg, #a855f7 0%, #3b82f6 100%);

$cosmic-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
$cosmic-glow: 0 0 30px rgba(102, 126, 234, 0.5);

// Cosmic fonts
$cosmic-font: 'Orbitron', 'Nunito', sans-serif;
$body-font: 'Nunito', sans-serif;

.about-screen {
  min-height: 100vh;
  background: $cosmic-primary;
  position: relative;
  overflow: hidden;
  padding: 80px 0 120px; // Added bottom padding for screenshot button
  font-family: $body-font;
}

// Language Toggle
.language-toggle {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  gap: 8px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 25px;
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.lang-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  
  &.active {
    background: rgba(255, 255, 255, 0.2);
    color: #ffffff;
  }
  
  &:hover {
    background: rgba(255, 255, 255, 0.15);
    color: #ffffff;
  }
}

// Cosmic Background
.cosmic-bg {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  pointer-events: none;
}

.star-field {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.star {
  position: absolute;
  width: 2px;
  height: 2px;
  background: #ffffff;
  border-radius: 50%;
  animation: starTwinkle 2s ease-in-out infinite;
  
  &:nth-child(3n) {
    width: 3px;
    height: 3px;
    background: #ffd700;
  }
  
  &:nth-child(5n) {
    width: 1px;
    height: 1px;
    background: #4facfe;
  }
}

@keyframes starTwinkle {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

.nebula {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  animation: nebulaFloat 20s ease-in-out infinite;
}

.nebula-1 {
  width: 300px;
  height: 200px;
  top: 10%;
  left: 10%;
  background: radial-gradient(circle, rgba(167, 85, 247, 0.3) 0%, transparent 70%);
}

.nebula-2 {
  width: 250px;
  height: 180px;
  top: 60%;
  right: 15%;
  background: radial-gradient(circle, rgba(79, 172, 254, 0.25) 0%, transparent 70%);
  animation-delay: -10s;
}

.nebula-3 {
  width: 200px;
  height: 150px;
  bottom: 20%;
  left: 60%;
  background: radial-gradient(circle, rgba(245, 87, 108, 0.2) 0%, transparent 70%);
  animation-delay: -5s;
}

@keyframes nebulaFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, -30px) scale(1.1); }
  66% { transform: translate(-15px, 20px) scale(0.9); }
}

// Main Panel
.panel {
  position: relative;
  z-index: 10;
  max-width: 900px;
  margin: 0 auto;
  padding: 60px 40px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.05));
  backdrop-filter: blur(30px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 40px;
  box-shadow: $cosmic-shadow;
  
  @media (max-width: 768px) {
    margin: 0 20px;
    padding: 40px 30px;
  }
}

// Enhanced Logo
.logo-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 40px;
}

.logo-aura {
  position: absolute;
  width: 200px;
  height: 200px;
}

.aura-ring {
  position: absolute;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  animation: ringRotate 15s linear infinite;
}

.ring-1 {
  width: 100%;
  height: 100%;
  animation-direction: normal;
}

.ring-2 {
  width: 120%;
  height: 120%;
  top: -10%;
  left: -10%;
  animation-direction: reverse;
  animation-duration: 20s;
}

.ring-3 {
  width: 140%;
  height: 140%;
  top: -20%;
  left: -20%;
  animation-direction: normal;
  animation-duration: 25s;
}

@keyframes ringRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.logo-wrapper {
  position: relative;
  z-index: 5;
}

.logo-img {
  width: 120px;
  height: 120px;
  filter: drop-shadow(0 10px 30px rgba(0, 0, 0, 0.5));
}

.logo-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  animation: logoGlow 3s ease-in-out infinite;
}

@keyframes logoGlow {
  0%, 100% { opacity: 0.5; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.1); }
}

// Hero Section
.hero {
  text-align: center;
  margin-bottom: 60px;
}

.title {
  margin: 0;
  font-family: $cosmic-font;
}

.title-main {
  display: block;
  font-size: clamp(3rem, 8vw, 5rem);
  font-weight: 900;
  background: linear-gradient(135deg, #ffffff 0%, #4facfe 50%, #ffd700 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 50px rgba(255, 255, 255, 0.5);
  margin-bottom: 15px;
}

.title-sub {
  display: block;
  font-size: clamp(1.2rem, 3vw, 1.8rem);
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.hero-tagline {
  margin-top: 30px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.tagline-text {
  font-size: clamp(1rem, 2.5vw, 1.4rem);
  color: rgba(255, 255, 255, 0.8);
  font-style: italic;
  font-weight: 600;
}

// Sections
.section {
  margin-bottom: 60px;
}

.section-title {
  font-size: clamp(1.8rem, 4vw, 2.5rem);
  font-weight: 800;
  font-family: $cosmic-font;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-align: center;
  margin-bottom: 30px;
}

// Story Section
.story-section {
  .story-header {
    text-align: center;
    margin-bottom: 40px;
  }
  
  .title-ornament {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    margin-top: 20px;
  }
  
  .ornament-line {
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #4facfe, transparent);
  }
  
  .ornament-gem {
    font-size: 24px;
    animation: gemGlow 2s ease-in-out infinite;
  }
  
  @keyframes gemGlow {
    0%, 100% { opacity: 0.7; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.2); }
  }
}

.story-paragraph {
  margin-bottom: 25px;
  
  &:nth-child(odd) {
    animation: slideInLeft 0.8s ease-out;
  }
  
  &:nth-child(even) {
    animation: slideInRight 0.8s ease-out;
  }
}

@keyframes slideInLeft {
  0% { opacity: 0; transform: translateX(-30px); }
  100% { opacity: 1; transform: translateX(0); }
}

@keyframes slideInRight {
  0% { opacity: 0; transform: translateX(30px); }
  100% { opacity: 1; transform: translateX(0); }
}

.story-text {
  font-size: clamp(1rem, 2.5vw, 1.25rem);
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.9);
  text-align: justify;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  padding: 25px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin: 0;
}

// Features Section
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
  margin-top: 40px;
}

.feature-card {
  position: relative;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 30px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.5s ease;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-10px);
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
    border-color: rgba(79, 172, 254, 0.5);
  }
}

.feature-icon {
  font-size: 2.5rem;
  filter: drop-shadow(0 5px 15px rgba(0, 0, 0, 0.3));
}

.feature-content {
  flex: 1;
}

.feature-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 10px;
  font-family: $cosmic-font;
}

.feature-desc {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
  margin: 0;
}

.feature-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at center, rgba(79, 172, 254, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.5s ease;
}

.feature-card:hover .feature-glow {
  opacity: 1;
}

// Quest Section
.quest-steps {
  position: relative;
  margin: 40px 0;
}

.quest-step {
  position: relative;
  display: flex;
  align-items: center;
  gap: 30px;
  margin-bottom: 40px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.step-number {
  width: 50px;
  height: 50px;
  background: $cosmic-accent;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 900;
  color: #ffffff;
  font-family: $cosmic-font;
  box-shadow: 0 10px 30px rgba(79, 172, 254, 0.5);
  flex-shrink: 0;
}

.step-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 25px;
}

.step-icon {
  font-size: 2rem;
  filter: drop-shadow(0 3px 10px rgba(0, 0, 0, 0.3));
}

.step-text {
  flex: 1;
}

.step-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px;
  font-family: $cosmic-font;
}

.step-desc {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
  margin: 0;
}

.step-connector {
  position: absolute;
  left: 24px;
  top: 50px;
  width: 2px;
  height: 40px;
  background: linear-gradient(180deg, rgba(79, 172, 254, 0.5), transparent);
}

.quest-warning {
  display: flex;
  align-items: center;
  gap: 15px;
  background: rgba(245, 87, 108, 0.1);
  border: 1px solid rgba(245, 87, 108, 0.3);
  border-radius: 15px;
  padding: 20px;
  margin-top: 30px;
}

.warning-icon {
  font-size: 1.5rem;
  filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.3));
}

.warning-text {
  flex: 1;
  color: rgba(255, 255, 255, 0.9);
  font-size: 1rem;
  line-height: 1.6;
  margin: 0;
}

// Team Section
.team-card {
  display: flex;
  align-items: center;
  gap: 30px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 25px;
  padding: 35px;
  margin-top: 30px;
  
  @media (max-width: 768px) {
    flex-direction: column;
    text-align: center;
    gap: 20px;
  }
}

.team-avatar {
  position: relative;
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.avatar-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: $cosmic-gold;
  border-radius: 50%;
  box-shadow: 0 10px 30px rgba(255, 215, 0, 0.5);
}

.avatar-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 2rem;
  z-index: 2;
}

.team-text {
  flex: 1;
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.7;
  margin: 0;
}

// Enhanced Actions
.actions {
  display: flex;
  gap: 25px;
  justify-content: center;
  margin-top: 60px;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 20px;
  }
}

.action-btn {
  position: relative;
  background: none;
  border: none;
  border-radius: 25px;
  padding: 0;
  cursor: pointer;
  transition: all 0.5s ease;
  min-width: 200px;
  height: 55px;
  
  &:hover {
    transform: translateY(-5px);
  }
  
  &:active {
    transform: translateY(-2px);
  }
}

.btn-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 25px;
  transition: all 0.5s ease;
}

.primary-btn .btn-bg {
  background: $cosmic-accent;
  box-shadow: 0 15px 35px rgba(79, 172, 254, 0.4);
}

.secondary-btn .btn-bg {
  background: transparent;
  border: 2px solid rgba(79, 172, 254, 0.6);
  box-shadow: 0 15px 35px rgba(79, 172, 254, 0.2);
}

.btn-glow {
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  bottom: -5px;
  border-radius: 25px;
  opacity: 0;
  transition: all 0.5s ease;
}

.primary-btn .btn-glow {
  background: radial-gradient(circle, rgba(79, 172, 254, 0.3) 0%, transparent 70%);
}

.secondary-btn .btn-glow {
  background: radial-gradient(circle, rgba(79, 172, 254, 0.2) 0%, transparent 70%);
}

.action-btn:hover .btn-glow {
  opacity: 1;
}

.btn-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 100%;
}

.btn-icon {
  font-size: 1.2rem;
  filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.3));
}

.btn-text {
  font-size: 1rem;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
  font-family: $cosmic-font;
}

// Responsive Design
@media (max-width: 768px) {
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .quest-step {
    flex-direction: column;
    text-align: center;
    gap: 20px;
  }
  
  .step-content {
    flex-direction: column;
    text-align: center;
  }
  
  .step-connector {
    display: none;
  }
}

/* Override ScreenshotShare styles for cosmic theme */
:deep(.screenshot-controls) {
  bottom: 40px;
  
  .screenshot-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: 2px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(20px);
    box-shadow: 0 15px 50px rgba(102, 126, 234, 0.5);
    font-family: $cosmic-font;
    
    &:hover:not(:disabled) {
      transform: translateY(-8px);
      box-shadow: 0 25px 80px rgba(102, 126, 234, 0.8);
    }
    
    .btn-content {
      gap: 12px;
    }
    
    .camera-icon {
      font-size: 1.5rem;
      filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.3));
    }
    
    .btn-text {
      font-weight: 700;
      text-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
      letter-spacing: 1px;
    }
    
    .sparkles {
      .sparkle {
        background: #ffd700;
        box-shadow: 0 0 6px #ffd700;
      }
    }
  }
}

:deep(.success-modal) {
  .success-content {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9));
    backdrop-filter: blur(30px);
    border: 2px solid rgba(102, 126, 234, 0.3);
    box-shadow: 0 30px 80px rgba(102, 126, 234, 0.4);
    
    h3 {
      color: #667eea;
      font-family: $cosmic-font;
      font-weight: 800;
    }
    
    p {
      color: #666;
      font-family: $body-font;
      font-weight: 600;
    }
  }
}

:deep(.screenshot-preview-container) {
  .preview-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    
    h3 {
      font-family: $cosmic-font;
      font-weight: 800;
    }
  }
  
  .share-btn {
    font-family: $cosmic-font;
    
    &.primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    &.secondary {
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      box-shadow: 0 8px 25px rgba(79, 172, 254, 0.4);
    }
  }
}
</style>
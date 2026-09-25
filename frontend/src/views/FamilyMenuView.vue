<template>
  <div class="game-container mx-auto max-w-6xl p-4 lg:p-8">
    <!-- Floating Hearts Background -->
    <div class="hearts-bg">
      <div class="heart" v-for="n in 12" :key="n" :style="{ animationDelay: `${n * 0.8}s` }">💕</div>
    </div>

    <!-- ─── Loading / Error ─── -->
    <div v-if="cmStore.loading || rcpStore.loading" class="loading-state">
      <div class="cooking-loader">
        <div class="pan">🍳</div>
        <div class="steam">💨</div>
      </div>
      <p class="loading-text">Preparing your love menu...</p>
    </div>
    
    <div v-else-if="cmStore.error || rcpStore.error" class="error-state">
      <div class="error-icon">💔</div>
      <p class="error-text">{{ cmStore.error || rcpStore.error }}</p>
      <button class="retry-btn" @click="$router.go(0)">Try Again</button>
    </div>

    <!-- ─── 空态 ─── -->
    <div v-else-if="!cards.length" class="empty-state">
      <div class="love-castle">
        <div class="castle-emoji">🏰</div>
        <div class="magic-sparkles">
          <span class="sparkle" v-for="n in 6" :key="n">✨</span>
        </div>
      </div>
      <h2 class="empty-title">Your Love Kitchen Awaits</h2>
      <p class="empty-description">
        Complete ingredient quests together to unlock<br/>
        <span class="highlight">magical recipes</span> and build your culinary kingdom!
      </p>
      <div class="action-buttons">
        <RouterLink to="/" class="game-btn primary pulse">
          <span class="btn-icon">📸</span>
          <span class="btn-text">Start Quest</span>
          <div class="btn-glow"></div>
        </RouterLink>
        <RouterLink to="/diary" class="game-btn secondary">
          <span class="btn-icon">📖</span>
          <span class="btn-text">Love Diary</span>
          <div class="btn-glow"></div>
        </RouterLink>
      </div>
    </div>

    <!-- ─── 主列表 ─── -->
    <TransitionGroup v-else name="card-list" tag="div" class="recipe-grid">
      <div v-for="rc in cards" :key="rc.id" class="recipe-card-container">
        <!-- Recipe Card -->
        <article 
          class="recipe-card"
          :class="{ 'locked': rc.is_locked, 'mastered': rc.progress === 100 }"
          @click="!rc.is_locked && toggle(rc.id)"
        >
          <!-- Mastery Crown -->
          <div v-if="rc.progress === 100" class="mastery-crown">
            <div class="crown-icon">👑</div>
            <div class="crown-glow"></div>
          </div>

          <!-- Lock Overlay -->
          <div v-if="rc.is_locked" class="lock-overlay">
            <div class="lock-chain">🔗</div>
            <div class="lock-icon">🔒</div>
            <p class="lock-text">Cook together to unlock!</p>
            <div class="lock-particles">
              <span class="particle" v-for="n in 8" :key="n">⭐</span>
            </div>
          </div>

          <!-- Recipe Image -->
          <div class="recipe-image">
            <div 
              class="image-content"
              :style="{ backgroundImage: rc.thumb ? `url('${rc.thumb}')` : 'none' }"
            >
              <div v-if="!rc.thumb" class="placeholder-icon">🍽️</div>
            </div>
            <div class="image-border"></div>
          </div>

          <!-- Recipe Info -->
          <div class="recipe-info">
            <header class="recipe-header">
              <h3 class="recipe-title">{{ rc.name }}</h3>
              <div class="recipe-badges">
                <div class="star-display" :title="`${rc.progress}% mastered`">
                  <span class="stars">{{ stars(rc) }}</span>
                  <div class="star-trail"></div>
                </div>
                <div v-if="rc.progress === 100" class="achievement-medal">
                  <div class="medal-icon">🏆</div>
                  <div class="medal-shine"></div>
                </div>
              </div>
            </header>

            <!-- Tags -->
            <div class="recipe-tags">
              <span class="tag cuisine">
                <span class="tag-icon">🌍</span>
                {{ recipeCuisine(rc.id) || 'Mystery' }}
              </span>
              <span class="tag type">
                <span class="tag-icon">🍴</span>
                {{ recipeType(rc.id) || 'Dish' }}
              </span>
            </div>

            <!-- Love Progress -->
            <div class="love-progress">
              <div class="progress-header">
                <span class="progress-label">Love Level</span>
                <span class="progress-value" :class="getProgressClass(rc.progress)">
                  {{ rc.progress }}%
                </span>
              </div>
              <div class="progress-bar-container">
                <div class="progress-track">
                  <div 
                    class="progress-fill"
                    :class="getProgressBarClass(rc.progress)"
                    :style="{ width: rc.progress + '%' }"
                  >
                    <div class="progress-glow"></div>
                  </div>
                  <div class="progress-hearts">
                    <span class="heart" v-for="n in 3" :key="n" :class="{ active: rc.progress >= n * 33.33 }">💖</span>
                  </div>
                </div>
              </div>
              <p class="adventures-text">
                {{ rc.unlocked }} of {{ rc.total }} adventures completed
              </p>
            </div>

            <!-- Battle Rounds (Expanded) -->
            <transition name="expand">
              <div v-if="openId === rc.id" class="battle-section">
                <h4 class="battle-title">
                  <span class="battle-icon">⚔️</span>
                  Epic Battles
                </h4>
                <div class="battle-grid">
                  <RouterLink
                    v-for="w in getUniqueRounds(rc.rounds)"
                    :key="w.id"
                    class="battle-card"
                    :to="{ name: 'RoundlyBattle', params: { roundId: w.id } }"
                  >
                    <div class="battle-bg"></div>
                    <div class="battle-content">
                      <div class="battle-round">Round {{ w.id }}</div>
                      <div class="battle-swords">⚔️</div>
                      <div class="battle-status">Ready!</div>
                    </div>
                    <div class="battle-glow"></div>
                  </RouterLink>
                </div>
              </div>
            </transition>
          </div>
        </article>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink }  from 'vue-router'
import { useCoupleMemoryStore } from '@/stores/couplememoryStore'
import { useRecipesStore }      from '@/stores/recipeStore'
import type { CoupleMemory, MemoryEntry } from '@/models/couplememory'
import type { Recipe } from '@/models/recipes'

/* ─── tiny helper：docker → 浏览器 host ─── */
const ORIGIN = location.origin
const fixUrl = (u: string | null | undefined) =>
  !u ? '' : u.startsWith('http')
    ? u.replace(/^https?:\/\/web:\d+/i, ORIGIN)
    : ORIGIN + u

/* ─── stores ─── */
const cmStore  = useCoupleMemoryStore()
const rcpStore = useRecipesStore()

onMounted(async () => {
  await Promise.all([
    cmStore.fetchMemories({ page_size: 100, ordering: '-round_start' }),
    rcpStore.recipes.length ? null : rcpStore.loadBasics(),
  ])
})

/* ─── 卡片类型 ─── */
type RecipeCard = {
  id: number; name: string; thumb: string | null;
  total: number; unlocked: number; progress: number;
  is_locked: boolean; rounds: CoupleMemory[]
}

/* ─── 聚合 ─── */
function collectCards(rounds: CoupleMemory[], recipes: Recipe[]): RecipeCard[] {
  const recipeMap = new Map<number, Recipe>(recipes.map(r => [r.id, r]))
  const map = new Map<number, RecipeCard>()

  for (const round of rounds)
    for (const ent of round.entries as MemoryEntry[]) {
      const recRaw: any = ent.recipe
      if (!recRaw) continue
      const recFull = typeof recRaw === 'object' && 'name' in recRaw
        ? recRaw : recipeMap.get(recRaw as number)
      if (!recFull) continue

      const slot = map.get(recFull.id) ?? {
        id: recFull.id, name: recFull.name, thumb: fixUrl(recFull.default_picture),
        total: 0, unlocked: 0, progress: 0, is_locked: false, rounds: [] as CoupleMemory[],
      }
      slot.total += 1
      slot.unlocked += 1
      slot.rounds.push(round)
      map.set(recFull.id, slot)
    }

  map.forEach(s => { s.progress = Math.round((s.unlocked / s.total) * 100) })
  return [...map.values()].sort((a, b) => b.progress - a.progress)
}
const cards = computed(() => collectCards(cmStore.memories, rcpStore.recipes))

/* ─── 读取额外字段 ─── */
const recipeCuisine = (id: number) => rcpStore.recipes.find(r => r.id === id)?.cuisine
const recipeType    = (id: number) => rcpStore.recipes.find(r => r.id === id)?.dish_type

/* ─── 折叠逻辑 ─── */
const openId = ref<number | null>(null)
const toggle = (id: number) => { openId.value = openId.value === id ? null : id }

/* ─── 星级 ─── */
const stars = (c: RecipeCard) => '★'.repeat(Math.max(1, Math.ceil(c.progress / 34)))

/* ─── 游戏化样式类 ─── */
const getProgressClass = (progress: number) => {
  if (progress === 100) return 'legendary'
  if (progress >= 75) return 'epic'
  if (progress >= 50) return 'rare'
  if (progress >= 25) return 'uncommon'
  return 'common'
}

const getProgressBarClass = (progress: number) => {
  if (progress === 100) return 'legendary'
  if (progress >= 75) return 'epic'
  if (progress >= 50) return 'rare'
  return 'common'
}

/* ─── 去重周数 ─── */
const getUniqueRounds = (rounds: CoupleMemory[]) => {
  const seen = new Set<number>()
  return rounds.filter(w => {
    if (seen.has(w.id)) return false
    seen.add(w.id)
    return true
  })
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Fredoka+One:wght@400&display=swap');

/* ===== Game Variables ===== */
:root {
  --love-pink: #ff69b4;
  --love-red: #ff1744;
  --love-purple: #e91e63;
  --gold: #ffd700;
  --silver: #c0c0c0;
  --bronze: #cd7f32;
  --magic-blue: #1e3a8a;
  --game-shadow: 0 10px 30px rgba(0,0,0,0.2);
  --love-gradient: linear-gradient(135deg, #ff69b4 0%, #ff1744 50%, #e91e63 100%);
  --legendary-gradient: linear-gradient(135deg, #ffd700 0%, #ff8c00 50%, #ff1744 100%);
  --epic-gradient: linear-gradient(135deg, #9c27b0 0%, #673ab7 100%);
  --rare-gradient: linear-gradient(135deg, #2196f3 0%, #03a9f4 100%);
  --common-gradient: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%);
}

/* ===== Game Container ===== */
.game-container {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(135deg, #ffeef8 0%, #f3e5f5 50%, #e8f4fd 100%);
  font-family: 'Fredoka One', cursive;
}

/* ===== Floating Hearts Background ===== */
.hearts-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.heart {
  position: absolute;
  font-size: 1.5rem;
  opacity: 0.3;
  animation: float-heart 8s infinite linear;
}

.heart:nth-child(odd) { left: 10%; }
.heart:nth-child(even) { left: 90%; }

/* ===== Loading State ===== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  gap: 2rem;
}

.cooking-loader {
  position: relative;
  font-size: 3rem;
}

.pan {
  animation: shake 0.5s infinite;
}

.steam {
  position: absolute;
  top: -2rem;
  left: 50%;
  transform: translateX(-50%);
  animation: steam-rise 2s infinite;
}

.loading-text {
  font-size: 1.2rem;
  color: var(--love-purple);
  animation: pulse 2s infinite;
}

/* ===== Error State ===== */
.error-state {
  text-align: center;
  padding: 3rem;
  background: linear-gradient(135deg, #ffebee 0%, #fce4ec 100%);
  border-radius: 2rem;
  margin: 2rem 0;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  animation: heartbreak 2s infinite;
}

.retry-btn {
  background: var(--love-gradient);
  color: white;
  padding: 0.8rem 2rem;
  border: none;
  border-radius: 2rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 1rem;
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--game-shadow);
}

/* ===== Empty State ===== */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  max-width: 500px;
  margin: 0 auto;
}

.love-castle {
  position: relative;
  margin-bottom: 2rem;
}

.castle-emoji {
  font-size: 4rem;
  animation: castle-glow 3s infinite;
}

.magic-sparkles {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 100px;
}

.magic-sparkles .sparkle {
  position: absolute;
  font-size: 1rem;
  animation: sparkle-dance 2s infinite;
}

.magic-sparkles .sparkle:nth-child(1) { top: 10%; left: 20%; animation-delay: 0s; }
.magic-sparkles .sparkle:nth-child(2) { top: 30%; right: 10%; animation-delay: 0.3s; }
.magic-sparkles .sparkle:nth-child(3) { bottom: 40%; left: 10%; animation-delay: 0.6s; }
.magic-sparkles .sparkle:nth-child(4) { bottom: 20%; right: 20%; animation-delay: 0.9s; }
.magic-sparkles .sparkle:nth-child(5) { top: 50%; left: 50%; animation-delay: 1.2s; }
.magic-sparkles .sparkle:nth-child(6) { top: 20%; right: 30%; animation-delay: 1.5s; }

.empty-title {
  font-size: 2rem;
  color: var(--love-purple);
  margin-bottom: 1rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.empty-description {
  font-size: 1.1rem;
  color: #666;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.highlight {
  color: var(--love-gradient);
  font-weight: bold;
}

/* ===== Action Buttons ===== */
.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.game-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 2rem;
  border-radius: 2rem;
  font-weight: bold;
  text-decoration: none;
  color: #666;
  transition: all 0.3s;
  overflow: hidden;
}

.game-btn.primary {
  background: var(--love-gradient);
}

.game-btn.secondary {
  background: var(--epic-gradient);
}

.game-btn.pulse {
  animation: button-pulse 2s infinite;
}

.game-btn:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 15px 35px rgba(0,0,0,0.3);
}

.btn-glow {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  transition: left 0.5s;
}

.game-btn:hover .btn-glow {
  left: 100%;
}

/* ===== Recipe Grid ===== */
.recipe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
  position: relative;
  z-index: 2;
}

/* ===== Recipe Card ===== */
.recipe-card {
  position: relative;
  background: white;
  border-radius: 2rem;
  overflow: hidden;
  box-shadow: var(--game-shadow);
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  cursor: pointer;
}

.recipe-card:hover {
  transform: translateY(-10px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}

.recipe-card.mastered {
  background: linear-gradient(135deg, #fff9c4 0%, #ffecb3 100%);
  box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
}

.recipe-card.locked {
  opacity: 0.7;
  filter: grayscale(0.5);
  cursor: not-allowed;
}

/* ===== Mastery Crown ===== */
.mastery-crown {
  position: absolute;
  top: -15px;
  right: 20px;
  z-index: 10;
}

.crown-icon {
  font-size: 2rem;
  animation: crown-float 3s infinite;
}

.crown-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255,215,0,0.3) 0%, transparent 70%);
  animation: crown-pulse 2s infinite;
}

/* ===== Lock Overlay ===== */
.lock-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 5;
}

.lock-chain {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  animation: chain-swing 2s infinite;
}

.lock-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  animation: lock-shake 3s infinite;
}

.lock-text {
  font-size: 1rem;
  color: var(--love-purple);
  text-align: center;
  font-weight: bold;
}

.lock-particles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  font-size: 0.8rem;
  animation: particle-float 4s infinite;
}

.particle:nth-child(1) { top: 20%; left: 20%; animation-delay: 0s; }
.particle:nth-child(2) { top: 30%; right: 20%; animation-delay: 0.5s; }
.particle:nth-child(3) { bottom: 30%; left: 30%; animation-delay: 1s; }
.particle:nth-child(4) { bottom: 20%; right: 30%; animation-delay: 1.5s; }
.particle:nth-child(5) { top: 50%; left: 10%; animation-delay: 2s; }
.particle:nth-child(6) { top: 40%; right: 10%; animation-delay: 2.5s; }
.particle:nth-child(7) { bottom: 40%; left: 50%; animation-delay: 3s; }
.particle:nth-child(8) { bottom: 50%; right: 50%; animation-delay: 3.5s; }

/* ===== Recipe Image ===== */
.recipe-image {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.image-content {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
}

.placeholder-icon {
  font-size: 3rem;
  color: #ccc;
}

.image-border {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--love-gradient);
}

/* ===== Recipe Info ===== */
.recipe-info {
  padding: 1.5rem;
}

.recipe-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.recipe-title {
  font-size: 1.3rem;
  color: var(--love-purple);
  margin: 0;
  flex: 1;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.recipe-badges {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.star-display {
  position: relative;
  background: white;
  padding: 0.3rem 0.8rem;
  border-radius: 1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stars {
  color: var(--gold);
  font-size: 0.9rem;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

.star-trail {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 1rem;
  background: linear-gradient(45deg, transparent, rgba(255,215,0,0.2), transparent);
  animation: star-shine 3s infinite;
}

.achievement-medal {
  position: relative;
  background: var(--legendary-gradient);
  padding: 0.3rem;
  border-radius: 50%;
  box-shadow: 0 2px 10px rgba(255,215,0,0.4);
}

.medal-icon {
  font-size: 1.2rem;
  animation: medal-rotate 4s infinite;
}

.medal-shine {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 50%;
  background: conic-gradient(transparent, rgba(255,255,255,0.3), transparent);
  animation: medal-spin 2s infinite;
}

/* ===== Recipe Tags ===== */
.recipe-tags {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tag {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.3rem 0.8rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 1rem;
  font-size: 0.8rem;
  color: #495057;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.tag-icon {
  font-size: 0.7rem;
}

/* ===== Love Progress ===== */
.love-progress {
  background: linear-gradient(135deg, #ffeef8 0%, #f3e5f5 100%);
  padding: 1rem;
  border-radius: 1rem;
  margin-bottom: 1rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.progress-label {
  font-size: 0.9rem;
  color: var(--love-purple);
  font-weight: bold;
}

.progress-value {
  font-size: 0.9rem;
  font-weight: bold;
  padding: 0.2rem 0.6rem;
  border-radius: 0.5rem;
  color: white;
}

.progress-value.common { background: var(--common-gradient); }
.progress-value.uncommon { background: var(--rare-gradient); }
.progress-value.rare { background: var(--rare-gradient); }
.progress-value.epic { background: var(--epic-gradient); }
.progress-value.legendary { background: var(--legendary-gradient); }

.progress-bar-container {
  margin-bottom: 0.5rem;
}

.progress-track {
  position: relative;
  height: 1rem;
  background: #e0e0e0;
  border-radius: 0.5rem;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  position: relative;
}

.progress-fill.common { background: var(--common-gradient); }
.progress-fill.rare { background: var(--rare-gradient); }
.progress-fill.epic { background: var(--epic-gradient); }
.progress-fill.legendary { 
  background: var(--legendary-gradient);
  animation: legendary-glow 2s infinite;
}

.progress-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: progress-shine 3s infinite;
}

.progress-hearts {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  gap: 0.5rem;
}

.progress-hearts .heart {
  font-size: 0.7rem;
  opacity: 0.3;
  transition: all 0.3s;
}

.progress-hearts .heart.active {
  opacity: 1;
  animation: heart-beat 1s infinite;
}

.adventures-text {
  font-size: 0.7rem;
  color: #666;
  text-align: center;
  margin: 0;
}

/* ===== Battle Section ===== */
.battle-section {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 1.5rem;
  border-radius: 1rem;
  margin-top: 1rem;
}

.battle-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: white;
  font-size: 1.1rem;
  margin-bottom: 1rem;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}

.battle-icon {
  animation: sword-clash 2s infinite;
}

.battle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 1rem;
}

.battle-card {
  position: relative;
  background: linear-gradient(135deg, #4a148c 0%, #6a1b9a 100%);
  border-radius: 1rem;
  padding: 1rem;
  text-decoration: none;
  color: white;
  overflow: hidden;
  transition: all 0.3s;
  text-align: center;
}

.battle-card:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 10px 25px rgba(106, 27, 154, 0.4);
}

.battle-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at center, rgba(255,255,255,0.1) 0%, transparent 70%);
  animation: battle-pulse 3s infinite;
}

.battle-content {
  position: relative;
  z-index: 1;
}

.battle-round {
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.battle-swords {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  animation: sword-spin 4s infinite;
}

.battle-status {
  font-size: 0.7rem;
  color: #00ff88;
  text-shadow: 0 0 10px rgba(0,255,136,0.5);
}

.battle-glow {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  transition: left 0.5s;
}

.battle-card:hover .battle-glow {
  left: 100%;
}

/* ===== Animations ===== */
@keyframes float-heart {
  0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
  10% { opacity: 0.3; }
  90% { opacity: 0.3; }
  100% { transform: translateY(-100vh) rotate(360deg); opacity: 0; }
}

@keyframes shake { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(-5px); } }
@keyframes steam-rise { 0% { transform: translateX(-50%) translateY(0); opacity: 1; } 100% { transform: translateX(-50%) translateY(-20px); opacity: 0; } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
@keyframes heartbreak { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
@keyframes castle-glow { 0%, 100% { filter: drop-shadow(0 0 10px rgba(255,215,0,0.3)); } 50% { filter: drop-shadow(0 0 20px rgba(255,215,0,0.6)); } }
@keyframes sparkle-dance { 0%, 100% { transform: scale(1) rotate(0deg); } 50% { transform: scale(1.2) rotate(180deg); } }
@keyframes button-pulse { 0%, 100% { box-shadow: 0 0 20px rgba(255,105,180,0.3); } 50% { box-shadow: 0 0 30px rgba(255,105,180,0.6); } }
@keyframes crown-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
@keyframes crown-pulse { 0%, 100% { transform: translate(-50%, -50%) scale(1); } 50% { transform: translate(-50%, -50%) scale(1.2); } }
@keyframes chain-swing { 0%, 100% { transform: rotate(0deg); } 50% { transform: rotate(10deg); } }
@keyframes lock-shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-2px); } 75% { transform: translateX(2px); } }
@keyframes particle-float { 0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.3; } 50% { transform: translateY(-10px) rotate(180deg); opacity: 0.8; } }
@keyframes star-shine { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
@keyframes medal-rotate { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
@keyframes medal-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
@keyframes legendary-glow { 0%, 100% { box-shadow: 0 0 10px rgba(255,215,0,0.3); } 50% { box-shadow: 0 0 20px rgba(255,215,0,0.6); } }
@keyframes progress-shine { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
@keyframes heart-beat { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
@keyframes sword-clash { 0%, 100% { transform: rotate(0deg); } 25% { transform: rotate(-10deg); } 75% { transform: rotate(10deg); } }
@keyframes battle-pulse { 0%, 100% { opacity: 0.1; } 50% { opacity: 0.3; } }
@keyframes sword-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

/* ===== Transitions ===== */
.card-list-enter-from { opacity: 0; transform: translateY(30px) scale(0.9); }
.card-list-enter-active { transition: all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94); }
.card-list-leave-to { opacity: 0; transform: translateY(-30px) scale(0.9); }
.card-list-leave-active { transition: all 0.3s ease; }

.expand-enter-from { opacity: 0; transform: translateY(-10px); max-height: 0; }
.expand-enter-active { transition: all 0.3s ease; }
.expand-leave-to { opacity: 0; transform: translateY(-10px); max-height: 0; }
.expand-leave-active { transition: all 0.3s ease; }

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .recipe-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .game-btn {
    width: 100%;
    max-width: 300px;
  }
}
</style>

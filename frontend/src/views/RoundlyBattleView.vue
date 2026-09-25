<!-- RoundlyBattleView.vue | Clean Couple Cooking Battle Experience
     Features: Cover Photo, Gallery/Comments dual-mode, clean interaction
     Focus: Ultimate clean gaming experience with precise interaction improvements
-->
<template>
  <v-container class="no-padding simple-battle-container">
    <!-- ── Loading / Error / Empty ── -->
    <template v-if="loading && !round">
      <div class="loading-arena">
        <v-progress-circular indeterminate color="orange" size="64" width="6" />
        <p class="loading-text">Preparing Battle Arena...</p>
      </div>
    </template>

    <v-alert
      v-else-if="error"
      type="error"
      variant="outlined"
      class="my-8"
    >
      {{ error }}
    </v-alert>

    <div v-else-if="!round" class="text-center my-12 text-grey">
      No active battles found.
    </div>

    <!-- ── Clean Battle Interface ── -->
    <template v-else>
      <!-- 🎮 Cover Photo Hero Section -->
      <div v-if="round.cover_photo" class="hero-cover-section">
        <div class="cover-image-container">
          <v-img 
            :src="fix(round.winner_entry?.best_media_url || round.cover_photo)" 
            class="hero-cover-image"
            cover
          />
          <div class="cover-overlay">
            <div class="battle-title-overlay">
              <v-icon size="32" color="orange">mdi-fire</v-icon>
              <h2 class="hero-title">CULINARY BATTLE</h2>
              <v-icon size="32" color="orange">mdi-fire</v-icon>
            </div>
          </div>
          <div class="date-overlay">
            <v-chip variant="elevated" color="primary" size="large">
              <v-icon start size="16">mdi-calendar</v-icon>
              {{ formattedRange }}
            </v-chip>
          </div>
          
          <!-- 🎯 Battle Detail Helper Icon -->
          <div v-if="hasBattleResult" class="battle-helper-icon" @click="openBattleDetailModal">
            <v-btn
              size="small"
              variant="elevated"
              class="helper-btn"
            >
              <v-icon size="30" color="white">mdi-sword-cross</v-icon>
              Kinny's Feedback
            </v-btn>
            <v-tooltip activator="parent" location="bottom">
              🎮 View Battle Details
            </v-tooltip>
          </div>

          <div  class="back-icon" @click="router.push('/battle_history')">
            <v-btn
              icon
              size="small"
              color="orange"
              variant="elevated"
              class="back-btn"
            >
              <v-icon size="30" color="white">mdi-arrow-left</v-icon>
            </v-btn>
            <v-tooltip activator="parent" location="bottom">
              🎮 View Battle Details
            </v-tooltip>
          </div>
        </div>
      </div>

  <!-- 🎮 Top Controls removed: gallery always visible; comments toggle moved below -->

  <!-- 🍳 Gallery + Kinny Results always visible -->
  <div class="gallery-mode">
        <!-- 🍳 VS Battle Layout - Two Columns Side by Side -->
        <div class="vs-battle-container" :class="{ 'single-only': !battleData.userB }">
          <!-- Current User Column -->
          <div class="battle-column user-column">
            <div v-if="battleData.userA?.photos?.length" class="user-dishes">
              <div
                v-for="(photo, index) in battleData.userA.photos"
                :key="photo.id || index"
                class="dish-card-vs"
                @click="openPhotoModal(photo.url, photo.entryId)"
              >
                <v-img
                  :src="fix(photo.url)"
                  class="dish-image-vs"
                  :class="{ 'highlight': photo.isHighlight }"
                  cover
                  aspect-ratio="1"
                />
                <!-- <div class="photo-score" v-if="photoScore(photo) !== null">
                  <v-icon size="14" color="amber">mdi-star</v-icon>
                  {{ Math.round(photoScore(photo) || 0) }}
                </div> -->
                <!-- <div class="dish-overlay">
                  <p v-if="photo.content" class="dish-title">{{ photo.content }}</p>
                </div> -->
              </div>
            </div>
            
            <div v-else class="no-dishes">
              <v-icon size="60" color="grey" class="empty-icon">mdi-chef-hat</v-icon>
              <p class="empty-text">No dishes yet, start cooking!</p>
            </div>

            <!-- <div class="column-header">
              <v-badge :content="Math.round(battleData.userA?.aiScore || 0)" color="purple" floating>
                <v-avatar size="80" class="user-avatar-large">
                  <v-img :src="currentUserAvatar" />
                </v-avatar>
              </v-badge>
              <div class="user-info">
                <h3>{{ userStore.user?.username || 'You' }}</h3>
                <div class="battle-stats">
                  <v-chip size="x-small" color="blue" variant="elevated" class="stat-chip">
                    {{ battleData.userA?.entriesCount || 0 }} dishes
                  </v-chip>
                  <v-chip v-if="battleData.userA?.aiScore && battleData.userA.aiScore > 0" 
                          size="x-small" color="purple" variant="elevated" class="stat-chip">
                    Score: {{ Math.round(battleData.userA.aiScore) }}
                  </v-chip>
                </div>
              </div>
              <v-icon v-if="isWinner('A')" color="gold" size="32" class="crown-icon">mdi-crown</v-icon>
            </div> -->
          </div>

          <!-- VS Divider -->
          <div class="vs-center">
            <div class="vs-circle">
              <span class="vs-text">VS</span>
            </div>
          </div>

          <!-- Partner Column -->
          <div class="battle-column partner-column">
            <div v-if="battleData.userB?.photos?.length" class="partner-dishes">
              <div
                v-for="(photo, index) in battleData.userB.photos"
                :key="photo.id || index"
                class="dish-card-vs"
                @click="openPhotoModal(photo.url, photo.entryId)"
              >
                <v-img
                  :src="fix(photo.url)"
                  class="dish-image-vs"
                  :class="{ 'highlight': photo.isHighlight }"
                  cover
                  aspect-ratio="1"
                />
                <!-- <div class="photo-score" v-if="photoScore(photo) !== null">
                  <v-icon size="14" color="amber">mdi-star</v-icon>
                  {{ Math.round(photoScore(photo) || 0) }}
                </div>
                <div class="dish-overlay">
                  <p v-if="photo.content" class="dish-title">{{ photo.content }}</p>
                </div> -->
              </div>
            </div>
            
            <div v-else class="no-dishes">
              <v-icon size="60" color="grey" class="empty-icon">mdi-account-heart</v-icon>
              <p v-if="partnerUser && battleData.userA?.photos?.length" class="empty-text">You’ve kicked off! invite partner to share!</p>
              <p v-else-if="partnerUser" class="empty-text">Remind your partner to join</p>
              <p v-else class="empty-text">No partner yet</p>
            </div>

            <!-- <div v-if="partnerUser" class="column-header">
              <v-badge :content="Math.round(battleData.userB?.aiScore || 0)" color="purple" floating>
                <v-avatar size="80" class="partner-avatar-large">
                  <v-img :src="partnerAvatar" />
                </v-avatar>
              </v-badge>
              <div class="partner-info">
                <h3>{{ partnerUser.username || 'Partner' }}</h3>
                <div class="battle-stats">
                  <v-chip size="x-small" color="pink" variant="elevated" class="stat-chip">
                    {{ battleData.userB?.entriesCount || 0 }} dishes
                  </v-chip>
                  <v-chip v-if="battleData.userB?.aiScore && battleData.userB.aiScore > 0" 
                          size="x-small" color="purple" variant="elevated" class="stat-chip">
                    Score: {{ Math.round(battleData.userB.aiScore) }}
                  </v-chip>
                </div>
              </div>
              <v-icon v-if="isWinner('B')" color="gold" size="32" class="crown-icon">mdi-crown</v-icon>
            </div> -->
          </div>
        </div>
      </div>

      <!-- Kinny Battle Results (compact, header removed for tighter layout) -->
      <div v-if="hasAIData" class="ai-results-section">
        <!-- Compact ribbon -->
          <div class="ai-ribbon">
            <div class="ai-ribbon-side">
              <v-avatar size="28"><v-img :src="battleData.userA?.avatar || placeholderAvatar" /></v-avatar>
              <template v-if="battleData.userA">
                <span class="ribbon-score">{{ Math.round(battleData.userA?.aiScore || 0) }}</span>
              </template>
              <template v-else>
                <span class="ribbon-score">?</span>
              </template>
            </div>
            <div class="ai-ribbon-center">VS</div>
            <div class="ai-ribbon-side">
              <template v-if="battleData.userB">
                <span class="ribbon-score">{{ Math.round(battleData.userB?.aiScore || 0) }}</span>
              </template>
              <template v-else>
                <span class="ribbon-score">?</span>
              </template>
              <v-avatar size="28"><v-img :src="battleData.userB?.avatar || placeholderAvatar" /></v-avatar>
            </div>
            <template v-if="battleData.userA && battleData.userB">
              <v-chip size="x-small" color="orange" variant="elevated">{{ commentary.short || 'Battle on' }}</v-chip>
              <v-btn size="x-small" variant="text" color="orange" class="ai-details-toggle" @click="aiDetailsOpen = !aiDetailsOpen">
                <v-icon size="20">{{ aiDetailsOpen ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
                Details
              </v-btn>
            </template>
            <template v-else>
              <ScrollNotice
                :messages="partnerCallout"
                class="gaming-notice-bar"
              />
            </template>
          </div>
        
        <v-expand-transition>
        <div v-show="aiDetailsOpen">
        <template v-if="battleData.userB">
        <div class="battle-fighters">
          
          <div :class="['fighter-simple', { 'winner': isWinner('A') }]">
            <div class="fighter-details">
              <v-icon v-if="isWinner('A')" color="gold" size="24" class="fighter-crown-icon">mdi-crown</v-icon>
              <div class="fighter-profile">
                <v-avatar size="50">
                  <v-img :src="battleData.userA?.avatar || placeholderAvatar" />
                </v-avatar>
                <div>
                  <h4>{{ battleData.userA?.name || 'Chef A' }}</h4>
                  <div class="score-badge">{{ Math.round(battleData.userA?.aiScore || 0) }}</div>
                </div>
              </div>
              <div v-if="battleData.userA?.metrics" class="metrics-mini">
                <div class="metric-row">
                  <span class="metric-label">Visual</span>
                  <v-progress-linear :model-value="battleData.userA.metrics.visual_appeal || 0" height="6" color="cyan" rounded />
                  <span class="metric-val">{{ Math.round(battleData.userA.metrics.visual_appeal || 0) }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">Technique</span>
                  <v-progress-linear :model-value="battleData.userA.metrics.cooking_technique || 0" height="6" color="amber" rounded />
                  <span class="metric-val">{{ Math.round(battleData.userA.metrics.cooking_technique || 0) }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">Freshness</span>
                  <v-progress-linear :model-value="battleData.userA.metrics.ingredient_freshness || 0" height="6" color="light-green" rounded />
                  <span class="metric-val">{{ Math.round(battleData.userA.metrics.ingredient_freshness || 0) }}</span>
                </div>
              </div>
            </div>
          </div>
                      
          <div :class="['fighter-simple', { 'winner': isWinner('B') }]">
            <div class="fighter-details">
              <v-icon v-if="isWinner('B')" color="gold" size="24" class="fighter-crown-icon">mdi-crown</v-icon>
              <div class="fighter-profile">
                <v-avatar size="50">
                  <v-img :src="battleData.userB?.avatar || placeholderAvatar" />
                </v-avatar>
                <div>
                  <h4>{{ battleData.userB?.name || 'Chef B' }}</h4>
                <div class="score-badge">{{ Math.round(battleData.userB?.aiScore || 0) }}</div>
                </div>
              </div>
              <div v-if="battleData.userB?.metrics" class="metrics-mini">
                <div class="metric-row">
                  <span class="metric-label">Visual</span>
                  <v-progress-linear :model-value="battleData.userB.metrics.visual_appeal || 0" height="6" color="cyan" rounded />
                  <span class="metric-val">{{ Math.round(battleData.userB.metrics.visual_appeal || 0) }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">Technique</span>
                  <v-progress-linear :model-value="battleData.userB.metrics.cooking_technique || 0" height="6" color="amber" rounded />
                  <span class="metric-val">{{ Math.round(battleData.userB.metrics.cooking_technique || 0) }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">Freshness</span>
                  <v-progress-linear :model-value="battleData.userB.metrics.ingredient_freshness || 0" height="6" color="light-green" rounded />
                  <span class="metric-val">{{ Math.round(battleData.userB.metrics.ingredient_freshness || 0) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Score bar & commentary -->
        <div class="ai-scorebar">
          <v-progress-linear
            :model-value="aiBarA"
            color="blue"
            height="10"
            rounded
            striped
          />
          <div class="ai-bar-labels">
            <span class="bar-side"><v-avatar size="18" class="bar-avatar"><v-img :src="battleData.userA?.avatar || placeholderAvatar" /></v-avatar> {{ Math.round(battleData.userA?.aiScore || 0) }}</span>
            <span class="diff-label" :class="{ lead: scoreDiff >= 10, close: scoreDiff < 10 }">
              {{ commentary.short }}
            </span>
            <span class="bar-side">{{ Math.round(battleData.userB?.aiScore || 0) }} <v-avatar size="18" class="bar-avatar"><v-img :src="battleData.userB?.avatar || placeholderAvatar" /></v-avatar></span>
          </div>
        </div>

        <div class="ai-commentary-card" v-if="commentary.text">
          <v-icon size="18" color="orange">mdi-sword-cross</v-icon>
          <span class="commentary-text">{{ commentary.text }}</span>
        </div>
        </template>
        <template v-else>
          <div class="partner-callout-card">
            <v-icon size="22" color="orange">mdi-bell-ring</v-icon>
            <span class="callout-text">{{ partnerCallout }}</span>
          </div>
        </template>
        </div>
        </v-expand-transition>
      </div>

      <!-- 💬 Comments & Memory Wall - Main Interface -->
      <div v-if="battleData.userA || battleData.userB" class="main-comment-wall">
        <!-- Memory Posts Section -->
        <div v-if="round?.summary" class="memory-posts-section">
          <div class="memory-post-card">
            <div class="post-header">
              <v-icon size="18" color="orange">mdi-memory</v-icon>
              <span class="post-label">Memory</span>
            </div>
            <div class="post-content">{{ round.summary }}</div>
          </div>
        </div>

        

        <BattleComment
          :comments="battleData.realComments"
          :current-user-avatar="currentUserAvatar"
          :partner-avatar="partnerAvatar"
          :user-username="userStore.user?.username || 'You'"
          :partner-username="partnerUser?.username || 'Partner'"
          :user-entries-count="battleData.userA?.entriesCount || 0"
          :partner-entries-count="battleData.userB?.entriesCount || 0"
          :solo-mode="!battleData.userB"
          :user-top-summary="battleData.userA?.topSummary || null"
          :partner-top-summary="battleData.userB?.topSummary || null"
          :round-summary="round?.summary || null"
          @add-comment="handleDanmakuComment"
        />
      </div>

      <!-- 📸 Photo Modal (accessible overlay) -->
      <PhotoDetailOverlay
        v-model="photoOverlayOpen"
        :photos="battleData.allPhotos"
        :entries="battleData.allEntries"
        :start-index="photoOverlayIndex"
        @changeIndex="onOverlayIndexChange"
      />

      <!-- 🎮 Battle Detail Modal -->
      <BattleDetailModal
        v-model="battleDetailModalOpen"
        :battle-result="firstBattleResult"
        :winner="amIWinner"
      />
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { computed, watch, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCoupleMemoryStore } from '@/stores/couplememoryStore'
import { useUserStore } from '@/stores/userStore'
import { resolveURL } from '@/utils/resolveURL'
import { CoupleMemory } from '@/models/couplememory'
import type { MemoryEntry } from '@/models/couplememory'
import DanmakuCommentWall from '@/components/DanmakuCommentWall.vue'
import BattleComment from '@/components/BattleComment.vue'
import PhotoDetailOverlay from '@/components/PhotoDetailOverlay.vue'
import BattleDetailModal from '@/components/BattleDetailModal.vue'
import defaultAvatar from '@/assets/default-avatar.png'

/* ── Store & routing ── */
const store = useCoupleMemoryStore()
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()

const loading = computed(() => store.loading)
const error = computed(() => store.error)

/* Active round id (optional) */
const roundId = computed(() => Number(route.params.roundId))

/* Round object */
const round = ref<CoupleMemory | null>(null)

/* Clean UI State Management */
const viewMode = ref<'commentwall' | 'gallery'>('commentwall') // Deprecated toggle; gallery always visible
const commentMode = ref<'wall' | 'list'>('wall')
const photoModal = ref<{ show: boolean; url: string; entryId?: number | null }>({ show: false, url: '', entryId: null })
// New accessible overlay state
const photoOverlayOpen = ref(false)
const photoOverlayIndex = ref(0)
const onOverlayIndexChange = (idx: number) => { photoOverlayIndex.value = idx }
const aiDetailsOpen = ref(false)
const newCommentText = ref('') // New comment input

/* Couple and Partner Logic (from ProfileView) */
const couple = computed(() => userStore.couple || null)
const partnerUser = computed(() => couple.value?.members?.find((m: any) => m.id !== userStore.user?.id))

// Fix avatar URL helper
const ORIGIN = import.meta.env.VITE_API_BASE_URL?.replace('/api', '') || location.origin
const fix = (u?: string) => {
  if (!u) return ''
  if (u.startsWith('http')) {
    // Handle various source URLs:
    // - web:911 (docker container)
    // - localhost:911 (local dev)
    // - <PRODUCTION_HOST>:911 (production)
    return u.replace(
      /^https?:\/\/(web|localhost|45\.79\.163\.242):\d+/i, 
      ORIGIN
    )
  }
  // For relative URLs, prepend with correct origin
  return ORIGIN + u
}

/* Placeholder avatar */
const placeholderAvatar = defaultAvatar
const currentUserAvatar = computed(() => fix(userStore.user?.avatar_url || undefined) || placeholderAvatar)
const partnerAvatar = computed(() => fix(partnerUser.value?.avatar_url || undefined) || placeholderAvatar)

/* Date range text */
const formattedRange = computed(() => {
  const ws = round.value?.round_start, we = round.value?.round_end
  if (!ws || !we) return ''
  return `${ws} – ${we}`
})

/* 判断是否有AI数据 */
const hasAIData = computed(() => {
  return battleData.value.aiComments.length > 0 || 
         (battleData.value.userA?.aiScore && battleData.value.userA.aiScore > 0) ||
         (battleData.value.userB?.aiScore && battleData.value.userB.aiScore > 0)
})

/* 🎯 判断是否有battle_result数据 */
const hasBattleResult = computed(() => {
  if (!round.value?.entries) return false
  return round.value.entries.some(entry => 
    entry.ai_judgment?.battle_result && 
    Object.keys(entry.ai_judgment.battle_result).length > 0
  )
})

/* 🎮 获取第一个有效的battle_result数据 */
const firstBattleResult = computed(() => {
  if (!round.value?.entries) return null
  const entryWithBattleResult = round.value.entries.find(entry => 
    entry.ai_judgment?.battle_result && 
    Object.keys(entry.ai_judgment.battle_result).length > 0
  )
  return entryWithBattleResult?.ai_judgment?.battle_result || null
})

/* 🎮 Battle Detail Modal控制 */
const battleDetailModalOpen = ref(false)
const openBattleDetailModal = () => {
  battleDetailModalOpen.value = true
}

/* 判断胜者 */
const isWinner = (fighter: 'A' | 'B'): boolean => {
  const scoreA = battleData.value.userA?.aiScore || 0
  const scoreB = battleData.value.userB?.aiScore || 0
  
  if (scoreA === scoreB) return false
  return fighter === 'A' ? scoreA > scoreB : scoreB > scoreA
}

const amIWinner = computed(() => {
  if (!round.value?.winner_entry) return false
  return round.value.winner_entry.author_username === (userStore.user?.username || '')
})

/* 转换数据为战斗格式 - 精准处理单用户或多用户场景 */
const battleData = computed(() => {
  const entries = (round.value?.entries || []) as any[]
  if (!entries.length) {
    return {
      userA: null,
      userB: null,
      allPhotos: [],
      allEntries: [],
      aiComments: [],
      realComments: [],
      isAnalyzing: false,
      recipeInfo: null,
      roundSummary: null
    }
  }

  // Group entries by author
  const userGroups = new Map<string, any[]>()
  entries.forEach((e: any) => {
    const name = e.author_username || 'Unknown'
    if (!userGroups.has(name)) userGroups.set(name, [])
    userGroups.get(name)!.push(e)
  })

  // Helper: collect photos from entries
  const photosFromEntries = (ens: any[]) => {
    const arr: any[] = []
    ens.forEach((entry: any) => {
      if (entry.media && entry.media.length) {
        entry.media.forEach((m: any) => {
          const url = fix(m.url || m.media)
          if (url) arr.push({ id: m.id || `${entry.id}-${m.media}` , url, isHighlight: !!m.is_highlight, entryId: entry.id, content: entry.content })
        })
      } else if (entry.best_media_url) {
        const url = fix(entry.best_media_url)
        if (url) arr.push({ id: `best-${entry.id}`, url, isHighlight: true, entryId: entry.id, content: entry.content })
      }
    })
    return arr
  }

  // Helper: convert one user's entries to battle user
  const convertUser = (username: string, userEntries: any[]) => {
    const userPhotos = photosFromEntries(userEntries)

    const avgScore = userEntries.length
      ? userEntries.reduce((sum: number, e: any) => {
          const s = (e.ai_judgment?.overall_score ?? e.effective_ai_score ?? e.ai_score ?? 0) as number
          return sum + (Number.isFinite(s) ? s : 0)
        }, 0) / userEntries.length
      : 0

    let topSummary: string | null = null
    let topComment: string | null = null
    let best = -1
    
    // 🎮 show the win/loss message that battle_result carries
    const isWinner = round.value?.winner_entry?.author_username === username
    
    userEntries.forEach((e: any) => {
      const score = (e.ai_judgment?.overall_score ?? e.effective_ai_score ?? e.ai_score ?? 0) as number
      if (score > best) {
        best = score
        
        // 🏆 优先显示battle结果的胜负专用消息，回退到传统消息
        const battleResult = e.ai_judgment?.battle_result
        if (battleResult && (battleResult.kinny_winner_message || battleResult.kinny_loser_message)) {
          topSummary = isWinner ? battleResult.kinny_winner_message : battleResult.kinny_loser_message
          // 🎮 不在个人消息中显示reason，保持个人消息的独特性
          topComment = e.ai_judgment?.individual_comment || e.ai_judgment?.ai_comment || null
        } else {
          // 回退到传统消息
          topSummary = e.ai_judgment?.individual_summary || e.ai_judgment?.ai_summary || null
          topComment = e.ai_judgment?.individual_comment || e.ai_judgment?.ai_comment || null
        }
      }
    })

    const metricEntries = userEntries.filter((e: any) => e.ai_judgment)
    const avgMetric = (key: 'visual_appeal' | 'cooking_technique' | 'ingredient_freshness') =>
      metricEntries.length
        ? Math.max(0, Math.min(100, Math.round(metricEntries.reduce((s: number, e: any) => s + ((e.ai_judgment?.[key] as number) || 0), 0) / metricEntries.length)))
        : 0
    const metrics = metricEntries.length ? {
      visual_appeal: avgMetric('visual_appeal'),
      cooking_technique: avgMetric('cooking_technique'),
      ingredient_freshness: avgMetric('ingredient_freshness')
    } : null

    const avatarGuess = (userEntries[0] as any)?.author_avatar_url
      ? fix((userEntries[0] as any).author_avatar_url)
      : (userStore.user?.username && username === userStore.user.username)
        ? currentUserAvatar.value
        : (partnerUser.value?.username && username === partnerUser.value.username)
          ? partnerAvatar.value
          : placeholderAvatar

    return {
      name: username,
      avatar: avatarGuess,
      photos: userPhotos.slice(0, 6),
      aiScore: avgScore,
      topSummary: topSummary || null,
      topComment: topComment || null,
      metrics,
      recipeName: userEntries[0]?.recipe_name || 'Battle Dish',
      mood: userEntries[0]?.mood || 'neutral',
      entriesCount: userEntries.length
    }
  }

  const users = Array.from(userGroups.entries())

  let userA: any = null
  let userB: any = null
  const currentName = userStore.user?.username
  if (users.length === 1) {
    if (users[0][0] === currentName) {
      userA = convertUser(users[0][0], users[0][1])
    } else {
      userB = convertUser(users[0][0], users[0][1])
    }
  } else if (users.length >= 2) {
    const aPair = users.find(([name]) => name === currentName) || users[0]
    const bPair = users.find(([name]) => name !== aPair[0]) || users[1]
    userA = convertUser(aPair[0], aPair[1])
    userB = convertUser(bPair[0], bPair[1])
  }

  // AI comments
  const aiComments = entries.flatMap((entry: any) => {
    const j = entry.ai_judgment
    if (!j) return [] as any[]
    const txt = j.effective_summary || j.individual_summary || j.ai_summary || ''
    if (!txt) return [] as any[]
    return [{
      id: `ai-${entry.id}`,
      text: txt,
      rawScore: j.overall_score,
      type: 'positive',
      category: 'Kinny Judge'
    }]
  })

  // Real comments: only from backend entries, no local pollution
  const allComments = entries.flatMap((e: any) => e.comments || [])
  
  // Normalize comment format with proper avatar mapping
  const realComments = allComments.map((comment: any) => {
    const username = comment.author_username || userStore.user?.username || 'Unknown'
    
    // Smart avatar mapping
    let avatar = placeholderAvatar
    if (username === userStore.user?.username) {
      avatar = currentUserAvatar.value
    } else if (username === partnerUser.value?.username) {
      avatar = partnerAvatar.value
    }
    
    return {
      id: String(comment.id),
      username,
      text: comment.content || '',
      timestamp: comment.created_at ? new Date(comment.created_at).getTime() : Date.now(),
      avatar,
      type: 'cheer' as const
    }
  })

  return {
    userA,
    userB,
    allPhotos: photosFromEntries(entries),
    allEntries: entries,
    aiComments,
    realComments,
    isAnalyzing: loading.value,
    recipeInfo: {
      coverPhoto: round.value?.cover_photo || undefined,
      totalPoints: round.value?.total_points,
      entriesCount: round.value?.entries_count
    },
    roundSummary: round.value?.summary || null
  }
})

/* Kinny Bars & Commentary */
const scoreA = computed(() => battleData.value.userA?.aiScore || 0)
const scoreB = computed(() => battleData.value.userB?.aiScore || 0)
const scoreTotal = computed(() => Math.max(1, scoreA.value + scoreB.value))
const aiBarA = computed(() => Math.round((scoreA.value / scoreTotal.value) * 100))
const scoreDiff = computed(() => Math.abs(Math.round(scoreA.value - scoreB.value)))
const leading = computed(() => scoreA.value > scoreB.value ? 'you' : (scoreB.value > scoreA.value ? 'partner' : 'tie'))
const commentary = computed(() => {
  if (!hasAIData.value) return { short: '', text: '' }
  
  // 🎯 prefer the dedicated win/loss message from battle_result
  const currentUserId = userStore.user?.id
  let battleResultData = null
  let isCurrentUserWinner = false
  
  // 查找有battle_result的entry
  if (round.value?.entries) {
    const entriesWithBattleResult = round.value.entries.filter(entry => 
      entry.ai_judgment?.battle_result && 
      Object.keys(entry.ai_judgment.battle_result).length > 0
    )
    
    if (entriesWithBattleResult.length > 0) {
      // 使用第一个有效的battle_result
      const battleEntry = entriesWithBattleResult[0]
      if (battleEntry.ai_judgment?.battle_result) {
        battleResultData = battleEntry.ai_judgment.battle_result
        
        // // 判断当前用户是否获胜
        // if (battleResultData.winner === 1) {
        //   // winner: 1 表示第一个参与者获胜，需要查看具体是谁
        //   isCurrentUserWinner = battleEntry.author === currentUserId
        // } else if (battleResultData.winner === 2) {
        //   // winner: 2 表示第二个参与者获胜，需要查看具体是谁
        //   isCurrentUserWinner = battleEntry.author !== currentUserId
        // }

        isCurrentUserWinner = battleData.value.userA?.aiScore > battleData.value.userB?.aiScore
      }
    }
  }
  
  // when battle_result is present, use its dedicated message
  if (battleResultData) {
    const winnerMessage = battleResultData.kinny_winner_message || '🏆 Victory achieved!'
    const loserMessage = battleResultData.kinny_loser_message || '💪 Great effort! Keep cooking!'
    const battleReason = battleResultData.reason || 'Epic cooking battle!'
    
    if (isCurrentUserWinner) {
      return { 
        short: 'Victory!', 
        text: `${winnerMessage}\n\n🎯 Battle Analysis: ${battleReason}`
      }
    } else {
      return { 
        short: 'Keep going!', 
        text: `${loserMessage}\n\n🎯 Battle Analysis: ${battleReason}`
      }
    }
  }
  
  // 回退到原有的通用逻辑
  if (leading.value === 'tie') return { short: 'Neck and neck!', text: '⚖️ It\'s a tie! Every move counts—push for the win!' }
  const side = leading.value === 'you' ? 'You' : 'Partner'
  if (scoreDiff.value >= 20) return { short: `${side} dominating!`, text: `🏆 ${side} is dominating this round! Legendary momentum!` }
  if (scoreDiff.value >= 10) return { short: `${side} in the lead`, text: `🔥 ${side} takes the lead—keep the heat up!` }
  return { short: 'Close battle!', text: '⚔️ Close match! A perfect dish could flip the tide!' }
})

// Game-like callout when partner hasn't posted yet
const partnerCallout = computed(() => {
  if (battleData.value.userB) return []
  const lines = [
    'You\'re dominating… but only because your partner hasn\'t joined. Ping them now! 🔔',
    'Arena is quiet on the right. Tag your partner to enter the fray! ⚔️',
    'Solo streak detected. Invite your partner to unlock duo bonuses! 🏅',
    'Combo meter paused. Get your partner in to build a streak! 🔥',
    'Victory by default isn\'t victory. Rally your partner! 📣',
    'Dominance pending. Partner hasn\'t posted—send a nudge! 👉',
    'Co-op locked. Partner missing—summon them for the PK! 🎮',
    'The crowd wants a duel. Call your partner to the stage! 🎤',
    'Hidden perks await when both sides post. Invite now! 🎁',
  'Kinny is waiting for a fair fight. Wake your partner! 🤖',
  'Right lane idle. Rally your duo to light it up! 💡',
  'Tag-in needed! Bring your partner for the next round! 🥊',
  'Power-up locked—needs partner action to activate! ⚡',
  'Scoreboard wants two names. Summon your teammate! 📜',
  'Kinny senses potential—complete the duo for bonus XP! ✨',
  'Ghost opponent mode—break it by inviting your partner! 👻',
  'Momentum stalled. Partner entry unlocks speed boost! 🚀',
  'Audience chants for duo play. Make the call! 📣',
  'No contest yet. Partner post starts the real PK! 🔥'
  ]
  return lines
})

/* Gating for details */
const bothHaveScores = computed(() => (battleData.value.userA?.aiScore || 0) > 0 && (battleData.value.userB?.aiScore || 0) > 0)
const canShowDetails = computed(() => aiDetailsOpen.value && bothHaveScores.value)

/* 简洁交互方法 */
const openPhotoModal = (url: string, entryId?: number) => {
  // Open new accessible overlay and compute index from allPhotos
  const idx = battleData.value.allPhotos.findIndex((p: any) => p.url === url && (entryId ? p.entryId === entryId : true))
  photoOverlayIndex.value = idx >= 0 ? idx : 0
  photoOverlayOpen.value = true
}

// Helper to find the best entry to attach comments to
const getBestEntryForComment = () => {
  if (!round.value?.entries?.length) return null
  
  // Prefer current user's entries first
  const userEntries = round.value.entries.filter(e => 
    e.author_username === userStore.user?.username
  )
  if (userEntries.length > 0) {
    // Get the most recent entry from current user
    return userEntries.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]
  }
  
  // Then prefer partner's most recent entry if available
  const partnerName = partnerUser.value?.username
  if (partnerName) {
    const partnerEntries = round.value.entries.filter(e => e.author_username === partnerName)
    if (partnerEntries.length > 0) {
      return partnerEntries.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]
    }
  }
  
  // Fallback to most recent entry from any user
  return round.value.entries.sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )[0]
}

const handleDanmakuComment = async (text: string, type?: string) => {
  console.log('💬 Danmaku comment:', { text, type })
  
  const targetEntry = getBestEntryForComment()
  if (!targetEntry) {
    console.warn('⚠️ No entries found to attach comment to')
    return
  }

  // Generate unique optimistic ID as number for compatibility
  const optimisticId = Date.now()
  
  // Create optimistic comment for instant UI feedback
  const optimisticComment = {
    id: optimisticId,
    entry: targetEntry.id,
    author: userStore.user?.id || 0,
    author_username: userStore.user?.username || 'You',
    content: text,
    created_at: new Date().toISOString(),
    emoji: '',
    _isOptimistic: true
  }
  
  // Add optimistic comment directly to the target entry
  if (round.value) {
    const entryIndex = round.value.entries.findIndex(e => e.id === targetEntry.id)
    if (entryIndex !== -1) {
      // Use type assertion to bypass type checking for optimistic comment
      round.value.entries[entryIndex].comments = [
        ...round.value.entries[entryIndex].comments,
        optimisticComment as any
      ]
    }
  }

  try {
    console.log('🚀 Posting comment to backend for entry:', targetEntry.id)
    const newComment = await store.createComment(targetEntry.id, text)
    
    if (newComment) {
      console.log('✅ Comment successfully posted to backend:', newComment)
      
      // Remove optimistic comment since real one is now in the store
      if (round.value) {
        const entryIndex = round.value.entries.findIndex(e => e.id === targetEntry.id)
        if (entryIndex !== -1) {
          // Remove optimistic comment by checking the _isOptimistic flag
          round.value.entries[entryIndex].comments = round.value.entries[entryIndex].comments
            .filter(c => !(c as any)._isOptimistic)
        }
      }
      
      console.log('✨ Comment sync completed')
    } else {
      console.error('❌ Backend returned null for comment creation')
    }
  } catch (error) {
    console.error('💥 Failed to post comment to backend:', error)
    // Mark optimistic comment as failed but keep it for user feedback
    if (round.value) {
      const entryIndex = round.value.entries.findIndex(e => e.id === targetEntry.id)
      if (entryIndex !== -1) {
        const commentIndex = round.value.entries[entryIndex].comments.findIndex(c => (c as any)._isOptimistic && c.id === optimisticId)
        if (commentIndex !== -1) {
          (round.value.entries[entryIndex].comments[commentIndex] as any)._failed = true
        }
      }
    }
  }
}

/* Comment functionality */
const submitComment = async () => {
  if (!newCommentText.value.trim()) return
  
  const targetEntry = getBestEntryForComment()
  if (!targetEntry) {
    console.warn('⚠️ No entries found to attach comment to')
    return
  }

  try {
    console.log('🚀 Submitting comment for entry:', targetEntry.id)
    const newComment = await store.createComment(targetEntry.id, newCommentText.value.trim())
    
    if (newComment) {
      console.log('✅ Comment successfully posted:', newComment)
      newCommentText.value = ''
    } else {
      console.error('❌ Backend returned null for comment creation')
    }
  } catch (error) {
    console.error('💥 Failed to post comment:', error)
    // Keep the input text so user can retry
  }
}

const formatCommentTime = (timestamp: number): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  
  return date.toLocaleDateString('en-US')
}

/* Fetch data when component mounts or id changes */
async function fetchRound() {
  if (isNaN(roundId.value)) {
    await store.fetchCurrent()
    round.value = store.current
  } else {
    const fetched = await store.fetchRoundById(roundId.value, true)
    round.value = fetched
  }
}

// Refresh round data to get updated comments
async function refreshRound() {
  if (!round.value) return
  
  try {
    const refreshed = await store.fetchRoundById(round.value.id, true)
    if (refreshed) {
      round.value = refreshed
      console.log('Round data refreshed with latest comments')
    }
  } catch (error) {
    console.error('Failed to refresh round data:', error)
  }
}

onMounted(fetchRound)
watch(() => roundId.value, fetchRound)

/* Entry-level Kinny helpers for modal */
const selectedEntry = computed(() => {
  if (!photoModal.value.entryId) return null
  return battleData.value.allEntries.find((e: any) => e.id === photoModal.value.entryId) || null
})

const entryMetrics = (entry: any) => {
  const j = entry?.ai_judgment
  if (!j) return null
  return {
    visual_appeal: j.visual_appeal ?? 0,
    cooking_technique: j.cooking_technique ?? 0,
    ingredient_freshness: j.ingredient_freshness ?? 0,
  }
}

const entryScore = (entry: any) => {
  const j = entry?.ai_judgment
  if (j && typeof j.overall_score === 'number') return j.overall_score
  return entry?.effective_ai_score ?? entry?.ai_score ?? null
}

const effectiveComment = (entry: any) => {
  const j = entry?.ai_judgment || {}
  return j.individual_comment || j.ai_comment || 'Kinny is analyzing this dish...'
}

/* Per-photo score helper */
const photoScore = (photo: any): number | null => {
  const entry = battleData.value.allEntries.find((e: any) => e.id === photo.entryId)
  if (!entry) return null
  const j = entry.ai_judgment
  if (j && typeof j.overall_score === 'number') return j.overall_score
  const s = entry.effective_ai_score ?? entry.ai_score
  return typeof s === 'number' ? s : null
}
</script>

<style scoped>
.simple-battle-container {
  padding: 12px !important;
  max-width: 100%;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  min-height: 100vh;
  color: white;
  /* 确保顶层容器不会阻止弹幕渲染 */
  overflow: visible !important;
  position: relative !important;
  z-index: 0 !important;
  contain: none !important;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

/* 🎮 Loading Arena */
.loading-arena {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
}

.loading-text {
  color: #ffa726;
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
}

/* 🎮 Hero Cover Section */
.hero-cover-section {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
  width: 100%;
  max-width: 1450px;
}

.cover-image-container {
  position: relative;
  height: 220px;
}

.hero-cover-image {
  width: 100%;
  height: 100%;
}

.cover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.3));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.battle-title-overlay {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-title {
  color: white;
  font-size: 2.0rem;
  font-weight: 900;
  text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.7);
  letter-spacing: 2px;
  margin: 0;
}

.date-overlay {
  position: absolute;
  bottom: 1rem;
  z-index: 10;
  justify-items: center;
  align-items: center;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
}

/* 🎮 Battle Helper Icon */
.battle-helper-icon {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  z-index: 10;
}

.helper-btn {
  background: linear-gradient(135deg, #1687f9, #570cea) !important;
  border: 2px solid #afaafe;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(48, 22, 249, 0.4);
  transition: all 0.3s ease;
  height: 40px;
  width: fit-content;
  text-transform: none;
  font-size: 1rem;
}

.helper-btn:hover {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 6px 20px rgba(48, 22, 249, 0.6);
}

.helper-btn:active {
  transform: scale(1.05) rotate(2deg);
}

/* Back Button */
.back-icon {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  z-index: 10;
}

.back-btn {
  background: linear-gradient(135deg, #f9b916, #ea7b0c) !important;
  border: 2px solid #fee3aa;
  box-shadow: 0 4px 12px rgba(249, 177, 22, 0.4);
  transition: all 0.3s ease;
  height: 40px;
  width: 40px;
}

/* 🎮 Simple Mode Controls */
.simple-mode-controls {
  display: flex;
  justify-content: center;
  margin-bottom: 32px;
}

.simple-mode-btn {
  min-width: 140px !important;
  height: 50px !important;
  font-weight: 700 !important;
  font-size: 1.1rem !important;
  text-transform: uppercase !important;
  letter-spacing: 1.5px !important;
}

/* 🖼️ Gallery Mode */
.gallery-mode {
  display: flex;
  flex-direction: column;
  gap: 20px;
  /* 确保弹幕能够渲染出来 */
  overflow: visible !important;
  position: relative !important;
  z-index: 1 !important;
  width: 100%;
  max-width: 1450px;
}

/* 🏆 Battle Results */
.battle-results-card {
  background: linear-gradient(135deg, rgba(103, 58, 183, 0.3), rgba(156, 39, 176, 0.2));
  border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(103, 58, 183, 0.35);
  box-shadow: 0 6px 24px rgba(103, 58, 183, 0.28);
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
}

.results-header h3 {
  color: #ba68c8;
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
}

.battle-fighters {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.fighter-simple {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 12px;
  flex: 1;
  transition: all 0.3s ease;
}

.fighter-simple.winner {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.3), rgba(255, 193, 7, 0.2));
  border: 2px solid #ffd700;
  transform: scale(1.05);
  box-shadow: 0 8px 24px rgba(255, 215, 0, 0.4);
}

.fighter-details {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  width: 100%;
}

.fighter-profile {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.fighter-crown-icon {
  animation: crownGlow 2s infinite alternate;
  position: absolute;
  z-index: 100;
  left: 25px;
  top: 0px;
}

.score-badge {
  background: rgba(186, 104, 200, 0.4);
  color: #ba68c8;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  margin-top: 4px;
  width: fit-content
}

.ai-scorebar {
  margin-top: 16px;
}

.ai-bar-labels {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.85);
}

.diff-label {
  font-weight: 800;
  color: #ffa726;
}
.diff-label.lead { color: #ffca28; }
.diff-label.close { color: #ffb74d; }

.ai-commentary-card {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 8px 10px;
}

/* Scorebar side avatars */
.bar-side { display: inline-flex; align-items: center; gap: 6px; }
.bar-avatar { border: 1px solid rgba(186, 104, 200, 0.6); }

.commentary-text {
  color: rgba(255, 255, 255, 0.95);
  font-weight: 700;
  white-space: pre-line; /* 🎮 精准改善：支持换行显示battle reason */
}

.ai-feed {
  margin-top: 10px;
  background: rgba(186, 104, 200, 0.08);
  border: 1px solid rgba(186, 104, 200, 0.3);
  border-radius: 10px;
  padding: 10px;
}

.ai-feed-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: #ba68c8;
  font-weight: 700;
}

.ai-feed-list {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
  overflow-x: auto;
}

.ai-chip {
  white-space: nowrap;
}

/* Kinny compact ribbon */
.gaming-notice-bar {
  position: relative;
  z-index: 5;
  background: linear-gradient(135deg, rgba(255, 87, 34, 0.9), rgba(255, 152, 0, 0.9)) !important;
  border: 2px solid rgba(255, 193, 7, 0.6);
  box-shadow: 0 0 20px rgba(255, 152, 0, 0.3), inset 0 0 20px rgba(255, 255, 255, 0.1);
}

.ai-results-section {
  justify-content: center;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1450px;
}

.ai-ribbon {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(186, 104, 200, 0.08);
  border: 1px solid rgba(186, 104, 200, 0.3);
  border-radius: 10px;
  padding: 6px 8px;
  width: 100%;
}
.ai-ribbon-side {
  display: flex; align-items: center; gap: 6px;
}
.ai-ribbon-center {
  font-weight: 900; color: #ffa726; padding: 0 6px;
}
.ribbon-score { font-weight: 800; color: #ba68c8; }
.ai-details-toggle { margin-left: auto; font-size: 14px; font-weight: 700; }

/* Metrics mini styles */
.metrics-mini {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.metric-row {
  display: grid;
  grid-template-columns: 64px 1fr 36px;
  align-items: center;
  gap: 6px;
}
.metric-label { font-size: 0.7rem; color: rgba(255,255,255,0.8); }
.metric-val { font-size: 0.75rem; color: rgba(255,255,255,0.9); font-weight: 700; text-align: right; }

/* Kinny modal analysis */
.ai-modal-panel {
  padding: 12px;
  border-top: 1px solid rgba(255,255,255,0.15);
}
.ai-modal-header { display: flex; align-items: center; gap: 8px; margin: 8px 0 10px; color: #ba68c8; font-weight: 700; }
.ai-metrics { display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px; }
.ai-comment-block { display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.06); padding: 8px 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.12); }
.ai-comment-text { font-size: 0.9rem; color: rgba(255,255,255,0.95); }

/* 🍳 Couple Cooking Battle Styles */
.couple-cooking-battle {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.chef-row {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.chef-row:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.chef-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.chef-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chef-info h3 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: white;
}

.chef-dishes-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}

.dish-card {
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
}

.dish-card:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 24px rgba(100, 181, 246, 0.3);
}

.dish-image {
  border-radius: 12px 12px 0 0;
}

.dish-image.highlight {
  border: 3px solid #ffd700;
  box-shadow: 0 0 12px rgba(255, 215, 0, 0.5);
}

.dish-info {
  padding: 12px;
}

.dish-description {
  margin: 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* VS Divider */
.vs-divider {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 16px 0;
}

.vs-badge {
  background: linear-gradient(135deg, #ff6b35, #f7931e);
  color: white;
  padding: 12px 24px;
  border-radius: 50px;
  font-size: 1.2rem;
  font-weight: 900;
  letter-spacing: 2px;
  box-shadow: 0 4px 16px rgba(255, 107, 53, 0.4);
}

/* Single User Display */
.single-chef-display {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.single-chef-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

/* 💬 Comments Section Styles */
.switch-to-comments {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.comment-btn {
  min-width: 200px !important;
  height: 56px !important;
  font-size: 1.1rem !important;
  font-weight: 700 !important;
  background: linear-gradient(135deg, #4fc3f7, #29b6f6) !important;
  box-shadow: 0 8px 24px rgba(79, 195, 247, 0.4) !important;
}

.comment-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(79, 195, 247, 0.6) !important;
}

.comments-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.comments-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  justify-content: center;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.comments-header h3 {
  color: #4fc3f7;
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
}

.comments-list {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 24px;
  padding-right: 8px;
}

.comment-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.comment-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateX(4px);
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.comment-author {
  font-weight: 600;
  color: #4fc3f7;
  font-size: 0.9rem;
}

.comment-time {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin-left: auto;
}

.comment-text {
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.5;
  font-size: 0.9rem;
}

.add-comment-section {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.comment-input-container {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.user-avatar {
  flex-shrink: 0;
  margin-top: 8px;
}

.comment-input {
  flex: 1;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
}

/* 🖼️ Single User Gallery */
.single-user-gallery {
  grid-column: 1 / -1;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.gallery-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  justify-content: center;
}

.gallery-header h3 {
  color: #64b5f6;
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
}

.all-photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.memory-photo-card {
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
}

.memory-photo-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(100, 181, 246, 0.3);
}

.photo-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
  padding: 12px;
  color: white;
  height: 100vh;
}

.photo-author {
  font-size: 0.8rem;
  font-weight: 600;
  color: #64b5f6;
  margin-bottom: 4px;
}

.photo-content {
  font-size: 0.7rem;
  opacity: 0.9;
  line-height: 1.3;
}

/* 🎯 CTA Section */
.cta-section {
  display: flex;
  justify-content: center;
}

.cta-btn {
  min-width: 200px !important;
  height: 56px !important;
  font-size: 1.1rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
  background: linear-gradient(135deg, #ff6b35, #f7931e) !important;
  box-shadow: 0 8px 24px rgba(255, 107, 53, 0.4) !important;
}

.cta-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(255, 107, 53, 0.6) !important;
}

/* 💬 Main Comment Wall Interface */
.main-comment-wall {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 1450px;
}

/* 📝 Memory Posts Section */
.memory-posts-section {
  margin-bottom: 12px;
}

.memory-post-card {
  background: rgba(255, 167, 38, 0.1);
  border: 1px solid rgba(255, 167, 38, 0.3);
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 8px;
}

.post-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.post-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #ffa726;
}

.post-content {
  font-size: 0.9rem;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.9);
}

/* 🎮 Compact VS Preview */
.compact-vs-preview {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.vs-preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.battle-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.switch-view-btn {
  font-size: 0.7rem !important;
  height: 28px !important;
  min-width: 60px !important;
}

.mini-vs-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.mini-fighter {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.mini-avatar {
  border: 1px solid rgba(255, 167, 38, 0.5);
}

.mini-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.mini-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-count {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.7);
}

.mini-vs {
  font-size: 0.7rem;
  font-weight: 900;
  color: #ffa726;
  padding: 0 8px;
}

/* 🔙 Back Button */
.back-to-comments {
  margin-bottom: 12px;
}

/* 💬 Comments Section in Main Wall */
.main-comment-wall .comments-section {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.main-comment-wall .comments-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.main-comment-wall .comments-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #81c784;
}

.main-comment-wall .comment-item {
  margin-bottom: 12px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.main-comment-wall .comment-input-container {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.main-comment-wall .comment-input {
  flex: 1;
}

.main-comment-wall .comment-actions {
  display: flex;
  justify-content: flex-end;
}

/* 📱 Mobile Optimizations for Comment Wall */
@media (max-width: 768px) {
  .main-comment-wall {
    gap: 12px;
  }
  
  .memory-post-card {
    padding: 10px;
  }
  
  .compact-vs-preview {
    padding: 10px;
  }
  
  .mini-avatar {
    width: 32px !important;
    height: 32px !important;
  }
  
  .mini-name {
    font-size: 0.7rem;
  }
  
  .mini-count {
    font-size: 0.6rem;
  }
}

@media (max-width: 480px) {
  .chef-photos-simple {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .simple-mode-btn {
    min-width: 80px !important;
    font-size: 0.8rem !important;
  }
}

/* 🎬 Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.gallery-mode,
.commentwall-mode {
  animation: fadeIn 0.5s ease-out;
}

.chef-gallery-card {
  animation: fadeIn 0.6s ease-out;
}

/* 🎮 Gaming Aesthetic */
.simple-battle-container::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(255, 107, 53, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(103, 58, 183, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 40% 80%, rgba(156, 39, 176, 0.1) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

/* ⚔️ VS Battle Container - Tight Gaming Layout */
.vs-battle-container {
  display: flex;
  align-items: stretch;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, rgba(255, 107, 53, 0.1), rgba(103, 58, 183, 0.1));
  border-radius: 16px;
  border: 2px solid rgba(255, 167, 38, 0.3);
  box-shadow: 0 8px 32px rgba(255, 107, 53, 0.2);
  position: relative;
  overflow: hidden;
  justify-content: center;
  max-height: 700px;
}

.vs-battle-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    linear-gradient(45deg, transparent 49%, rgba(255, 167, 38, 0.1) 50%, transparent 51%),
    linear-gradient(-45deg, transparent 49%, rgba(255, 107, 53, 0.1) 50%, transparent 51%);
  pointer-events: none;
}

/* 👤 Battle Columns - Compact Fighter Layout */
.battle-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 12px 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  z-index: 1;
  max-width: 680px;
}

.user-column {
  border-left: 3px solid #4caf50;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(0, 0, 0, 0.3));
}

.partner-column {
  border-right: 3px solid #f44336;
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.1), rgba(0, 0, 0, 0.3));
}

/* 🏆 Column Headers - Compact Fighter Info */
.column-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  position: relative;
}

.user-info, .partner-info {
  flex: 1;
  min-width: 0;
}

.user-info h3, .partner-info h3 {
  margin: 0 0 4px 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.battle-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}

.stat-chip {
  font-size: 0.65rem !important;
  height: 18px !important;
  font-weight: 600 !important;
}

.crown-icon {
  animation: crownGlow 2s infinite alternate;
  position: absolute;
  left: 15px;
  top: -15px;
}

@keyframes crownGlow {
  0% { filter: drop-shadow(0 0 4px #ffd700); }
  100% { filter: drop-shadow(0 0 8px #ffd700) drop-shadow(0 0 12px #ffa000); }
}

.user-avatar-large, .partner-avatar-large {
  border: 2px solid #ffa726;
  box-shadow: 0 0 12px rgba(255, 167, 38, 0.5);
}

/* 🥘 Dish Cards - Tight Gaming Grid */
.user-dishes, .partner-dishes {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.dish-card-vs {
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.dish-card-vs:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(255, 167, 38, 0.4);
  border-color: #ffa726;
}

.dish-image-vs {
  border-radius: 8px;
  aspect-ratio: 1;
}

.dish-image-vs.highlight {
  border: 2px solid #ffd700;
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
}

.dish-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
  padding: 4px 6px;
  color: white;
}

.dish-title {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ⚡ VS Center - Epic Battle Divider */
.vs-center {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 50px;
  position: relative;
  z-index: 2;
}

.vs-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b35, #ffa726);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
  box-shadow: 
    0 0 0 3px rgba(255, 167, 38, 0.3),
    0 4px 16px rgba(255, 107, 53, 0.5);
  animation: pulseVS 2s infinite;
}

.vs-text {
  font-size: 0.8rem;
  font-weight: 900;
  color: white;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
}

@keyframes pulseVS {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(255, 167, 38, 0.2), 0 6px 20px rgba(255, 107, 53, 0.6); }
}

/* � No Dishes State - Clean & Simple */
.no-dishes {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 12px;
  text-align: center;
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  min-height: 120px;
  opacity: 0.7;
}

.empty-icon {
  opacity: 0.5;
  margin-bottom: 4px;
}

.empty-text {
  margin: 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.3;
  font-weight: 500;
}

.no-dishes .v-btn {
  margin-top: 4px;
  font-size: 0.7rem !important;
  padding: 0 12px !important;
  height: 32px !important;
  font-weight: 600 !important;
}

/* 📱 Mobile Optimizations */
@media (max-width: 768px) {
  .vs-battle-container {
    gap: 6px;
    padding: 8px;
  }
  
  .battle-column {
    padding: 8px 6px;
  }
  
  .column-header {
    padding: 6px;
    gap: 6px;
  }
  
  .user-avatar-large, .partner-avatar-large {
    width: 50px !important;
    height: 50px !important;
  }
  
  .user-info h3, .partner-info h3 {
    font-size: 0.8rem;
  }
  
  .vs-circle {
    width: 35px;
    height: 35px;
  }
  
  .vs-text {
    font-size: 0.7rem;
  }
  
  .dish-card-vs {
    border-radius: 6px;
  }
  
  .dish-title {
    font-size: 0.6rem;
  }
  
  .no-dishes {
    padding: 12px 6px;
    min-height: 100px;
  }
  
  .no-dishes .v-icon {
    font-size: 40px !important;
  }
}

@media (max-width: 480px) {
  .vs-battle-container {
    gap: 4px;
    padding: 6px;
  }
  
  .user-dishes, .partner-dishes {
    grid-template-columns: 1fr 1fr;
    gap: 4px;
  }
  
  .vs-circle {
    width: 30px;
    height: 30px;
  }
  
  .vs-text {
    font-size: 0.6rem;
  }
}

.gallery-mode,
.commentwall-mode {
  position: relative;
  z-index: 1;
}

/* 🎯 force the danmaku to render, so the voting layer appears */
.simple-battle-container :deep(.danmaku-item) {
  position: absolute !important;
  z-index: 999999 !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  pointer-events: auto !important;
  transform-style: preserve-3d !important;
  will-change: transform, opacity !important;
  contain: none !important;
  isolation: isolate !important;
  mix-blend-mode: normal !important;
  clip: unset !important;
  clip-path: none !important;
  mask: none !important;
  overflow: visible !important;
}

.simple-battle-container :deep(.danmaku-display) {
  overflow: visible !important;
  contain: none !important;
  position: relative !important;
  z-index: 10 !important;
}

/* 确保所有父容器不会阻止弹幕 */
.simple-battle-container,
.simple-battle-container .gallery-mode,
.simple-battle-container .battle-comment-wall {
  overflow: visible !important;
  contain: none !important;
}
</style>

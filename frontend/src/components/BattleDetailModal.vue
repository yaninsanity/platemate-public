<!-- 
🎮 Kinny's Battle Detail Modal
=============================
gamified modal dedicated to showing detailed battle_result data

功能：
- 显示胜负结果和专用消息
- 展示完整的battle_result数据
- 游戏化UI设计
- 响应式布局
-->

<template>
  <v-dialog
    v-model="internalShow"
    max-width="600"
    persistent
    scrollable
  >
    <v-card class="battle-detail-card">
      <!-- Header -->
      <v-card-title class="battle-header">
        <div class="header-content">
          <v-icon size="24" color="orange">mdi-sword-cross</v-icon>
          <span class="title-text">🎮 KINNY'S ARENA BATTLE REPORT</span>
          <v-btn
            icon
            size="small"
            color="grey"
            variant="text"
            @click="closeModal"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>
      </v-card-title>

      <v-card-text class="battle-content">
        <template v-if="battleResult">
          <!-- Winner Announcement -->
          <div class="winner-section">
            <div class="winner-banner" :class="{ victory: winner, defeat: !winner }">
              <v-icon size="32" :color="winner ? 'gold' : 'silver'">
                {{ winner ? 'mdi-crown' : 'mdi-shield' }}
              </v-icon>
              <h2 class="winner-title">
                {{ winner ? '🏆 VICTORY ACHIEVED!' : '💪 BRAVE BATTLE!' }}
              </h2>
            </div>
          </div>

          <!-- Kinny's Message -->
          <div class="kinny-message-section">
            <div class="message-card" :class="{ winner: winner, loser: !winner }">
              <div class="message-header">
                <v-avatar size="32">
                  <v-icon color="orange">mdi-robot</v-icon>
                </v-avatar>
                <span class="kinny-label">Kinny says:</span>
              </div>
              <p class="kinny-text">
                {{ winner ? battleResult.kinny_winner_message : battleResult.kinny_loser_message }}
              </p>
            </div>
          </div>

          <!-- Battle Reason -->
          <div v-if="battleResult.reason" class="reason-section">
            <div class="section-header">
              <v-icon color="purple">mdi-chart-line</v-icon>
              <span>Battle Analysis</span>
            </div>
            <div class="reason-card">
              <p class="reason-text">{{ battleResult.reason }}</p>
            </div>
          </div>

          <!-- Couple Story -->
          <div v-if="battleResult.kinny_couple_story" class="story-section">
            <div class="section-header">
              <v-icon color="pink">mdi-heart</v-icon>
              <span>Your Cooking Journey</span>
            </div>
            <div class="story-card">
              <p class="story-text">{{ battleResult.kinny_couple_story }}</p>
            </div>
          </div>

          <!-- Future Cooking Suggestions -->
          <div v-if="battleResult.future_cooking_suggestions?.length" class="suggestions-section">
            <div class="section-header">
              <v-icon color="green">mdi-lightbulb</v-icon>
              <span>Next Level Tips</span>
            </div>
            <div class="suggestions-grid">
              <div
                v-for="(suggestion, index) in battleResult.future_cooking_suggestions"
                :key="index"
                class="suggestion-card"
              >
                <div class="suggestion-number">{{ index + 1 }}</div>
                <p class="suggestion-text">{{ suggestion }}</p>
              </div>
            </div>
          </div>

          <!-- Recipe Information -->
          <div v-if="battleResult.recipe_name" class="recipe-section">
            <div class="section-header">
              <v-icon color="amber">mdi-chef-hat</v-icon>
              <span>Battle Recipe</span>
            </div>
            <v-chip color="amber" variant="elevated" size="large">
              {{ battleResult.recipe_name }}
            </v-chip>
          </div>
        </template>

        <template v-else>
          <div class="no-data-section">
            <v-icon size="64" color="grey">mdi-robot-confused</v-icon>
            <h3>No Battle Data Available</h3>
            <p>Kinny is still analyzing this battle...</p>
          </div>
        </template>
      </v-card-text>

      <!-- Footer Actions -->
      <v-card-actions class="battle-footer">
        <v-spacer />
        <v-btn
          color="orange"
          variant="elevated"
          @click="closeModal"
        >
          <v-icon start>mdi-check</v-icon>
          Got it!
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useUserStore } from '@/stores/userStore'

interface Props {
  modelValue: boolean
  battleResult?: any
  winner?: boolean
}

interface Emits {
  (event: 'update:modelValue', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const userStore = useUserStore()

const internalShow = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const closeModal = () => {
  internalShow.value = false
}
</script>

<style scoped>
/* Battle Detail Card */
.battle-detail-card {
  background: linear-gradient(145deg, #0f0f23 0%, #1a1a3a 50%, #2d1b69 100%);
  color: white;
  border: 2px solid #4c1d95;
  border-radius: 1rem;
  overflow: hidden;
}

/* Header */
.battle-header {
  background: linear-gradient(135deg, #7c3aed, #5b21b6);
  border-bottom: 1px solid #8b5cf6;
  padding: 1rem;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.title-text {
  flex: 1;
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Content */
.battle-content {
  padding: 1.5rem;
  max-height: 70vh;
  overflow-y: auto;
}

/* Winner Section */
.winner-section {
  margin-bottom: 2rem;
}

.winner-banner {
  text-align: center;
  padding: 1.5rem;
  border-radius: 1rem;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(21, 128, 61, 0.1));
  border: 2px solid #22c55e;
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
}

.winner-banner.victory {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.3), rgba(245, 158, 11, 0.2));
  border-color: #fbbf24;
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4);
}

.winner-banner.defeat {
  background: linear-gradient(135deg, rgba(148, 163, 184, 0.2), rgba(100, 116, 139, 0.1));
  border-color: #64748b;
  box-shadow: 0 4px 12px rgba(148, 163, 184, 0.3);
}

.winner-title {
  margin: 0.5rem 0 0 0;
  font-size: 1.5rem;
  font-weight: 900;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

/* Kinny Message */
.kinny-message-section {
  margin-bottom: 2rem;
}

.message-card {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(124, 58, 237, 0.1));
  border: 1px solid #8b5cf6;
  border-radius: 0.75rem;
  padding: 1rem;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.message-card.winner {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(21, 128, 61, 0.1));
  border-color: #22c55e;
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
}

.message-card.loser {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(219, 39, 119, 0.1));
  border-color: #ec4899;
  box-shadow: 0 2px 8px rgba(236, 72, 153, 0.3);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.kinny-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.kinny-text {
  font-size: 1rem;
  line-height: 1.6;
  color: #f1f5f9;
  margin: 0;
  font-style: italic;
}

/* Section Headers */
.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Reason Section */
.reason-section {
  margin-bottom: 2rem;
}

.reason-card {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid #475569;
  border-radius: 0.5rem;
  padding: 0.75rem;
}

.reason-text {
  font-size: 0.875rem;
  line-height: 1.5;
  color: #e2e8f0;
  margin: 0;
}

/* Story Section */
.story-section {
  margin-bottom: 2rem;
}

.story-card {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.1), rgba(219, 39, 119, 0.05));
  border: 1px solid rgba(236, 72, 153, 0.3);
  border-radius: 0.5rem;
  padding: 0.75rem;
}

.story-text {
  font-size: 0.875rem;
  line-height: 1.5;
  color: #f8fafc;
  margin: 0;
  font-style: italic;
}

/* Suggestions Section */
.suggestions-section {
  margin-bottom: 2rem;
}

.suggestions-grid {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: 1fr;
}

.suggestion-card {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 0.5rem;
  padding: 0.75rem;
}

.suggestion-number {
  flex-shrink: 0;
  width: 1.5rem;
  height: 1.5rem;
  background: #22c55e;
  color: #064e3b;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
}

.suggestion-text {
  font-size: 0.875rem;
  line-height: 1.5;
  color: #dcfce7;
  margin: 0;
}

/* Recipe Section */
.recipe-section {
  margin-bottom: 1rem;
  text-align: center;
}

/* No Data Section */
.no-data-section {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}

.no-data-section h3 {
  margin: 1rem 0 0.5rem 0;
  color: #d1d5db;
}

.no-data-section p {
  margin: 0;
  font-size: 0.875rem;
}

/* Footer */
.battle-footer {
  background: rgba(30, 41, 59, 0.8);
  border-top: 1px solid #475569;
  padding: 1rem 1.5rem;
}

/* Mobile Optimizations */
@media (max-width: 640px) {
  .battle-content {
    padding: 1rem;
    max-height: 60vh;
  }
  
  .winner-banner {
    padding: 1rem;
  }
  
  .winner-title {
    font-size: 1.25rem;
  }
  
  .suggestions-grid {
    gap: 0.5rem;
  }
  
  .suggestion-card {
    padding: 0.5rem;
  }
  
  .title-text {
    font-size: 0.875rem;
  }
}
</style>

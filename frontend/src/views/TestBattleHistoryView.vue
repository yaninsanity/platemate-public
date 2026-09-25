<template>
  <div class="test-container">
    <h2>Roundly Battle History - Before & After</h2>
    
    <div class="preview-section">
      <h3>✨ New Love Kitchen Design</h3>
      <RoundlyBattleHistoryView />
    </div>
  </div>
</template>

<script setup lang="ts">
import RoundlyBattleHistoryView from './RoundlyBattleHistoryView.vue'
</script>

<style scoped>
.test-container {
  padding: 2rem;
  background: #f5f5f5;
  min-height: 100vh;
}

.preview-section {
  margin-bottom: 3rem;
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 2rem;
}

h3 {
  color: #666;
  margin-bottom: 1rem;
}
</style>

<template>
  <div class="stat" :class="{'critical': value < 30}">
    <v-icon :icon="icon" :color="value < 30 ? 'error' : color" size="16" />
    <div class="progress-container">
      <v-progress-linear
        :model-value="value"
        :max="100"
        height="4"
        :color="value < 30 ? 'error' : color"
        class="bar"
      />
      <span class="stat-value" :style="{'color': value < 30 ? 'var(--error-color)' : color}">{{ value }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ icon: string; value: number; color: string }>()
</script>

<style scoped>
.stat {
  flex: 1 1 0;                /* 允许收缩，平均占行宽 */
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 0;               /* ⬅ 防止进度条被 flex 算法撑大 */
  position: relative;
}
.progress-container {
  position: relative;
  width: 100%;
}
.bar { 
  width: 100%;
  border-radius: 2px;
}
.stat-value {
  position: absolute;
  right: -2px;
  top: -22px;
  font-size: 15px;
  font-weight: bold;
}
.critical .bar :deep(.v-progress-linear__determinate) {
  background-color: #f44336 !important;
}
</style>
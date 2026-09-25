<template>
  <div class="overlay">
    <span class="checkmark">✔️</span>
  </div>
</template>

<script setup lang="ts">
// 纯展示，无逻辑
</script>

<style scoped>
.overlay {
  position: absolute;
  top: 0;
  right: 0;
  width: 3rem;
  height: 3rem;
  background: rgba(16, 185, 129, 0.85); /* emerald-500 半透明 */
  border-bottom-left-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transform: translate(25%, -25%);
  pointer-events: none;
}
.checkmark {
  font-size: 1.5rem;
  color: white;
  text-shadow: 0 0 4px rgba(0,0,0,0.4);
}
</style>

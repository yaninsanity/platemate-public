<template>
  <div class="notice-container">
    <div class="scroll-wrapper">
      <div class="scroll-content">
        <!-- First render of messages -->
        <span
          v-for="(message, index) in messages"
          :key="'first-' + index"
          class="notice-message"
        >
          {{ message }}
        </span>
        <!-- Duplicate for seamless scroll -->
        <span
          v-for="(message, index) in messages"
          :key="'second-' + index"
          class="notice-message"
        >
          {{ message }}
        </span>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ScrollNotice',
  props: {
    messages: {
      type: Array as () => string[],
      required: true,
    },
    interval: {
      type: Number,
      default: 5000,
    },
  },
  setup() {
    return {}
  },
})
</script>

<style scoped>
.notice-container {
  width: 100%;
  overflow: hidden;
  background: linear-gradient(90deg, #d7ccc8, #bcaaa4);
  position: relative;
  padding: 4px 12px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  box-sizing: border-box;
}

.notice-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: -50%;
  width: 200%;
  height: 100%;
  background: linear-gradient(120deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transform: skewX(-25deg);
  animation: shimmer 2s infinite;
  pointer-events: none;
}

@keyframes shimmer {
  0% { left: -50%; }
  100% { left: 100%; }
}

.scroll-wrapper {
  width: 100%;
  overflow: hidden;
}

.scroll-content {
  display: flex;
  align-items: center;
  animation: scroll 30s linear infinite;
}

.notice-message {
  font-size: 0.95rem;
  font-weight: 700;
  color: #3e2723;
  text-shadow: 1px 1px 3px rgba(255, 255, 255, 0.7), 0 0 10px rgba(0, 0, 0, 0.1);
  white-space: nowrap;
  margin-right: 32px;
  position: relative;
}

.notice-message::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(62, 39, 35, 0.5), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}

.notice-message:hover::after { opacity: 1; }

@keyframes scroll {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}

@media (max-width: 768px) {
  .notice-message { font-size: 0.9rem; margin-right: 24px; }
}
</style>

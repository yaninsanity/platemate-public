<!-- Mobiletuning的空厨师位 -->
<template>
  <div class="empty-chef-slot">
    <div class="chef-placeholder">
      <div class="chef-icon">👨‍🍳</div>
      <div class="chef-name">{{ chefName }}</div>
      <div class="status-text">hasn't cooked</div>
    </div>
    
    <button @click="onRemind" class="remind-btn-compact">
      <span class="btn-icon">🔔</span>
      <span class="btn-text">Remind</span>
    </button>
  </div>
</template>

<script setup lang="ts">
interface Props {
  chefName: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  remind: [chefName: string]
}>()

const onRemind = () => {
  emit('remind', props.chefName)
}
</script>

<style scoped>
.empty-chef-slot {
  width: 100%;
  height: 140px; /* 更紧凑的高度 */
  background: rgba(255, 255, 255, 0.08);
  border: 1px dashed rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.empty-chef-slot::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  animation: shimmer 3s infinite;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

.chef-placeholder {
  text-align: center;
  opacity: 0.8;
}

.chef-icon {
  font-size: 1.8rem;
  margin-bottom: 4px;
  animation: float 2s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.chef-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 2px;
}

.status-text {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  font-style: italic;
}

.remind-btn-compact {
  background: linear-gradient(135deg, #ff6b6b, #ff8e53);
  border: none;
  color: white;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
  min-width: 80px;
}

.remind-btn-compact:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
  background: linear-gradient(135deg, #ff5252, #ff7043);
}

.remind-btn-compact:active {
  transform: translateY(0);
}

.btn-icon {
  font-size: 0.8rem;
  animation: ring 2s infinite;
}

@keyframes ring {
  0%, 90%, 100% { transform: rotate(0deg); }
  5%, 15% { transform: rotate(10deg); }
  10% { transform: rotate(-10deg); }
}

.btn-text {
  font-size: 0.7rem;
}

/* Mobiletuning */
@media (max-width: 768px) {
  .empty-chef-slot {
    height: 120px;
  }
  
  .chef-icon {
    font-size: 1.5rem;
  }
  
  .chef-name {
    font-size: 0.8rem;
  }
  
  .remind-btn-compact {
    padding: 5px 10px;
    min-width: 70px;
  }
  
  .btn-text {
    font-size: 0.65rem;
  }
}

@media (max-width: 480px) {
  .empty-chef-slot {
    height: 100px;
    gap: 8px;
  }
  
  .chef-icon {
    font-size: 1.3rem;
  }
  
  .chef-name {
    font-size: 0.75rem;
  }
  
  .status-text {
    font-size: 0.7rem;
  }
  
  .remind-btn-compact {
    padding: 4px 8px;
    min-width: 60px;
    gap: 2px;
  }
  
  .btn-icon {
    font-size: 0.7rem;
  }
  
  .btn-text {
    font-size: 0.6rem;
  }
}
</style>

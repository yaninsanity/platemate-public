<template>
  <div class="inventory-total" role="status" aria-live="polite">
    <div class="total-bg"></div>
    <div class="total-content">
      <div class="icon">🎒</div>
      <div class="label">Inventory</div>
      <div class="value">{{ totalItems }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePetStore } from '@/stores/petStore'

type InventoryItem = { quantity?: number } & Record<string, any>

const petStore = usePetStore()

// Sum all quantities; fallback to 0 if store not ready
const totalItems = computed(() => {
  const items = (petStore.foodInventory as InventoryItem[] | undefined) ?? []
  return items.reduce((sum, it) => sum + (Number(it?.quantity) || 0), 0)
})
</script>

<style scoped>
.inventory-total {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 14px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(255,255,255,0.25), rgba(255,255,255,0.15));
  border: 2px solid rgba(255,255,255,0.5);
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  overflow: hidden;
  backdrop-filter: blur(16px) saturate(1.4);
}

.total-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.25), transparent 60%),
              radial-gradient(circle at 70% 70%, rgba(255,255,255,0.2), transparent 60%);
  pointer-events: none;
}

.total-content { 
  position: relative; 
  display: inline-flex; 
  align-items: center; 
  gap: 10px; 
}

.icon { font-size: 16px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)); }
.label { 
  font-weight: 800; 
  color: #ffffff; 
  letter-spacing: 1px; 
  text-transform: uppercase; 
  font-size: 12px; 
  text-shadow: 0 2px 6px rgba(0,0,0,0.4);
}
.value { 
  font-weight: 900; 
  font-size: 16px; 
  color: #fff; 
  padding: 2px 8px; 
  background: linear-gradient(135deg, #4ecdc4, #44a08d); 
  border-radius: 12px; 
  border: 2px solid rgba(255,255,255,0.7);
  text-shadow: 0 3px 8px rgba(0,0,0,0.5);
}

@media (max-width: 480px) {
  .inventory-total { padding: 6px 12px; border-width: 1.5px; }
  .label { font-size: 11px; }
  .value { font-size: 14px; }
}
</style>

<template>
  <button
    class="petfood-card"
    :disabled="count === 0"
    @click="feed"
    title="Feed your pet!"
  >
    <!-- ① 食物图片 -->
    <img :src="fruitImg" alt="Pet food" class="food-img" />

    <!-- ② 余量数字 -->
    <span class="qty" :class="{ zero: count === 0 }">{{ count }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref } from "vue"
import fruitImg from "/assets/fruit.png"   // 根据你的路径调整

/* 余量（默认 6）——纯前端状态，不持久化 */
const count = ref(6)

/* 点击后 -1（不少于 0） */
function feed() {
  if (count.value > 0) count.value--
}
</script>

<style scoped>
/* 基础卡片 */
.petfood-card{
  position:relative;display:inline-flex;justify-content:center;align-items:center;
  width:7rem;height:7rem;margin:.5rem;border-radius:1rem;background:#fff;cursor:pointer;
  box-shadow:0 5px 14px rgba(0,0,0,.08);transition:.2s;
}
.petfood-card:disabled{cursor:default;opacity:.5;filter:grayscale(.2)}
.petfood-card:not(:disabled):hover{transform:translateY(-3px);box-shadow:0 8px 18px rgba(0,0,0,.12)}

/* 食物图 */
.food-img{width:70%;height:70%;object-fit:contain;user-select:none;pointer-events:none}

/* 数字徽章 */
.qty{
  position:absolute;bottom:.45rem;right:.55rem;
  min-width:1.9rem;padding:.1rem .2rem;border-radius:1.1rem;
  background:#f59e0b;color:#fff;font-weight:700;font-size:.8rem;text-align:center;
  box-shadow:0 2px 6px rgba(0,0,0,.18);
  transition:.25s;
}
.qty.zero{background:#9ca3af}
</style>

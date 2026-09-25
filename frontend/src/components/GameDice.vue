<!-- src/components/GameDice.vue -->
<template>
  <div class="dice-panel">
    <!-- ——— 单颗骰子 ——— -->
    <div
      class="slot"
      @pointerdown="pressed = true"
      @pointerup="pressed = false"
    >
      <transition name="fade" mode="out-in">
        <!-- rolling 动画 -->
        <img
          v-if="rolling"
          src="/assets/dice-roll.gif"
          class="die-gif"
          key="gif"
        />
        <!-- idle 按钮 -->
        <button
          v-else
          class="die-btn"
          :class="{ pressed, disabled: !hasDice }"
          :disabled="!hasDice"
          @click="roll"
          key="btn"
        >
          🎲
        </button>
      </transition>

      <!-- 数字徽标 -->
      <!-- <span v-if="balance" class="badge">{{ balance }}</span> -->

      <!-- sparkle -->
      <div v-if="spark" class="sparkles"></div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRecipesStore } from '@/stores/recipeStore'

const store    = useRecipesStore()
const balance  = computed(() => store.dice?.balance ?? 0)
const hasDice  = computed(() => balance.value > 0)

const rolling  = ref(false)
const pressed  = ref(false)
const spark    = ref(false)

onMounted(() => store.loadDice())

async function roll() {
  if (!hasDice.value || rolling.value) return
  rolling.value = true
  try {
    /* ↓ 调用 Pinia action（步骤 2 中补充）*/
    await store.reroll()
  } catch (err) {
    console.error('🎲 reroll failed:', err)
  }
  /* 700 ms 之后切换 sparkle */
  setTimeout(() => {
    rolling.value = false
    spark.value   = true
    setTimeout(() => (spark.value = false), 600)
  }, 700)
}
</script>

<style scoped>
:root { --size: 78px; }              /* 一处改尺寸 */

.dice-panel { display:flex; flex-direction:column; align-items:center; }

.slot { position:relative; width:var(--size); height:var(--size); }

.die-btn, .die-gif { width:100%; height:100%; border-radius:14px; display:flex;
  align-items:center; justify-content:center; font-size:3rem;
  background:linear-gradient(145deg,#102a49,#031021); border:2px solid #0b5cad;
  color:#d0e8ff; cursor:pointer; transition:transform .15s, box-shadow .15s;
  box-shadow:inset 0 0 6px rgba(0,255,255,.35),0 6px 12px rgba(0,0,0,.55); }

.die-btn.disabled{opacity:.38;cursor:not-allowed;}
.die-btn.pressed {transform:scale(.9);}
.die-btn:hover:not(.disabled){transform:rotateX(18deg) rotateY(-12deg) translateZ(6px);
  box-shadow:inset 0 0 10px rgba(0,255,255,.6),0 12px 24px rgba(0,0,0,.7); }

.die-gif { object-fit: contain; backface-visibility:hidden; animation:flip .4s ease-out; }
@keyframes flip{0%{transform:rotateY(90deg);opacity:0}60%{transform:rotateY(-12deg);opacity:1}}

.badge{position:absolute;bottom:-10px;right:-10px;min-width:30px;
  padding:2px 6px;background:#ffca28;color:#000;font-weight:700;font-size:.82rem;
  border-radius:16px;box-shadow:0 0 4px rgba(0,0,0,.6);}

@keyframes sparkle{0%{opacity:1;transform:scale(.5)}100%{opacity:0;transform:scale(2) translateY(-12px)}}
.sparkles{position:absolute;top:-12px;left:-12px;width:calc(100% + 24px);height:calc(100% + 24px);
  background:radial-gradient(circle,#00fff8 0,transparent 70%);border-radius:50%;
  pointer-events:none;animation:sparkle .6s ease-out forwards;}

.info{margin-top:12px;font-weight:600;
  background:linear-gradient(90deg,#00e0ff,#00ffb3);-webkit-background-clip:text;
  color:transparent;text-shadow:0 0 6px rgba(0,0,0,.45);}

.fade-enter-active,.fade-leave-active{transition:opacity .3s;}
.fade-enter-from,.fade-leave-to{opacity:0;}
</style>
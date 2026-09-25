<!-- src/components/TimeProgressBar.vue -->
<template>
  <div class="tpb" :class="wrapperClass">
    <!-- Hour-glass -->
    <span class="tpb__icon" :class="{ swing: isLast48h }">⏳</span>

    <!-- Bar -->
    <div class="tpb__bar">
      <div
        class="tpb__fill"
        :class="fillClass"
        :style="{ width: progressPercent + '%' }"
      />
    </div>

    <!-- Countdown -->
    <span class="tpb__time" :class="{ critical: isFinal1h }">
      {{ timeRemainingText }}
    </span>

    <!-- Badge -->
    <!-- <template v-if="rerolled">
      <span class="badge red">Rerolled</span>
    </template>
    <template v-else> -->
      <!-- <span v-if="inGoldenWindow && !isLast48h" class="badge green">Reroll</span> -->
      <span v-if="isLast24h && !isFinal1h" class="badge yellow pulse">24&nbsp;h Left</span>
      <span v-else-if="isFinal1h" class="badge red pulse-fast">⚡1&nbsp;h Left</span>
      <span v-else-if="isOver" class="badge gray">Locked</span>
      <span v-else class="badge green">Chill</span>
    <!-- </template> -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { DateTime } from 'luxon'
import { diffBreakdown } from '@/utils/tz'
import { useUserStore } from '@/stores/userStore'

/* ── Props ───────────────────────────────────────────── */
const props = defineProps<{ round: string; rerolled: boolean }>()

/* ── Zone (IANA)──────────────────────────────────────── */
const userStore = useUserStore()
const zone = computed(() => 'America/New_York') // Timezone fixed to EST
// const zone = computed(() => userStore.user?.timezone || DateTime.local().zoneName)

/* ── Reactive now ───────────────────────────────────── */
const now = ref(DateTime.local().setZone(zone.value))
onMounted(() => {
  const t = setInterval(() => (now.value = DateTime.local().setZone(zone.value)), 30_000)
  onUnmounted(() => clearInterval(t))
})

/* ── Base Start Day 00:00 *in zone* ───────────────────────
 * 传进来的 round = "YYYY-MM-DD"（周一），直接在玩家时区解析 */
const start = computed(() =>
  DateTime.fromISO(props.round, { zone: zone.value }).startOf('day')
)

/* ► goldenEnd = 48 h 后           */
const goldenEnd = computed(() => start.value.plus({ hours: 48 }))

/* ► roundEnd   = 3*24 h 后减 1 ms   */
const roundEnd  = computed(() => start.value.plus({ days: 7 }).minus({ millisecond: 1 }))


/* ── Remaining ms & windows ─────────────────────────── */
const msLeft      = computed(() => Math.max(0, roundEnd.value.diff(now.value).milliseconds))
const isLast48h   = computed(() => msLeft.value <= 48 * 3_600_000 && msLeft.value > 0)
const isLast24h   = computed(() => msLeft.value <= 24 * 3_600_000 && msLeft.value > 0)
const isFinal3h   = computed(() => msLeft.value <=  3 * 3_600_000 && msLeft.value > 0)
const isFinal1h   = computed(() => msLeft.value <=  1 * 3_600_000 && msLeft.value > 0)
const isOver      = computed(() => msLeft.value <= 0)
const inGoldenWindow = computed(() => now.value >= start.value && now.value < goldenEnd.value)

/* ── Progress [%] ───────────────────────────────────── */
const progressPercent = computed(() => {
  const total   = roundEnd.value.diff(start.value).milliseconds
  const elapsed = total - msLeft.value
  return Math.min(100, (elapsed / total) * 100)
})

/* ── Countdown text ─────────────────────────────────── */
const timeRemainingText = computed(() => {
  if (msLeft.value === 0) return '0 h'
  const { d, h, m } = diffBreakdown(msLeft.value)
  return isFinal1h.value ? `${m} m`
       : isFinal3h.value ? `${h} h ${m} m`
       : d              ? `${d} d ${h} h`
                        : `${h} h`
})

/* ── Dynamic class helpers ─────────────────────────── */
const wrapperClass = computed(() => ({
  rush   : isLast48h.value,
  danger : isFinal3h.value,
}))
const fillClass = computed(() => ({
  warn  : isLast48h.value,
  flash : isFinal3h.value,
  boom  : isFinal1h.value,
}))

/* ── Dev log (disabled in prod) ─────────────────────── */
if (import.meta.env.DEV) {
  console.info('[TPB] zone', zone.value,
    '| start', start.value.toISO(),
    '| roundEnd', roundEnd.value.toISO(),
    '| left(ms)', msLeft.value)
}
</script>

<style scoped>
/* ===== Wrapper & Icon ================================================= */
.tpb{display:flex;align-items:center;gap:.65rem;font-size:.8rem;font-weight:600;color:#374151} /* 🎯 增加gap和字体，提升可读性 */
.tpb__icon{font-size:1.05rem;display:inline-block;transform-origin:50% 90%}
.swing{animation:sandSwing 1.4s ease-in-out infinite}
@keyframes sandSwing{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(8deg)}}

/* ===== Progress bar =================================================== */
.tpb__bar{flex:1;min-width:120px;height:12px;position:relative;background:#e5e7eb;border-radius:6px;overflow:hidden;box-shadow:inset 0 0 3px rgba(0,0,0,.12)} /* 🎯 从48px→120px，高度10px→12px */
.tpb__fill{position:absolute;left:0;top:0;height:100%;background:linear-gradient(90deg,#8b5cf6 0%,#ec4899 100%);box-shadow:0 0 6px rgba(236,72,153,.6);transition:width .28s ease}
.warn {background:linear-gradient(90deg,#f59e0b 0%,#ef4444 100%);box-shadow:0 0 8px rgba(239,68,68,.7)}
.flash{background-image:repeating-linear-gradient(45deg,#ef4444 0 10px,#f59e0b 10px 20px);animation:stripeMove .6s linear infinite}
.boom {animation:boomFlash .9s steps(2) infinite}
@keyframes stripeMove{to{background-position:20px 0}}
@keyframes boomFlash{0%,100%{filter:brightness(1)}50%{filter:brightness(1.7)}}

/* ===== Time text ====================================================== */
.tpb__time{min-width:58px;text-align:right}
.critical{color:#b91c1c;font-weight:700;animation:textPulse .9s ease-in-out infinite}
@keyframes textPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}

/* ===== Badges ========================================================= */
.badge{padding:0 .5rem;border-radius:9999px;font-size:.74rem;font-weight:700;white-space:nowrap;box-shadow:0 1px 2px rgba(0,0,0,.12)}
.green {background:#bbf7d0;color:#065f46}
.red   {background:#fecaca;color:#7f1d1d}
.gray  {background:#e5e7eb;color:#374151}
.yellow{background:#fef9c3;color:#a16207}
.pulse      {animation:badgePulse 1.3s ease-in-out infinite}
.pulse-fast {animation:badgePulseFast .8s ease-in-out infinite}
@keyframes badgePulse{0%,100%{transform:scale(1)}50%{transform:scale(1.12)}}
@keyframes badgePulseFast{0%,100%{transform:scale(1)}50%{transform:scale(1.18)}}

/* ===== Icon glow states ============================================== */
.rush   .tpb__icon{filter:drop-shadow(0 0 2px #ef4444aa)}
.danger .tpb__icon{filter:drop-shadow(0 0 4px #ef4444ff)}
</style>

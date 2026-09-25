<!-- src/components/BaseLayout.vue -->
<template>
  <!-- fluid 让内容铺满；class 注入额外控制 -->
  <v-container
    :fluid="fluid"
    class="base-layout"
    :class="{
      'fill-screen': fillScreen,
      'px-0': noPadding,
    }"
  >
    <slot />
  </v-container>
</template>

<script setup lang="ts">
/**
 * Props:
 * - fillScreen: fills the viewport height, paired with a flex-column page
 * - noPadding:  remove the default 16px padding from v-container
 * - fluid:      是否全宽（默认为 true）
 */
const props = withDefaults(
  defineProps<{
    fillScreen?: boolean
    noPadding?: boolean
    fluid?: boolean
  }>(),
  { fillScreen: true, noPadding: false, fluid: true },
)
</script>

<style scoped>
/* fillScreen pages take the full height, alongside .d-flex / flex-col */
.fill-screen {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>

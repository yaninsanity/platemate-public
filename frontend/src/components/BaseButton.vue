<template>
  <v-btn
    :color="variant"
    :rounded="rounded"
    :block="block"
    class="base-button"
    @click="$emit('click', $event)"
  >
    <slot />
  </v-btn>
</template>

<script setup lang="ts">
import { PropType } from 'vue'
const props = defineProps({
  variant: { type: String as PropType<'primary'|'secondary'|'success'|'info'>, default: 'primary' },
  rounded: { type: Boolean, default: true },
  block:   { type: Boolean, default: false },
})
</script>

<style scoped>
.base-button { font-weight: 500; text-transform: none; }
</style>

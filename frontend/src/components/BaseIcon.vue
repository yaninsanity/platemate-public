<template>
  <v-icon :size="size" :color="color">{{ name }}</v-icon>
</template>

<script setup lang="ts">
import { PropType } from 'vue'
const props = defineProps({
  name:  { type: String, required: true },
  size:  { type: [Number,String] as PropType<number|string>, default: 24 },
  color: { type: String, default: 'primary' },
})
</script>

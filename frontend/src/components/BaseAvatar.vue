<template>
  <v-avatar size="48">
    <img :src="src" :alt="alt" />
  </v-avatar>
</template>
<script setup lang="ts">
import { PropType } from 'vue'
const props = defineProps({
  src: { type: String, required: true },
  alt: { type: String, default: 'avatar' },
})
</script>

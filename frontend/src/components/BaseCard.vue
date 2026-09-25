<template>
  <v-card class="base-card" :elevation="elevation">
    <v-card-title><slot name="title" /></v-card-title>
    <v-card-text><slot /></v-card-text>
    <v-card-actions><slot name="actions" /></v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { PropType } from 'vue'
const props = defineProps({
  elevation: { type: Number as PropType<0|2|4|8>, default: 2 },
})
</script>

<style scoped>
.base-card { border-radius: 12px; }
</style>

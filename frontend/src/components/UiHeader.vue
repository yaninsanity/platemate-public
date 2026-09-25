<!-- src/components/UiHeader.vue -->
<template>
  <header>
    <h1>{{ title }}</h1>
    <BaseButton @click="onClick">喂食一下</BaseButton>
  </header>
</template>

<script setup lang="ts">
const props = defineProps<{ title: string }>()

const onClick = () => {
  // Add your click handler logic here
}
</script>

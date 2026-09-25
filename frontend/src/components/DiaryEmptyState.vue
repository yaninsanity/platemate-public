<template>
  <div class="text-center text-gray-700 py-12">
    <p class="text-2xl mb-4">🐾 Your PlateMate is waiting for its first meal!</p>
    <p class="mb-6">No cooking battles yet. Whip up your first dish to feed your pet and earn some bragging rights!</p>
    <button
      @click="$emit('start')"
      class="bg-pink-500 text-white px-4 py-2 rounded shadow hover:bg-pink-600 transition"
    >Cook Now</button>
  </div>
</template>

<script setup>
// purely visual; emits "start" when button clicked
</script>

<style scoped>
/* customize empty state styles here */
</style>

<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white p-6 rounded-lg w-full max-w-md">
      <h2 class="text-xl font-semibold mb-4">Upload Your Dish (up to 4 pics)</h2>
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div
          v-for="(preview, idx) in previews"
          :key="idx"
          class="relative border rounded overflow-hidden cursor-pointer h-24 flex items-center justify-center"
          :class="{ 'border-pink-500': idx === selectedIndex }"
          @click="select(idx)"
        >
          <img
            v-if="preview"
            :src="preview"
            class="w-full h-full object-cover"
          />
          <div
            v-else
            class="text-gray-400 text-2xl"
          >
            +
          </div>
        </div>
      </div>
      <div class="flex justify-end space-x-2">
        <button @click="emitCancel" class="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">Cancel</button>
        <button
          @click="onSubmit"
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          :disabled="!isValid"
        >Submit</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Define emit types
const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'submit', files: File[], selected: number): void
}>()

// Local state
const previews = ref<(string | null)[]>([null, null, null, null])
const files = ref<(File | null)[]>([null, null, null, null])
const selectedIndex = ref(0)

// Valid when at least one file chosen
const isValid = computed(() => files.value.some(f => f !== null))

function select(idx: number) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = () => {
    const file = input.files?.[0] || null
    if (file) {
      files.value[idx] = file
      const reader = new FileReader()
      reader.onload = e => {
        previews.value[idx] = e.target?.result as string
      }
      reader.readAsDataURL(file)
      selectedIndex.value = idx
    }
  }
  input.click()
}

function onSubmit() {
  const chosen = files.value.filter((f): f is File => f !== null)
  emit('submit', chosen, selectedIndex.value)
}

function emitCancel() {
  emit('cancel')
}
</script>

<style scoped>
/* uploader modal styles */
</style>

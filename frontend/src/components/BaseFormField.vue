<!-- src/components/base/BaseFormField.vue -->
<template>
  <v-row class="mb-4" align="center">
    <v-col cols="12" md="4">
      <label class="font-weight-medium" :for="inputId">{{ label }}</label>
    </v-col>
    <v-col cols="12" md="8">
      <slot :id="inputId" />
      <v-messages v-if="errors" color="red">{{ errors }}</v-messages>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import { defineProps, computed } from 'vue'

const props = defineProps<{
  label: string
  errors?: string | string[]
}>()

const inputId = computed(() => `base-form-field-${Math.random().toString(36).substr(2, 9)}`)
</script>

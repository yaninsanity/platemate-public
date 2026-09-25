<!-- src/components/base/BaseSelect.vue -->
<template>
  <BaseFormField :label="label" :errors="errorMessages">
    <v-select
      v-model="modelValue"
      :items="items"
      :placeholder="placeholder"
      :rules="rules"
      :field="name"
      outlined
      dense
      hide-details="auto"
    />
  </BaseFormField>
</template>

<script setup lang="ts">
import { toRefs, watch } from 'vue'
import BaseFormField from './BaseFormField.vue'

const props = defineProps<{
  modelValue: any
  name: string
  label: string
  items: any[]
  placeholder?: string
  rules?: Array<(v: any) => boolean | string>
  errorMessages?: string | string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: any): void
}>()

const { modelValue } = toRefs(props)
watch(modelValue, val => emit('update:modelValue', val))
</script>

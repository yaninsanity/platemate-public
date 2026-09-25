<!-- src/components/base/BaseCheckbox.vue -->
<template>
  <BaseFormField :label="label" :errors="errorMessages">
    <v-checkbox
      v-model="modelValue"
      :label="checkboxLabel"
      :field="name"
      hide-details
      dense
    />
  </BaseFormField>
</template>

<script setup lang="ts">
import { toRefs, watch } from 'vue'
import BaseFormField from './BaseFormField.vue'

const props = defineProps<{
  modelValue: boolean
  name: string
  label: string
  checkboxLabel?: string
  errorMessages?: string | string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const { modelValue } = toRefs(props)
watch(modelValue, val => emit('update:modelValue', val))
</script>

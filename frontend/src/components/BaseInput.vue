<!-- src/components/BaseInput.vue -->
<template>
  <v-text-field
    v-bind="$attrs"                     
    :model-value="modelValue"           
    @update:modelValue="onUpdate"       
    :label="label"
    :placeholder="placeholder"
    :type="type"
    :rules="rules"
    :error-messages="errorMessages"
    :clearable="clearable"
    :prepend-inner-icon="prependInnerIcon"
    :append-inner-icon="appendInnerIcon"
    class="base-input"
  />
</template>

<script setup lang="ts">
import { withDefaults } from 'vue'

/* ---------------- props ---------------- */
const props = withDefaults(
  defineProps<{
    /** v-model 绑定值 */
    modelValue?: string | number
    label?: string
    placeholder?: string
    type?: 'text' | 'password' | 'email' | string
    rules?: Array<(v: any) => boolean | string>
    errorMessages?: string | string[]
    clearable?: boolean
    prependInnerIcon?: string
    appendInnerIcon?: string
  }>(),
  {
    modelValue: '',
    label: '',
    placeholder: '',
    type: 'text',
    rules: () => [],
    errorMessages: () => [],
    clearable: false,
    prependInnerIcon: '',
    appendInnerIcon: '',
  },
)

/* --------------- emits ----------------- */
const emit = defineEmits<{
  (e: 'update:modelValue', val: string | number): void
}>()

function onUpdate(val: string | number) {
  emit('update:modelValue', val)
}
</script>

<style scoped>
.base-input {
  width: 100%;
}
@media (max-width: 600px) {
  .base-input {
    font-size: 0.9rem;
  }
}
</style>

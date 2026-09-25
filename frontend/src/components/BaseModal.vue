<template>
  <v-dialog v-model="visible" max-width="400">
    <v-card>
      <v-card-title>{{ title }}</v-card-title>
      <v-card-text><slot /></v-card-text>
      <v-card-actions>
        <v-spacer/>
        <v-btn text @click="visible = false">Cancel</v-btn>
        <v-btn color="primary" @click="$emit('confirm')">OK</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup lang="ts">
import { ref, defineEmits, defineProps } from 'vue'
const props = defineProps({ title: String })
const emit  = defineEmits(['confirm'])
const visible = ref(true)
</script>

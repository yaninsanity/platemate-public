<template>
  <v-btn
    icon
    class="message-bell"
    color="deep-purple accent-4"
    elevation="8"
    @click="goMessages"
  >
    <v-badge
      :content="sms.unreadCount"
      :model-value="sms.hasUnread"
      overlap
      color="red"
    >
      <v-icon size="26">mdi-bell</v-icon>
    </v-badge>
  </v-btn>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter }             from 'vue-router'
import { useSMSStore }           from '@/stores/smsStore'

const router = useRouter()
const sms    = useSMSStore()

function goMessages() {
  router.push({ name: 'Messages' })
}

let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  sms.fetchUnreadCount()
  timer = setInterval(() => sms.fetchUnreadCount(), 15_000)
})
onUnmounted(() => { timer && clearInterval(timer) })
</script>

<style scoped>
.message-bell {
  position: fixed;
  top: calc(env(safe-area-inset-top) + 12px);
  right: 12px;
  z-index: 1000;
}
</style>

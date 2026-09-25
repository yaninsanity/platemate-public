<template>
  <v-app class="messages-view">
    <!-- 顶栏 -->
    <v-toolbar flat color="transparent" class="hud-bar">
      <v-btn icon @click="router.back()" aria-label="Back">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <v-toolbar-title class="text-h6">📬 Inbox</v-toolbar-title>
      <v-spacer/>
      <v-btn
        v-if="sms.hasUnread"
        color="primary"
        variant="text"
        :loading="marking"
        @click="markAll"
      >Mark all read</v-btn>
    </v-toolbar>

    <!-- 列表 -->
    <div class="content">
      <v-skeleton-loader v-if="sms.loading" type="card" class="my-4"/>
      <v-alert v-else-if="!sms.list.length" type="info" class="my-4">
        No messages yet. 📭
      </v-alert>
      <div v-else class="message-grid">
        <div
          v-for="item in sms.list"
          :key="item.id"
          class="msg-wrapper"
          :class="{ unread: !item.is_read }"
          @click="select(item)"
        >
          <v-card class="game-card" :elevation="item.is_read ? 2 : 6">
            <v-card-title>
              <v-icon :color="statusColor(item.status)">
                {{ statusIcon(item.status) }}
              </v-icon>
              <span class="ml-2 msg-text">{{ item.message }}</span>
            </v-card-title>
            <v-card-subtitle class="sub-text">{{ formatDate(item.created_at) }}</v-card-subtitle>
            <v-chip v-if="!item.is_read" small class="new-chip">NEW</v-chip>
          </v-card>
        </div>
      </div>
    </div>

    <!-- 高端玻璃拟态弹窗 -->
    <v-dialog
      v-model="detail.visible"
      persistent
      width="440"
      transition="dialog-transition"
    >
      <!-- 遮罩 -->
      <template #activator="{ on, attrs }"></template>
      <v-card class="glass-dialog" elevation="0">
        <v-toolbar flat dense class="dialog-header">
          <v-icon class="mr-2">mdi-email-open-outline</v-icon>
          <v-toolbar-title class="dialog-title">Message</v-toolbar-title>
          <v-spacer/>
          <v-btn icon @click="closeDetail">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        <v-card-text class="dialog-content">
          <p class="detail-msg">{{ detail.item.message }}</p>
          <p class="sub-text">Sent: {{ formatDate(detail.item.created_at) }}</p>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { useSMSStore } from '@/stores/smsStore'
import type { SMSRecord } from '@/models/sms'

const router = useRouter()
const sms    = useSMSStore()
const marking = ref(false)

const detail  = ref<{ visible: boolean; item: SMSRecord }>({
  visible: false,
  item: { id:0, message:'', status:'pending', is_read:true, created_at:'', phone_number:'' }
})

function formatDate(ts: string) {
  return dayjs(ts).format('MMM D, YYYY HH:mm')
}
function statusIcon(s: SMSRecord['status']) {
  return s === 'success' ? 'mdi-message-check-outline'
       : s === 'pending' ? 'mdi-timer-sand'
       : 'mdi-alert-circle-outline'
}
function statusColor(s: SMSRecord['status']) {
  return s === 'success' ? '#4CAF50'
       : s === 'pending' ? '#FB8C00'
       : '#F44336'
}

async function select(item: SMSRecord) {
  if (!item.is_read) {
    await sms.markRead(item.id)
  }
  detail.value = { visible: true, item }
}
function closeDetail() {
  detail.value.visible = false
}
async function markAll() {
  marking.value = true
  await sms.markAllRead()
  marking.value = false
}

let timer: ReturnType<typeof setInterval>
onMounted(async () => {
  await sms.fetchHistory()
  timer = setInterval(() => sms.fetchHistory(), 15000)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped lang="scss">
.messages-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f8ff, #e8f7ff);
  display: flex;
  flex-direction: column;
}

/* HUD */
.hud-bar {
  position: sticky;
  top: 0;
  backdrop-filter: blur(8px);
  background: rgba(255,255,255,0.6)!important;
  z-index: 5;
}

/* 列表 & 卡片 */
.content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}
.message-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
}
.msg-wrapper {
  cursor: pointer;
  transition: transform .15s;
}
.msg-wrapper:hover {
  transform: translateY(-3px);
}
.game-card {
  border-radius: 12px;
  background: #ffffffcc;
  backdrop-filter: blur(6px);
  transition: box-shadow .2s;
}
.card-unread {
  box-shadow: 0 0 0 2px #ff4081 inset;
}
.new-chip {
  background: #ff4081!important;
  color: #fff!important;
  margin-top: 4px;
}
.msg-text { font-size: .9rem; color: #333; }
.sub-text { font-size: .75rem; color: #666; margin-top: .3rem; }

/* 玻璃拟态弹窗 */
.glass-dialog {
  border-radius: 16px;
  background: rgba(255,255,255,0.4);
  backdrop-filter: blur(12px);
  overflow: hidden;
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
  transform-origin: center;
}
.dialog-header {
  background: transparent!important;
  border-bottom: 1px solid rgba(255,255,255,0.3);
}
.dialog-title {
  font-weight: 600;
  color: #333;
}
.dialog-content {
  padding: 1.25rem;
}
.detail-msg {
  font-size: 1rem;
  margin-bottom: .75rem;
  color: #222;
}

/* 弹框缩放淡入 */
.dialog-transition-enter-active,
.dialog-transition-leave-active {
  transition: all .25s ease;
}
.dialog-transition-enter-from {
  transform: scale(0.8);
  opacity: 0;
}
.dialog-transition-leave-to {
  transform: scale(0.8);
  opacity: 0;
}
</style>

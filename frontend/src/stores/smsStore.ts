// src/stores/smsStore.ts

import { defineStore } from 'pinia'
import api from '@/plugins/axios'
import type {
  SMSRecord,
  SMSStatus,
  SendSMSPayload,
  BulkSMSPayload,
  SendOTPPayload,
  VerifyOTPPayload,
  SMSHistoryQuery,
  SMSHistoryResponse,
  UnreadCountResponse,
} from '@/models/sms'

export const useSMSStore = defineStore('sms', {
  state: () => ({
    list        : [] as SMSRecord[],
    totalCount  : 0,
    unreadCount : 0,
    loading     : false,
    error       : null as string | null,
  }),

  getters: {
    hasUnread: (s) => s.unreadCount > 0,
    byStatus:
      (s) => (status: SMSStatus) =>
        s.list.filter(item => item.status === status),
  },

  actions: {
    /* ───────── 拉取历史列表 & 未读数 ───────── */
    async fetchHistory(params?: SMSHistoryQuery) {
      this.loading = true
      this.error   = null
      try {
        // 接口返回 { sms_list, total_count, unread_count }
        const { data } = await api.get<SMSHistoryResponse>('/sms/my-sms/', { params })
        this.list        = data.sms_list
        this.totalCount  = data.total_count
        this.unreadCount = data.unread_count
      } catch (e: any) {
        console.error('fetchHistory error', e)
        this.error = e?.response?.data?.message || e.message || 'Failed to load SMS'
      } finally {
        this.loading = false
      }
    },

    /* ───────── 单独拉取未读数 ───────── */
    async fetchUnreadCount() {
      try {
        const { data } = await api.get<UnreadCountResponse>('/sms/sms/unread-count/')
        this.unreadCount = data.unread_count
      } catch (e) {
        console.warn('fetchUnreadCount failed', e)
      }
    },

    /* ───────── 发送单条 SMS ───────── */
    async sendSMS(payload: SendSMSPayload) {
      try {
        const { data } = await api.post('/sms/send/', payload)
        return data
      } catch (e: any) {
        console.error('sendSMS error', e)
        throw e
      }
    },

    /* ───────── 群发 SMS ───────── */
    async bulkSend(payload: BulkSMSPayload) {
      try {
        const { data } = await api.post('/sms/bulk-send/', payload)
        return data
      } catch (e: any) {
        console.error('bulkSend error', e)
        throw e
      }
    },

    /* ───────── 发送 OTP ───────── */
    async sendOTP(payload: SendOTPPayload) {
      try {
        const { data } = await api.post('/sms/otp/send/', payload)
        return data
      } catch (e: any) {
        console.error('sendOTP error', e)
        throw e
      }
    },

    /* ───────── 验证 OTP ───────── */
    async verifyOTP(payload: VerifyOTPPayload) {
      try {
        const { data } = await api.post('/sms/otp/verify/', payload)
        return data
      } catch (e: any) {
        console.error('verifyOTP error', e)
        throw e
      }
    },

    /* ───────── 标记单条为已读 ───────── */
    async markRead(smsId: number) {
      try {
        await api.post(`/sms/sms/${smsId}/read/`)
        const msg = this.list.find(i => i.id === smsId)
        if (msg && !msg.is_read) {
          msg.is_read = true
          this.unreadCount = Math.max(0, this.unreadCount - 1)
        }
      } catch (e: any) {
        console.error('markRead error', e)
        throw e
      }
    },

    /* ───────── 标记全部为已读 ───────── */
    async markAllRead() {
      try {
        await api.post('/sms/sms/mark-all-read/')
        this.list.forEach(i => i.is_read = true)
        this.unreadCount = 0
      } catch (e: any) {
        console.error('markAllRead error', e)
        throw e
      }
    },

    /* ───────── 清空 Store（通常在登出时调用） ───────── */
    clear() {
      this.list        = []
      this.totalCount  = 0
      this.unreadCount = 0
      this.loading     = false
      this.error       = null
    },
  },
})

/* ────────────────────────────────────────────────────────────
 * 类型定义：与后端 SMS / OTP 接口保持一一对应
 * ──────────────────────────────────────────────────────────── */

/** 后端状态枚举 */
export type SMSStatus = 'success' | 'failed' | 'pending'

/** 单条 SMS 记录（列表 & 详情通用） */
export interface SMSRecord {
  id           : number
  phone_number : string
  message      : string
  status       : SMSStatus
  is_read      : boolean
  created_at   : string
  /* 可选错误信息 - 仅 status = failed 时后端可能返回 */
  error?       : string
}

/* ---------- 请求载荷 ---------- */
export interface SendSMSPayload {
  phone_number : string
  message      : string
  user_id?     : number
}

export interface BulkSMSPayload {
  user_ids : number[]
  message  : string
}

export interface SendOTPPayload {
  phone_number      : string
  purpose?          : string
  user_id?          : number
  message_template? : string
}

export interface VerifyOTPPayload {
  phone_number : string
  otp_code     : string
  purpose?     : string
  user_id?     : number
}

export interface SMSHistoryQuery {
  status?  : SMSStatus
  is_read? : boolean
  search?  : string
}

/* ---------- 响应 ---------- */
/** 返回和后端完全一致的结构 */
export interface SMSHistoryResponse {
  success     : boolean
  sms_list    : SMSRecord[]
  total_count : number
  unread_count: number
}

export interface UnreadCountResponse {
  unread_count : number
}

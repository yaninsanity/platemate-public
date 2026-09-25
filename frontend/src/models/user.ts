// src/models/user.ts

/**
 * 与后端 CustomUser 对应的接口
 */
export interface CustomUser {
  id: number
  username: string
  email: string
  first_name: string | null
  last_name: string | null
  bio: string | null
  birth_date: string | null        // ISO 日期
  phone: string | null
  phone_verified: boolean
  timezone: string
  sms_opt_in: boolean
  email_opt_in: boolean
  address: string | null
  role: string | null
  avatar_url: string | null        // 新增：头像 URL
  last_login: string | null        // ISO 时间
  date_joined: string              // ISO 时间
  couple_code: string | null       // 可选：用户所在couple的code
  coins?: number                   // 可选：后端若返回用户的金币数
  notifications_unread?: number    // 可选：未读通知数
  is_active?: boolean              // 可选：后端若返回用户是否激活
  is_online?: boolean              // 🟢 可选：后端计算的在线状态（基于Session）
}

/**
 * 与后端 Couple 对应的接口
 */
export interface Couple {
  id: number
  code: string
  name: string | null
  created_at: string                // ISO 时间
  members_count?: number            // 可选：后端若返回成员数
  is_complete?: boolean             // 可选：后端若返回是否完整
  members?: CustomUser[]            // 可选：嵌套成员列表
}

/**
 * 用于 joinCouple 的请求体
 */
export interface JoinCouplePayload {
  code: string
}

/* Basic model types coming from /api/petcare/ serializers */

export interface PetStatus {
  hunger   : number
  happiness: number
  hygiene  : number
  last_tick?: string           // 可选
}

export interface Pet {
  id       : number
  nickname : string
  skin     : string
  level    : number
  xp       : number
  next_level?: number          // 后端新加
  /* ── 两种格式 ── */
  /* A. 扁平字段（旧） */
  health?  : number
  energy?  : number
  hygiene? : number
  /* B. 嵌套 status（新） */
  status?  : PetStatus
}

export interface RewardBox {
  id: number
  kind: string
  opened_at: string | null
}

export interface Badge {
  slug: string        // 主键
  desc: string        // 徽章描述
  added: string       // ISO 字符串
}

export interface PetMessage {
  id: number
  title: string
  body: string
  is_read: boolean
  created_at: string
}

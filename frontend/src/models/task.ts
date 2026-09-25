/* ---------- 给组件使用的严格 Task ---------- */
export type Task = {
  id: number
  recipe?: number        // 任务里并不会用到，可留可去
  ingredient: {
    id: number
    name: string
    default_picture: string | null
    info: string
  }
  is_uploaded: boolean
  is_verified: boolean
  scanned_at: string | null
  created_at?: string      // ← 强制存在
  updated_at?: string      // ← 强制存在
  couple?: number
  user?: number            // ← 新增用户字段，确保用户级别验证
}

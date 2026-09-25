/* ──────────────────────────────────────────────
   轻量版数据结构 —— 保持与后端 serializer 对齐
   （the frontend may also attach local fields such as _loading and _error)
────────────────────────────────────────────── */

export interface RecipeLite {
  id: number
  name: string
  slug: string
  default_picture: string | null
}

export interface FamilyMenuEntry {
  /* 原生字段 */
  id          : number
  is_locked   : boolean
  unlocked_at : string | null

  /* 嵌套 menu */
  menu: {
    id             : number
    name           : string
    description    : string
    recipes_count  : number
  }

  /* 可选统计 */
  unlocked_recipes?: number

  /* 懒加载 */
  recipes?: RecipeLite[]

  /* —— 本地 UI 状态（Pinia 不会发给后端） —— */
  _loading?: boolean           // 正在拉取详情
  _error?  : string | null     // 拉详情失败
}

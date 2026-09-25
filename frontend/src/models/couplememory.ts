export interface MemoryMedia {
  id           : number
  media        : string
  url?         : string
  is_highlight?: boolean
  created_at   : string
}

export interface MemoryComment {
  id              : number
  entry           : number
  author          : number
  author_username?: string
  content         : string
  emoji?          : string
  created_at      : string
}

// 🤖 AIdetailed score payload, extended for the battle system
export interface AIJudgment {
  id                   : number
  overall_score        : number
  visual_appeal        : number
  cooking_technique    : number
  ingredient_freshness : number
  creativity_innovation?: number  // New enhanced metric
  nutrition_balance    ?: number  // New enhanced metric
  
  // ═══ Separated AI Comments System ═══
  individual_comment  ?: string   // 个人菜品评语
  individual_summary  ?: string   // 个人菜品总结
  battle_comment      ?: string   // 情侣PK评语
  battle_summary      ?: string   // 情侣PK总结
  battle_result       ?: {        // PK对战详细结果
    winner            : number
    reason            : string
    [key: string]     : any
  }
  
  // ═══ Legacy Compatibility ═══
  ai_comment           : string   // 向后兼容
  ai_summary           : string   // 向后兼容
  
  confidence           : number
  model_version        : string
  created_at           : string
  updated_at          ?: string
  mastery_level       ?: string   // New mastery level
  improvement_tips    ?: string[] // New improvement tips
  metrics_breakdown   ?: {        // Make optional for backward compatibility
    visual_appeal        : number
    cooking_technique    : number
    ingredient_freshness : number
    creativity_innovation?: number
    nutrition_balance    ?: number
  }
  average_metrics     ?: number   // Make optional for backward compatibility
  
  // ═══ Helper Properties ═══
  has_battle_data     ?: boolean  // 是否有PK数据
  effective_comment   ?: string   // 有效评语（优先个人）
  effective_summary   ?: string   // 有效总结（优先个人）
}

export const MOODS = ['nailed', 'grind', 'love', 'lucky', 'chaos'] as const
export type Mood = typeof MOODS[number]

export const moodEmoji: Record<Mood, string> = {
  nailed: '🏆',
  grind : '🛠',
  love  : '💖',
  lucky : '🎲',
  chaos : '🔥',
}

export interface MemoryEntry {
  id               : number
  memory           : number
  author           : number
  author_username? : string
  recipe?          : number | null
  recipe_name?     : string
  content          : string
  mood             : Mood
  ai_score?        : number | null
  best_media_url?  : string
  created_at       : string
  media            : MemoryMedia[]
  comments         : MemoryComment[]
  
  // 🤖 新的AI评分字段
  ai_judgment?     : AIJudgment | null
  effective_ai_score?: number | null
  ai_metrics?      : {
    visual_appeal       : number
    cooking_technique   : number
    ingredient_freshness: number
  } | null
}

export interface MemoryEntryMini {
  id              : number
  author_username?: string
  ai_score?       : number | null
  best_media_url?: string
  recipe_name?    : string
}

export interface CoupleMemory {
  id               : number
  couple           : number
  round_start       : string
  round_end         : string
  summary          : string
  battle_commentary?: string  // 🎮 New unified Kinny battle commentary
  cover_photo?     : string | null
  winner_entry?    : MemoryEntryMini | null
  total_points     : number
  entries_count    : number
  comments_count   : number
  top_ingredients?: TopIngredients
  entries          : MemoryEntry[]
  created_at?      : string
  updated_at?      : string
}

export interface TopIngredients {
  [recipeName: string]: number
}

// ═══════════════════════════════════════════════════════════════
// 🎮 Battle Arena System Types - 战斗竞技场系统专用类型
// ═══════════════════════════════════════════════════════════════

// 战斗照片接口
export interface BattlePhoto {
  url: string
  isHighlight?: boolean
  aiAnalysis?: {
    score: number
    reason: string
    category: string
  }
}

// 战斗用户接口
export interface BattleUser {
  name: string
  avatar?: string
  photos: BattlePhoto[]
  aiScore?: number | null
  battleStatus?: 'ready' | 'fighting' | 'winner' | 'defeated'
}

// AI评论接口（用于战斗系统）
export interface BattleAIComment {
  id: string
  type: 'positive' | 'neutral' | 'suggestion' | 'comparison' | 'technical'
  category: string
  text: string
  confidence: number
  insights?: string[]
}

// 战斗历史记录接口
export interface BattleHistoryItem {
  id: string
  date: string
  winner: string
  scoreA: number
  scoreB: number
}

// 战斗画廊状态接口
export interface BattleGalleryState {
  show: boolean
  fighter: string
  photos: BattlePhoto[]
  currentIndex: number
}

// ═══════════════════════════════════════════════════════════════
// 🎮 Extended Battle System Types - 扩展战斗系统类型
// ═══════════════════════════════════════════════════════════════

// 弹幕评论数据接口
export interface CommentData {
  id: string
  username: string
  text: string
  timestamp: number
  type?: 'praise' | 'suggestion' | 'cheer'
}

// AI评论数据接口（扩展版）
export interface AICommentData {
  id: string
  type: 'positive' | 'neutral' | 'suggestion' | 'comparison' | 'technical'
  category: string
  text: string
  detailedText?: string
  confidence: number
  timestamp?: string
  isAI?: boolean
  rawScore?: number | null
  author?: string
  metrics?: {
    visual_appeal: number
    cooking_technique: number
    ingredient_freshness: number
  }
}

export interface ChefBattleUser extends BattleUser {
  recipeName?: string
  ai_judgment?: {
    id: number
    overall_score: number
    visual_appeal: number
    cooking_technique: number
    ingredient_freshness: number
    ai_comment: string
    ai_summary: string
    confidence: number
    model_version: string
    created_at: string
  } | null
}

// 食谱信息接口
export interface RecipeInfo {
  winnerRecipe?: string | null
  topIngredients?: Record<string, number>
  coverPhoto?: string | null
  totalPoints?: number
  entriesCount?: number
}

// 周总结接口
export interface RoundSummary {
  roundStart?: string
  roundEnd?: string
  winner?: any
  totalPoints?: number
  commentsCount?: number
}

// 建议接口
export interface Suggestion {
  id: string
  target: string
  text: string
}

// battle user payload, the extended form used by FlexibleBattleGallery and similar components
export interface FlexibleBattleUser {
  name: string
  avatar?: string
  photos: BattlePhoto[]
  aiScore?: number | null
  recipeName?: string
  mood?: string
  content?: string
  entryId?: number
}
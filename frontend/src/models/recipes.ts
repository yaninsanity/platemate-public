/* eslint-disable @typescript-eslint/no-explicit-any */

/** 通用时间戳 + ID */
export interface TimeStamped {
  id: number
  created_at: string
  updated_at: string
}

/** Ingredient */
export interface Ingredient extends TimeStamped {
  name: string
  default_picture: string | null
  info: string
}

/** IngredientInRecipe */
export interface IngredientInRecipe extends TimeStamped {
  ingredient: Ingredient
  // the backend JSON omits ingredient_id, so it stays optional
  ingredient_id?: number
  quantity: string
}

/** RecipeIngredientTask */
export interface RecipeIngredientTask extends TimeStamped {
  id: number
  // recipe 只返回 ID
  recipe: number
  ingredient: Ingredient
  // 同理 ingredient_id 可选
  ingredient_id?: number
  quantity: string | null
  is_uploaded: boolean
  is_verified: boolean
  scanned_at: string | null
  couple?: number
  user: number
}

/** Recipe */
export interface Recipe extends TimeStamped {
  id: number
  name: string
  slug: string
  preparation: string
  instructions: string
  cuisine: string
  dish_type: string
  default_picture: string | null
  main_ingredient: number | null
  ingredient_count: number
  ingredients_detail: IngredientInRecipe[]
  family_recipes: any[]
}

/** RoundBracket */
export interface RoundBracket extends TimeStamped {
  round: string                  // 本周周一
  couple: number                // ★ 后端字段补上
  recipe: Recipe | null  // ★ 既可能是对象也可能是 ID
  active_recipe: Recipe | null  // Changed from 'recipe' to 'active_recipe'
  ingredient_tasks: RecipeIngredientTask[]
  rerolled: boolean
  rerolled_at: string | null
  roll_url?: string | null      // 兼容旧版
}

/** DicePocket */
export interface DicePocket {
  id: number
  balance: number
  updated: string
}

/** Reroll Response */
export interface RerollResponse {
  bracket: RoundBracket
  dice: DicePocket
}

/** CookingDiary */
export interface CookingDiary extends TimeStamped {
  couple: number
  recipe: Recipe
  recipe_id: number
  turn: number
  ai_summary: string | null
  winner: 'user1' | 'user2' | 'draw' | ''
}

/** CookingDiaryImage */
export interface CookingDiaryImage extends TimeStamped {
  diary: number
  uploader: number | null
  image: string
}

/** CookingDiaryEntry */
export interface CookingDiaryEntry extends TimeStamped {
  diary: number
  user: string
  user_id: number
  selected_image: number | null
  ai_score: number | null
  ai_feedback: string | null
}

/** Comment */
export interface Comment extends TimeStamped {
  diary: number
  author: string
  author_id: number
  content: string
  posted_at: string
}

/**
 * Analytics Tracking Utility - Clean & Precise Edition
 * =====================================================
 * 
 * 🎯 Design Principles:
 * 1. ONE function per user action (no overloaded functions)
 * 2. Clear naming: track{Action}{Target} (e.g., trackFeedPet, trackPlayGame)
 * 3. Required params first, optional params with defaults
 * 4. All metadata follows backend schema
 * 
 * 📊 Usage Pattern:
 * import { trackFeedPet, trackViewRecipeDetail } from '@/utils/analytics'
 * 
 * // In Vue component:
 * onMounted(() => {
 *   trackViewRecipeDetail(recipe.id, recipe.name, recipe.isFavorite)
 * })
 * 
 * async function feedPet() {
 *   const hungerBefore = pet.hunger
 *   await api.post(...)
 *   const hungerAfter = pet.hunger
 *   trackFeedPet(selectedFood, hungerBefore, hungerAfter, 'feed_panel')
 * }
 */

import api from '@/plugins/axios'

// ============================================================================
// 🔧 Core Tracking Infrastructure
// ============================================================================

interface EventMetadata {
  [key: string]: any
}

/**
 * Low-level event tracking function
 * @internal - Use specific track functions instead
 */
async function trackEvent(
  eventName: string,
  metadata: EventMetadata,
  durationMs?: number
): Promise<void> {
  try {
    await api.post('/analytics/track/', {
      event_name: eventName,
      metadata: metadata,
      duration_ms: durationMs,
      timestamp: new Date().toISOString(),
    })
    
    console.log('[Analytics] ✅ Tracked:', eventName, metadata)
  } catch (error) {
    // Silent failure - don't block user actions
    console.warn('[Analytics] ❌ Failed to track:', eventName, error)
  }
}

// ============================================================================
// 🐾 Pet Care Tracking Functions
// ============================================================================

/**
 * Track feeding pet
 * 
 * @param foodType - Food type (apple, banana, etc.)
 * @param hungerBefore - Hunger level before feeding (0-100)
 * @param hungerAfter - Hunger level after feeding (0-100)
 * @param sourceContext - Where feed action originated
 */
export function trackFeedPet(
  foodType: string,
  hungerBefore: number,
  hungerAfter: number,
  sourceContext: 'feed_panel' | 'game_reward' | 'auto_feed' = 'feed_panel'
): void {
  trackEvent('feed_pet', {
    resource_type: 'pet',
    food_type: foodType,
    hunger_before: hungerBefore,
    hunger_after: hungerAfter,
    source_context: sourceContext,
    hunger_increase: hungerAfter - hungerBefore,
  })
}

/**
 * Track opening feed panel
 * 
 * @param totalItems - Total food items in inventory
 * @param uniqueTypes - Number of unique food types
 * @param canHarvest - Whether user can harvest food
 */
export function trackOpenFeedPanel(
  totalItems: number,
  uniqueTypes: number,
  canHarvest?: boolean
): void {
  trackEvent('open_feed_panel', {
    resource_type: 'inventory',
    total_items: totalItems,
    unique_types: uniqueTypes,
    can_harvest: canHarvest,
  })
}

/**
 * Track checking game rewards inventory
 * 
 * @param totalItems - Total food items available
 * @param gameType - Type of game that gave rewards
 * @param rewardsEarned - List of rewards received
 */
export function trackCheckGameRewards(
  totalItems: number,
  gameType: string,
  rewardsEarned?: string[]
): void {
  trackEvent('check_game_rewards', {
    resource_type: 'inventory',
    total_items: totalItems,
    game_type: gameType,
    rewards_earned: rewardsEarned,
  })
}

/**
 * Track playing game with pet
 * 
 * @param gameType - Type of game (rock_paper_scissors, etc.)
 * @param result - Game outcome
 * @param energyUsed - Energy consumed
 * @param rewardsEarned - Rewards received from winning
 */
export function trackPlayGame(
  gameType: string,
  result: 'win' | 'lose' | 'draw',
  energyUsed?: number,
  rewardsEarned?: string[]
): void {
  trackEvent('play_game', {
    resource_type: 'game',
    game_type: gameType,
    result: result,
    energy_used: energyUsed,
    rewards_earned: rewardsEarned,
    rewards_count: rewardsEarned?.length || 0,
  })
}

/**
 * Track checking pet message
 * 
 * @param messageType - Type of message displayed
 * @param isNew - Whether message is new
 */
export function trackCheckPetMessage(
  messageType: string,
  isNew: boolean
): void {
  trackEvent('check_pet_message', {
    resource_type: 'pet_message',
    message_type: messageType,
    is_new: isNew,
  })
}

/**
 * Track daily check-in (slot machine)
 * 
 * @param rewardsEarned - List of food items received
 * @param slotResult - Slot machine result (jackpot/double/single)
 */
export function trackDailyCheckin(
  rewardsEarned: string[],
  slotResult: 'jackpot' | 'double' | 'single'
): void {
  trackEvent('daily_checkin', {
    resource_type: 'reward',
    rewards_earned: rewardsEarned,
    slot_result: slotResult,
    total_items: rewardsEarned.length,
  })
}

// ============================================================================
// 🍳 Recipe & Cooking Tracking Functions
// ============================================================================

/**
 * Track viewing recipe page (Step 1 & 2: RoundlyQuestView)
 * 
 * @param recipeId - Recipe ID
 * @param recipeName - Recipe name
 * @param hasRolledDice - Whether user rolled dice to get this recipe
 */
export function trackViewRecipePage(
  recipeId: number,
  recipeName?: string,
  hasRolledDice?: boolean
): void {
  trackEvent('view_recipe_page', {
    resource_type: 'recipe',
    resource_id: recipeId,
    recipe_id: recipeId,
    recipe_name: recipeName,
    has_rolled_dice: hasRolledDice,
  })
}

/**
 * Track viewing recipe reference in memory post (Step 3)
 * 
 * @param recipeId - Recipe ID
 * @param recipeName - Recipe name
 * @param step - Memory creation step
 */
export function trackViewRecipeReference(
  recipeId: number,
  recipeName: string,
  step: string = 'step3_cooking_reference'
): void {
  trackEvent('view_recipe_reference', {
    resource_type: 'recipe',
    resource_id: recipeId,
    recipe_id: recipeId,
    recipe_name: recipeName,
    step: step,
  })
}

/**
 * Track viewing battle history
 * 
 * @param battleCount - Number of battles displayed
 * @param filter - Filter applied (ongoing/completed/all)
 */
export function trackViewBattleHistory(
  battleCount: number,
  filter?: string
): void {
  trackEvent('view_battle_history', {
    resource_type: 'battle',
    battle_count: battleCount,
    filter: filter,
  })
}

/**
 * Track viewing battle detail
 * 
 * @param roundId - Battle round ID (for aggregation)
 * @param participantCount - Number of participants
 * @param commentCount - Number of comments
 */
export function trackViewBattleDetail(
  roundId: number,
  participantCount: number,
  commentCount: number
): void {
  trackEvent('view_battle_detail', {
    resource_type: 'battle_round',
    resource_id: roundId,
    round_id: roundId,
    participant_count: participantCount,
    comment_count: commentCount,
  })
}

// ============================================================================
// 💑 Memory & Diary Tracking Functions
// ============================================================================

/**
 * Track viewing diary page (Step 3 & 4: MemoryPostView)
 * 
 * @param recipeId - Recipe ID being referenced
 * @param recipeName - Recipe name
 * @param hasExistingMemories - Whether user has existing memories
 */
export function trackViewDiaryPage(
  recipeId: number,
  recipeName?: string,
  hasExistingMemories?: boolean
): void {
  trackEvent('view_diary_page', {
    resource_type: 'memory',
    recipe_id: recipeId,
    recipe_name: recipeName,
    has_existing_memories: hasExistingMemories,
  })
}

/**
 * Track viewing memory list
 * 
 * @param memoryCount - Total number of memories
 * @param hasMemories - Whether user has memories
 * @param filter - Filter applied
 */
export function trackViewMemoryList(
  memoryCount: number,
  hasMemories: boolean,
  filter?: string
): void {
  trackEvent('view_memory_list', {
    resource_type: 'memory',
    memory_count: memoryCount,
    has_memories: hasMemories,
    filter: filter,
  })
}

/**
 * Track viewing memory detail
 * 
 * @param memoryId - Memory ID
 * @param hasComments - Whether memory has comments
 * @param commentCount - Number of comments
 */
export function trackViewMemoryDetail(
  memoryId: number,
  hasComments?: boolean,
  commentCount?: number
): void {
  trackEvent('view_memory_detail', {
    resource_type: 'memory',
    resource_id: memoryId,
    memory_id: memoryId,
    has_comments: hasComments,
    comment_count: commentCount,
  })
}

// ============================================================================
// 💬 Social Tracking Functions
// ============================================================================

/**
 * Track posting comment
 * 
 * @param context - Context where comment was posted
 * @param resourceId - ID of resource being commented on
 * @param commentLength - Length of comment text
 * @param hasEmoji - Whether comment contains emoji
 * @param hasMention - Whether comment mentions other users
 */
export function trackPostComment(
  context: 'battle' | 'recipe' | 'memory',
  resourceId: number,
  commentLength: number,
  hasEmoji?: boolean,
  hasMention?: boolean
): void {
  trackEvent('post_comment', {
    resource_type: 'comment',
    context: context,
    resource_id: resourceId,
    comment_length: commentLength,
    has_emoji: hasEmoji,
    has_mention: hasMention,
  })
}

// ============================================================================
// 🛒 Shopping Tracking Functions
// ============================================================================

/**
 * Track searching for stores
 * 
 * @param searchQuery - Search query text
 * @param resultCount - Number of results found
 * @param searchDurationMs - How long search took
 * @param userLocation - User's location (if available)
 */
export function trackSearchStores(
  searchQuery: string,
  resultCount: number,
  searchDurationMs?: number,
  userLocation?: { lat: number; lng: number }
): void {
  trackEvent('search_stores', {
    resource_type: 'store',
    search_query: searchQuery,
    result_count: resultCount,
    search_duration_ms: searchDurationMs,
    user_location: userLocation,
  }, searchDurationMs)
}

// ============================================================================
// 🌍 Timezone Tracking Functions
// ============================================================================

/**
 * Track checking time lag
 * 
 * @param yourTimezone - User's timezone
 * @param partnerTimezone - Partner's timezone
 * @param timeDifferenceHours - Time difference in hours
 * @param partnerOnline - Whether partner is online
 */
export function trackCheckTimeLag(
  yourTimezone: string,
  partnerTimezone: string,
  timeDifferenceHours: number,
  partnerOnline?: boolean
): void {
  trackEvent('check_time_lag', {
    resource_type: 'timezone',
    your_timezone: yourTimezone,
    partner_timezone: partnerTimezone,
    time_difference_hours: timeDifferenceHours,
    partner_online: partnerOnline,
  })
}

// ============================================================================
// 🤖 AI Tracking Functions
// ============================================================================

/**
 * Track AI food detection
 * 
 * @param imageSize - Size of uploaded image (KB)
 * @param confidence - AI confidence score (0-1)
 * @param detectedItems - List of detected food items
 * @param detectionTimeMs - Detection processing time
 */
export function trackDetectFoodImage(
  imageSize: number,
  confidence: number,
  detectedItems: string[],
  detectionTimeMs?: number
): void {
  trackEvent('detect_food_image', {
    resource_type: 'ai_interaction',
    image_size: imageSize,
    confidence: confidence,
    detected_items: detectedItems,
    detection_count: detectedItems.length,
  }, detectionTimeMs)
}

/**
 * Track starting AI chat
 * 
 * @param chatContext - Context of chat initiation
 */
export function trackStartAIChat(chatContext?: string): void {
  trackEvent('start_ai_chat', {
    resource_type: 'ai_interaction',
    chat_context: chatContext,
  })
}

/**
 * Track sending AI message
 * 
 * @param messageLength - Length of user message
 * @param responseLength - Length of AI response
 * @param conversationTurn - Turn number in conversation
 * @param responseTimeMs - AI response time
 */
export function trackSendAIMessage(
  messageLength: number,
  responseLength: number,
  conversationTurn: number,
  responseTimeMs?: number
): void {
  trackEvent('send_ai_message', {
    resource_type: 'ai_interaction',
    message_length: messageLength,
    response_length: responseLength,
    conversation_turn: conversationTurn,
  }, responseTimeMs)
}

// ============================================================================
// 📊 Helper Functions
// ============================================================================

/**
 * Check if emoji exists in text
 */
export function containsEmoji(text: string): boolean {
  return /[\u{1F300}-\u{1F9FF}]/u.test(text)
}

/**
 * Check if text mentions users
 */
export function containsMention(text: string): boolean {
  return text.includes('@')
}

/**
 * Calculate time difference between timezones
 */
export function calculateTimeDifference(tz1: string, tz2: string): number {
  // This is a simplified calculation - use proper timezone library in production
  const now = new Date()
  const offset1 = new Date(now.toLocaleString('en-US', { timeZone: tz1 })).getTime()
  const offset2 = new Date(now.toLocaleString('en-US', { timeZone: tz2 })).getTime()
  return Math.round((offset2 - offset1) / (1000 * 60 * 60))
}

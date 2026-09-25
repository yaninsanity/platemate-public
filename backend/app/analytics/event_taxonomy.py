"""
PlateMate Analytics Event Taxonomy - Clean & Precise Edition
============================================================

🎯 Design Principles:
1. Every event has ONE clear purpose
2. Event names follow pattern: {verb}_{noun}_{context?}
3. Frontend explicit tracking for user actions
4. Backend auto-tracking for system events
5. No deprecated events - clean slate

📊 Event Naming Convention:
- User Actions: {action}_{target} (e.g., feed_pet, create_memory)
- Page Views: view_{page}_{type?} (e.g., view_recipe_list, view_recipe_detail)
- System Events: {system}_{action} (e.g., api_request, session_start)

🔍 Tracking Strategy:
- HIGH PRIORITY: Explicit frontend tracking with full context
- MEDIUM PRIORITY: Backend auto-tracking with path mapping
- LOW PRIORITY: Generic fallback events (page_view, api_request)
"""

# ============================================================================
# 🎯 PRECISE USER ACTION EVENTS (Frontend Explicit Tracking)
# ============================================================================

USER_ACTION_EVENTS = {
    # ========== Pet Care Actions ==========
    'pet_care': {
        'display_name': 'Pet Care',
        'description': 'Virtual pet interactions - feeding, playing, rewards',
        'color': '#e83e8c',
        'icon': '🐾',
        'events': [
            # Feed Actions
            ('feed_pet', 'Feed Pet', 'User feeds pet with food item'),
            
            # Inventory Management
            ('open_feed_panel', 'Open Feed Panel', 'User opens feed panel to check food inventory'),
            ('check_game_rewards', 'Check Game Rewards', 'Game system checks reward inventory after win'),
            ('harvest_food', 'Harvest Food', 'User harvests food from inventory'),
            
            # Games
            ('play_game', 'Play Game with Pet', 'User plays mini-game with pet'),
            
            # Rewards
            ('daily_checkin', 'Daily Check-in', 'User claims daily reward (slot machine)'),
            ('open_reward_box', 'Open Reward Box', 'User opens reward chest'),
            
            # Messages
            ('check_pet_message', 'Check Pet Message', 'User views pet status message'),
        ]
    },
    
    # ========== Recipe & Cooking ==========
    'recipes': {
        'display_name': 'Recipes & Cooking',
        'description': 'Recipe browsing, cooking tasks, and battle participation',
        'color': '#fd7e14',
        'icon': '🍳',
        'events': [
            # Recipe Browsing (RoundlyQuestView - Step 1 & 2)
            ('view_recipe_page', 'View Recipe Page', 'User views recipe page (Step 1 & 2: Roll dice + View recipe)'),
            
            # Memory Creation (MemoryPostView - Step 3)
            ('view_recipe_reference', 'View Recipe Reference', 'User references recipe in memory post (Step 3: Cooking reference)'),
            
            # Battle/Bracket
            ('view_battle_history', 'View Battle History', 'User browses past cooking battles'),
            ('view_battle_detail', 'View Battle Detail', 'User views specific battle round'),
            ('check_battle_bracket', 'Check Battle Bracket', 'User checks weekly battle bracket status'),
            
            # Tasks & Resources
            ('verify_cooking_task', 'Verify Cooking Task', 'User submits task for verification'),
            ('query_recipe_tasks', 'Query Recipe Tasks', 'User queries tasks for specific recipe'),
            ('check_dice_pocket', 'Check Dice Pocket', 'User checks dice balance'),
        ]
    },
    
    # ========== Memory & Diary ==========
    'memories': {
        'display_name': 'Couple Memories',
        'description': 'Shared couple memories and photo diaries',
        'color': '#20c997',
        'icon': '💑',
        'events': [
            # Memory Creation Flow (MemoryPostView - Step 3 & 4)
            ('view_diary_page', 'View Diary Page', 'User views diary/memory page (Step 3 & 4: Recipe reference + Composer)'),
            
            # Memory List & Detail
            ('view_memory_list', 'View Memory List', 'User browses memory timeline'),
            ('view_memory_detail', 'View Memory Detail', 'User views specific memory post'),
            
            # Memory Actions
            ('create_memory', 'Create Memory', 'User successfully creates new memory'),
            ('edit_memory', 'Edit Memory', 'User edits existing memory'),
            ('delete_memory', 'Delete Memory', 'User deletes memory'),
        ]
    },
    
    # ========== Social Interactions ==========
    'social': {
        'display_name': 'Social Interactions',
        'description': 'Comments, sharing, and engagement',
        'color': '#6f42c1',
        'icon': '💬',
        'events': [
            ('post_comment', 'Post Comment', 'User posts comment on battle/recipe/memory'),
            ('like_content', 'Like Content', 'User likes a post/battle/recipe'),
            ('share_content', 'Share Content', 'User shares content externally'),
        ]
    },
    
    # ========== Shopping & Discovery ==========
    'shopping': {
        'display_name': 'Shopping',
        'description': 'Store search and shopping features',
        'color': '#28a745',
        'icon': '🛒',
        'events': [
            ('search_stores', 'Search Stores', 'User searches for nearby stores'),
            ('view_store_detail', 'View Store Detail', 'User views store information'),
            ('save_store', 'Save Store', 'User bookmarks store location'),
        ]
    },
    
    # ========== Timezone Features ==========
    'timezone': {
        'display_name': 'Timezone & Time',
        'description': 'Time zone checking and conversion',
        'color': '#17a2b8',
        'icon': '🌍',
        'events': [
            ('check_time_lag', 'Check Time Lag', 'User clicks clock to view time difference'),
        ]
    },
    
    # ========== AI Interactions ==========
    'ai': {
        'display_name': 'AI Assistant',
        'description': 'AI food detection and chat interactions',
        'color': '#6f42c1',
        'icon': '🤖',
        'events': [
            ('detect_food_image', 'Detect Food Image', 'AI analyzes uploaded food photo'),
            ('start_ai_chat', 'Start AI Chat', 'User initiates AI conversation'),
            ('send_ai_message', 'Send AI Message', 'User sends message to AI'),
            ('end_ai_chat', 'End AI Chat', 'User ends AI conversation'),
        ]
    },
}

# ============================================================================
# 🔧 SYSTEM EVENTS (Backend Auto-Tracking)
# ============================================================================

SYSTEM_EVENTS = {
    # ========== Authentication ==========
    'auth': {
        'display_name': 'Authentication',
        'description': 'User authentication and account management',
        'color': '#6c757d',
        'icon': '🔐',
        'events': [
            ('register_account', 'Register Account', 'User creates new account'),
            ('login', 'Login', 'User logs into account'),
            ('logout', 'Logout', 'User logs out'),
            ('refresh_token', 'Refresh Token', 'System refreshes auth token'),
            ('upload_avatar', 'Upload Avatar', 'User uploads profile picture'),
        ]
    },
    
    # ========== Session Management ==========
    'session': {
        'display_name': 'Sessions',
        'description': 'User session lifecycle',
        'color': '#007bff',
        'icon': '📊',
        'events': [
            ('session_start', 'Session Start', 'User starts new session'),
            ('session_end', 'Session End', 'User session expires'),
        ]
    },
    
    # ========== Generic Fallback ==========
    'system': {
        'display_name': 'System Events',
        'description': 'Generic system operations and fallback events',
        'color': '#6c757d',
        'icon': '⚙️',
        'events': [
            ('api_request', 'API Request', 'Generic API call (fallback)'),
            ('page_view', 'Page View', 'Generic page view (fallback)'),
            ('error', 'Error', 'Application error occurred'),
        ]
    },
}

# ============================================================================
# 📋 EVENT METADATA STANDARDS
# ============================================================================

EVENT_METADATA_SCHEMA = {
    # Pet Care Events
    'feed_pet': {
        'required': ['food_type', 'hunger_before', 'hunger_after'],
        'optional': ['source_context', 'feeding_method'],
    },
    'open_feed_panel': {
        'required': ['total_items', 'unique_types'],
        'optional': ['can_harvest'],
    },
    'check_game_rewards': {
        'required': ['total_items', 'game_type'],
        'optional': ['rewards_earned'],
    },
    'play_game': {
        'required': ['game_type', 'result'],
        'optional': ['energy_used', 'rewards_earned'],
    },
    
    # Recipe Events
    'view_recipe_page': {
        'required': ['recipe_id'],
        'optional': ['recipe_name', 'has_rolled_dice'],
    },
    'view_recipe_reference': {
        'required': ['recipe_id', 'step'],
        'optional': ['recipe_name'],
    },
    'view_battle_detail': {
        'required': ['round_id'],
        'optional': ['participant_count', 'comment_count'],
    },
    
    # Memory Events
    'view_diary_page': {
        'required': ['recipe_id'],
        'optional': ['recipe_name', 'has_existing_memories'],
    },
    'view_memory_list': {
        'required': ['memory_count', 'has_memories'],
        'optional': ['filter'],
    },
    'view_memory_detail': {
        'required': ['memory_id'],
        'optional': ['has_comments', 'comment_count'],
    },
    
    # Social Events
    'post_comment': {
        'required': ['context', 'resource_id', 'comment_length'],
        'optional': ['has_emoji', 'has_mention'],
    },
    
    # Shopping Events
    'search_stores': {
        'required': ['search_query', 'result_count'],
        'optional': ['search_duration_ms', 'user_location'],
    },
    
    # Timezone Events
    'check_time_lag': {
        'required': ['your_timezone', 'partner_timezone', 'time_difference_hours'],
        'optional': ['partner_online'],
    },
}

# ============================================================================
# 🎯 HELPER FUNCTIONS
# ============================================================================

def get_all_events():
    """Get combined list of all events (user actions + system events)"""
    all_events = {}
    all_events.update(USER_ACTION_EVENTS)
    all_events.update(SYSTEM_EVENTS)
    return all_events

def get_event_category(event_name):
    """Get category for a given event name"""
    for category, config in get_all_events().items():
        for event_tuple in config['events']:
            if event_tuple[0] == event_name:
                return category
    return 'system'

def is_important_event(event_name):
    """
    Determine if event is important for HCI research
    
    Important events = User actions that reveal behavior patterns
    """
    # All user action events are important
    user_action_event_names = []
    for category_config in USER_ACTION_EVENTS.values():
        for event_tuple in category_config['events']:
            user_action_event_names.append(event_tuple[0])
    
    # Plus critical auth events
    critical_system_events = ['register_account', 'login', 'logout']
    
    return event_name in user_action_event_names or event_name in critical_system_events

def should_track_duration(event_name):
    """
    Events that should measure duration (performance-critical operations)
    """
    duration_events = [
        # AI operations (potentially slow)
        'detect_food_image', 'send_ai_message',
        
        # Game operations
        'play_game', 'daily_checkin',
        
        # Page load performance
        'view_recipe_list', 'view_battle_history', 'view_memory_list',
        
        # Search operations
        'search_stores',
    ]
    return event_name in duration_events

def get_event_metadata_schema(event_name):
    """Get expected metadata schema for an event"""
    return EVENT_METADATA_SCHEMA.get(event_name, {})

def validate_event_metadata(event_name, metadata):
    """
    Validate that event has required metadata fields
    
    Returns: (is_valid, missing_fields)
    """
    schema = get_event_metadata_schema(event_name)
    required = schema.get('required', [])
    
    missing = [field for field in required if field not in metadata]
    is_valid = len(missing) == 0
    
    return is_valid, missing

# ============================================================================
# 📊 EVENT HIERARCHY (For Admin Filtering)
# ============================================================================

EVENT_HIERARCHY = {
    'User Actions': [
        'pet_care',
        'recipes',
        'memories',
        'social',
        'shopping',
        'timezone',
        'ai',
    ],
    'System Events': [
        'auth',
        'session',
        'system',
    ]
}

# ============================================================================
# 🎯 BEST PRACTICES
# ============================================================================

BEST_PRACTICES = """
# Analytics Best Practices

## When to Use Frontend Explicit Tracking
✅ User clicks a button (feed_pet, post_comment)
✅ User navigates to a page (view_recipe_list, view_memory_detail)
✅ User completes an action (play_game, search_stores)
✅ You need specific context (source_context, step, filter)

## When to Rely on Backend Auto-Tracking
✅ System operations (token_refresh, session_start)
✅ API success/failure monitoring
✅ Error tracking
✅ Fallback for unmapped endpoints

## Event Naming Rules
1. Use snake_case: feed_pet (not feedPet or feed-pet)
2. Start with verb: view_recipe, create_memory, check_time_lag
3. Be specific: view_recipe_detail (not view_recipe)
4. Avoid abbreviations: view_battle_detail (not view_btl_dtl)

## Metadata Standards
1. Always include resource_type and resource_id
2. Use consistent naming: recipe_id (not recipeId or recipe_ID)
3. Include context: source_context, step, action
4. Store IDs for aggregation: round_id, memory_id, recipe_id

## Avoid Common Pitfalls
❌ Don't track same event from both frontend and backend
❌ Don't use generic names (click, view, action)
❌ Don't forget to include context metadata
❌ Don't create events for every single API call
❌ Don't mix user actions with system events in same category

## Example: Good vs Bad

BAD:
event_name: "view"
metadata: {}

GOOD:
event_name: "view_recipe_detail"
metadata: {
  recipe_id: 123,
  recipe_name: "Pasta Carbonara",
  is_favorite: true,
  view_duration_ms: 15000
}
"""

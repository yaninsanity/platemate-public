"""
Analytics Middleware - Automatic Event Tracking

Zero-touch middleware that automatically tracks:
- Page views
- API calls
- User sessions (30-min timeout)
- Request/response metrics

Industrial-grade async tracking with minimal performance impact.

DATA GOVERNANCE:
- Deduplication: Prevents identical events within 2-second window
- Rate Limiting: Max 10 events/second per user
- Fingerprinting: Unique hash for each event to detect true duplicates
"""

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from datetime import timedelta
import threading
import json
import hashlib
import time
from collections import defaultdict, deque

from .models import UserEvent, UserSession, EventType


class AnalyticsMiddleware(MiddlewareMixin):
    """
    Automatic analytics tracking middleware with data governance.
    
    Tracks every request and creates UserEvent + UserSession records.
    Uses threading for async-like behavior without blocking requests.
    
    Data Governance Features:
    1. Deduplication: Block identical events within 2 seconds
    2. Rate Limiting: Max 10 events/second per user
    3. Event Fingerprinting: Detect true duplicates vs legitimate repeats
    """
    
    # Class-level cache for deduplication (thread-safe)
    _event_cache = {}  # {fingerprint: timestamp}
    _cache_lock = threading.Lock()
    _cache_max_size = 10000  # Prevent memory bloat
    
    # Rate limiting: {user_id: deque of timestamps}
    _rate_limit_cache = defaultdict(lambda: deque(maxlen=100))
    _rate_limit_lock = threading.Lock()
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Start background cache cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_cache_periodically, daemon=True)
        cleanup_thread.start()
    
    def process_request(self, request):
        """Mark request start time for duration calculation"""
        request._analytics_start_time = timezone.now()
        return None
    
    def process_response(self, request, response):
        """
        Track the request after response is ready.
        Runs in background thread to avoid blocking.
        """
        # 🎯 Check if analytics tracking is enabled via SystemConfig
        from system.models import SystemConfig
        if not SystemConfig.is_analytics_tracking_enabled():
            return response  # Analytics disabled - skip tracking
        
        # 🎯 Skip if this request was explicitly tracked by frontend (prevent double-counting)
        if getattr(request, '_analytics_explicitly_tracked', False):
            return response
        
        # Skip admin, static, and media requests
        if self._should_skip_tracking(request):
            return response
        
        # Track in background thread (async-like)
        thread = threading.Thread(
            target=self._track_request_async,
            args=(request, response)
        )
        thread.daemon = True
        thread.start()
        
        return response
    
    def _should_skip_tracking(self, request):
        """
        Precision filtering for academic research.
        
        CRITICAL FOR HCI RESEARCH:
        - Track ALL user-facing API calls (petcare, cookai, recipes, etc.)
        - Skip only: static files, media, admin UI (not admin API)
        
        This ensures we capture 100% of user interactions for behavior analysis.
        """
        path = request.path
        
        # Skip ONLY static resources and admin UI pages
        # Do NOT skip API endpoints under /admin/ (they may be user actions)
        skip_prefixes = [
            '/static/',           # Static files (CSS, JS, images)
            '/media/',            # User-uploaded media
            '/favicon.ico',       # Browser requests
            '/admin/jsi18n/',     # Admin translation files
            '/admin/autocomplete/',  # Admin autocomplete UI
        ]
        
        for skip_prefix in skip_prefixes:
            if path.startswith(skip_prefix):
                return True
        
        # Skip admin UI pages but NOT admin API calls
        # Admin UI pages usually end with /change/, /add/, etc.
        if path.startswith('/admin/'):
            # Check if it's a UI page vs API call
            ui_patterns = ['/change/', '/add/', '/delete/', '/changelist/']
            is_ui_page = any(pattern in path for pattern in ui_patterns)
            
            # Only skip UI pages, track admin API calls
            if is_ui_page and not path.endswith('/'):
                return True
        
        return False
    
    def _track_request_async(self, request, response):
        """
        Background tracking logic with data governance.
        Creates UserEvent and updates/creates UserSession.
        
        DATA GOVERNANCE CHECKS:
        1. Rate Limiting: Reject if user exceeds 10 events/second
        2. Deduplication: Skip if identical event within 2 seconds
        3. Fingerprinting: Create unique hash to detect duplicates
        """
        try:
            # Get or determine user
            user = request.user if request.user.is_authenticated else None
            user_id = user.id if user else None
            
            # ========== RATE LIMITING CHECK ==========
            if not self._check_rate_limit(user_id):
                import logging
                logger = logging.getLogger('analytics')
                logger.warning(f"🚫 Rate limit exceeded for user {user_id}")
                return  # Drop event - user is spamming
            
            # Calculate duration
            start_time = getattr(request, '_analytics_start_time', timezone.now())
            duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            
            # Determine event type based on request
            event_type = self._determine_event_type(request)
            if not event_type:
                return  # Skip if no matching event type
            
            # Extract metadata
            metadata = self._extract_metadata(request, response)
            
            # Get resource info
            resource_type = self._get_resource_type(request)
            resource_id = self._get_resource_id(request)
            
            # ========== EVENT FINGERPRINTING ==========
            fingerprint = self._create_event_fingerprint(
                user_id=user_id,
                event_type_id=event_type.id,
                resource_type=resource_type,
                resource_id=resource_id,
                path=request.path
            )
            
            # ========== DEDUPLICATION CHECK ==========
            if not self._is_unique_event(fingerprint):
                import logging
                logger = logging.getLogger('analytics')
                logger.info(f"⏭️ Duplicate event dropped: {event_type.name} for user {user_id}")
                return  # Skip duplicate
            
            # Determine status
            status = 'success' if 200 <= response.status_code < 400 else 'failed'
            error_message = None
            if status == 'failed':
                error_message = f"HTTP {response.status_code}"
            
            # Get or create session
            session_id = self._get_or_create_session(request, user)
            
            # Create UserEvent
            UserEvent.objects.create(
                user=user,
                event_type=event_type,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                session_id=session_id,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata=metadata,
                duration_ms=duration_ms,
                status=status,
                error_message=error_message
            )
            
            # Update session
            if user and session_id:
                self._update_session(user, session_id, duration_ms)
                
        except Exception as e:
            # Silent failure - don't break the request
            import logging
            logger = logging.getLogger('analytics')
            logger.error(f"Analytics tracking error: {e}")
    
    def _determine_event_type(self, request):
        """
        🎯 Map request path to EventType
        
        核心设计原则:
        1. captures all eleven core events without any frontend tracking
        2. supports aggregation across battle rounds
        3. 区分list view和detail view
        4. 捕获AI所有交互
        
        优先级顺序:
        1. Regex patterns (最精准 - battle detail, memory detail等)
        2. Exact path matching (完全匹配 - feed, play等)
        3. Prefix matching (前缀匹配 - inventory等)
        4. Generic fallback (兜底 - page_view等)
        """
        path = request.path.lower()
        method = request.method
        
        # ========================================================================
        # 🎯 PHASE 1: REGEX PATTERNS (最高优先级 - 精准匹配带ID的路径)
        # ========================================================================
        import re
        
        # 🎯 Battle Detail View (必须在battle history之前检查)
        # Match: /api/recipes/brackets/{id}/ (具体某个round)
        battle_detail_pattern = re.compile(r'^/api/recipes/brackets/(\d+)/?$')
        battle_match = battle_detail_pattern.match(path)
        if battle_match and method == 'GET':
            try:
                round_id = battle_match.group(1)
                request._analytics_round_id = round_id
                event_type = EventType.objects.get(name='view_battle_detail')
                request._event_type_name = 'view_battle_detail'
                logger.info(f'🎯 Battle Detail View: round_id={round_id}')
                return event_type
            except EventType.DoesNotExist:
                pass
        
        # 🎯 Memory Detail View
        # Match: /api/couplememory/memories/{id}/
        memory_detail_pattern = re.compile(r'^/api/couplememory/memories/(\d+)/?$')
        memory_match = memory_detail_pattern.match(path)
        if memory_match and method == 'GET':
            try:
                memory_id = memory_match.group(1)
                request._analytics_memory_id = memory_id
                event_type = EventType.objects.get(name='view_memory_detail')
                request._event_type_name = 'view_memory_detail'
                return event_type
            except EventType.DoesNotExist:
                pass
        
        # ========================================================================
        # 🎯 PHASE 2: EXACT PATH MATCHING (精确路径 - 核心操作)
        # ========================================================================
        
        # URL到Event的映射 - 完整的核心事件 + AI交互
        exact_map = {
            # ========== Pet Care (核心交互 - Backend自动采集) ==========
            # 🎯 Feed Pet
            '/api/petcare/pet/feed/': 'feed_pet',
            '/api/petcare/food-inventory/use-any/': 'feed_pet',  # 也是喂食行为
            
            # 🎯 Open Feed Panel
            '/api/petcare/food-inventory/': 'open_feed_panel' if method == 'GET' else None,
            
            # 🎯 Harvest Food
            '/api/petcare/food-inventory/harvest/': 'harvest_food',
            
            # 🎯 Play Game with Pet
            '/api/petcare/pet/play_game/': 'play_game',
            
            # 🎯 Daily Checkin
            '/api/petcare/food-inventory/checkin/': 'daily_checkin',
            
            # 🎯 Open Reward Box
            '/api/petcare/boxes/open/': 'open_reward_box',
            
            # 🎯 Check Pet Message
            '/api/petcare/pet-message-state/refresh/': 'check_pet_message',
            '/api/petcare/pet-message-state/': 'check_pet_message' if method == 'GET' else None,
            
            # Other Pet Actions
            '/api/petcare/food-inventory/use/': 'feed_pet',
            '/api/petcare/food-inventory/couple_comparison/': 'check_game_rewards',
            
            # ========== Recipe & Battle (Backend自动采集) ==========
            # 🎯 Check Battle Bracket Status (只在POST时)
            '/api/recipes/brackets/check/': 'check_battle_bracket' if method == 'POST' else None,
            
            # 🎯 Verify Cooking Task
            '/api/recipes/tasks/verify/': 'verify_cooking_task',
            
            # 🎯 Query Recipe Tasks (新增 - 查询食谱任务)
            '/api/recipes/tasks/by-recipe-enhanced/': 'query_recipe_tasks' if method == 'POST' else None,
            
            # 🎯 Check Dice Pocket (新增 - 查看骰子余额)
            '/api/recipes/dice-pocket/': 'check_dice_pocket' if method == 'GET' else None,
            
            # ========== AI Interactions (Backend自动采集) ==========
            '/api/cookai/detect/': 'detect_food_image',
            '/api/cookai/chat/start/': 'start_ai_chat',
            '/api/cookai/chat/message/': 'send_ai_message',
            '/api/cookai/chat/end/': 'end_ai_chat',
            
            # ========== Memory (POST创建由Backend采集) ==========
            '/api/couplememory/memories/': 'create_memory' if method == 'POST' else None,
            
            # ========== Shopping (Backend自动采集) ==========
            '/api/stores/find/': 'search_stores',
            
            # ========== Auth & Users (Backend自动采集) ==========
            '/api/users/auth/register/': 'register_account',
            '/api/users/auth/logout/': 'logout',
            '/api/token/': 'login',
            '/api/token/refresh/': 'refresh_token',
            '/api/avatar/': 'upload_avatar',
            '/api/users/me/couple/leave/': 'leave_couple',
            
            # ========== System ==========
            '/api/health/': 'health_check',
        }
        
        # 尝试完全匹配
        if path in exact_map:
            event_name = exact_map[path]
            try:
                event_type = EventType.objects.get(name=event_name)
                request._event_type_name = event_name
                return event_type
            except EventType.DoesNotExist:
                pass
        
        # ========================================================================
        # 🎯 PHASE 3: PREFIX MATCHING (前缀匹配 - 列表和查看操作)
        # ========================================================================
        
        # 🎯 精准改善: order matters: the detail pattern was handled in phase 1
        # 这里只处理list view (不带ID的路径)
        
        # Battle History (list) matches /api/recipes/brackets/ without an id
        if path == '/api/recipes/brackets/' and method == 'GET':
            try:
                event_type = EventType.objects.get(name='view_battle_history')
                request._event_type_name = 'view_battle_history'
                logger.info(f'🎯 Battle History View (list)')
                return event_type
            except EventType.DoesNotExist:
                pass
        
        # Memory List - matches /api/couplememory/memories/ without an id
        if path == '/api/couplememory/memories/' and method == 'GET':
            try:
                event_type = EventType.objects.get(name='view_memory_list')
                request._event_type_name = 'view_memory_list'
                return event_type
            except EventType.DoesNotExist:
                pass
        
        # ========================================================================
        # 🎯 PHASE 4: COMMENT TRACKING (评论系统)
        # ========================================================================
        
        # 🎯 11. User Comment
        # Match: POST to any comment endpoint
        comment_patterns = [
            '/api/recipes/brackets/',  # Battle comments
            '/api/couplememory/memories/',  # Memory comments
            '/api/recipes/recipes/',  # Recipe comments (if exists)
        ]
        
        if method == 'POST':
            for pattern in comment_patterns:
                if pattern in path and 'comment' in path:
                    try:
                        return EventType.objects.get(name='create_comment')
                    except EventType.DoesNotExist:
                        pass
        
        # ========================================================================
        # 🎯 PHASE 5: GENERIC FALLBACK ONLY
        # ========================================================================
        # page views are tracked explicitly by the frontend (trackViewRecipePage, trackViewDiaryPage等)
        # Middlewarea generic fallback only; no attempt to infer the page
        
        # Generic fallback based on method
        if method == 'GET':
            event_name = 'page_view'
        elif method == 'POST':
            event_name = 'api_request'
        else:
            event_name = 'api_request'
        
        try:
            event_type = EventType.objects.get(name=event_name)
            # 🎯 新增：设置事件类型名称，用于resource字段增强
            request._event_type_name = event_name
            return event_type
        except EventType.DoesNotExist:
            # if even the fallback event is missing, log it but let the request through
            import logging
            logger = logging.getLogger('analytics')
            logger.warning(f"Missing fallback event type: {event_name}")
            return None
            return None
    
    def _extract_metadata(self, request, response):
        """
        🎯 Extract rich metadata for deep analysis
        
        核心增强:
        1. 自动提取round_id, memory_id等关键ID (支持aggregation)
        2. 记录POST body关键字段（非敏感数据）
        3. 捕获AI响应质量指标
        4. 记录评论长度、emoji等用户行为细节
        5. 🎯 full URL information, which makes page-view events legible
        """
        metadata = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
        }
        
        # 🎯 full URL information, which page-view events previously lacked
        # 记录完整的请求URL，让用户知道具体访问了哪个页面
        full_url = request.build_absolute_uri()
        metadata['full_url'] = full_url
        
        # take the path without the query string, to identify the page
        from urllib.parse import urlparse
        parsed_url = urlparse(full_url)
        metadata['page_path'] = parsed_url.path
        
        # Add query params if present
        if request.GET:
            metadata['query_params'] = dict(request.GET)
        
        # ========================================================================
        # 🎯 pull the key, non-sensitive fields out of the POST body
        # ========================================================================
        if request.method == 'POST':
            try:
                import json
                # 尝试解析JSON body
                if hasattr(request, 'body') and request.body:
                    try:
                        body_data = json.loads(request.body.decode('utf-8'))
                        
                        # 🎯 Feed Pet - 记录食物类型和饥饿度
                        if 'food_type' in body_data:
                            metadata['food_type'] = body_data['food_type']
                        if 'hunger_before' in body_data:
                            metadata['hunger_before'] = body_data['hunger_before']
                        if 'hunger_after' in body_data:
                            metadata['hunger_after'] = body_data['hunger_after']
                        
                        # 🎯 Play Game - 记录游戏结果
                        if 'game_type' in body_data:
                            metadata['game_type'] = body_data['game_type']
                        if 'result' in body_data:
                            metadata['result'] = body_data['result']
                        
                        # 🎯 User Comment - 记录评论详情
                        if 'text' in body_data and 'comment' in request.path:
                            comment_text = body_data['text']
                            metadata['comment_length'] = len(comment_text)
                            # 检测emoji
                            import re
                            emoji_pattern = re.compile("["
                                u"\U0001F600-\U0001F64F"  # emoticons
                                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                u"\U0001F680-\U0001F6FF"  # transport & map
                                u"\U0001F1E0-\U0001F1FF"  # flags
                                "]+", flags=re.UNICODE)
                            metadata['has_emoji'] = bool(emoji_pattern.search(comment_text))
                        
                        # 🎯 AI Detection - 记录图片信息
                        if 'image' in request.FILES:
                            image_file = request.FILES['image']
                            metadata['image_size'] = image_file.size
                            metadata['image_type'] = image_file.content_type
                    
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        pass
            except Exception as e:
                pass
        
        # ========================================================================
        # 🎯 pull the interesting parts out of the response body, such as AI output and rewards
        # ========================================================================
        try:
            # 只对成功的响应提取数据
            if 200 <= response.status_code < 300:
                import json
                if hasattr(response, 'content') and response.content:
                    try:
                        response_data = json.loads(response.content.decode('utf-8'))
                        
                        # 🎯 AI Detection - 记录识别结果
                        if 'confidence' in response_data:
                            metadata['ai_confidence'] = response_data['confidence']
                        if 'items' in response_data and isinstance(response_data['items'], list):
                            metadata['detection_count'] = len(response_data['items'])
                            metadata['detected_items'] = [item.get('name', '') for item in response_data['items'][:5]]
                        
                        # 🎯 Collect Reward - 记录奖励内容
                        if 'rewards' in response_data:
                            rewards = response_data['rewards']
                            if isinstance(rewards, list):
                                metadata['reward_count'] = len(rewards)
                                metadata['reward_items'] = [r.get('item', '') for r in rewards[:5]]
                        
                        # 🎯 Battle/Memory list - 记录数量
                        if 'results' in response_data and isinstance(response_data['results'], list):
                            metadata['result_count'] = len(response_data['results'])
                        elif isinstance(response_data, list):
                            metadata['result_count'] = len(response_data)
                        
                        # 🎯 Pet status - 记录宠物状态
                        if 'hunger' in response_data:
                            metadata['pet_hunger'] = response_data['hunger']
                        if 'energy' in response_data:
                            metadata['pet_energy'] = response_data['energy']
                    
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        pass
        except Exception as e:
            pass
        
        # Add referer
        if request.META.get('HTTP_REFERER'):
            metadata['referer'] = request.META['HTTP_REFERER']
        
        # ========================================================================
        # 🎯 精准改善：从临时属性提取关键ID
        # ========================================================================
        # these ids are set in _determine_event_type and support aggregation
        if hasattr(request, '_analytics_round_id'):
            metadata['round_id'] = request._analytics_round_id
        if hasattr(request, '_analytics_memory_id'):
            metadata['memory_id'] = request._analytics_memory_id
        
        return metadata
    
    def _get_or_create_session(self, request, user):
        """
        Get or create session ID for user.
        Uses 30-minute timeout.
        """
        if not user:
            # Use Django session ID for anonymous users
            return request.session.session_key or 'anonymous'
        
        # Check for existing active session
        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        session = UserSession.objects.filter(
            user=user,
            last_activity_at__gte=thirty_min_ago,
            ended_at__isnull=True
        ).first()
        
        if session:
            return session.session_id
        
        # Create new session
        session_id = f"{user.id}_{timezone.now().timestamp()}"
        UserSession.objects.create(
            user=user,
            session_id=session_id,
            started_at=timezone.now(),
            last_activity_at=timezone.now(),
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            device_type=self._detect_device_type(request)
        )
        
        return session_id
    
    def _update_session(self, user, session_id, duration_ms):
        """Update existing session with new activity"""
        try:
            session = UserSession.objects.get(
                user=user,
                session_id=session_id,
                ended_at__isnull=True
            )
            
            session.last_activity_at = timezone.now()
            session.event_count += 1
            
            # Calculate total duration
            if session.started_at:
                total_seconds = (session.last_activity_at - session.started_at).total_seconds()
                session.duration_seconds = int(total_seconds)
            
            session.save()
            
        except UserSession.DoesNotExist:
            pass
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'
    
    def _detect_device_type(self, request):
        """Detect device type from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        else:
            return 'desktop'
    
    def _get_resource_type(self, request):
        """
        🎯 Determine resource type from path
        
        用于后期筛选和分析特定资源类型的事件
        """
        path = request.path.lower()
        
        # 🎯 richer resource information for API requests and page views, highest priority
        event_type_name = getattr(request, '_event_type_name', '')
        if path.startswith('/api/'):
            return 'api_endpoint'
        elif event_type_name == 'page_view':
            return 'page_url'
        
        # 精准匹配 - 按路径优先级排序
        if '/recipes/brackets/' in path:
            return 'battle_round'
        elif '/store' in path or '/shopping' in path:
            return 'store'
        elif '/cookai' in path or '/ai' in path:
            return 'ai_interaction'
        elif '/couplememory' in path or '/memories' in path:
            return 'memory'
        elif '/comment' in path:
            return 'comment'
        elif '/box' in path:
            return 'reward'
        elif '/message' in path:
            return 'pet_message'
        elif '/pet' in path or '/food-inventory' in path:
            return 'pet'
        elif '/recipe' in path:  # 这个条件放在最后，避免覆盖API条件
            return 'recipe'
        
        return None
    
    def _get_resource_id(self, request):
        """
        🎯 Extract resource ID from path or temp attributes
        
        prefer the transient attributes, falling back to a regex
        这确保了round_id, memory_id等关键ID能被正确提取用于aggregation
        """
        # 🎯 新增：为所有API请求提供完整的URL信息
        path = request.path.lower()
        if path.startswith('/api/'):
            # for API requests, resource_id holds the full path
            full_url = request.build_absolute_uri()
            return full_url
        
        # 🎯 新增：为页面访问提供完整的URL信息
        event_type_name = getattr(request, '_event_type_name', '')
        if event_type_name == 'page_view':
            # for page views, resource_id holds the full page URL
            full_url = request.build_absolute_uri()
            return full_url
        
        # prefer the transient attributes set in _determine_event_type
        if hasattr(request, '_analytics_round_id'):
            return request._analytics_round_id
        if hasattr(request, '_analytics_memory_id'):
            return request._analytics_memory_id
        
        # Fallback: Look for numeric ID in path like /api/recipes/123/
        import re
        match = re.search(r'/(\d+)/?', request.path)
        if match:
            return match.group(1)
        
        return None
    
    # ========================================
    # DATA GOVERNANCE METHODS
    # ========================================
    
    def _create_event_fingerprint(self, user_id, event_type_id, resource_type, resource_id, path):
        """
        ACADEMIC-GRADE DEDUPLICATION FINGERPRINTING
        
        Smart fingerprinting distinguishes:
        1. Legitimate repeated actions (feed pet 3 times in 10 seconds) ✅ TRACK ALL
        2. Frontend pollution (same API called twice from onMounted) ❌ BLOCK DUPLICATES
        
        Strategy:
        - For ACTION events (feed, play): Include timestamp bucket (1-second granularity)
          → Allows multiple actions per minute, blocks exact duplicates within 1 second
        - For VIEW events (page_view, view_*): Use full deduplication
          → Blocks repeated views within 2 seconds
        
        Examples:
        - user:123 + feed_pet + pet + t:1728123456 → Unique per second
        - user:123 + page_view + /home/ + t:1728123456 → Blocks rapid reloads
        """
        # Determine if this is an action event (should allow rapid succession)
        action_events = ['feed_pet', 'play_game', 'daily_checkin', 
                        'open_reward_box', 'detect_food_image', 'verify_cooking_task']
        
        # Get event type name for smart deduplication
        try:
            event_type = EventType.objects.get(id=event_type_id)
            event_name = event_type.name
            is_action_event = event_name in action_events
        except:
            is_action_event = False
        
        # Build fingerprint components
        components = [
            str(user_id or 'anon'),
            str(event_type_id),
            str(resource_type or ''),
            str(resource_id or ''),
            path
        ]
        
        # For action events, include timestamp bucket for per-second uniqueness
        if is_action_event:
            # Use 1-second buckets: allows 1 event per second, blocks millisecond duplicates
            timestamp_bucket = int(time.time())
            components.append(str(timestamp_bucket))
        
        fingerprint_string = '|'.join(components)
        return hashlib.md5(fingerprint_string.encode()).hexdigest()
    
    def _is_unique_event(self, fingerprint):
        """
        ACADEMIC-GRADE EVENT DEDUPLICATION
        
        Checks if event fingerprint is unique within time window.
        Works with smart fingerprinting to distinguish:
        - Legitimate repeated actions (different timestamp buckets) ✅
        - Frontend pollution (same fingerprint, rapid fire) ❌
        
        Uses thread-safe cache with automatic cleanup.
        
        Returns:
            True if unique (should track)
            False if duplicate (should skip for data quality)
        """
        now = time.time()
        deduplication_window = 0.5  # 500ms - catches frontend double-calls
        
        with self._cache_lock:
            # Check if fingerprint exists in cache
            if fingerprint in self._event_cache:
                last_seen = self._event_cache[fingerprint]
                
                # If within deduplication window, it's a duplicate
                if (now - last_seen) < deduplication_window:
                    return False  # Duplicate!
            
            # Update cache with current timestamp
            self._event_cache[fingerprint] = now
            
            # Prevent memory bloat - remove oldest if cache too large
            if len(self._event_cache) > self._cache_max_size:
                # Remove entries older than 10 seconds
                cutoff = now - 10
                self._event_cache = {
                    fp: ts for fp, ts in self._event_cache.items()
                    if ts > cutoff
                }
        
        return True  # Unique event
    
    def _check_rate_limit(self, user_id):
        """
        Check if user is within rate limit (max 10 events/second).
        
        Uses sliding window algorithm with deque.
        
        Returns:
            True if within limit (allow)
            False if exceeded (block)
        """
        if user_id is None:
            # Don't rate limit anonymous users (they might be different people)
            return True
        
        now = time.time()
        window = 1.0  # 1 second window
        max_events = 10
        
        with self._rate_limit_lock:
            # Get user's event timestamps
            timestamps = self._rate_limit_cache[user_id]
            
            # Remove timestamps outside window
            while timestamps and (now - timestamps[0]) > window:
                timestamps.popleft()
            
            # Check if within limit
            if len(timestamps) >= max_events:
                return False  # Rate limit exceeded!
            
            # Add current timestamp
            timestamps.append(now)
        
        return True  # Within limit
    
    def _cleanup_cache_periodically(self):
        """
        Background thread to cleanup stale cache entries.
        Runs every 60 seconds to prevent memory bloat.
        """
        while True:
            try:
                time.sleep(60)  # Run every minute
                
                now = time.time()
                cutoff = now - 10  # Remove entries older than 10 seconds
                
                with self._cache_lock:
                    original_size = len(self._event_cache)
                    self._event_cache = {
                        fp: ts for fp, ts in self._event_cache.items()
                        if ts > cutoff
                    }
                    cleaned = original_size - len(self._event_cache)
                    
                    if cleaned > 0:
                        import logging
                        logger = logging.getLogger('analytics')
                        logger.debug(f"🧹 Cleaned {cleaned} stale cache entries (cache size: {len(self._event_cache)})")
                
                # Also cleanup rate limit cache
                with self._rate_limit_lock:
                    # Remove users with no recent events
                    users_to_remove = []
                    for user_id, timestamps in self._rate_limit_cache.items():
                        if not timestamps or (now - timestamps[-1]) > 60:
                            users_to_remove.append(user_id)
                    
                    for user_id in users_to_remove:
                        del self._rate_limit_cache[user_id]
                        
            except Exception as e:
                import logging
                logger = logging.getLogger('analytics')
                logger.error(f"Cache cleanup error: {e}")
    
    def _cleanup_cache_periodically(self):
        """
        Background thread: Clean up expired cache entries every 5 minutes
        
        Prevents memory bloat by removing old fingerprints and rate limit records.
        """
import logging
from datetime import timedelta

from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import models
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

# CRITICAL FOR HCI RESEARCH: Import analytics tracking
from analytics.decorators import track_event

from users.models import Couple
from .models import (
    Pet, PetStatus, PetFeed,
    Activity,
    Mission,
    Reminder, ReminderRule,
    RewardBox,
    Badge,
    PetMessage,
    DicePocket,
    PetMessageTemplate,
    UserPetMessageState,
    FoodInventory,
)
from .serializers import (
    PetSerializer,
    PetFeedSerializer,
    ActivitySerializer,
    MissionSerializer,
    ReminderSerializer,
    ReminderRuleSerializer,
    RewardBoxSerializer,
    BadgeSerializer,
    PetMessageSerializer,
    DicePocketSerializer,
    PetMessageStateSerializer,
)

logger = logging.getLogger(__name__)


def _get_couple(user) -> Couple:
    """Helper: return the current user’s Couple or raise."""
    cp = getattr(user, "couple", None)
    if cp is None:
        raise PermissionDenied("User is not in a couple")
    return cp


def _get_pet(user) -> Pet:
    """Helper: return or create this couple’s Pet and its status."""
    cp = _get_couple(user)
    pet, _ = Pet.objects.get_or_create(couple=cp)
    PetStatus.objects.get_or_create(pet=pet)
    return pet


# ─────────────────────────────────────────────────────────────
# 1. Pet & PetStatus & PetFeed
# ─────────────────────────────────────────────────────────────
class PetViewSet(viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin):
    """
    GET    /pet/         → 列表当前用户夫妇的宠物（通常只有一只）
    GET    /pet/{id}/    → 查看单条
    PATCH  /pet/{id}/    → 更新 nickname / skin
    POST   /pet/feed/    → 给宠物喂食并加 XP
    POST   /pet/tick/    → 手动触发日常衰减（仅 Admin）
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = PetSerializer

    def get_queryset(self):
        cp = _get_couple(self.request.user)
        return Pet.objects.filter(couple=cp)

    def list(self, request, *args, **kwargs):
        """Apply decay before serializing all pets"""
        queryset = self.get_queryset()
        for pet in queryset:
            if hasattr(pet, 'status'):
                pet.status.check_and_apply_decay()
        return super().list(request, *args, **kwargs)

    def get_object(self):
        # 取第一只
        pet = self.get_queryset().first()
        if pet and hasattr(pet, 'status'):
            pet.status.check_and_apply_decay()  # Auto-apply decay when retrieving pet
        return pet

    @action(detail=False, methods=["post"])
    @track_event('feed_pet', category='pet', resource_type='pet', important=True)
    def feed(self, request):
        """
        POST /pet/feed/
        Body: {
          "points": <int,>=0>,
          "food_type": <str>,
          "amount": <int,>=1>
        }
        
        CRITICAL HCI EVENT: User feeds pet - core engagement action
        """
        # 参数校验
        try:
            pts  = max(0, int(request.data.get("points", 1)))
            amt  = max(1, int(request.data.get("amount", 1)))
            food = str(request.data.get("food_type", "treat")).strip() or "treat"
        except (TypeError, ValueError):
            return Response({"detail": "Invalid 'points' or 'amount'"}, status=status.HTTP_400_BAD_REQUEST)

        pet = _get_pet(request.user)

        # 记录喂食
        PetFeed.objects.create(couple=pet.couple, food_type=food, amount=amt)

        # 加 XP
        Pet.add_xp(pet.couple, pts)
        logger.info("Pet fed %s x%s (+%s XP) by %s", food, amt, pts, request.user.username)

        return Response(self.get_serializer(pet).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsAdminUser])
    def tick(self, request):
        """手动触发日常状态衰减"""
        PetStatus.daily_tick()
        return Response({"detail": "Daily decay applied"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    @track_event('play_with_pet', category='pet', resource_type='game', important=True)
    def play_game(self, request):
        """
        POST /pet/play_game/
        Body: {
          "game_type": "rock-paper-scissors",
          "result": "win|lose|draw", 
          "hunger_cost": 8
        }
        
        CRITICAL HCI EVENT: User plays game with pet - core engagement action
        """
        try:
            game_type = str(request.data.get("game_type", "unknown"))
            result = str(request.data.get("result", "lose"))
            hunger_cost = max(1, int(request.data.get("hunger_cost", 8)))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid game parameters"}, status=status.HTTP_400_BAD_REQUEST)

        pet = _get_pet(request.user)
        
        # Check if pet has enough hunger to play
        if pet.status.hunger < hunger_cost:
            return Response({
                "detail": f"Not enough hunger to play! Current: {pet.status.hunger}, Required: {hunger_cost}",
                "current_hunger": pet.status.hunger,
                "required_hunger": hunger_cost
            }, status=status.HTTP_400_BAD_REQUEST)

        # Apply hunger cost immediately - 移除win reward，胜利只给食物奖励
        original_hunger = pet.status.hunger
        pet.status.hunger = max(0, pet.status.hunger - hunger_cost)
        
        # 胜利时给予食物奖励，不再给hunger奖励避免重复
        food_reward = None
        if result == "win":
            # 连胜食物奖励系统
            import random
            # 计算连胜次数 (简化版，可以后续tuning)
            recent_activities = Activity.objects.filter(
                couple=pet.couple,
                kind=Activity.GAME,
                created__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # 基于连胜给予不同食物奖励到个人库存
            if recent_activities == 0:  # 首胜
                food_types = ['apple', 'banana']
                food_reward = random.choice(food_types)
                FoodInventory.add_food(request.user, food_reward, amount=1)
            elif recent_activities < 3:  # 连胜1-2次
                food_types = ['orange', 'strawberry']
                food_reward = random.choice(food_types)
                FoodInventory.add_food(request.user, food_reward, amount=2)
            elif recent_activities < 5:  # 连胜3-4次
                food_types = ['grapes', 'watermelon']
                food_reward = random.choice(food_types)
                FoodInventory.add_food(request.user, food_reward, amount=3)
            else:  # 连胜5+次
                food_types = ['pineapple', 'cherry']
                food_reward = random.choice(food_types)
                FoodInventory.add_food(request.user, food_reward, amount=4)
            
            # 记录游戏胜利活动
            Activity.create_generic(
                couple=pet.couple,
                kind=Activity.GAME,
                meta={'game_type': game_type, 'result': result, 'food_reward': food_reward, 'user_id': request.user.id}
            )
        
        pet.status.save()
        
        # Log the game activity
        logger.info("Game played: %s result=%s, hunger: %d->%d, food_reward=%s by %s", 
                   game_type, result, original_hunger, pet.status.hunger, food_reward, request.user.username)

        return Response({
            "result": result,
            "pet": self.get_serializer(pet).data,
            "hunger_cost": hunger_cost,
            "final_hunger": pet.status.hunger,
            "original_hunger": original_hunger,
            "food_reward": food_reward
        }, status=status.HTTP_200_OK)


class PetFeedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /pet/feeds/ → 拉取当前宠物的所有喂食记录
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = PetFeedSerializer

    def get_queryset(self):
        pet = _get_pet(self.request.user)
        return PetFeed.objects.filter(pet=pet)


# ─────────────────────────────────────────────────────────────
# 2. Activity
# ─────────────────────────────────────────────────────────────
class ActivityViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    GET /activities/ → 列表所有行为流水
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = ActivitySerializer

    def get_queryset(self):
        cp = _get_couple(self.request.user)
        return Activity.objects.filter(couple=cp).order_by("-created")


# ─────────────────────────────────────────────────────────────
# 3. Mission
# ─────────────────────────────────────────────────────────────
class MissionViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """
    GET    /missions/      → 列表当前周期任务
    POST   /missions/regen → (Admin) 重新生成本周期任务
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = MissionSerializer

    def get_queryset(self):
        cp = _get_couple(self.request.user)
        return Mission.objects.filter(couple=cp).order_by("start")

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsAdminUser])
    def regen(self, request):
        Mission.seed_roundly()
        return Response({"detail": "Missions regenerated"}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────
# 4. Reminder & ReminderRule
# ─────────────────────────────────────────────────────────────
class ReminderViewSet(viewsets.ModelViewSet):
    """
    CRUD   /reminders/
    POST   /reminders/due/ → 标记所有到期并重排
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = ReminderSerializer

    def get_queryset(self):
        cp = _get_couple(self.request.user)
        return Reminder.objects.filter(couple=cp)

    @action(detail=False, methods=["post"])
    def due(self, request):
        cp = _get_couple(request.user)
        for r in Reminder.due().filter(couple=cp):
            r.mark_sent()
        return Response({"detail": "Due reminders sent"}, status=status.HTTP_200_OK)


class ReminderRuleViewSet(viewsets.ModelViewSet):
    """
    CRUD /reminder_rules/
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = ReminderRuleSerializer

    def get_queryset(self):
        cp = _get_couple(self.request.user)
        return ReminderRule.objects.filter(couple=cp)


# ─────────────────────────────────────────────────────────────
# 5. RewardBox
# ─────────────────────────────────────────────────────────────
class RewardBoxViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    """
    GET    /boxes/          → 列表箱子（可过滤 opened=false）
    POST   /boxes/{pk}/open → 打开奖励箱
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = RewardBoxSerializer

    def get_queryset(self):
        cp = _get_couple(self.request.user)
        qs = RewardBox.objects.filter(couple=cp)
        if self.request.query_params.get("opened") == "false":
            qs = qs.filter(opened_at__isnull=True)
        return qs.order_by("-created")

    @action(detail=True, methods=["post"])
    def open(self, request, pk=None):
        box = self.get_object()
        reward = box.open()
        return Response({"reward": reward}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────
# 6. Badge
# ─────────────────────────────────────────────────────────────
class BadgeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    GET /badges/ → 查看并自动发放可领徽章
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = BadgeSerializer

    def get_queryset(self):
        cp = _get_couple(self.request.user)
        Badge.audit()
        return cp.badges.all()


# ─────────────────────────────────────────────────────────────
# 7. PetMessage
# ─────────────────────────────────────────────────────────────
class PetMessageViewSet(mixins.ListModelMixin,
                        mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    """
    GET  /pet_messages/           → 列表留言
    PATCH /pet_messages/{pk}/     → 标记已读
    POST /pet_messages/roundly/    → 生成周报 (Admin)
    POST /pet_messages/daily_rec/ → 生成每日推荐 (Admin)
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = PetMessageSerializer

    def get_queryset(self):
        cp = _get_couple(self.request.user)
        return PetMessage.objects.filter(couple=cp).order_by("-created_at")

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsAdminUser])
    def roundly(self, request):
        PetMessage.roundly_summary()
        return Response({"detail": "Roundly summaries sent"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsAdminUser])
    def daily_rec(self, request):
        PetMessage.daily_recommend()
        return Response({"detail": "Daily recommendations sent"}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────
# 8. DicePocket
# ─────────────────────────────────────────────────────────────
class DicePocketViewSet(viewsets.ViewSet):
    """
    GET  /dice-pocket/           → 当前余额
    POST /dice-pocket/recharge/  → (Admin) 补充骰子
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        pocket = DicePocket._get(request.user)
        return Response(DicePocketSerializer(pocket).data)

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def recharge(self, request):
        try:
            amt = int(request.data.get("amount", 0))
        except (TypeError, ValueError):
            return Response({"detail": "amount must be int"}, status=status.HTTP_400_BAD_REQUEST)
        if amt <= 0:
            return Response({"detail": "amount must be > 0"}, status=status.HTTP_400_BAD_REQUEST)

        pocket = DicePocket.earn(request.user, amt)
        return Response({"balance": pocket}, status=status.HTTP_201_CREATED)


class PetMessageStateViewSet(viewsets.ViewSet):
    """
    宠物消息状态API

    GET  /pet-message-state/         → 获取当前用户消息状态
    POST /pet-message-state/refresh/ → 手动刷新状态
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """获取当前用户的消息状态"""
        try:
            # 尝试获取用户的消息状态
            user_state = UserPetMessageState.objects.filter(user=request.user).first()

            if user_state:
                # 有状态记录，直接返回
                serializer = PetMessageStateSerializer(user_state)
                return Response(serializer.data)
            else:
                # 无状态记录，返回默认数据（新格式）
                default_data = {
                    "current_states": [],
                    "available_messages": {
                        "default": {
                            "name": "",  # 默认消息name为空
                            "messages": ["Welcome to the game! Start your cooking journey!"]
                        }
                    },
                    "last_updated": None
                }
                return Response(default_data)

        except Exception as e:
            logger.error(f"Error getting pet message state for {request.user.username}: {e}")

            # 出错时返回默认数据（新格式）
            default_data = {
                "current_states": [],
                "available_messages": {
                    "default": {
                        "name": "",  # 出错时name为空
                        "messages": ["欢迎来到游戏！开始你的烹饪之旅吧！"]
                    }
                },
                "last_updated": None
            }
            return Response(default_data)

    @action(detail=False, methods=["post"])
    def refresh(self, request):
        """手动刷新用户消息状态"""
        try:
            # 检查用户是否有couple
            if not hasattr(request.user, 'couple') or not request.user.couple:
                return Response(
                    {"success": False, "message": "User does not have a couple, cannot refresh messages."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 调用刷新服务
            from .pet_message_service import refresh_user_pet_messages
            refresh_user_pet_messages(request.user, "api_manual_refresh")

            return Response({
                "success": True,
                "message": "State refreshed successfully."
            })

        except Exception as e:
            logger.error(f"Error refreshing pet messages for {request.user.username}: {e}")
            return Response(
                {"success": False, "message": f"State refresh failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ─────────────────────────────────────────────────────────────
# Food Inventory ViewSet - 食物库存管理
# ─────────────────────────────────────────────────────────────
class FoodInventoryViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    GET    /food-inventory/         → 获取当前用户的个人食物库存
    POST   /food-inventory/harvest/ → 收获食物到个人库存
    POST   /food-inventory/use/     → 使用个人食物喂宠物
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # 修改为基于用户的个人库存
        return FoodInventory.objects.filter(user=self.request.user).order_by('food_type')
    
    def list(self, request):
        """获取用户个人食物库存列表"""
        queryset = self.get_queryset()
        
        # 转换为前端友好的格式
        inventory_data = []
        for item in queryset:
            food_display = dict(FoodInventory.FOOD_TYPES).get(item.food_type, item.food_type)
            inventory_data.append({
                'food_type': item.food_type,
                'food_display': food_display,
                'quantity': item.quantity,
                'can_harvest': FoodInventory.can_harvest(request.user, item.food_type),
                'last_harvest': item.last_harvest
            })
        
        return Response({
            'inventory': inventory_data,
            'total_items': sum(item.quantity for item in queryset),
            'user_id': request.user.id  # 添加用户ID用于engagement对比
        })

    @action(detail=False, methods=["get"])
    def couple_comparison(self, request):
        """
        GET /food-inventory/couple_comparison/
        compare both partners food inventories, which drives engagement
        """
        try:
            couple = _get_couple(request.user)
        except PermissionDenied:
            return Response({
                "detail": "User not in a couple"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取情侣双方的用户
        user_self = request.user
        partner = couple.members.exclude(id=user_self.id).first()
        
        def get_user_inventory(user):
            """获取用户的食物库存数据"""
            user_inventory = FoodInventory.objects.filter(user=user).order_by('food_type')
            inventory_data = []
            for item in user_inventory:
                food_display = dict(FoodInventory.FOOD_TYPES).get(item.food_type, item.food_type)
                inventory_data.append({
                    'food_type': item.food_type,
                    'food_display': food_display,
                    'quantity': item.quantity,
                    'can_harvest': FoodInventory.can_harvest(user, item.food_type) if user == user_self else False,
                    'last_harvest': item.last_harvest
                })
            return {
                'user_id': user.id,
                'username': user.username,
                'inventory': inventory_data,
                'total_items': sum(item.quantity for item in user_inventory),
            }
        
        # 构建双方对比数据
        self_data = get_user_inventory(user_self)
        partner_data = get_user_inventory(partner) if partner else None
        
        # 创建所有食物类型的完整对比视图
        all_food_types = [choice[0] for choice in FoodInventory.FOOD_TYPES]
        comparison_data = []
        
        for food_type in all_food_types:
            food_display = dict(FoodInventory.FOOD_TYPES).get(food_type, food_type)
            
            # 查找自己的库存
            self_item = next((item for item in self_data['inventory'] if item['food_type'] == food_type), None)
            self_quantity = self_item['quantity'] if self_item else 0
            self_can_harvest = self_item['can_harvest'] if self_item else FoodInventory.can_harvest(user_self, food_type)
            
            # 查找情侣的库存
            partner_quantity = 0
            if partner_data:
                partner_item = next((item for item in partner_data['inventory'] if item['food_type'] == food_type), None)
                partner_quantity = partner_item['quantity'] if partner_item else 0
            
            comparison_data.append({
                'food_type': food_type,
                'food_display': food_display,
                'self_quantity': self_quantity,
                'partner_quantity': partner_quantity,
                'total_quantity': self_quantity + partner_quantity,
                'can_use': self_quantity > 0,  # 只能使用自己的食物
                'can_harvest': self_can_harvest,
                'advantage': 'self' if self_quantity > partner_quantity else 'partner' if partner_quantity > self_quantity else 'equal'
            })
        
        return Response({
            'comparison': comparison_data,
            'self': self_data,
            'partner': partner_data,
            'couple_id': couple.id,
            'engagement_stats': {
                'self_total': self_data['total_items'],
                'partner_total': partner_data['total_items'] if partner_data else 0,
                'combined_total': self_data['total_items'] + (partner_data['total_items'] if partner_data else 0),
                'self_advantage_count': sum(1 for item in comparison_data if item['advantage'] == 'self'),
                'partner_advantage_count': sum(1 for item in comparison_data if item['advantage'] == 'partner'),
                'equal_count': sum(1 for item in comparison_data if item['advantage'] == 'equal')
            }
        })
    
    @action(detail=False, methods=["post"])
    def checkin(self, request):
        """
        POST /food-inventory/checkin/
        3-slot system with precise multipliers: 3-different=3, 2-same=5, 3-same=9.
        Cooldown is environment-configured (CHECKIN_COOLDOWN_HOURS), admin can override.
        Admin control: admin_override, force_jackpot, force_double.
        """
        import random
        from datetime import timedelta
        from collections import Counter
        from django.conf import settings

        user = request.user

        # Admin flags
        admin_override = bool(request.data.get('admin_override', False))
        force_jackpot = bool(request.data.get('force_jackpot', False))
        force_double  = bool(request.data.get('force_double', False))
        is_admin = bool(user.is_staff or user.is_superuser)

        if (admin_override or force_jackpot or force_double) and not is_admin:
            return Response({
                "success": False,
                "error": "Admin privileges required for reward control",
                "message": "Only admins can override game mechanics"
            }, status=status.HTTP_403_FORBIDDEN)

        # Admin gating via env or special inventory flag
        gated = False
        try:
            if str(user.id) in getattr(settings, 'CHECKIN_BLOCKLIST_IDS', set()):
                gated = True
            if user.username in getattr(settings, 'CHECKIN_BLOCKLIST_USERNAMES', set()):
                gated = True
            gate_rec = FoodInventory.objects.filter(user=user, food_type='reward_blocked').first()
            if gate_rec and (gate_rec.quantity or 0) > 0:
                gated = True
        except Exception:
            gated = False

        if gated and not admin_override and not is_admin:
            return Response({
                "success": False,
                "gated": True,
                "message": "Rewards are temporarily disabled by admin.",
                "slot_preview": {
                    "next_reward_locked": True,
                    "next_possible_reward": "Temporarily unavailable",
                    "next_possible_emoji": "⛔️",
                    "next_possible_amount": 0,
                    "preview_message": "Rewards are currently paused by admin",
                    "cooldown_display": False
                }
            }, status=status.HTTP_200_OK)

        # Check cooldown (admin_override skips)
        checkin_record, created = FoodInventory.objects.get_or_create(
            user=user, food_type='checkin_record', defaults={'quantity': 0}
        )
        
        # 🎯 read the cooldown from SystemConfig so it can be tuned at runtime
        from system.models import SystemConfig
        cooldown_enabled = SystemConfig.is_reward_cooldown_enabled()
        cooldown_hours = SystemConfig.get_reward_cooldown_hours()
        
        # 如果关闭冷却或冷却时间为0，则跳过冷却检查
        if cooldown_enabled and cooldown_hours > 0 and not created and checkin_record.last_harvest and not admin_override:
            time_since_last = timezone.now() - checkin_record.last_harvest
            if time_since_last < timedelta(hours=cooldown_hours):
                remaining = timedelta(hours=cooldown_hours) - time_since_last
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                seconds = int(remaining.total_seconds() % 60)
                next_available = checkin_record.last_harvest + timedelta(hours=cooldown_hours)
                return Response({
                    "success": False,
                    "on_cooldown": True,
                    "remaining_time": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                    "next_checkin": next_available.isoformat(),
                    "next_available": next_available.isoformat(),
                    "cooldown_seconds": int(remaining.total_seconds()),
                    "total_checkins": checkin_record.quantity,
                    "message": f"⏰ Come back in {hours:02d}:{minutes:02d}:{seconds:02d} for your next spin!",
                    "slot_preview": {
                        "next_reward_locked": False,
                        "next_possible_reward": "Random fruits",
                        "next_possible_emoji": "🎰",
                        "next_possible_amount": 3,
                        "preview_message": f"🎰 Next spin in {hours:02d}:{minutes:02d}:{seconds:02d}",
                        "cooldown_display": True
                    }
                }, status=status.HTTP_200_OK)

        # Generate slot results (optionally forced by admin)
        foods = ['apple', 'banana', 'orange', 'strawberry', 'grapes', 'watermelon', 'pineapple', 'cherry']
        if force_jackpot and is_admin:
            f = random.choice(foods)
            slot_fruits = [f, f, f]
        elif force_double and is_admin:
            f = random.choice(foods)
            other = random.choice([x for x in foods if x != f])
            slot_fruits = [f, f, other]
            random.shuffle(slot_fruits)
        else:
            slot_fruits = [random.choice(foods) for _ in range(3)]

        counts = Counter(slot_fruits)
        unique = len(counts)
        if unique == 1:
            total_amount = 9
            reward_level = "JACKPOT"
            multiplier = 3
            bonus_text = "JACKPOT! ×3"
        elif unique == 2:
            total_amount = 5
            reward_level = "DOUBLE"
            multiplier = 2
            bonus_text = "DOUBLE! ×2"
        else:
            total_amount = 3
            reward_level = "NORMAL"
            multiplier = 1
            bonus_text = ""

        # Build slot result objects
        slot_results = []
        main_food_type = slot_fruits[0]
        
        logger.info(
            "🎰 [slot_machine] Generated slot_fruits: %s (unique=%s, reward=%s)",
            slot_fruits, unique, reward_level
        )
        
        for i, ft in enumerate(slot_fruits):
            emoji = self._get_food_emoji(ft)
            logger.info(
                "🎰 [slot_machine] Slot %s: food_type=%s → emoji=%s",
                i + 1, ft, emoji
            )
            slot_results.append({
                "slot_id": i + 1,
                "has_reward": True,
                "food_type": ft,
                "name": dict(FoodInventory.FOOD_TYPES).get(ft, ft),
                "emoji": emoji,
                "amount": total_amount if i == 0 else 0,
                "base_amount": 1,
                "multiplier": multiplier,
                "bonus_text": bonus_text if i == 0 else "",
                "effect": f"Kinny's energy +{random.randint(15, 25)}%",
            })

        # Apply reward to inventory
        inv = FoodInventory.add_food(user, main_food_type, total_amount)
        if inv:
            inv.last_harvest = timezone.now()
            inv.save(update_fields=['last_harvest'])

        # Update check-in record
        checkin_record.quantity += 1
        checkin_record.last_harvest = timezone.now()
        checkin_record.save()

        logger.info(
            "🎰 [slot_machine] User %s won %s with fruits: %s (Total: %s)",
            user.username, reward_level, slot_fruits, total_amount
        )

        # 🎯 计算下次可用时间（如果冷却启用）
        if cooldown_enabled and cooldown_hours > 0:
            next_available = checkin_record.last_harvest + timedelta(hours=cooldown_hours)
        else:
            next_available = timezone.now()  # 立即可用

        return Response({
            "success": True,
            "message": f"🎰 SLOT MACHINE! {reward_level} - Total: {total_amount} fruits!",
            "total_harvests": checkin_record.quantity,
            "cooldown_hours": cooldown_hours,
            "cooldown_enabled": cooldown_enabled,
            "next_available": next_available.isoformat(),
            "total_checkins": checkin_record.quantity,
            "food_type": main_food_type,
            "user_id": user.id,
            "slot_animation": {
                "num_slots": 3,
                "winning_slots": multiplier,
                "spin_duration": 3000,
                "reel_stop_delays": [1000, 2000, 3000],
                "celebration_duration": 2000,
                "jackpot_mode": reward_level == "JACKPOT",
                "winning_symbol": self._get_food_emoji(main_food_type)
            },
            "slot_results": slot_results,
            "food_received": main_food_type,
            "food_display": dict(FoodInventory.FOOD_TYPES).get(main_food_type, main_food_type),
            "amount": total_amount,
            "new_quantity": total_amount,
            "slot_result": slot_results[0],
            "jackpot_bonus": reward_level == "JACKPOT",
            "total_rewards_won": len(slot_fruits),
            "admin_controlled": {
                "is_admin": is_admin,
                "admin_override_used": admin_override,
                "forced_jackpot": bool(force_jackpot and is_admin),
                "forced_double": bool(force_double and is_admin),
                "reward_level": reward_level,
                "multiplier": multiplier
            } if is_admin else None
        }, status=status.HTTP_200_OK)
    
    def _get_food_emoji(self, food_type):
        """获取食物对应的emoji"""
        emoji_map = {
            'apple': '🍎',
            'banana': '🍌',
            'orange': '🍊', 
            'strawberry': '🍓',
            'grapes': '🍇',
            'watermelon': '🍉',
            'pineapple': '🍍',
            'cherry': '🍒'
        }
        return emoji_map.get(food_type, '🍎')
    
    @action(detail=False, methods=["post"])
    def harvest(self, request):
        """
        POST /food-inventory/harvest/
        Body: {
          "food_type": "apple"
        }
        """
        logger.info(f"[harvest] Request data: {request.data}")
        
        food_type = request.data.get('food_type')
        logger.info(f"[harvest] Food type received: '{food_type}'")
        
        # 验证食物类型
        valid_food_types = [choice[0] for choice in FoodInventory.FOOD_TYPES]
        logger.info(f"[harvest] Valid food types: {valid_food_types}")
        
        if not food_type:
            logger.warning(f"[harvest] No food_type provided")
            return Response({
                "detail": "food_type is required"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if food_type not in valid_food_types:
            logger.warning(f"[harvest] Invalid food_type: '{food_type}'. Valid types: {valid_food_types}")
            return Response({
                "detail": f"Invalid food_type: '{food_type}'. Valid types: {valid_food_types}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 修改为基于用户的个人收获
        user = request.user
        logger.info(f"[harvest] User: {user.username} ({user.id})")
        
        # 🎯 check for food waiting to be collected, whether from a win or a check-in
        try:
            # 查找用户的food inventory记录
            inventory = FoodInventory.objects.get(user=user, food_type=food_type)
            
            # 检查是否有pending food（quantity > 0 但尚未显式收获）
            has_pending_food = inventory.quantity > 0
            can_harvest_cooldown = FoodInventory.can_harvest(user, food_type)
            
            logger.info(f"[harvest] {food_type} - Has pending: {has_pending_food}, Can harvest (cooldown): {can_harvest_cooldown}, Quantity: {inventory.quantity}")
            
            # 🎯 如果有待收获的食物，允许harvest
            if has_pending_food:
                logger.info(f"[harvest] User {user.username} has pending {food_type} (qty: {inventory.quantity}) - allowing harvest")
                can_harvest = True
            else:
                can_harvest = can_harvest_cooldown
                
        except FoodInventory.DoesNotExist:
            # 如果没有记录，检查cooldown
            can_harvest = FoodInventory.can_harvest(user, food_type)
            logger.info(f"[harvest] No existing inventory for {food_type}, checking cooldown: {can_harvest}")
        
        # 🔑 Adminunlimited harvest: skips every cooldown and quantity cap
        if user.is_superuser:
            logger.info(f"[harvest] Admin {user.username} has unlimited harvest privileges for {food_type}")
            can_harvest = True
            force_harvest = True
        else:
            # 🎯 开发环境：管理员可以跳过所有限制
            if not can_harvest and user.is_superuser:
                logger.info(f"[harvest] Admin {user.username} bypassing all restrictions for {food_type}")
                can_harvest = True
                force_harvest = True
            else:
                force_harvest = can_harvest
        
        logger.info(f"[harvest] Final decision - Can harvest {food_type}: {can_harvest}")
        
        if not can_harvest:
            return Response({
                "detail": "No pending food to harvest and still in cooldown (8 hours)"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 收获食物到个人库存
        logger.info(f"[harvest] Attempting to harvest {food_type} for user {user.username}")
        inventory = FoodInventory.harvest_food(user, food_type, amount=3, force=force_harvest)
        
        if inventory:
            food_display = dict(FoodInventory.FOOD_TYPES).get(food_type, food_type)
            logger.info(f"[harvest] Successfully harvested {food_type}, new quantity: {inventory.quantity}")
            return Response({
                "success": True,
                "food_type": food_type,
                "food_display": food_display,
                "harvested": 3,
                "new_quantity": inventory.quantity,
                "next_harvest": inventory.last_harvest + timedelta(hours=8) if inventory.last_harvest else None,
                "user_id": user.id
            })
        else:
            logger.error(f"[harvest] Failed to harvest {food_type} for user {user.username}")
            return Response({
                "detail": "Harvest failed"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["post"])
    def use_food(self, request):
        """
        POST /food-inventory/use/
        Body: {
          "food_type": "apple",
          "amount": 1
        }
        """
        food_type = request.data.get('food_type')
        amount = max(1, int(request.data.get('amount', 1)))
        
        if not food_type or food_type not in [choice[0] for choice in FoodInventory.FOOD_TYPES]:
            return Response({
                "detail": "Invalid food_type"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 修改为基于用户的个人库存使用
        user = request.user
        
        # 尝试使用个人食物
        success = FoodInventory.use_food(user, food_type, amount)
        if success:
            # 喂食宠物
            pet = _get_pet(request.user)
            hunger_gain = amount * 10  # 每个食物恢复10点饥饿值
            pet.status.hunger = min(100, pet.status.hunger + hunger_gain)
            pet.status.save()
            
            # 获取更新后的个人库存
            try:
                inventory = FoodInventory.objects.get(user=user, food_type=food_type)
                remaining = inventory.quantity
            except FoodInventory.DoesNotExist:
                remaining = 0
            
            food_display = dict(FoodInventory.FOOD_TYPES).get(food_type, food_type)
            return Response({
                "success": True,
                "food_type": food_type,
                "food_display": food_display,
                "used": amount,
                "hunger_gain": hunger_gain,
                "remaining_quantity": remaining,
                "new_hunger": pet.status.hunger,
                "user_id": user.id
            })
        else:
            return Response({
                "detail": "Not enough food in inventory"
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=["post"], url_path="use-any")
    def use_any_food(self, request):
        """
        POST /food-inventory/use-any/
        Body: {
          "amount": 1
        }
        🍽️ Kinny Food Unified API - Auto-selects first available food type
        Frontend abstraction: no need to specify food_type
        """
        amount = max(1, int(request.data.get('amount', 1)))
        user = request.user
        
        # Find first available food type with quantity > 0
        available_foods = FoodInventory.objects.filter(
            user=user,
            quantity__gte=amount
        ).order_by('food_type')
        
        if not available_foods.exists():
            return Response({
                "success": False,
                "detail": "No food available in inventory"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use first available food
        food_item = available_foods.first()
        food_type = food_item.food_type
        
        # Use the food
        success = FoodInventory.use_food(user, food_type, amount)
        if success:
            # Feed pet
            pet = _get_pet(request.user)
            hunger_gain = amount * 10  # 10 hunger per food
            pet.status.hunger = min(100, pet.status.hunger + hunger_gain)
            pet.status.save()
            
            # Get remaining total across all food types
            remaining_total = FoodInventory.objects.filter(user=user).aggregate(
                total=models.Sum('quantity')
            )['total'] or 0
            
            return Response({
                "success": True,
                "food_emoji": "🍽️",
                "food_display": "Kinny Food",
                "used": amount,
                "hunger_gain": hunger_gain,
                "new_hunger": pet.status.hunger,
                "remaining_total": remaining_total,
                "user_id": user.id
            })
        else:
            return Response({
                "success": False,
                "detail": "Failed to use food"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
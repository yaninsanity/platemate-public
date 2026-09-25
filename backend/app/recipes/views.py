# apps/recipes/views.py

from __future__ import annotations

import logging
import random
import time
from typing import Optional

from django.db import connection, transaction, models
from django.shortcuts import get_object_or_404
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .models import (
    Ingredient,
    Recipe,
    RecipeIngredientTask,
    FamilyRecipe,
    Menu,
    FamilyMenu,
    RoundBracket,
    IngredientPhotoProof,
)
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    RecipeIngredientTaskSerializer,
    FamilyRecipeSerializer,
    MenuSerializer,
    FamilyMenuSerializer,
    RoundBracketSerializer,
    IngredientPhotoProofSerializer,
)
from cookai.models import AIPrompt, AIRequestLog
from cookai.client import CookAIClient
from petcare.models import DicePocket

logger = logging.getLogger(__name__)


def _random_pk_sample(qs, attempts: int = 5) -> Optional[int]:
    if not qs.exists():
        return None
    lo, hi = qs.aggregate(lo=models.Min("pk"), hi=models.Max("pk")).values()
    for _ in range(attempts):
        pk = random.randint(lo, hi)
        candidate = qs.filter(pk__gte=pk).first() or qs.filter(pk__lte=pk).last()
        if candidate:
            return candidate.pk
    return qs.order_by("?").values_list("pk", flat=True).first()


def pick_random(qs):
    if connection.vendor == "postgresql":
        tbl = qs.model._meta.db_table
        try:
            rs = qs.model.objects.raw(
                f"SELECT * FROM {tbl} TABLESAMPLE SYSTEM (2) LIMIT 1;"
            )
            return next(iter(rs), None)
        except Exception:
            logger.debug("TABLESAMPLE fallback")
    pk = _random_pk_sample(qs)
    return qs.filter(pk=pk).first() if pk else None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all().order_by("name")
    serializer_class = IngredientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name", "cuisine", "dish_type"]
    filterset_fields = ["cuisine", "dish_type"]

    def get_queryset(self):
        return (
            Recipe.objects.all()
            .prefetch_related(
                "ingredientinrecipe_set__ingredient",
                "tasks",
                "family_recipes",
            )
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        context = {**self.get_serializer_context(), "include_ai": True}
        serializer = self.get_serializer(instance, context=context)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def add_ingredient(self, request, pk=None):
        recipe = self.get_object()
        ing_id = request.data.get("ingredient_id")
        if not ing_id:
            return Response({"detail": "ingredient_id required"}, status=400)
        ing = get_object_or_404(Ingredient, pk=ing_id)
        recipe.add_ingredient(ing, request.data.get("quantity", ""))
        return Response({"status": "ingredient added"}, status=201)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def start_scan(self, request, pk=None):
        recipe = self.get_object()
        ing_id = request.data.get("ingredient_id")
        if not ing_id:
            return Response({"detail": "ingredient_id required"}, status=400)
        ing = get_object_or_404(Ingredient, pk=ing_id)

        user_cpl = getattr(request.user, "couple", None)
        if not user_cpl:
            return Response({"detail": "User has no couple"}, status=400)

        # 创建任务并标记上传
        with transaction.atomic():
            task = RecipeIngredientTask.objects.create(
                recipe=recipe,
                ingredient=ing,
                couple=user_cpl,
                user=request.user,
                is_uploaded=True,
            )
            try:
                # 给 AI 调用设置超时保护
                start = time.time()
                detected, match = CookAIClient.detect_ingredients(
                    request.build_absolute_uri(task.proofs.last().image.url),
                    [ing.name],
                    timeout=10  # 假定 client 支持超时参数
                )
                if not match:
                    raise ValueError(f"AI did not detect “{ing.name}” in the image.")
                RecipeIngredientTask.objects.verify_and_unlock(task, request.user)
            except Exception as e:
                # 回滚状态，保留任务以便用户重试上传
                transaction.set_rollback(True)
                return Response({"detail": str(e)}, status=400)

        ser = RecipeIngredientTaskSerializer(task, context={"request": request})
        return Response(ser.data, status=201)
# apps/recipes/views.py（只贴出新的 ViewSet，其他代码保持不动）
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import RecipeIngredientTask
from .serializers import RecipeIngredientTaskSerializer


class RecipeIngredientTaskViewSet(viewsets.ModelViewSet):
    """
    任务接口

    • POST   /api/recipes/tasks/by-recipe/      body={"recipe": <id>}
    • GET    /api/recipes/tasks/?recipe=<id>
    • POST   /api/recipes/tasks/verify/         body={"id": <taskId>}
    • POST   /api/recipes/tasks/{pk}/complete/
    """
    queryset = RecipeIngredientTask.objects.select_related("recipe", "ingredient")
    serializer_class = RecipeIngredientTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = []          # 关闭 DRF 自动过滤

    def create(self, request, *args, **kwargs):
        """Override create to add logging"""
        logger.info(f"create called with data: {request.data}")
        logger.info(f"user: {request.user.id}")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Set user and couple when creating a task"""
        user_couple = getattr(self.request.user, 'couple', None)
        logger.info(f"perform_create called with user={self.request.user.id}, couple={user_couple}")
        serializer.save(
            user=self.request.user,
            couple=user_couple
        )

    def get_queryset(self):
        """return the tasks of the couple, with the current user tasks first"""
        user_couple = getattr(self.request.user, 'couple', None)
        if not user_couple:
            # 如果用户没有couple，只返回分配给该用户的任务
            return super().get_queryset().filter(user=self.request.user)
        
        # return every task of the couple, but a user may only act on their own
        return super().get_queryset().filter(couple=user_couple)

    # ---------- ① body 里带 recipe ----------
    @action(detail=False, methods=["post"], url_path="by-recipe")
    def by_recipe(self, request):
        recipe_pk = request.data.get("recipe")
        if not recipe_pk:
            return Response({"detail": "recipe is required"}, status=400)

        user_couple = getattr(request.user, 'couple', None)
        if not user_couple:
            # an unpaired user sees only their own tasks
            qs = self.get_queryset().filter(recipe=recipe_pk, user=request.user)
        else:
            # a paired user sees every task of the couple but still creates their own
            qs = self.get_queryset().filter(recipe=recipe_pk)
            
            # create every ingredient task of this recipe for the current user
            from .models import IngredientInRecipe
            # recipe_ingredients = IngredientInRecipe.objects.filter(recipe=recipe_pk)
            # for ing_recipe in recipe_ingredients:
            #     RecipeIngredientTask.objects.get_or_create(
            #         recipe_id=recipe_pk,
            #         ingredient=ing_recipe.ingredient,
            #         user=request.user,
            #         couple=user_couple,
            #         defaults={'is_verified': False, 'is_uploaded': False}
            #     )
            # 重新获取更新后的任务
            qs = RecipeIngredientTask.objects.filter(
                recipe=recipe_pk, 
                user=request.user,
                couple=user_couple
            ).select_related("recipe", "ingredient")

        serializer = self.get_serializer(qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    # ---------- ② Enhanced couple-aware recipe tasks ----------
    @action(detail=False, methods=["post"], url_path="by-recipe-enhanced")
    def by_recipe_enhanced(self, request):
        """
        Enhanced endpoint that returns:
        1. Current user's tasks (full detail)
        2. Partner's task completion status (for interaction awareness)
        """
        recipe_pk = request.data.get("recipe")
        if not recipe_pk:
            return Response({"detail": "recipe is required"}, status=400)

        user_couple = getattr(request.user, 'couple', None)
        if not user_couple:
            # 确保为无couple用户创建任务
            from .models import IngredientInRecipe
            # recipe_ingredients = IngredientInRecipe.objects.filter(recipe=recipe_pk)
            # for ing_recipe in recipe_ingredients:
            #     RecipeIngredientTask.objects.get_or_create(
            #         recipe_id=recipe_pk,
            #         ingredient=ing_recipe.ingredient,
            #         user=request.user,
            #         defaults={'is_verified': False, 'is_uploaded': False, 'couple': None}
            #     )
            
            qs = RecipeIngredientTask.objects.filter(
                recipe=recipe_pk, 
                user=request.user
            ).select_related("recipe", "ingredient")
            
            serializer = self.get_serializer(qs, many=True, context=self.get_serializer_context())
            return Response({
                "user_tasks": serializer.data,
                "partner_progress": None,
                "couple_id": None
            })

        # create every ingredient task of this recipe for the current user
        from .models import IngredientInRecipe
        # recipe_ingredients = IngredientInRecipe.objects.filter(recipe=recipe_pk)
        # for ing_recipe in recipe_ingredients:
        #     RecipeIngredientTask.objects.get_or_create(
        #         recipe_id=recipe_pk,
        #         ingredient=ing_recipe.ingredient,
        #         user=request.user,
        #         couple=user_couple,
        #         defaults={'is_verified': False, 'is_uploaded': False}
        #     )

        # Get current user's tasks
        user_tasks = RecipeIngredientTask.objects.filter(
            recipe=recipe_pk,
            user=request.user,
            couple=user_couple
        ).select_related("recipe", "ingredient")
        user_serializer = self.get_serializer(user_tasks, many=True, context=self.get_serializer_context())

        # Get partner's completion status
        partner_users = user_couple.members.exclude(id=request.user.id)
        partner_progress = {}
        
        for partner in partner_users:
            # 确保为partner也创建任务
            # for ing_recipe in recipe_ingredients:
            #     RecipeIngredientTask.objects.get_or_create(
            #         recipe_id=recipe_pk,
            #         ingredient=ing_recipe.ingredient,
            #         user=partner,
            #         couple=user_couple,
            #         defaults={'is_verified': False, 'is_uploaded': False}
            #     )
            
            partner_tasks = RecipeIngredientTask.objects.filter(
                recipe=recipe_pk,
                user=partner,
                couple=user_couple
            ).select_related('ingredient')
            
            partner_progress[partner.username] = {
                "user_id": partner.id,
                "completed_ingredients": [
                    {
                        "ingredient_id": task.ingredient.id,
                        "ingredient_name": task.ingredient.name,
                        "verified_at": task.scanned_at.isoformat() if task.scanned_at else None,
                        "task_id": task.id  # 添加任务ID用于精确匹配
                    }
                    for task in partner_tasks if task.is_verified
                ],
                "total_tasks": partner_tasks.count(),
                "completed_tasks": partner_tasks.filter(is_verified=True).count()
            }

        return Response({
            "user_tasks": user_serializer.data,
            "partner_progress": partner_progress,
            "couple_id": user_couple.id
        })

    # ---------- ② query 参数带 recipe ----------
    def list(self, request, *args, **kwargs):
        recipe_pk = request.query_params.get("recipe")
        if recipe_pk:
            user_couple = getattr(request.user, 'couple', None)
            if not user_couple:
                # an unpaired user sees only their own tasks
                qs = self.get_queryset().filter(recipe=recipe_pk, user=request.user)
            else:
                # create every ingredient task of this recipe for the current user
                from .models import IngredientInRecipe
                # recipe_ingredients = IngredientInRecipe.objects.filter(recipe=recipe_pk)
                # for ing_recipe in recipe_ingredients:
                #     RecipeIngredientTask.objects.get_or_create(
                #         recipe_id=recipe_pk,
                #         ingredient=ing_recipe.ingredient,
                #         user=request.user,
                #         couple=user_couple,
                #         defaults={'is_verified': False, 'is_uploaded': False}
                #     )
                # 只返回当前用户的任务
                qs = RecipeIngredientTask.objects.filter(
                    recipe=recipe_pk, 
                    user=request.user,
                    couple=user_couple
                ).select_related("recipe", "ingredient")
            
            serializer = self.get_serializer(qs, many=True, context=self.get_serializer_context())
            return Response(serializer.data)
        
        # 如果没有recipe参数，返回当前用户的所有任务
        if hasattr(self.request.user, 'couple') and self.request.user.couple:
            qs = RecipeIngredientTask.objects.filter(
                user=self.request.user,
                couple=self.request.user.couple
            ).select_related("recipe", "ingredient")
        else:
            qs = RecipeIngredientTask.objects.filter(
                user=self.request.user
            ).select_related("recipe", "ingredient")
        
        serializer = self.get_serializer(qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    # ---------- ③ 验证 ----------
    @action(detail=False, methods=["post"], url_path="verify")
    def verify(self, request):
        task_id = request.data.get("id")
        if not task_id:
            return Response({"detail": "id is required"}, status=400)
            
        try:
            task = RecipeIngredientTask.objects.select_related("recipe", "ingredient").get(
                pk=task_id, 
                user=request.user
            )
        except RecipeIngredientTask.DoesNotExist:
            return Response({"detail": "Task not found or not assigned to current user"}, status=404)
        
        try:
            task.verify(user=request.user)
            # 返回更新后的任务状态
            serializer = self.get_serializer(task, context={"request": request})
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ---------- ④ 完成 ----------
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        try:
            task = RecipeIngredientTask.objects.select_related("recipe", "ingredient").get(
                pk=pk, 
                user=request.user
            )
        except RecipeIngredientTask.DoesNotExist:
            return Response({"detail": "Task not found or not assigned to current user"}, status=404)
            
        try:
            task.verify(user=request.user)
            # 返回更新后的任务状态
            serializer = self.get_serializer(task, context={"request": request})
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FamilyRecipeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FamilyRecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FamilyRecipe.objects.filter(couple=self.request.user.couple)


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [IsAuthenticated]


class FamilyMenuViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FamilyMenuSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FamilyMenu.objects.filter(couple=self.request.user.couple)


class RoundBracketViewSet(viewsets.ReadOnlyModelViewSet):      # ← ① 改成只读
    http_method_names = ["get", "post", "head", "options"]       # Allow POST for compatibility
    serializer_class   = RoundBracketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RoundBracket.objects.filter(couple=self.request.user.couple)

    # kept for older frontends: POST /roundly-bracket/ still works
    def create(self, request, *args, **kwargs):
        wb = RoundBracket.current(request.user.couple)         # ← ② 不再手动 roll
        return Response(self.get_serializer(wb).data, status=201)

    # 推荐前端统一调用 ↓
    @action(detail=False, methods=["post"])
    def refresh(self, request):
        wb = RoundBracket.current(request.user.couple, request.user)         # already rolled
        return Response(self.get_serializer(wb).data)
    
    # 检查并创建新bracket
    @action(detail=False, methods=["post"])
    def check(self, request):
        wb = RoundBracket.checkCurrent(request.user.couple)         # already rolled
        return Response(self.get_serializer(wb).data)

class IngredientPhotoProofViewSet(viewsets.ModelViewSet):
    throttle_classes = [UserRateThrottle]
    queryset = IngredientPhotoProof.objects.all()
    serializer_class = IngredientPhotoProofSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "head", "options"]

    def create(self, request, *args, **kwargs):
        task_id = request.data.get('task')
        if not task_id:
            return Response({"error": "task is required"}, status=400)

        # 删除已存在的 proof（覆盖逻辑）
        IngredientPhotoProof.objects.filter(task_id=task_id).delete()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proof = serializer.save(uploader=request.user)

        image_url = request.build_absolute_uri(proof.image.url)
        
        # 🔧 corrects the production port so the model can reach the image URL
        if hasattr(settings, 'HTTPS_PORT') and settings.HTTPS_PORT:
            # 替换内部端口为外部HTTPS端口
            image_url = image_url.replace(f":{settings.BACKEND_PORT}/", f":{settings.HTTPS_PORT}/")
            # 确保使用HTTPS协议
            if image_url.startswith('http://'):
                image_url = image_url.replace('http://', 'https://')
        
        task = proof.task
        
        # Security check: ensure task belongs to user's couple or user
        user_couple = getattr(request.user, 'couple', None)
        if user_couple and task.couple != user_couple:
            return Response({"error": "Task does not belong to user's couple"}, status=403)
        elif not user_couple and task.user != request.user:
            return Response({"error": "Task does not belong to current user"}, status=403)
        
        # Ensure task has user field set to current user
        if task.user != request.user:
            if task.user is None:
                # If task.user is None, assign it to current user
                task.user = request.user
                task.save(update_fields=['user'])
            else:
                # If task is assigned to different user, deny access
                return Response({"error": "Task is assigned to different user"}, status=403)
        
        start = time.time()

        # 🎭 AI service factory: switches between the real service and the mock
        try:
            from system.services import AIServiceFactory
            
            logger.info(f"Starting AI detection for task {task.id}, ingredient: {task.ingredient.name}")
            logger.info(f"Image URL: {image_url}")
            logger.info(f"Using {'Mock' if AIServiceFactory.is_using_mock() else 'Real'} AI Service")
            
            # 🔧 使用工厂方法获取AI服务（真实或Mock）
            ai_result = AIServiceFactory.detect_ingredients(
                image_url, [task.ingredient.name], timeout=15
            )
            
            detected = ai_result.get('detected', [])
            match = ai_result.get('match', False)
            confidence = ai_result.get('confidence', 0.85)
            kinny_message = ai_result.get('message', '')
            is_mock = ai_result.get('is_mock', False)
            
            logger.info(f"AI detection results: detected={detected}, match={match}, is_mock={is_mock}, message={kinny_message}")
            
            if match:
                RecipeIngredientTask.objects.verify_and_unlock(task, request.user)
                logger.info(f"Task {task.id} verified and unlocked successfully")
                
            # 返回前端期望的格式，包含Kinny消息
            response_data = {
                'id': proof.id,
                'task': proof.task_id,
                'image': proof.image.url,
                'created_at': proof.created_at,
                'detected': detected,
                'match': match,
                'confidence': confidence,
                'message': kinny_message,
                'error': None if match else f"Could not detect {task.ingredient.name}. AI found: {', '.join(detected) if detected else 'nothing recognizable'}"
            }
            
            AIRequestLog.objects.log(
                prompt_obj=AIPrompt.objects.filter(kind=AIPrompt.KIND_DETECT, is_active=True).first(),
                kind=AIPrompt.KIND_DETECT,
                user=request.user,
                request_payload={"image": image_url, "targets": [task.ingredient.name]},
                response={"detected": detected, "match": match, "message": kinny_message},
                latency=time.time() - start,
            )
            
            return Response(response_data, status=201)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"AI detection failed for task {task.id}: {error_msg}")
            
            AIRequestLog.objects.log(
                prompt_obj=AIPrompt.objects.filter(kind=AIPrompt.KIND_DETECT, is_active=True).first(),
                kind=AIPrompt.KIND_DETECT,
                user=request.user,
                request_payload={"image": image_url, "targets": [task.ingredient.name]},
                response={"error": error_msg},
                latency=time.time() - start,
            )
            
            # 返回错误但保持统一格式
            response_data = {
                'id': proof.id,
                'task': proof.task_id,
                'image': proof.image.url,
                'created_at': proof.created_at,
                'detected': [],
                'match': False,
                'confidence': 0.0,
                'message': '',
                'error': f"Detection failed: {error_msg}"
            }
            return Response(response_data, status=201)  # 返回201因为文件上传成功

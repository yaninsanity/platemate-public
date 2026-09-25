"""Couple-Memory API views
────────────────────────────────────────────────────────────────────
• /memories/…        — 周记容器
• /entries/…         — 单条做饭记录（支持一次 POST 多文件）
• /comments/…        — 评论

改进要点
• _require_couple()      —— 统一获取 Couple；无绑定则 HTTP 400
• 超级管理员 is_superuser —— 可查看 / 写全部数据
• get_queryset()         —— returns an empty set rather than raising when there is no couple
• perform_create()       —— 多文件上传 / 自动关联当前周记
• add_media / set_ai_score Action 与权限校验
"""
from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import exceptions, filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CoupleMemory, MemoryComment, MemoryEntry, MemoryMedia
from .serializers import (
    CoupleMemorySerializer,
    MemoryCommentSerializer,
    MemoryEntryReadSerializer,
    MemoryEntryWriteSerializer,
    MemoryMediaSerializer,
)
from collections import defaultdict
from recipes.models     import Recipe
from recipes.serializers import RecipeSerializer
from users.models import CoupleMembership


# ─────────────────────── helpers ────────────────────────────
def _require_couple(request):
    """
    Return the first Couple for current user.
    • 若用户未配对 → HTTP 400
    • 若配对多个   → 取第一个（可按业务扩展）
    """
    try:
        return request.user.couples.all()[0]
    except IndexError:
        raise exceptions.ValidationError("You haven’t linked to any couple yet.")

# ───────────────────── pagination ───────────────────────────
class StandardResults(PageNumberPagination):
    page_size            = 10
    page_size_query_param = "page_size"
    max_page_size        = 100

# ──────────────────── 1. Roundly bucket ──────────────────────
class CoupleMemoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class   = CoupleMemorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardResults
    filter_backends    = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields    = ["round_start", "total_points"]
    search_fields      = ["summary"]

    def get_queryset(self):
        qs = (
            CoupleMemory.objects
            .select_related("winner_entry__recipe")  # 预取 winner_entry 的 recipe
            .prefetch_related("entries__recipe")     # 预取所有 entries 的 recipe
        )
        if self.request.user.is_superuser:      # 管理员查看全部
            return qs
        return qs.filter(couple__members=self.request.user)

    # GET /memories/current/
    @action(detail=False, methods=["get"])
    def current(self, request):
        mem = CoupleMemory.current(_require_couple(request))
        return Response(self.get_serializer(mem).data)

    # PATCH /memories/{pk}/summary/
    @action(detail=True, methods=["patch"])
    def summary(self, request, pk=None):
        mem = self.get_object()
        mem.summary = request.data.get("summary", mem.summary)
        mem.save(update_fields=["summary"])
        return Response(self.get_serializer(mem).data)

    # GET /memories/{pk}/top_ingredients/
    @action(detail=True, methods=["get"])
    def top_ingredients(self, request, pk=None):
        return Response(self.get_object().top_ingredients())

# ───────────────────── 2. Entry ─────────────────────────────
class MemoryEntryViewSet(viewsets.ModelViewSet):
    """
    • create/update use WriteSerializer, which accepts several files in one POST
      -F files[]=pic1 -F files[]=pic2 …
    • list/retrieve use ReadSerializer, which nests media and comments
    • add_media / set_ai_score actions
    """
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardResults
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ["content"]
    ordering_fields    = ["created_at", "ai_score"]

    # —— queryset —— --------------------------------------------------------
    def get_queryset(self):
        qs = (
            MemoryEntry.objects
            .select_related("author", "memory")
            .prefetch_related("media", "comments")
        )
        if self.request.user.is_superuser:
            return qs
        return qs.filter(memory__couple__members=self.request.user)

    # —— serializer switch —— ----------------------------------------------
    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return MemoryEntryWriteSerializer
        return MemoryEntryReadSerializer

    # —— create —— ----------------------------------------------------------
    @transaction.atomic
    def perform_create(self, serializer):
        memory = CoupleMemory.current(_require_couple(self.request))
        files  = self.request.FILES.getlist("files")  # 允许为空
        entry  = serializer.save(author=self.request.user, memory=memory)

        if files:
            MemoryMedia.objects.bulk_create(
                [MemoryMedia(entry=entry, media=f) for f in files]
            )
            
            # 自动触发AI评分
            from cookai.scoring import ScoringService
            ScoringService.score_memory_entry(entry.pk)

    # —— custom actions —— --------------------------------------------------
    # POST /entries/{pk}/add_media/
    @action(detail=True, methods=["post"])
    def add_media(self, request, pk=None):
        entry = self.get_object()
        s = MemoryMediaSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        s.save(entry=entry)
        return Response(
            MemoryEntryReadSerializer(entry, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    # PATCH /entries/{pk}/set_ai_score/
    @action(detail=True, methods=["patch"])
    def set_ai_score(self, request, pk=None):
        entry = self.get_object()
        score = request.data.get("ai_score")
        if score is None:
            return Response({"detail": "ai_score is required"}, status=400)
        entry.ai_score = score
        entry.save(update_fields=["ai_score"])
        return Response(
            MemoryEntryReadSerializer(entry, context=self.get_serializer_context()).data
        )

    # POST /entries/{pk}/trigger_ai_scoring/
    @action(detail=True, methods=["post"])
    def trigger_ai_scoring(self, request, pk=None):
        """手动触发AI评分（如果自动评分失败）"""
        entry = self.get_object()
        
        # 检查是否有图片
        if not entry.media.exists():
            return Response(
                {"detail": "No media found for this entry"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 使用cookai模块的干净接口触发评分
        from cookai.scoring import ScoringService
        
        # 异步触发AI评分
        ScoringService.score_memory_entry(entry.pk)
        
        return Response(
            {
                "detail": "AI scoring triggered successfully",
                "entry_id": entry.pk,
                "message": "🤖 PlateMate is analyzing your dish... Scoring will complete shortly!"
            },
            status=status.HTTP_202_ACCEPTED
        )

    # GET /entries/{pk}/ai-judgment/
    @action(detail=True, methods=["get"])
    def ai_judgment(self, request, pk=None):
        """获取entry的AI判断结果"""
        entry = self.get_object()
        
        try:
            judgment = entry.ai_judgment
            if not judgment:
                return Response(
                    {"detail": "AI judgment not found for this entry"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 使用serializer确保数据格式正确
            from .serializers import AIJudgmentSerializer
            data = AIJudgmentSerializer(judgment).data
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"detail": f"Error retrieving AI judgment: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ───────────────────── 3. Comment ───────────────────────────
class MemoryCommentViewSet(viewsets.ModelViewSet):
    serializer_class   = MemoryCommentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardResults
    filter_backends    = [filters.OrderingFilter]
    ordering_fields    = ["created_at"]

    def get_queryset(self):
        qs = MemoryComment.objects.select_related("author", "entry")
        if self.request.user.is_superuser:
            return qs
        return qs.filter(entry__memory__couple__members=self.request.user)

    def perform_create(self, serializer):
        qs = MemoryEntry.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(memory__couple__members=self.request.user)
        entry = get_object_or_404(
            qs,
            pk=self.request.data.get("entry")
        )
        serializer.save(author=self.request.user, entry=entry)

    # 只允许作者本人删除
    def perform_destroy(self, instance):
        if not (instance.author == self.request.user or self.request.user.is_superuser):
            return Response({"detail": "Not allowed"}, status=403)
        instance.delete()

class FamilyMenuViewSet(viewsets.ViewSet):
    """
    GET /couplememory/family-menu/            → 聚合后的菜谱清单
    GET /couplememory/family-menu/{recipe_pk}/ → 某菜全部历史
    ※ 只实现这 2 条，其余 HTTP 动作 405
    """
    permission_classes = [IsAuthenticated]

    # ---------- 1. 聚合菜谱列表 ----------
    def list(self, request):
        couple = _require_couple(request)

        # 抓所有已打分的条目（跨周）
        qs = (
            MemoryEntry.objects
            .filter(memory__couple=couple,
                    ai_score__isnull=False,
                    recipe__isnull=False)
            .select_related("recipe")
            .prefetch_related("media")  # 预加载 media
            .order_by("recipe__name", "-created_at")
        )

        data: dict[int, dict] = {}
        for e in qs:
            rid = e.recipe_id
            rec = e.recipe
            slot = data.setdefault(
                rid,
                {
                    "recipe_id"     : rid,
                    "recipe_name"   : rec.name,
                    "last_cooked"   : e.created_at,
                    "winner_entry"  : None,
                    "cover_photo"   : None,
                    "entries_count" : 0,
                    "total_score"   : 0,
                    "winner_entries": 0,
                },
            )
            
            # 更新统计数据
            slot["entries_count"] += 1
            if e.ai_score and e.ai_score >= 70:
                slot["total_score"] += 1
                
            # 更新时间
            if e.created_at > slot["last_cooked"]:
                slot["last_cooked"] = e.created_at
                
            # 只取第一张图作封面
            if slot["cover_photo"] is None:
                media = e.media.first()
                if media and media.media:
                    try:
                        slot["cover_photo"] = media.media.url
                    except ValueError:
                        pass

        # 标记周冠军对应的 recipe
        for cm in (
            CoupleMemory.objects
            .filter(couple=couple, winner_entry__isnull=False)
            .select_related("winner_entry__recipe")
        ):
            rid = cm.winner_entry.recipe_id
            if rid in data:
                data[rid]["winner_entries"] += 1
                if data[rid]["winner_entry"] is None:
                    data[rid]["winner_entry"] = cm.winner_entry_id

        # 添加额外的计算字段
        for slot in data.values():
            slot["is_unlocked"] = slot["total_score"] > 0
            slot["mastery_level"] = min(3, slot["entries_count"] // 2 + 1) if slot["is_unlocked"] else 0

        return Response(list(data.values()))

    # ---------- 2. 单菜历史记录 ----------
    def retrieve(self, request, pk=None):
        couple = _require_couple(request)  # 🔥 这里是问题所在！之前忘记定义了
        recipe = get_object_or_404(Recipe, pk=pk)

        entries = (
            MemoryEntry.objects
            .filter(memory__couple=couple,
                    recipe=recipe,
                    ai_score__isnull=False)
            .select_related("author", "memory")
            .prefetch_related("media", "comments")
            .order_by("-created_at")
        )

        # 按日期分组
        grouped = defaultdict(list)
        for e in entries:
            grouped[e.created_at.strftime("%Y-%m-%d")].append(e)

        by_date = [
            {
                "date"   : date,
                "entries": MemoryEntryReadSerializer(ents, many=True,
                            context={"request": request}).data,
            }
            for date, ents in sorted(grouped.items(), reverse=True)
        ]

        return Response({
            "recipe"         : RecipeSerializer(recipe,
                                 context={"request": request}).data,
            "entries_by_date": by_date,
        })


# ═══════════════════════════════════════════════════════════════
# Admin AI Comment Handler
# ═══════════════════════════════════════════════════════════════
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse

@staff_member_required
def admin_ai_comment_handler(request):
    """handle an AI judgment requested from the admin; writes only the AIJudgment record"""
    action = request.GET.get('action')
    entry_id = request.GET.get('entry_id')
    
    if not entry_id:
        messages.error(request, "❌ Missing entry_id parameter")
        return HttpResponseRedirect('/admin/couplememory/memoryentry/')
    
    try:
        entry = MemoryEntry.objects.get(id=entry_id)
        
        if action == 'regenerate':
            # Regenerate AI analysis - directly update AIJudgment record
            from cookai.backend import OpenAIBackend
            from cookai.scoring import ScoringService
            
            highlight_media = entry.media.filter(is_highlight=True).first()
            if not highlight_media:
                highlight_media = entry.media.first()
            
            if highlight_media:
                # Call OpenAI to get new AI analysis
                image_url = f"http://localhost:911{highlight_media.media.url}"
                ai_result = OpenAIBackend.score_images_detailed([image_url])
                
                # Save to AIJudgment record (one-to-one relationship)
                ScoringService._handle_scoring_result(entry, ai_result, 'couplememory')
                
                # Update entry's basic score
                entry.ai_score = ai_result.get('overall_score')
                entry.save(update_fields=['ai_score'])
                
                # Get updated analysis information
                judgment = entry.ai_judgment
                ai_comment = judgment.ai_comment if judgment else "AI analysis record not found"
                
                messages.success(request, f"✅ Entry #{entry_id} AI analysis regenerated successfully!")
                messages.info(request, f"🤖 AI Analysis: {ai_comment}")
                messages.info(request, f"📊 Total Score: {ai_result.get('overall_score', 'N/A')}")
            else:
                messages.error(request, f"❌ Entry #{entry_id} has no image files")
        else:
            messages.error(request, f"❌ Unknown action: {action}")
            
    except MemoryEntry.DoesNotExist:
        messages.error(request, f"❌ Entry #{entry_id} does not exist")
    except Exception as e:
        messages.error(request, f"❌ AI analysis generation failed: {str(e)}")
    
    # Redirect back to admin page
    return HttpResponseRedirect(f'/admin/couplememory/memoryentry/{entry_id}/change/')
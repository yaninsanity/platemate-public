"""
🤖 Cookai Scoring Service
Centralized AI scoring service for image scoring and analysis tasks
Completely independent of business models, providing clean AI functionality interface
"""
'''
import logging
import threading
from typing import Dict, Any, Optional
from django.apps import apps
from .backend import OpenAIBackend

logger = logging.getLogger(__name__)


class ScoringService:
    """
    🎯 AI scoring service - Pure AI functionality, independent of specific business models
    Provides unified AI scoring interface for other modules to call
    """
    
    @classmethod
    def score_memory_entry(cls, entry_id: int, callback_module: str = 'couplememory') -> None:
        """
        Async scoring for memory entry
        
        Args:
            entry_id: Memory entry ID
            callback_module: Callback module name for business logic decoupling
        """
        thread = threading.Thread(
            target=cls._score_entry_task,
            args=(entry_id, callback_module),
            daemon=True
        )
        thread.start()
        logger.info(f"AI scoring task queued for entry {entry_id}")
    
    @classmethod
    def _score_entry_task(cls, entry_id: int, callback_module: str) -> None:
        """
        Internal task: Execute AI scoring
        """
        try:
            # Get models (decoupled approach)
            MemoryEntry = apps.get_model(callback_module, "MemoryEntry")
            MemoryMedia = apps.get_model(callback_module, "MemoryMedia")
            
            entry = MemoryEntry.objects.get(pk=entry_id)
            
            # Get image
            media = (
                MemoryMedia.objects.filter(entry=entry, is_highlight=True).first()
                or MemoryMedia.objects.filter(entry=entry).order_by("created_at").first()
            )
            
            if not media:
                logger.warning(f"No media found for entry {entry_id}")
                return
            
            # Fix image URL
            media_url = cls._fix_media_url(media.media.url)
            logger.info(f"Scoring image: {media_url}")
            
            # Execute AI scoring with recipe context
            score_data = cls._perform_scoring(media_url, entry)
            
            # Handle result via business module callback
            cls._handle_scoring_result(entry, score_data, callback_module)
            
        except Exception as e:
            logger.exception(f"AI scoring task failed for entry {entry_id}: {e}")
    
    @classmethod
    def _fix_media_url(cls, media_url: str) -> str:
        """
        Fix media URL, handle Docker internal address conversion
        """
        if not media_url:
            return media_url
        
        # Docker internal address conversion
        if media_url.startswith("http://web:"):
            from django.conf import settings
            media_url = media_url.replace("http://web:", f"{settings.DEFAULT_HOST}:")
        
        # Complete relative URL
        if not media_url.startswith('http'):
            from django.conf import settings
            base_url = getattr(settings, 'DEFAULT_HOST', 'http://localhost:911')
            media_url = f"{base_url}{media_url}"
        
        return media_url
    
    @classmethod
    def _perform_scoring(cls, media_url: str, entry=None) -> Dict[str, Any]:
        """
        Execute AI scoring with recipe context; no artificial fallbacks. Errors bubble up for admin retry.
        """
        try:
            # build the recipe context when the entry carries recipe data
            recipe_context = None
            if entry and hasattr(entry, 'recipe') and entry.recipe:
                recipe = entry.recipe
                
                # fetch the recipe ingredients
                ingredients = []
                if hasattr(recipe, 'ingredientinrecipe_set'):
                    ingredients = [
                        {
                            'name': ing.ingredient.name if hasattr(ing, 'ingredient') else str(ing),
                            'quantity': getattr(ing, 'quantity', '适量')
                        }
                        for ing in recipe.ingredientinrecipe_set.all()
                    ]
                
                recipe_context = {
                    'name': recipe.name,
                    'instructions': getattr(recipe, 'instructions', ''),
                    'ingredients': ingredients
                }
                
                logger.info(f"🍳 Scoring with recipe context: {recipe.name} ({len(ingredients)} ingredients)")
            
            score_data = OpenAIBackend.score_images_detailed([media_url], recipe_context, memory_entry_id=entry.id)
            logger.info(f"AI scoring successful: {score_data['overall_score']:.1f} points")
            return score_data
        except Exception as e:
            logger.error(f"AI scoring failed (no fallback will be used): {e}")
            # Re-raise to let caller decide (admin can retry, signals will skip saving)
            raise
    
    # ⚠️ the duplicate definition was removed; see the single version at line 383


# Backward compatible function alias
async_score_entry = ScoringService.score_memory_entry

# Simple sync function for direct model calls
def score_memory_entry(entry):
    """
    Simple sync function for direct MemoryEntry model calls
    Automatically async processing, non-blocking main thread
    
    Args:
        entry: MemoryEntry instance
    
    Returns:
        bool: Whether scoring task started successfully
    """
    try:
        ScoringService.score_memory_entry(entry.id)
        return True
    except Exception as e:
        logger.error(f"Failed to start scoring for entry {entry.id}: {e}")
        return False
'''
import logging
import threading
from typing import Dict, Any, Optional
from django.apps import apps
from .backend import OpenAIBackend

logger = logging.getLogger(__name__)


class ScoringService:
    """
    🎯 AI评分服务 - 纯净的AI功能，不依赖具体业务模型
    提供统一的AI评分接口，供其他模块调用
    """
    
    @classmethod
    def score_memory_entry(cls, entry_id: int, callback_module: str = 'couplememory') -> None:
        """
        异步评分记忆条目
        
        Args:
            entry_id: 记忆条目ID
            callback_module: 回调模块名，用于解耦业务逻辑
        """
        thread = threading.Thread(
            target=cls._score_entry_task,
            args=(entry_id, callback_module),
            daemon=True
        )
        thread.start()
        logger.info(f"🤖 AI scoring task queued for entry {entry_id}")
    
    @classmethod
    def _score_entry_task(cls, entry_id: int, callback_module: str) -> None:
        """
        内部任务：执行AI评分
        """
        try:
            # 获取模型（解耦方式）
            MemoryEntry = apps.get_model(callback_module, "MemoryEntry")
            MemoryMedia = apps.get_model(callback_module, "MemoryMedia")
            
            entry = MemoryEntry.objects.get(pk=entry_id)
            
            # 获取图片
            media = (
                MemoryMedia.objects.filter(entry=entry, is_highlight=True).first()
                or MemoryMedia.objects.filter(entry=entry).order_by("created_at").first()
            )
            
            if not media:
                logger.warning(f"Entry {entry_id} has no images, skipping AI scoring")
                return
            
            # 修复图片URL
            media_url = cls._fix_media_url(media.media.url)
            logger.info(f"🔗 Scoring image: {media_url}")
            
            # 执行AI评分（带recipe context）
            score_data = cls._perform_scoring(media_url, entry)
            
            # 回调业务模块处理结果
            cls._handle_scoring_result(entry, score_data, callback_module)
            
        except Exception as e:
            logger.exception(f"🚨 AI scoring task failed for entry {entry_id}: {e}")
    
    @classmethod
    def _fix_media_url(cls, media_url: str) -> str:
        """
        修复媒体URL，处理Docker内部地址转换
        """
        if not media_url:
            return media_url
        
        # Docker内部地址转换
        if media_url.startswith("http://web:"):
            from django.conf import settings
            media_url = media_url.replace("http://web:", f"{settings.DEFAULT_HOST}:")
        
        # 补全相对URL
        if not media_url.startswith('http'):
            from django.conf import settings
            base_url = getattr(settings, 'DEFAULT_HOST', 'http://localhost:911')
            media_url = f"{base_url}{media_url}"
        
        return media_url
    
    @classmethod
    def _perform_scoring(cls, media_url: str, entry=None) -> Dict[str, Any]:
        """
        score with the recipe context; no manual fallback, errors surface for an admin retry
        """
        try:
            # build the recipe context when the entry carries recipe data
            recipe_context = None
            if entry and hasattr(entry, 'recipe') and entry.recipe:
                recipe = entry.recipe
                
                # fetch the recipe ingredients
                ingredients = []
                if hasattr(recipe, 'ingredientinrecipe_set'):
                    ingredients = [
                        {
                            'name': ing.ingredient.name if hasattr(ing, 'ingredient') else str(ing),
                            'quantity': getattr(ing, 'quantity', '适量')
                        }
                        for ing in recipe.ingredientinrecipe_set.all()
                    ]
                
                recipe_context = {
                    'name': recipe.name,
                    'instructions': getattr(recipe, 'instructions', ''),
                    'ingredients': ingredients
                }
                
                logger.info(f"🍳 使用recipe context评分: {recipe.name}")
            
            score_data = OpenAIBackend.score_images_detailed([media_url], recipe_context)
            logger.info(f"✅ AI评分成功: {score_data['overall_score']:.1f}分")
            return score_data
        except Exception as e:
            logger.error(f"🚨 AI评分失败（不使用fallback）: {e}")
            # raise and let the caller decide: the admin can retry, the signal path skips the save
            raise
    
    @classmethod
    def _handle_scoring_result(cls, entry, score_data: Dict[str, Any], callback_module: str) -> None:
        """
        处理评分结果，通过回调方式解耦业务逻辑
        """
        try:
            # 获取业务模型
            AIJudgment = apps.get_model(callback_module, "AIJudgment")
            MemoryComment = apps.get_model(callback_module, "MemoryComment")
            
            logger.info(f"💾 Saving AI scoring result for entry {entry.id}")
            
            # 🎯 Confidence Score weighted normalisation, folding in the punishment system
            confidence = score_data.get('confidence', 0.8)
            punishment_applied = score_data.get('punishment_applied', 'none')
            
            # adjust confidence by punishment severity
            # 严重惩罚 → 高置信度（我们很确定这是错误的）
            # 无惩罚且高分 → 高置信度（我们很确定这是好的）
            # if punishment_applied == 'severe':
            #     adjusted_confidence = max(confidence, 0.9)  # 严重错误，高置信度
            #     logger.info(f"⚠️ Severe punishment → confidence boosted to {adjusted_confidence}")
            # elif punishment_applied == 'major':
            #     adjusted_confidence = max(confidence, 0.85)  # 主要错误，较高置信度
            #     logger.info(f"⚠️ Major punishment → confidence boosted to {adjusted_confidence}")
            # elif punishment_applied in ['moderate', 'minor']:
            #     adjusted_confidence = confidence  # 小问题，保持原 confidence
            # else:
            #     # 无惩罚：根据分数调整置信度
            #     overall_score = score_data['overall_score']
            #     if overall_score >= 90:
            #         adjusted_confidence = max(confidence, 0.88)  # 高分 → 高置信度
            #     elif overall_score <= 40:
            #         adjusted_confidence = max(confidence, 0.85)  # 低分 → 高置信度（确实不好）
            #     else:
            #         adjusted_confidence = confidence  # 中等分数保持原值
            
            # 🎯 应用 Confidence 加权到最终得分（标准化）
            # 低置信度 → 向平均分 75 回归
            base_score = score_data['overall_score']
            # weighted_score = (base_score * adjusted_confidence) + (75 * (1 - adjusted_confidence))
            
            # logger.info(f"📊 Score standardization: base={base_score:.1f}, confidence={adjusted_confidence:.2f}, weighted={weighted_score:.1f}")
            
            # 🎯 3维度评分验证和降级策略
            visual = score_data.get('visual_appeal', 75)
            technique = score_data.get('cooking_technique', 75)
            freshness = score_data.get('ingredient_freshness', 75)
            
            # 检测不完整的3维度数据（全为0或缺失）
            # if visual == 0 and technique == 0 and freshness == 0:
            #     logger.warning(f"⚠️ Incomplete 3D scores detected (all zeros), applying degradation strategy")
                
            #     # degraded path: estimate the three dimensions from overall_score
            #     # if overall_score is also 0, fall back to conservative defaults
            #     if base_score > 0:
            #         # 均匀分配（可以根据实际情况调整比例）
            #         visual = base_score
            #         technique = base_score
            #         freshness = base_score
            #         logger.info(f"   📊 Estimated 3D scores from overall: {base_score:.1f}")
            #     else:
            #         # 完全失败的情况，使用最低可接受分数
            #         visual = technique = freshness = 50.0
            #         logger.warning(f"   ⚠️ Using minimum acceptable scores (50.0) for all dimensions")
            # elif visual == 0 or technique == 0 or freshness == 0:
            #     # 部分维度为0，使用其他维度平均值补充
            #     non_zero_scores = [s for s in [visual, technique, freshness] if s > 0]
            #     if non_zero_scores:
            #         avg_score = sum(non_zero_scores) / len(non_zero_scores)
            #         if visual == 0:
            #             visual = avg_score
            #             logger.info(f"   📊 Estimated visual_appeal from average: {avg_score:.1f}")
            #         if technique == 0:
            #             technique = avg_score
            #             logger.info(f"   📊 Estimated cooking_technique from average: {avg_score:.1f}")
            #         if freshness == 0:
            #             freshness = avg_score
            #             logger.info(f"   📊 Estimated ingredient_freshness from average: {avg_score:.1f}")
            #     else:
            #         # 兜底：使用默认值
            #         visual = visual or 50.0
            #         technique = technique or 50.0
            #         freshness = freshness or 50.0
            
            defaults = {
                'overall_score': round(base_score, 1),  # ✅ 使用未加权的分数
                'visual_appeal': round(visual, 1),
                'cooking_technique': round(technique, 1),
                'ingredient_freshness': round(freshness, 1),
                'individual_comment': score_data.get('individual_comment', score_data.get('ai_comment', '🤖 AI analysis complete')),
                'individual_summary': score_data.get('individual_summary', score_data.get('ai_summary', 'Scored dish')),
                'ai_comment': score_data.get('ai_comment', '🤖 AI analysis complete'),
                'ai_summary': score_data.get('ai_summary', 'Scored dish'),
                'confidence': confidence,  # ✅ 保存未调整的置信度
                'model_version': 'gpt-5',
            }

            ai_judgment, created = AIJudgment.objects.update_or_create(
                entry=entry,
                defaults=defaults
            )
            
            action = "created" if created else "updated"
            logger.info(f"✅ AIJudgment {action} for entry {entry.id} with score {score_data['overall_score']}")
            
            # 🔗 link the AIScoreLog to the AIJudgment when _score_log_id is present
            if '_score_log_id' in score_data:
                try:
                    AIScoreLog = apps.get_model('cookai', 'AIScoreLog')
                    score_log_id = score_data['_score_log_id']
                    score_log = AIScoreLog.objects.get(id=score_log_id)
                    score_log.ai_judgment = ai_judgment
                    score_log.save(update_fields=['ai_judgment'])
                    logger.info(f"📊 Linked AIScoreLog {score_log_id} to AIJudgment {ai_judgment.id}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not link AIScoreLog to AIJudgment: {e}")
            
            # 更新legacy评分字段（向后兼容）
            entry.ai_score = score_data['overall_score']
            entry.save(update_fields=['ai_score'])
            logger.info(f"✅ Updated entry.ai_score to {score_data['overall_score']}")
            
            # 🔧 AI judgment lives only on AIJudgment; no MemoryComment is created
            # AIanalysis belongs in AIJudgment.ai_comment, not in a user comment
            logger.info(f"ℹ️ AI judgment stored in AIJudgment record, not as user comment")
            
            # 更新统计和winner计算
            if hasattr(entry, 'memory'):
                entry.memory.recalc_winner()
                entry.memory.refresh_counters()
                logger.info(f"✅ Updated memory statistics for round {entry.memory.id}")
            
            logger.info(f"🎉 Complete scoring result saved for entry {entry.id}")

            import couplememory.signals as memory_signals

            try:
                logger.info(f"🔍 Checking battle conditions after scoring entry {entry.id}")
                memory_signals._check_and_trigger_couple_battle(entry)
            except Exception as battle_e:
                logger.warning(f"⚠️ Battle check failed after scoring entry {entry.id}: {battle_e}")

        except Exception as e:
            logger.exception(f"🚨 Failed to save scoring result for entry {entry.id}: {e}")


# 向后兼容的函数别名
async_score_entry = ScoringService.score_memory_entry

# 简单同步函数供模型直接调用
def score_memory_entry(entry):
    """
    a plain synchronous helper the MemoryEntry model calls directly
    自动异步处理，不阻塞主线程
    
    Args:
        entry: MemoryEntry 实例
    
    Returns:
        bool: 是否成功启动评分任务
    """
    try:
        ScoringService.score_memory_entry(entry.id)
        return True
    except Exception as e:
        logger.error(f"Failed to start scoring for entry {entry.id}: {e}")
        return False

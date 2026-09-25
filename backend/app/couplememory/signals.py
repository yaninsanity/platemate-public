# apps/couplememory/signals.py
from __future__ import annotations

import logging, threading
from typing import Optional

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import MemoryEntry, MemoryComment, MemoryMedia, CoupleMemory, PHOTO_REWARD_PTS
from petcare.models import Activity, DicePocket

logger = logging.getLogger(__name__)


def _check_and_trigger_couple_battle(entry):
    """
    🥊 battle trigger: wait for the AI judge to finish before comparing
    wait until both users have a complete AIJudgment before running the interactive battle comparison
    """
    try:
        memory = entry.memory
        couple = memory.couple
        
        # 获取当前round中所有entries，按作者分组
        all_entries = memory.entries.select_related('author', 'ai_judgment')
        
        # 按作者分组
        authors_entries = {}
        for e in all_entries:
            author_id = e.author.id
            if author_id not in authors_entries:
                authors_entries[author_id] = []
            authors_entries[author_id].append(e)
        
        # 检查是否有至少两个不同作者
        if len(authors_entries) >= 2:
            authors = list(authors_entries.keys())
            
            # 为每个作者找到最适合battle的entry
            battle_entries = []
            for author_id in authors[:2]:  # 只取前两个作者
                author_entries = authors_entries[author_id]
                
                # prefer an entry that has an AIJudgment with a score
                entries_with_judgment = [e for e in author_entries 
                                       if hasattr(e, 'ai_judgment') and e.ai_judgment 
                                       and e.ai_score is not None]
                
                if entries_with_judgment:
                    # 选择分数最高的entry
                    best_entry = max(entries_with_judgment, key=lambda x: x.ai_score or 0)
                    battle_entries.append(best_entry)
                else:
                    # without a complete AIJudgment, hold the battle back
                    logger.info(f"🕐 Waiting for AI judgment completion for author {author_id}")
                    return
            
            # 确保我们有两个ready的entries
            if len(battle_entries) == 2:
                entry1, entry2 = battle_entries[0], battle_entries[1]
                
                # 检查这两个entries是否都没有battle结果
                needs_battle = True
                if (entry1.ai_judgment and entry1.ai_judgment.battle_result):
                    needs_battle = False
                if (entry2.ai_judgment and entry2.ai_judgment.battle_result):
                    needs_battle = False
                
                if needs_battle:
                    logger.info(f"🥊 AI Judgments ready! Triggering enhanced couple battle: {entry1.author.username} vs {entry2.author.username}")
                    # 异步触发增强的interactive battle
                    threading.Thread(
                        target=_execute_couple_battle,
                        args=(entry1.id, entry2.id),
                        daemon=True
                    ).start()
                else:
                    logger.info(f"⏭️ Battle already completed for {entry1.author.username} vs {entry2.author.username}")
            else:
                logger.info(f"🕐 Waiting for complete AI judgments in round {memory.id}")
        else:
            logger.info(f"🕐 Waiting for more entries in round {memory.id} (current: {len(authors_entries)} authors)")
            
    except Exception as e:
        logger.exception(f"🚨 Failed to check couple battle conditions: {e}")


def _execute_couple_battle(entry1_id: int, entry2_id: int):
    """
    🥊 Kinnyinteractive couple battle system
    fold in the AIJudgment score and voice it as the virtual pet, for a playful couple interaction
    """
    try:
        from cookai.backend import OpenAIBackend
        from couplememory.models import MemoryEntry, AIJudgment
        
        entry1 = MemoryEntry.objects.get(id=entry1_id)
        entry2 = MemoryEntry.objects.get(id=entry2_id)
        
        # 获取两个菜品的最佳图片
        image1_url = safe_best_media_url(entry1)
        image2_url = safe_best_media_url(entry2)
        
        if not image1_url or not image2_url:
            logger.warning(f"🚨 Cannot start battle: missing images for entries {entry1_id}, {entry2_id}")
            return
        
        # 🎯 fetch AI judgment data for the interactive comparison
        judgment1 = getattr(entry1, 'ai_judgment', None)
        judgment2 = getattr(entry2, 'ai_judgment', None)
        
        if not judgment1 or not judgment2:
            logger.warning(f"🚨 Missing AI judgments for battle - entry1: {bool(judgment1)}, entry2: {bool(judgment2)}")
            return
            
        logger.info(f"🥊 Starting Kinny's interactive couple battle with AI judgment integration...")
        
        # 🎯 构建recipe context
        recipe_context = None
        if entry1.recipe or entry2.recipe:
            recipe = entry1.recipe or entry2.recipe
            
            recipe_context = {
                'name': recipe.name,
                'instructions': recipe.instructions,
                'ingredients': []
            }
            
            # 获取ingredients信息
            try:
                from recipes.models import IngredientInRecipe
                ingredients = IngredientInRecipe.objects.filter(recipe=recipe).select_related('ingredient')
                recipe_context['ingredients'] = [
                    {
                        'name': ing.ingredient.name,
                        'quantity': ing.quantity
                    }
                    for ing in ingredients
                ]
                logger.info(f"🍳 Recipe context loaded: {recipe.name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not load recipe ingredients: {e}")
        
        # 🎮 build the enhanced comparison prompt with AI judgment integration
        enhanced_prompt = _build_interactive_comparison_prompt(
            entry1, entry2, judgment1, judgment2, recipe_context
        )
        
        # 调用enhanced comparison API
        battle_result = OpenAIBackend.compare_images(image1_url, image2_url, recipe_context, enhanced_prompt)
        
        # 确定胜负
        winner_idx = battle_result.get("winner", 1)
        if winner_idx == 1:
            winner_entry, loser_entry = entry1, entry2
            winner_judgment, loser_judgment = judgment1, judgment2
        elif winner_idx == 2:
            winner_entry, loser_entry = entry2, entry1
            winner_judgment, loser_judgment = judgment2, judgment1
        else:  # 平局
            winner_entry, loser_entry = entry1, entry2
            winner_judgment, loser_judgment = judgment1, judgment2
        
        # 🎭 更新battle数据 with Kinny's interactive storytelling
        winner_judgment.battle_comment = f"🏆 {battle_result.get('kinny_winner_message', 'Kinny cheers for your victory! 🎉')}"
        winner_judgment.battle_summary = f"Triumphed over {loser_entry.author.username}"
        
        loser_judgment.battle_comment = f"💪 {battle_result.get('kinny_loser_message', 'Kinny believes in your potential! Keep cooking! 🌟')}"
        loser_judgment.battle_summary = f"Brave challenge vs {winner_entry.author.username}"
        
        # 保存battle结果
        for judgment in [winner_judgment, loser_judgment]:
            judgment.battle_result = battle_result
            judgment.save()
        
        logger.info(f"🏆 Kinny's interactive battle completed: {winner_entry.author.username} wins vs {loser_entry.author.username}")
        
        # 重新计算round winner
        entry1.memory.recalc_winner()
        
    except Exception as e:
        logger.exception(f"🚨 Kinny's couple battle execution failed: {e}")


def _build_interactive_comparison_prompt(entry1, entry2, judgment1, judgment2, recipe_context):
    """
    🎮 build the interactive comparison prompt for Kinny
    fold in the AI judgment to make the couple interaction playful
    """
    # 🎯 resolves a display name that works in every case
    def get_display_name(author):
        """精准获取用户显示名称，处理各种edge cases"""
        if hasattr(author, 'first_name') and author.first_name and author.first_name.strip():
            return author.first_name.strip()
        elif hasattr(author, 'last_name') and author.last_name and author.last_name.strip():
            return author.last_name.strip()
        elif hasattr(author, 'username') and author.username:
            return author.username
        else:
            return "Unknown User"  # 最后的fallback
    
    user1_name = get_display_name(entry1.author)
    user2_name = get_display_name(entry2.author)
    
    # 获取individual scoring数据
    score1_data = {
        'overall': judgment1.overall_score,
        'visual': judgment1.visual_appeal,
        'technique': judgment1.cooking_technique,
        'freshness': judgment1.ingredient_freshness,
        'comment': getattr(judgment1, 'ai_comment', ''),
        'summary': getattr(judgment1, 'ai_summary', ''),
    }
    
    score2_data = {
        'overall': judgment2.overall_score,
        'visual': judgment2.visual_appeal,
        'technique': judgment2.cooking_technique,
        'freshness': judgment2.ingredient_freshness,
        'comment': getattr(judgment2, 'ai_comment', ''),
        'summary': getattr(judgment2, 'ai_summary', ''),
    }
    
    recipe_info = ""
    if recipe_context:
        ingredients_list = ', '.join([ing['name'] for ing in recipe_context.get('ingredients', [])])
        recipe_info = f"""
� RECIPE CHALLENGE: {recipe_context['name']}
📋 Instructions: {recipe_context['instructions']}
🥘 Required Ingredients: {ingredients_list}
"""
    
    interactive_prompt = f"""
🎮 KINNY'S COUPLE COOKING BATTLE ARENA 🎮

💕 Welcome to Kinny's special couple battle! I've been watching {user1_name} and {user2_name} cook with such love and passion!

{recipe_info}

🤖 KINNY'S INDIVIDUAL ASSESSMENTS:

👨‍🍳 {user1_name}'s Dish Analysis:
• Overall Score: {score1_data['overall']:.1f}/100
• Visual Appeal: {score1_data['visual']:.1f} | Technique: {score1_data['technique']:.1f} | Freshness: {score1_data['freshness']:.1f}
• Kinny's Previous Comment: "{score1_data['comment']}"
• Summary: "{score1_data['summary']}"

👩‍🍳 {user2_name}'s Dish Analysis:
• Overall Score: {score2_data['overall']:.1f}/100
• Visual Appeal: {score2_data['visual']:.1f} | Technique: {score2_data['technique']:.1f} | Freshness: {score2_data['freshness']:.1f}
• Kinny's Previous Comment: "{score2_data['comment']}"
• Summary: "{score2_data['summary']}"

🎯 KINNY'S INTERACTIVE BATTLE MISSION:
As your adorable virtual pet chef, I want to create a fun, loving comparison that brings you two closer together! 

🏆 Enhanced Comparison Criteria:
1. Recipe Adherence (if recipe provided) - Most Important!
2. Cooking Skills shown in both individual assessments
3. Visual presentation that would make Kinny proud
4. How each dish reflects the love put into cooking
5. Potential for couple bonding and learning from each other

💝 KINNY'S COUPLE INTERACTION GOALS:
- Create playful competitive spirit
- Highlight each person's strengths
- Suggest cute ways they can learn from each other
- Plant seeds for future cooking adventures together
- Make both feel loved and appreciated

Return enhanced JSON with these additional fields:
{{
  "winner": 1 or 2,
  "reason": "Detailed comparison considering individual assessments",
  "kinny_winner_message": "Cute congratulatory message with couple interaction hints",
  "kinny_loser_message": "Encouraging message with learning opportunities",
  "kinny_couple_story": "Sweet narrative about their cooking journey together",
  "future_cooking_suggestions": ["Cute ideas for cooking together"]
}}

🎭 KINNY'S PERSONALITY TRAITS:
- Playful and encouraging virtual pet
- Loves bringing couples together through food
- Always finds something positive in both dishes
- Creates adorable storylines about couple's cooking adventures
- Suggests fun ways to improve together

💕 Remember: This isn't just about winning - it's about celebrating love through cooking!
"""
    
    return interactive_prompt


# ─────────────────────── helpers ────────────────────────────
def _first_partner(couple) -> Optional[object]:
    """tolerates different related_names; takes the first user."""
    for attr in ("users", "members", "partners", "user_set"):
        if hasattr(couple, attr):
            return getattr(couple, attr).first()
    return None


def safe_best_media_url(entry: MemoryEntry) -> Optional[str]:
    """
    same behaviour as the old best_media_url(), but never raises ValueError.
    """
    try:
        media = entry.media.order_by("-created_at").first()
        return media.media.url if media and getattr(media.media, "name", "") else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# async scorer - 使用cookai模块的干净接口
# ─────────────────────────────────────────────────────────────
def _score_in_background(entry_id: int):
    """
    后台线程：使用cookai模块的干净接口进行AI评分
    once scoring finishes, check whether a couple battle should start
    """
    try:
        from cookai.scoring import ScoringService
        from couplememory.models import MemoryEntry
        
        # 执行AI评分
        ScoringService.score_memory_entry(entry_id)
        logger.info(f"✅ AI scoring completed for entry {entry_id}")
        
        # after scoring, check whether a couple battle should start
        try:
            entry = MemoryEntry.objects.get(id=entry_id)
            logger.info(f"🔍 Checking battle conditions after scoring entry {entry_id}")
            _check_and_trigger_couple_battle(entry)
        except Exception as battle_e:
            logger.warning(f"⚠️ Battle check failed after scoring entry {entry_id}: {battle_e}")
            
    except Exception as e:
        logger.exception(f"🚨 Failed to trigger AI scoring for entry {entry_id}: {e}")


def _touch_round(cm: CoupleMemory):
    """刷新周统计数据（非阻塞）"""
    try:
        cm.recalc_winner()
        cm.refresh_counters()
    except Exception as e:
        logger.exception(f"Failed to refresh round stats: {e}")


# ─────────────────────────────────────────────────────────────
# signal receivers
# ─────────────────────────────────────────────────────────────

@receiver(post_save, sender=MemoryEntry)
def on_entry_saved(sender, instance: MemoryEntry, created: bool, **kwargs):
    """
    MemoryEntry 保存时触发：
    1. 新条目 → 奖励 + 自动 AI 打分
    2. 编辑条目且无评分 → 重新 AI 打分
    """
    couple = instance.memory.couple
    cm = instance.memory

    if created:
        # ① 上传奖励
        Activity.create_generic(couple, Activity.PHOTO, meta={"entry_id": instance.pk})
        DicePocket.earn(_first_partner(couple), PHOTO_REWARD_PTS)

        # ② 后台 AI 打分（非阻塞）
        threading.Thread(
            target=_score_in_background, args=(instance.pk,), daemon=True
        ).start()
    else:
        # 若编辑过且仍无分数 → 尝试再次打分
        if instance.ai_score is None:
            threading.Thread(
                target=_score_in_background, args=(instance.pk,), daemon=True
            ).start()

    # 基础统计刷新
    _touch_round(cm)


@receiver(post_save, sender=MemoryComment)
def on_comment_saved(sender, instance: MemoryComment, created: bool, **kwargs):
    """
    MemoryComment 保存时触发：活动记录 + 奖励 + 刷新统计
    """
    if created:
        couple = instance.entry.memory.couple
        # Activity 没有 COMMENT 枚举，这里使用“夸奖/互动”类型 COMPLIMENT 记录用户互动
        Activity.create_generic(couple, Activity.COMPLIMENT, meta={"comment_id": instance.pk})
        DicePocket.earn(_first_partner(couple), 1)

    # 每次评论都刷新统计
    _touch_round(instance.entry.memory)


@receiver(post_save, sender=MemoryMedia)
def on_media_saved(sender, instance: MemoryMedia, created: bool, **kwargs):
    """
    🔥 saving a MemoryMedia kicks off scoring
    这是 AI 评分系统的主要入口点
    """
    if not created:
        return  # 只在新建时触发
    
    entry = instance.entry
    
    # 获取日志记录器
    logger.info(f"🖼️ MemoryMedia created: ID={instance.id}, entry={entry.id}, highlight={instance.is_highlight}")
    
    # 判断是否需要触发 AI 评分
    should_trigger_scoring = False
    trigger_reason = ""
    
    # 条件 1: 这是 highlight 图片
    if instance.is_highlight:
        should_trigger_scoring = True
        trigger_reason = "highlight_image"
        logger.info(f"🌟 Highlight image uploaded for entry {entry.id}")
    
    # 条件 2: first image on this entry, and the entry has no AI score yet
    elif not entry.media.exclude(id=instance.id).exists() and entry.ai_score is None:
        should_trigger_scoring = True
        trigger_reason = "first_image_no_score"
        logger.info(f"📸 First image for entry {entry.id} with no AI score")
    
    # 条件 3: entry 有 AI 评判但置信度较低，需要重新评分
    elif (hasattr(entry, 'ai_judgment') and entry.ai_judgment and 
          getattr(entry.ai_judgment, 'confidence', 1.0) < 0.5):
        should_trigger_scoring = True
        trigger_reason = "low_confidence_rescore"
        logger.info(f"🔄 Low confidence AI judgment for entry {entry.id}, rescoring")
    
    # 触发 AI 评分
    if should_trigger_scoring:
        logger.info(f"🤖 Triggering AI scoring for entry {entry.id}, reason: {trigger_reason}")
        
        # 使用延迟启动确保数据库事务完成
        def delayed_scoring():
            threading.Timer(1.0, lambda: threading.Thread(
                target=_score_in_background, 
                args=(entry.id,), 
                daemon=True
            ).start()).start()
        
        # 确保在事务提交后执行
        transaction.on_commit(delayed_scoring)
    else:
        logger.info(f"⏸️ AI scoring not triggered for entry {entry.id} - conditions not met")
    
    # 刷新 round 统计
    _touch_round(entry.memory)

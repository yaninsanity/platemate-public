# cookai/admin.py — minimal-risk, self-contained admin + playground
#
# ▪ zero 3rd-party *requirements* (auto-enables `django-import-export` if present)
# ▪ handy `/admin/cookai/openai-test/` page for three AI modes
# ▪ keeps existing DB schema – only fixes missing imports / wrong field names

from __future__ import annotations

import json
import logging
import time
from typing import List

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

try:
    # optional – makes export / import actions available if installed
    from import_export import resources  # type: ignore
    from import_export.admin import ImportExportModelAdmin  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    resources = None  # type: ignore
    ImportExportModelAdmin = admin.ModelAdmin  # type: ignore

from cookai.models import AIPrompt, AIRequestLog
from cookai.backend import OpenAIBackend

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────
# import-export resources (only if lib present)
# ────────────────────────────────────────────────────────────────
if resources:

    class AIPromptResource(resources.ModelResource):
        class Meta:
            model = AIPrompt
            import_id_fields = ("name",)
            fields = (
                "name",
                "kind",
                "model_name",
                "is_active",
                "template",
                "created_at",
                "updated_at",
            )
            skip_unchanged = True
            report_skipped = True

    class AIRequestLogResource(resources.ModelResource):
        class Meta:
            model = AIRequestLog
            import_id_fields = ("id",)
            fields = (
                "id",
                "kind",
                "latency",
                "created_at",
            )
            skip_unchanged = True
            report_skipped = False
else:
    AIPromptResource = AIRequestLogResource = None  # type: ignore


class _BaseAdmin(ImportExportModelAdmin):  # type: ignore
    """Falls back to plain `ModelAdmin` when `django-import-export` is absent."""

    def __init__(self, *args, **kwargs):
        if resources is None:
            self.resource_class = None  # type: ignore[attr-defined]
        super().__init__(*args, **kwargs)


# ────────────────────────────────────────────────────────────────
# AIPrompt admin
# ────────────────────────────────────────────────────────────────
@admin.register(AIPrompt)
class AIPromptAdmin(_BaseAdmin):
    resource_class   = AIPromptResource  # type: ignore

    list_display     = ("name", "kind", "model_name", "is_active", "updated_at")
    list_editable    = ("model_name", "is_active")
    list_filter      = ("kind", "is_active")
    search_fields    = ("name", "template")
    readonly_fields  = ("created_at", "updated_at")
    change_list_template = "admin/cookai/aiprompt/change_list.html"

    actions = ["activate_prompts", "deactivate_prompts", "sample_test"]

    @admin.action(description="Activate selected")
    def activate_prompts(self, request, qs):
        n = qs.update(is_active=True, updated_at=timezone.localtime(timezone.now()))
        self.message_user(request, f"Activated {n} prompt(s)")

    @admin.action(description="Deactivate selected")
    def deactivate_prompts(self, request, qs):
        n = qs.update(is_active=False, updated_at=timezone.localtime(timezone.now()))
        self.message_user(request, f"Deactivated {n} prompt(s)")

    @admin.action(description="Run sample test via OpenAI")
    def sample_test(self, request, qs):
        samples = {
            AIPrompt.KIND_SCORE:   ["https://picsum.photos/seed/1/300"],
            AIPrompt.KIND_COMPARE: ["https://picsum.photos/seed/2/300", "https://picsum.photos/seed/3/300"],
            AIPrompt.KIND_DETECT:  ["https://picsum.photos/seed/4/300"],
        }
        for p in qs:
            try:
                if p.kind == AIPrompt.KIND_SCORE:
                    s, r = OpenAIBackend.score_images(samples[p.kind])
                    msg = f"score={s} reason={r[:40]}…"
                elif p.kind == AIPrompt.KIND_COMPARE:
                    msg = json.dumps(OpenAIBackend.compare_images(*samples[p.kind]))
                else:
                    det, match = OpenAIBackend.detect_ingredients(samples[p.kind][0], [])
                    msg = f"{det} | match={match}"
                self.message_user(request, f"{p.name}: {msg}")
            except Exception as exc:
                logger.exception("playground sample_test error")
                self.message_user(request, f"{p.name}: {exc}", level=messages.ERROR)


# ────────────────────────────────────────────────────────────────
# AIRequestLog admin – read-only, lightweight
# ────────────────────────────────────────────────────────────────
@admin.register(AIRequestLog)
class AIRequestLogAdmin(_BaseAdmin):
    resource_class    = AIRequestLogResource  # type: ignore

    list_display      = ("id", "kind", "latency", "created_at")
    list_filter       = ("kind", "created_at")
    readonly_fields   = ("prompt", "response", "latency", "created_at")
    ordering          = ("-created_at",)

    def has_add_permission(self, *a, **kw):    return False
    def has_change_permission(self, *a, **kw): return False
    def has_delete_permission(self, *a, **kw): return False


# ────────────────────────────────────────────────────────────────
# 🎯 AIScoreLog admin – 精准查看和测试 AI 评分
# ────────────────────────────────────────────────────────────────
from cookai.models import AIScoreLog

@admin.register(AIScoreLog)
class AIScoreLogAdmin(_BaseAdmin):
    """
    🎯 AI 评分日志管理 - 精准查看每条评分请求的完整细节
    
    功能：
    1. 查看完整的 prompt（包含 TIER 系统）
    2. 查看所有输入图片和 Base64 数据
    3. 查看 recipe context（食谱信息）
    4. 查看完整的 API 请求参数和响应
    5. 在 Admin 中重新运行相同的评分请求
    6. 比对不同时间的评分结果
    """
    
    list_display = (
        'id_short',
        'memory_entry_link',
        'status_badge',
        'score_quick_view',
        'model_name',
        'latency_display',
        'created_at'
    )
    list_filter = ('status', 'model_name', 'created_at')
    search_fields = ('id', 'memory_entry__id', 'recipe_context__name')
    
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'memory_entry_link_full',
        'ai_judgment_link',
        'status_badge',
        'score_display',
        'image_preview',
        'recipe_info_display',
        'prompt_display',
        'api_request_display',
        'api_response_display',
        'performance_metrics'
    )
    
    fieldsets = (
        ('📊 基本信息', {
            'fields': (
                'id',
                'memory_entry_link_full',
                'ai_judgment_link',
                'status_badge',
                'created_at',
                'updated_at'
            )
        }),
        ('📸 输入数据 - 图片', {
            'fields': (
                'image_preview',
                'image_urls',
            ),
            'classes': ('collapse',)
        }),
        ('🍳 输入数据 - Recipe Context', {
            'fields': (
                'recipe_info_display',
                'recipe_context',
            ),
            'classes': ('collapse',)
        }),
        ('💬 Prompt 详情', {
            'fields': (
                'prompt_display',
                'full_prompt',
            ),
            'classes': ('collapse',)
        }),
        ('🤖 API 请求', {
            'fields': (
                'model_name',
                'api_request_display',
                'api_request_params',
            ),
            'classes': ('collapse',)
        }),
        ('✅ API 响应', {
            'fields': (
                'api_response_display',
                'api_response',
            ),
            'classes': ('collapse',)
        }),
        ('🎯 评分结果', {
            'fields': (
                'score_display',
                'parsed_score',
            ),
            'classes': ('collapse',)
        }),
        ('⚡ 性能指标', {
            'fields': (
                'performance_metrics',
                'latency',
                'token_count',
            )
        }),
        ('❌ 错误信息', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['rerun_scoring', 'export_for_testing']
    
    def id_short(self, obj):
        """显示短 ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def memory_entry_link(self, obj):
        """Entry 链接（列表）"""
        if obj.memory_entry:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:couplememory_memoryentry_change', args=[obj.memory_entry.id])
            return format_html('<a href="{}">{}</a>', url, f"Entry {obj.memory_entry.id}")
        return "-"
    memory_entry_link.short_description = 'Entry'
    
    def memory_entry_link_full(self, obj):
        """Entry 详细链接"""
        if obj.memory_entry:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:couplememory_memoryentry_change', args=[obj.memory_entry.id])
            recipe = obj.memory_entry.recipe.name if obj.memory_entry.recipe else "无食谱"
            return format_html(
                '<a href="{}" target="_blank">📝 Entry {} | {}</a>',
                url,
                obj.memory_entry.id,
                recipe
            )
        return "-"
    memory_entry_link_full.short_description = 'Memory Entry'
    
    def ai_judgment_link(self, obj):
        """AIJudgment 链接"""
        if obj.ai_judgment:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:couplememory_aijudgment_change', args=[obj.ai_judgment.id])
            score = obj.ai_judgment.overall_score
            return format_html(
                '<a href="{}" target="_blank">🤖 AIJudgment {} | Score: {:.1f}</a>',
                url,
                obj.ai_judgment.id,
                score
            )
        return "-"
    ai_judgment_link.short_description = 'AI Judgment'
    
    def status_badge(self, obj):
        """状态徽章"""
        from django.utils.html import format_html
        colors = {
            'pending': '#FFA500',
            'success': '#28a745',
            'failed': '#dc3545',
            'timeout': '#6c757d'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_badge.short_description = '状态'
    
    def score_quick_view(self, obj):
        """快速查看分数"""
        if obj.parsed_score and obj.is_success:
            score = obj.parsed_score.get('overall_score', 0)
            return f"{score:.1f}"
        return "-"
    score_quick_view.short_description = '总分'
    
    def latency_display(self, obj):
        """延迟显示"""
        if obj.latency > 0:
            return f"{obj.latency:.2f}s"
        return "-"
    latency_display.short_description = '延迟'
    
    def image_preview(self, obj):
        """🖼️ 完整高清图片预览 - 用于精准视觉验证"""
        from django.utils.html import format_html
        if not obj.image_urls and not obj.image_base64_data:
            return "无图片"
        
        html = '<div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">'
        
        # 📊 数据重量分析（顶部显示，帮助诊断问题）
        if obj.image_base64_data:
            data_size_kb = len(obj.image_base64_data) / 1024
            data_size_mb = data_size_kb / 1024
            
            # 判断图片质量
            if data_size_kb < 20:
                quality_badge = '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⚠️ 极低质量</span>'
                quality_note = '<p style="color: #dc3545; font-weight: bold;">� 图片太小！可能严重影响 AI 评分质量！</p>'
            elif data_size_kb < 50:
                quality_badge = '<span style="background: #ffc107; color: #000; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⚠️ 低质量</span>'
                quality_note = '<p style="color: #856404; font-weight: bold;">⚠️ 图片质量较低，可能影响 AI 评分准确性</p>'
            elif data_size_kb < 200:
                quality_badge = '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">✅ 良好质量</span>'
                quality_note = '<p style="color: #155724; font-weight: bold;">✅ 图片质量适中，足够 AI 分析</p>'
            else:
                quality_badge = '<span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">🏆 高清质量</span>'
                quality_note = '<p style="color: #004085; font-weight: bold;">🏆 高清图片，AI 能获取最佳细节！</p>'
            
            html += f'''
            <div style="background: #fff; border: 3px solid #007bff; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="color: #007bff; margin-top: 0; display: flex; align-items: center; gap: 10px;">
                    📊 Input 数据重量分析 {quality_badge}
                </h3>
                {quality_note}
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Base64 字符数</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{len(obj.image_base64_data):,} chars</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">估算大小 (KB)</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong style="color: #007bff; font-size: 16px;">{data_size_kb:.2f} KB</strong></td>
                    </tr>
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">估算大小 (MB)</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong style="color: #007bff; font-size: 16px;">{data_size_mb:.3f} MB</strong></td>
                    </tr>
                </table>
                <p style="margin-top: 10px; color: #6c757d; font-size: 12px;">
                    💡 提示：高质量图片（200KB+）能显著提升 AI 评分准确性
                </p>
            </div>
            '''
        
        # 🤖 AI 实际看到的图片（完整高清显示，不限制尺寸）
        if obj.image_base64_data:
            html += '<div style="background: white; border: 3px solid #28a745; border-radius: 8px; padding: 20px; margin-bottom: 20px;">'
            html += '<h3 style="color: #28a745; margin-top: 0;">🤖 AI 实际接收的图片 (完整分辨率)</h3>'
            html += '<p style="color: #155724; font-weight: bold; font-size: 14px;">✨ 这是 AI 看到的完整图片 - 用于精准视觉验证</p>'
            
            # 显示完整高清图片（移除尺寸限制，保持原始分辨率）
            if obj.image_base64_data.startswith('data:image'):
                html += f'''
                <div style="border: 3px dashed #28a745; padding: 15px; background: #f0fff4; text-align: center;">
                    <img src="{obj.image_base64_data}" 
                         style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" 
                         alt="AI Input Image - Full Resolution" />
                    <p style="margin-top: 15px; color: #28a745; font-weight: bold; font-size: 14px;">⬆️ full-resolution image at original quality, click to enlarge</p>
                </div>
                '''
            else:
                html += f'''
                <div style="border: 3px dashed #28a745; padding: 15px; background: #f0fff4; text-align: center;">
                    <img src="data:image/jpeg;base64,{obj.image_base64_data}" 
                         style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" 
                         alt="AI Input Image - Full Resolution" />
                    <p style="margin-top: 15px; color: #28a745; font-weight: bold; font-size: 14px;">⬆️ full-resolution image at original quality, click to enlarge</p>
                </div>
                '''
            html += '</div>'
        
        # 📸 原始 URL 图片（对比用）
        if obj.image_urls:
            html += '<div style="background: white; border: 2px solid #6c757d; border-radius: 8px; padding: 20px;">'
            html += '<h4 style="color: #6c757d; margin-top: 0;">📸 原始图片 URL (对比参考):</h4>'
            html += '<div style="display: flex; gap: 15px; flex-wrap: wrap;">'
            for i, url in enumerate(obj.image_urls[:3], 1):
                html += f'''
                <div style="border: 1px solid #dee2e6; padding: 10px; border-radius: 5px; background: #f8f9fa;">
                    <p style="font-size: 11px; color: #6c757d; margin: 0 0 5px 0;">图片 {i}</p>
                    <img src="{url}" style="max-width: 200px; max-height: 200px; border-radius: 3px;" />
                    <p style="font-size: 10px; color: #6c757d; margin: 5px 0 0 0; word-break: break-all;">{url[:50]}...</p>
                </div>
                '''
            html += '</div>'
            html += '</div>'
        
        html += '</div>'
        return format_html(html)
    image_preview.short_description = '🖼️ 完整图片预览'
    
    def recipe_info_display(self, obj):
        """Recipe 信息显示"""
        from django.utils.html import format_html
        if obj.recipe_context:
            rc = obj.recipe_context
            name = rc.get('name', 'N/A')
            instructions = rc.get('instructions', 'N/A')
            ingredients = rc.get('ingredients', [])
            
            html = f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <h4 style="margin-top: 0;">🍳 {name}</h4>
                <p><strong>做法：</strong><br/>{instructions[:200]}{'...' if len(instructions) > 200 else ''}</p>
                <p><strong>食材：</strong></p>
                <ul>
            """
            for ing in ingredients[:10]:  # 最多显示10个
                ing_name = ing.get('name', str(ing))
                html += f"<li>{ing_name}</li>"
            if len(ingredients) > 10:
                html += f"<li><em>...还有 {len(ingredients) - 10} 个食材</em></li>"
            html += "</ul></div>"
            return format_html(html)
        return "无 Recipe Context"
    recipe_info_display.short_description = 'Recipe 信息'
    
    def prompt_display(self, obj):
        """完整的 AI Input 显示（system + user + image）"""
        from django.utils.html import format_html
        
        html = '<div style="background: #f8f9fa; padding: 20px; border-radius: 5px;">'
        
        # 🚀 最重要：显示最终发送给API的完整拼接字符串
        final_input_string = obj.api_request_params.get('final_input_string', None)
        if final_input_string:
            html += '<h3 style="color: #dc3545; margin-top: 0; background: #fff3cd; padding: 10px; border-radius: 5px;">🚀 the exact string sent to the API</h3>'
            html += f'<pre style="background: #fff3cd; padding: 15px; border-radius: 5px; max-height: 500px; overflow-y: auto; white-space: pre-wrap; border: 3px solid #ffc107; font-family: monospace; font-size: 13px;">{final_input_string[:3000]}...\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n[Total: {len(final_input_string):,} chars]\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</pre>'
            html += '<p style="color: #856404; font-weight: bold; margin-top: 10px;">⬆️ this is the exact prompt text the model received. System + User拼接后的最终字符串</p>'
        else:
            html += '<h3 style="color: #dc3545;">⚠️ 未找到最终拼接字符串</h3>'
            html += '<p style="color: #dc3545;">this log may predate the current format; re-run scoring for complete data</p>'
        
        html += '<hr style="margin: 30px 0; border: none; border-top: 2px dashed #ccc;" />'
        
        # 1. System Message（详细展开）
        system_msg = obj.api_request_params.get('system_message', 'N/A')
        html += '<h3 style="color: #007bff; margin-top: 0;">📋 System Message (AI 系统指令)</h3>'
        html += f'<pre style="background: #e7f3ff; padding: 15px; border-radius: 5px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; border-left: 4px solid #007bff;">{system_msg[:1000]}...\n\n[Total: {len(system_msg):,} chars]</pre>'
        
        # 2. User Prompt（详细展开）
        prompt = obj.full_prompt
        prompt_html = prompt.replace('TARGET RECIPE', '<strong style="color: #d9534f;">TARGET RECIPE</strong>')
        prompt_html = prompt_html.replace('TIER', '<strong style="color: #5cb85c;">TIER</strong>')
        html += '<h3 style="color: #28a745; margin-top: 20px;">💬 User Prompt (评分任务描述)</h3>'
        html += f'<pre style="background: #d4edda; padding: 15px; border-radius: 5px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; border-left: 4px solid #28a745;">{prompt_html}</pre>'
        
        # 3. Image Data Info
        html += '<h3 style="color: #ffc107; margin-top: 20px;">🖼️ Image Data (图片数据)</h3>'
        if obj.image_base64_data:
            img_len = len(obj.image_base64_data)
            html += f'''
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <p><strong>格式:</strong> Base64 encoded image</p>
                <p><strong>长度:</strong> {img_len:,} 字符</p>
                <p><strong>大小:</strong> ~{img_len/1024:.1f} KB</p>
                <p><strong>预览:</strong> 见上方 "图片预览" 部分查看 decoded 图片</p>
            </div>
            '''
        else:
            html += '<p style="color: #dc3545;">❌ 无图片数据</p>'
        
        # 4. Complete Input Summary
        html += '<h3 style="color: #6c757d; margin-top: 20px;">📋 Complete AI Input Summary</h3>'
        html += '<div style="background: #e9ecef; padding: 15px; border-radius: 5px; border-left: 4px solid #6c757d;">'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += f'<tr><td style="padding: 5px;"><strong>System Message:</strong></td><td>{len(system_msg):,} chars</td></tr>'
        html += f'<tr><td style="padding: 5px;"><strong>User Prompt:</strong></td><td>{len(prompt):,} chars</td></tr>'
        html += f'<tr><td style="padding: 5px;"><strong>Image Data:</strong></td><td>{len(obj.image_base64_data):,} chars</td></tr>'
        if final_input_string:
            html += f'<tr style="background: #fff3cd;"><td style="padding: 5px;"><strong>📌 Final Concat String:</strong></td><td style="font-weight: bold; color: #d9534f;">{len(final_input_string):,} chars</td></tr>'
        html += f'<tr><td style="padding: 5px;"><strong>Total Token:</strong></td><td>{obj.token_count:,} tokens</td></tr>'
        html += '</table>'
        html += '</div>'
        
        html += '</div>'
        return format_html(html)
    prompt_display.short_description = '完整 AI Input'
    
    def api_request_display(self, obj):
        """API 请求显示"""
        from django.utils.html import format_html
        params = obj.api_request_params
        return format_html(
            '<pre style="background: #e7f3ff; padding: 15px; border-radius: 5px; max-height: 300px; overflow-y: auto;">{}</pre>',
            json.dumps(params, indent=2, ensure_ascii=False)
        )
    api_request_display.short_description = 'API 请求参数'
    
    def api_response_display(self, obj):
        """API 响应显示"""
        from django.utils.html import format_html
        if obj.api_response:
            return format_html(
                '<pre style="background: #d4edda; padding: 15px; border-radius: 5px; max-height: 300px; overflow-y: auto;">{}</pre>',
                json.dumps(obj.api_response, indent=2, ensure_ascii=False)
            )
        return "无响应"
    api_response_display.short_description = 'API 响应'
    
    def score_display(self, obj):
        """评分结果显示"""
        from django.utils.html import format_html
        if obj.parsed_score and obj.is_success:
            ps = obj.parsed_score
            
            # ✅ stringify every value first, so format_html() cannot raise KeyError
            overall = ps.get('overall_score', 0)
            visual = ps.get('visual_appeal', 0)
            technique = ps.get('cooking_technique', 0)
            freshness = ps.get('ingredient_freshness', 0)
            confidence_val = ps.get('confidence', 0)
            mastery = ps.get('mastery_level', 'N/A')
            comment = ps.get('ai_comment', 'N/A')
            summary = ps.get('ai_summary', 'N/A')
            
            # Punishment 信息
            punishment = ps.get('punishment_applied', 'none')
            punishment_reason = ps.get('punishment_reason', '')
            punishment_feedback = ps.get('punishment_feedback', '')
            
            html_parts = [
                '<div style="background: #fff3cd; padding: 20px; border-radius: 5px;">',
                '<h3 style="margin-top: 0;">🎯 评分结果</h3>',
                '<table style="width: 100%; border-collapse: collapse;">',
                f'<tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>总分</strong></td>',
                f'<td style="padding: 8px; border-bottom: 1px solid #ddd; font-size: 24px; font-weight: bold; color: #d9534f;">{overall:.1f}</td></tr>',
                f'<tr><td style="padding: 8px; border-bottom: 1px solid #ddd;">视觉呈现 (Visual Appeal)</td>',
                f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{visual:.1f}</td></tr>',
                f'<tr><td style="padding: 8px; border-bottom: 1px solid #ddd;">烹饪技巧 (Cooking Technique)</td>',
                f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{technique:.1f}</td></tr>',
                f'<tr><td style="padding: 8px; border-bottom: 1px solid #ddd;">ingredient freshness</td>',
                f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{freshness:.1f}</td></tr>',
                f'<tr><td style="padding: 8px; border-bottom: 1px solid #ddd;">置信度 (Confidence)</td>',
                f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{confidence_val:.2f}</td></tr>',
                f'<tr><td style="padding: 8px; border-bottom: 1px solid #ddd;">等级 (Mastery Level)</td>',
                f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{mastery}</td></tr>',
            ]
            
            # Punishment 信息（如果有）
            if punishment != 'none':
                html_parts.extend([
                    f'<tr style="background: #ffe5e5;"><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>⚠️ Punishment Applied</strong></td>',
                    f'<td style="padding: 8px; border-bottom: 1px solid #ddd; color: #d9534f;"><strong>{punishment.upper()}</strong></td></tr>',
                    f'<tr style="background: #ffe5e5;"><td style="padding: 8px; border-bottom: 1px solid #ddd;">Punishment Reason</td>',
                    f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{punishment_reason}</td></tr>',
                ])
            
            html_parts.extend([
                '</table>',
                '<div style="margin-top: 15px;">',
                f'<p><strong>💬 AI 评论：</strong><br/>{comment}</p>',
                f'<p><strong>📝 总结：</strong> {summary}</p>',
            ])
            
            # Punishment Feedback（如果有）
            if punishment_feedback:
                html_parts.append(
                    f'<div style="background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin-top: 10px;">'
                    f'<p style="margin: 0;"><strong>🎮 Gamified Feedback:</strong><br/>{punishment_feedback}</p></div>'
                )
            
            html_parts.extend([
                '</div>',
                '</div>'
            ])
            
            # ✅ join the parts rather than letting format_html() interpret them
            return format_html(''.join(html_parts))
        return "无评分结果"
    score_display.short_description = '评分详情'
    
    def performance_metrics(self, obj):
        """性能指标"""
        from django.utils.html import format_html
        
        # ✅ format the values first so format_html() cannot raise KeyError
        latency_val = f"{obj.latency:.2f}" if obj.latency else "N/A"
        token_val = f"{obj.token_count:,}" if obj.token_count else "0"
        model_val = obj.model_name or "N/A"
        
        html = (
            '<div style="background: #e9ecef; padding: 10px; border-radius: 5px;">'
            f'<p><strong>⏱️ 延迟：</strong> {latency_val} 秒</p>'
            f'<p><strong>🔢 Token 数：</strong> {token_val}</p>'
            f'<p><strong>🤖 模型：</strong> {model_val}</p>'
            '</div>'
        )
        
        return format_html(html)
    performance_metrics.short_description = '性能指标'
    
    @admin.action(description="🔄 重新运行评分（使用相同参数）")
    def rerun_scoring(self, request, qs):
        """在 Admin 中重新运行评分"""
        for log in qs:
            try:
                logger.info(f"🔄 Admin rerun scoring for log {log.id}")
                
                # 调用相同的评分接口
                from cookai.backend import OpenAIBackend
                result = OpenAIBackend.score_images_detailed(
                    log.image_urls,
                    log.recipe_context
                )
                
                self.message_user(
                    request,
                    f"✅ Log {str(log.id)[:8]} - 重新评分成功！总分: {result.get('overall_score', 0):.1f}",
                    level=messages.SUCCESS
                )
                
            except Exception as e:
                logger.exception(f"❌ Admin rerun scoring error for log {log.id}")
                self.message_user(
                    request,
                    f"❌ Log {str(log.id)[:8]} - 评分失败: {str(e)}",
                    level=messages.ERROR
                )
    
    @admin.action(description="📤 导出为测试数据（JSON）")
    def export_for_testing(self, request, qs):
        """导出为可复用的测试数据"""
        test_data = []
        for log in qs:
            test_data.append({
                'id': str(log.id),
                'image_urls': log.image_urls,
                'recipe_context': log.recipe_context,
                'expected_score': log.parsed_score if log.is_success else None,
                'model': log.model_name,
                'created_at': log.created_at.isoformat()
            })
        
        self.message_user(
            request,
            f"✅ 已导出 {len(test_data)} 条测试数据",
            level=messages.SUCCESS
        )
        
        # TODO: 可以扩展为下载 JSON 文件
        logger.info(f"📤 Exported test data: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    def has_add_permission(self, *a, **kw):
        return False  # 不允许手动创建
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # 只有超级用户可以删除


# ────────────────────────────────────────────────────────────────
# Admin playground form
# ────────────────────────────────────────────────────────────────
class OpenAITestForm(forms.Form):
    MODE_CHOICES = [
        (AIPrompt.KIND_SCORE,   "Personal Critique"),
        (AIPrompt.KIND_COMPARE, "Couples Cook-Off"),
        (AIPrompt.KIND_DETECT,  "Ingredient Detective"),
    ]
    mode         = forms.ChoiceField(choices=MODE_CHOICES)

    image1_url   = forms.URLField(required=False, label="Image 1 URL")
    image1_file  = forms.FileField(required=False, label="Upload Image 1")
    image2_url   = forms.URLField(required=False, label="Image 2 URL")
    image2_file  = forms.FileField(required=False, label="Upload Image 2")
    targets      = forms.CharField(required=False, label="Targets (comma-sep.)")

    def clean(self):
        cleaned = super().clean()
        if not (cleaned.get("image1_url") or cleaned.get("image1_file")):
            self.add_error("image1_url", "Image 1 is required.")
        if (
            cleaned.get("mode") == AIPrompt.KIND_COMPARE and
            not (cleaned.get("image2_url") or cleaned.get("image2_file"))
        ):
            self.add_error("image2_url", "Image 2 is required for compare mode.")
        return cleaned

    def _persist_and_url(self, f) -> str:
        """Save uploaded file to `default_storage` and return accessible URL."""
        name = default_storage.save(
            f"cookai_pg/{int(time.time())}_{f.name}",
            f
        )
        return default_storage.url(name)

    def get_urls(self) -> List[str]:
        """Return list [url1, url2?]."""
        data = self.cleaned_data
        u1 = data["image1_url"] or (
            self._persist_and_url(data["image1_file"])
            if data["image1_file"] else ""
        )
        urls = [u1]
        if data["mode"] == AIPrompt.KIND_COMPARE:
            u2 = data["image2_url"] or (
                self._persist_and_url(data["image2_file"])
                if data["image2_file"] else ""
            )
            urls.append(u2)
        return urls


# ────────────────────────────────────────────────────────────────
# The playground view itself
# ────────────────────────────────────────────────────────────────
@staff_member_required
def playground(request):
    form   = OpenAITestForm(request.POST or None, request.FILES or None)
    result = None

    if request.method == "POST" and form.is_valid():
        urls = form.get_urls()
        mode = form.cleaned_data["mode"]
        try:
            if mode == AIPrompt.KIND_SCORE:
                score, reason = OpenAIBackend.score_images(urls)
                result = {"score": score, "reason": reason}
            elif mode == AIPrompt.KIND_COMPARE:
                result = OpenAIBackend.compare_images(urls[0], urls[1])
            else:  # detect
                toks = form.cleaned_data["targets"].split(",")
                targets = [t.strip() for t in toks if t.strip()]
                det, match = OpenAIBackend.detect_ingredients(urls[0], targets)
                result = {"detected": det, "match": match}
        except Exception as exc:
            logger.exception("playground OpenAI error")
            messages.error(request, f"OpenAI error: {exc}")

    ctx = {
        "form":   form,
        "result": result,
        "title":  "OpenAI Playground",
    }
    return TemplateResponse(request, "admin/cookai/openai_test.html", ctx)


# ────────────────────────────────────────────────────────────────
# Hook into the admin URLconf
# ────────────────────────────────────────────────────────────────
_original_get_urls = admin.site.get_urls

def _patched_urls():
    return [
        path(
            "cookai/openai-test/",
            admin.site.admin_view(playground),
            name="cookai-openai-test",
        )
    ] + _original_get_urls()

admin.site.get_urls = _patched_urls  # type: ignore

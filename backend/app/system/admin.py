from django.contrib import admin
from .models import SystemConfig


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'ai_verification_enabled', 
        'nice_guy_card_mode',
        'nice_guy_score_floor',
        'nice_guy_upscale_base',
        'nice_guy_upscale_range',
        'enable_reward_cooldown', 
        'reward_cooldown_hours',
        'enable_analytics_tracking',
        'pet_prompt_display_seconds',
        'maintenance_mode', 
        'updated_at'
    ]
    list_editable = [
        'ai_verification_enabled', 
        'nice_guy_card_mode',
        'nice_guy_score_floor',
        'nice_guy_upscale_base',
        'nice_guy_upscale_range',
        'enable_reward_cooldown', 
        'reward_cooldown_hours',
        'enable_analytics_tracking',
        'pet_prompt_display_seconds',
        'maintenance_mode'
    ]
    
    fieldsets = (
        ('🤖 AI Configuration', {
            'fields': ('ai_verification_enabled', 'nice_guy_card_mode'),
            'description': (
                'AI Verification: Enable/disable AI recipe verification. '
                'Nice Guy Mode: When enabled, AI scores are boosted to 80-100 range (encouragement mode).'
            )
        }),
        ('🎯 Nice Guy Scoring Parameters', {
            'fields': ('nice_guy_score_floor', 'nice_guy_upscale_base', 'nice_guy_upscale_range'),
            'description': (
                '⚙️ Fine-tune Nice Guy mode behavior (only active when nice_guy_card_mode=True):\n'
                '• Score Floor (60): Minimum score protection, prevents scores below this value\n'
                '• Upscale Base (80): Starting point for upscale mapping (0-100 → base to base+range)\n'
                '• Upscale Range (20): Score range after upscaling (default 80-100)\n'
                'Example: base=85, range=15 → scores mapped to 85-100 range'
            )
        }),
        ('🎁 Reward System', {
            'fields': ('enable_reward_cooldown', 'reward_cooldown_hours'),
            'description': (
                '⚙️ Best Practice: Cooldown disabled by default (dev-friendly). '
                'When disabled, hours parameter is ignored and players can claim infinitely. '
                'For production, enable with 1-24 hours.'
            )
        }),
        ('📊 Analytics & Features', {
            'fields': ('enable_analytics_tracking', 'enable_pet_system', 'enable_memory_system'),
            'description': 'Analytics Tracking: When disabled, no user events will be collected. Feature toggles for pet and memory systems.'
        }),
        ('🐾 Pet UI Configuration', {
            'fields': ('pet_prompt_display_seconds',),
            'description': 'Best Practice: Control how long pet messages are displayed (in seconds). Default: 60s. Range: 10-300s recommended.'
        }),
        ('🔧 System Control', {
            'fields': ('maintenance_mode',),
            'description': 'Enable maintenance mode to block all user access temporarily.'
        }),
        ('📝 Metadata', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        return not SystemConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

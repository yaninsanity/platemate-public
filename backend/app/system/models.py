from django.db import models
from django.conf import settings


class SystemConfig(models.Model):
    ai_verification_enabled = models.BooleanField(default=False)
    maintenance_mode = models.BooleanField(default=False)
    enable_pet_system = models.BooleanField(default=True)
    enable_memory_system = models.BooleanField(default=True)
    nice_guy_card_mode = models.BooleanField(
        default=False,
        help_text='启用"好人卡"mode: rescale AI scores into an encouraging 80-100 band. Off means the raw 0-100 score.'
    )
    
    # � encouraging-score settings, used only when nice_guy_card_mode=True 时生效）
    nice_guy_score_floor = models.PositiveIntegerField(
        default=60,
        help_text='floor applied in encouraging mode. Range: 50-80。defaults to 60, so nobody is scored too harshly.'
    )
    nice_guy_upscale_base = models.PositiveIntegerField(
        default=80,
        help_text='starting score for the encouraging upscale. Range: 70-90。defaults to 80, mapping 0-100 onto 80-100.'
    )
    nice_guy_upscale_range = models.PositiveIntegerField(
        default=20,
        help_text='score span for the encouraging upscale. Range: 10-30。defaults to 20, so the upscale band is[base, base+range]。'
    )
    
    # �🎁 奖励系统配置
    enable_reward_cooldown = models.BooleanField(
        default=False,
        help_text='Enable reward cooldown. When disabled, players can claim infinitely (dev-friendly).'
    )
    reward_cooldown_hours = models.PositiveIntegerField(
        default=2,
        help_text='Cooldown duration in hours. Only effective when enable_reward_cooldown=True.'
    )
    
    # 📊 Analytics Data Collection
    enable_analytics_tracking = models.BooleanField(
        default=True,
        help_text='Enable analytics event tracking. When disabled, no events will be collected.'
    )
    
    # 🐾 Pet Prompt Display Control
    pet_prompt_display_seconds = models.PositiveIntegerField(
        default=60,
        help_text='Pet message display duration in seconds. Default: 60s (1 minute).'
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'system_config'

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(pk=1, defaults={'ai_verification_enabled': False})
        return config
    
    @classmethod
    def is_ai_enabled(cls):
        return cls.get_config().ai_verification_enabled
    
    @classmethod
    def is_mock_mode(cls):
        return not cls.is_ai_enabled()
    
    @classmethod
    def is_nice_guy_card_enabled(cls):
        """检查是否启用好人卡模式（80-100评分区间）"""
        return cls.get_config().nice_guy_card_mode
    
    @classmethod
    def get_nice_guy_score_floor(cls):
        """获取好人卡模式下的最低分保护（默认60）"""
        return cls.get_config().nice_guy_score_floor
    
    @classmethod
    def get_nice_guy_upscale_base(cls):
        """获取好人卡 upscale 起始分数（默认80）"""
        return cls.get_config().nice_guy_upscale_base
    
    @classmethod
    def get_nice_guy_upscale_range(cls):
        """获取好人卡 upscale 分数范围（默认20）"""
        return cls.get_config().nice_guy_upscale_range
    
    @classmethod
    def get_reward_cooldown_hours(cls):
        """
        获取奖励冷却时间（小时）
        
        返回:
            int: Cooldown in hours. When enable_reward_cooldown=False，则返回0（无限制领取）
        """
        config = cls.get_config()
        if not config.enable_reward_cooldown:
            return 0  # 🎯 with the cooldown off the hours value is ignored and claims are unlimited
        return config.reward_cooldown_hours
    
    @classmethod
    def is_reward_cooldown_enabled(cls):
        """Check if reward cooldown is enabled"""
        return cls.get_config().enable_reward_cooldown
    
    @classmethod
    def is_analytics_tracking_enabled(cls):
        """Check if analytics event tracking is enabled"""
        return cls.get_config().enable_analytics_tracking
    
    @classmethod
    def get_pet_prompt_display_seconds(cls):
        """Get pet prompt display duration in seconds"""
        return cls.get_config().pet_prompt_display_seconds

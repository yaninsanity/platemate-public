from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
import uuid


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating 'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(auto_now=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class AIPrompt(TimeStampedModel):
    """
    Storable prompt template, editable in Django admin.

    Supported placeholders:
      {urls}    -> CSV of image URLs
      {target}  -> Target ingredients as CSV
    """
    KIND_SCORE = 'score'
    KIND_COMPARE = 'compare'
    KIND_DETECT = 'detect'
    KIND_CHOICES = [
        (KIND_SCORE, 'Score'),
        (KIND_COMPARE, 'Compare'),
        (KIND_DETECT, 'Detect Ingredients'),
    ]

    kind = models.CharField(
        max_length=12,
        choices=KIND_CHOICES,
        db_index=True,
        help_text='Type of prompt operation'
    )
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique identifier for this prompt template'
    )
    template = models.TextField(
        help_text='Prompt template; use Python str.format placeholders'
    )
    model_name = models.CharField(
        'Model',
        max_length=50,
        default='gpt-5',
        help_text='Default LLM model to use'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Designates whether this prompt is active'
    )

    class Meta:
        indexes = [
            models.Index(fields=['kind'], name='idx_ai_prompt_kind'),
            models.Index(fields=['is_active'], name='idx_ai_prompt_active'),
        ]
        ordering = ['kind', 'name']
        verbose_name = 'AI Prompt'
        verbose_name_plural = 'AI Prompts'

    def render(self, **kwargs) -> str:
        """
        Render the template with provided keyword arguments.
        """
        return self.template.format(**kwargs)

    def __str__(self):
        return f"[{self.get_kind_display()}] {self.name}"

    def get_absolute_url(self):
        return reverse('admin:ai_aiprompt_change', args=[self.pk])


class AIRequestLogManager(models.Manager):
    """
    Custom manager to encapsulate logging logic.
    """
    def log(
        self,
        *,
        prompt_obj: AIPrompt = None,
        kind: str,
        user=None,
        couple=None,
        request_payload: dict = None,
        response: dict = None,
        latency: float = 0.0
    ):
        """
        Create a log entry if logging is enabled via settings.AI_LOG_ENABLED.
        """
        if not getattr(settings, 'AI_LOG_ENABLED', True):
            return None
        return self.create(
            prompt=prompt_obj,
            prompt_name=prompt_obj.name if prompt_obj else "",
            kind=kind,
            user=user,
            couple=couple,
            request_payload=request_payload or {},
            response=response or {},
            latency=latency,
            created_at=timezone.localtime(timezone.now())
        )


class AIRequestLog(TimeStampedModel):
    """
    Audit log for each OpenAI/LLM request.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for this log entry'
    )
    prompt = models.ForeignKey(
        AIPrompt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        help_text='Reference to the used prompt template'
    )
    prompt_name = models.CharField(
        max_length=50,
        blank=True,
        help_text='Snapshot of prompt.name at log time'
    )
    kind = models.CharField(
        max_length=12,
        db_index=True,
        help_text='Category of the request'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_logs',
        help_text='User who triggered the request'
    )
    couple = models.ForeignKey(
        'users.Couple',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Associated couple, if applicable'
    )
    request_payload = models.JSONField(
        blank=True,
        null=True,
        help_text='Full payload sent to the LLM'
    )
    response = models.JSONField(
        blank=True,
        null=True,
        help_text='Raw JSON response from the LLM'
    )
    latency = models.FloatField(
        default=0.0,
        help_text='Round-trip latency in seconds'
    )

    objects = AIRequestLogManager()

    class Meta:
        indexes = [
            models.Index(fields=['kind'], name='idx_ai_log_kind'),
            models.Index(fields=['created_at'], name='idx_ai_log_created'),
        ]
        ordering = ['-created_at']
        verbose_name = 'AI Request Log'
        verbose_name_plural = 'AI Request Logs'

    def __str__(self):
        ts = self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        actor = self.user or 'system'
        return f"[{ts}] {self.kind} by {actor}"

    def get_absolute_url(self):
        return reverse('admin:ai_airequestlog_change', args=[self.pk])


class AIScoreLog(TimeStampedModel):
    """
    🎯 专门记录 AI 评分请求的详细日志
    
    用于 Admin 精准查看和测试：
    - 记录完整 prompt（包含 TIER 系统）
    - 记录所有输入图片的 URL 和 Base64
    - record the recipe context: name, ingredients and method
    - 记录完整的 OpenAI 请求参数和响应
    - 支持在 Admin 中重新运行相同的评分
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='日志唯一标识'
    )
    
    # 关联信息
    memory_entry = models.ForeignKey(
        'couplememory.MemoryEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_score_logs',
        help_text='the related MemoryEntry'
    )
    ai_judgment = models.ForeignKey(
        'couplememory.AIJudgment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='score_logs',
        help_text='the related AIJudgment'
    )
    
    # 输入数据
    image_urls = models.JSONField(
        default=list,
        help_text='原始图片 URL 列表 ["http://..."]'
    )
    image_base64_data = models.TextField(
        blank=True,
        help_text='Base64 encoded image data for the OpenAI API'
    )
    recipe_context = models.JSONField(
        default=dict,
        help_text='Recipe context: {name, instructions, ingredients}'
    )
    
    # Prompt 详情
    full_prompt = models.TextField(
        help_text='the full prompt sent to OpenAI, tier system included'
    )
    model_name = models.CharField(
        max_length=50,
        default='gpt-5',
        help_text='使用的模型名称'
    )
    
    # API 请求和响应
    api_request_params = models.JSONField(
        default=dict,
        help_text='the complete OpenAI API request parameters'
    )
    api_response = models.JSONField(
        blank=True,
        null=True,
        help_text='OpenAI API 原始响应'
    )
    
    # 解析后的评分结果
    parsed_score = models.JSONField(
        blank=True,
        null=True,
        help_text='解析后的评分结果 {overall_score, visual_appeal, ...}'
    )
    
    # 性能指标
    latency = models.FloatField(
        default=0.0,
        help_text='API 响应延迟（秒）'
    )
    token_count = models.IntegerField(
        default=0,
        help_text='估算的 token 数量'
    )
    
    # 状态
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('timeout', '超时'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text='请求状态'
    )
    error_message = models.TextField(
        blank=True,
        help_text='错误信息（如果失败）'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['status'], name='idx_ai_score_status'),
            models.Index(fields=['created_at'], name='idx_ai_score_created'),
            models.Index(fields=['model_name'], name='idx_ai_score_model'),
        ]
        ordering = ['-created_at']
        verbose_name = 'AI 评分日志'
        verbose_name_plural = 'AI 评分日志'
    
    def __str__(self):
        ts = self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        entry_info = f"Entry {self.memory_entry_id}" if self.memory_entry_id else "测试"
        return f"[{ts}] {entry_info} | {self.model_name} | {self.get_status_display()}"
    
    def get_absolute_url(self):
        return reverse('admin:cookai_aiscorelog_change', args=[self.pk])
    
    @property
    def is_success(self):
        return self.status == 'success'
    
    @property
    def score_summary(self):
        """快速查看评分摘要"""
        if not self.parsed_score:
            return "无评分"
        return f"总分: {self.parsed_score.get('overall_score', 'N/A')} | " \
               f"视觉: {self.parsed_score.get('visual_appeal', 'N/A')} | " \
               f"技巧: {self.parsed_score.get('cooking_technique', 'N/A')} | " \
               f"食材: {self.parsed_score.get('ingredient_freshness', 'N/A')}"

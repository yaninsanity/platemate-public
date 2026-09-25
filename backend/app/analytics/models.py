"""
User Behavior Analytics - Data Models

Industrial-grade models for comprehensive user behavior tracking
Designed for scalability, performance, and deep quantitative insights
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json

User = get_user_model()


class EventCategory(models.Model):
    """Event Category - Top-level grouping (Navigation, AI, Recipe, etc.)"""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Category Name',
        help_text='Unique identifier: navigation, ai, recipe, pet'
    )
    display_name = models.CharField(
        max_length=100,
        verbose_name='Display Name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    icon = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Icon'
    )
    color = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name='Color Code'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_event_category'
        verbose_name = 'Event Category'
        verbose_name_plural = 'Event Categories'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.icon} {self.display_name}" if self.icon else self.display_name


class EventType(models.Model):
    """Event Type - Specific trackable user behaviors"""
    
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.CASCADE,
        related_name='event_types',
        verbose_name='Category'
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Event Name'
    )
    display_name = models.CharField(
        max_length=150,
        verbose_name='Display Name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    is_important = models.BooleanField(
        default=False,
        verbose_name='Important Event'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Enable Tracking'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_event_type'
        verbose_name = 'Event Type'
        verbose_name_plural = 'Event Types'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_important']),
        ]
    
    def __str__(self):
        return f"{self.category.icon} {self.display_name}"


class UserEvent(models.Model):
    """User Event - Core tracking table for all user behaviors"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='behavior_events',
        verbose_name='User',
        null=True,
        blank=True
    )
    event_type = models.ForeignKey(
        EventType,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Event Type'
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name='Timestamp',
        db_index=True
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Address'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    session_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Session ID',
        db_index=True
    )
    resource_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Resource Type'
    )
    resource_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Resource ID'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadata'
    )
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Duration (ms)'
    )
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='success',
        verbose_name='Status'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='Error Message'
    )
    
    class Meta:
        db_table = 'analytics_user_event'
        verbose_name = 'User Behavior Event'
        verbose_name_plural = 'User Behavior Events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['session_id', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-timestamp']),
            models.Index(fields=['event_type', 'user', '-timestamp']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.event_type.display_name}"
    
    @property
    def category_name(self):
        return self.event_type.category.name
    
    def get_metadata_display(self):
        if not self.metadata:
            return '-'
        return json.dumps(self.metadata, indent=2, ensure_ascii=False, cls=DjangoJSONEncoder)


class EventAggregate(models.Model):
    """Event Aggregate - Pre-calculated statistics for fast queries"""
    
    PERIOD_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    event_type = models.ForeignKey(
        EventType,
        on_delete=models.CASCADE,
        related_name='aggregates',
        verbose_name='Event Type'
    )
    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        verbose_name='Period'
    )
    period_start = models.DateTimeField(
        verbose_name='Period Start',
        db_index=True
    )
    period_end = models.DateTimeField(
        verbose_name='Period End'
    )
    total_count = models.IntegerField(
        default=0,
        verbose_name='Total Count'
    )
    unique_users = models.IntegerField(
        default=0,
        verbose_name='Unique Users'
    )
    success_count = models.IntegerField(
        default=0,
        verbose_name='Success Count'
    )
    failed_count = models.IntegerField(
        default=0,
        verbose_name='Failed Count'
    )
    avg_duration_ms = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Avg Duration (ms)'
    )
    aggregated_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Aggregated Data'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_event_aggregate'
        verbose_name = 'Event Statistics'
        verbose_name_plural = 'Event Statistics'
        ordering = ['-period_start']
        unique_together = [['event_type', 'period', 'period_start']]
        indexes = [
            models.Index(fields=['event_type', 'period', '-period_start']),
            models.Index(fields=['period', '-period_start']),
        ]
    
    def __str__(self):
        return f"{self.event_type.display_name} - {self.period}"
    
    @property
    def success_rate(self):
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100


class UserSession(models.Model):
    """User Session - Track complete user visit sessions"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='User',
        null=True,
        blank=True
    )
    session_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Session ID',
        db_index=True
    )
    started_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Started At'
    )
    last_activity_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Last Activity At'
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Ended At'
    )
    event_count = models.IntegerField(
        default=0,
        verbose_name='Event Count'
    )
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Duration (seconds)'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Address'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    device_type = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Device Type'
    )
    
    class Meta:
        db_table = 'analytics_user_session'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['-started_at']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration_display(self):
        if self.duration_seconds is None:
            return 'Active'
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f'{minutes}m {seconds}s'

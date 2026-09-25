"""
Analytics Decorators - Manual Event Tracking

Decorators for tracking specific HCI research events:
- @track_event - General event tracking
- @track_duration - Track action duration
- @track_conversion - Track conversion events

Use these for critical user actions that need precise tracking.
"""

from functools import wraps
from django.utils import timezone
import threading
import json

from .models import UserEvent, EventType


def track_event(event_name, category=None, resource_type=None, important=False):
    """
    Decorator to track a specific event.
    
    Usage:
        @track_event('feed_pet', category='pet', resource_type='pet', important=True)
        def feed_pet_view(request, pet_id):
            ...
    
    Args:
        event_name: Name of the event (matches EventType.name)
        category: Category name (optional)
        resource_type: Type of resource being acted upon
        important: Whether this is a critical event
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = timezone.now()
            exception_occurred = None
            result = None
            
            try:
                # Execute the actual view
                result = func(request, *args, **kwargs)
                return result
            except Exception as e:
                exception_occurred = e
                raise
            finally:
                # Track in background thread
                thread = threading.Thread(
                    target=_track_event_async,
                    args=(
                        request, event_name, category, resource_type,
                        start_time, result, exception_occurred, kwargs
                    )
                )
                thread.daemon = True
                thread.start()
        
        return wrapper
    return decorator


def track_duration(event_name, threshold_ms=None):
    """
    Decorator specifically for tracking action duration.
    Useful for performance monitoring of AI generation, recipe search, etc.
    
    Usage:
        @track_duration('ai_generate_recipe', threshold_ms=5000)
        def generate_recipe(request):
            ...  # Long-running AI operation
    
    Args:
        event_name: Name of the event
        threshold_ms: Log warning if duration exceeds this (optional)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = timezone.now()
            
            result = func(request, *args, **kwargs)
            
            duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            
            # Log warning if threshold exceeded
            if threshold_ms and duration_ms > threshold_ms:
                import logging
                logger = logging.getLogger('analytics')
                logger.warning(f"Event {event_name} took {duration_ms}ms (threshold: {threshold_ms}ms)")
            
            # Track with duration
            thread = threading.Thread(
                target=_track_duration_async,
                args=(request, event_name, duration_ms, kwargs)
            )
            thread.daemon = True
            thread.start()
            
            return result
        return wrapper
    return decorator


def track_conversion(from_event, to_event, funnel_name=None):
    """
    Track conversion between two events (funnel tracking).
    
    Usage:
        @track_conversion('view_recipe_detail', 'favorite_recipe', funnel_name='recipe_engagement')
        def favorite_recipe(request, recipe_id):
            ...
    
    This helps track user journey and conversion rates.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            result = func(request, *args, **kwargs)
            
            # Track conversion in background
            thread = threading.Thread(
                target=_track_conversion_async,
                args=(request, from_event, to_event, funnel_name, kwargs)
            )
            thread.daemon = True
            thread.start()
            
            return result
        return wrapper
    return decorator


# Async tracking functions

def _track_event_async(request, event_name, category, resource_type, 
                       start_time, result, exception, view_kwargs):
    """Background event tracking"""
    try:
        # 🎯 Check if analytics tracking is enabled
        from system.models import SystemConfig
        if not SystemConfig.is_analytics_tracking_enabled():
            return  # Analytics disabled - skip tracking
        
        # Get event type
        event_type = EventType.objects.filter(name=event_name).first()
        if not event_type:
            return
        
        # Get user
        user = request.user if request.user.is_authenticated else None
        
        # Calculate duration
        duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
        
        # Determine status
        status = 'success'
        error_message = None
        
        if exception:
            status = 'failed'
            error_message = str(exception)[:500]
        elif hasattr(result, 'status_code') and result.status_code >= 400:
            status = 'failed'
            error_message = f"HTTP {result.status_code}"
        
        # Extract resource ID
        resource_id = None
        if 'pk' in view_kwargs:
            resource_id = str(view_kwargs['pk'])
        elif 'id' in view_kwargs:
            resource_id = str(view_kwargs['id'])
        elif resource_type and resource_type + '_id' in view_kwargs:
            resource_id = str(view_kwargs[resource_type + '_id'])
        
        # Build metadata
        metadata = {
            'method': request.method,
            'path': request.path,
        }
        
        if view_kwargs:
            # Add view kwargs (excluding sensitive data)
            safe_kwargs = {k: str(v) for k, v in view_kwargs.items() 
                          if k not in ['password', 'token', 'secret']}
            metadata['view_kwargs'] = safe_kwargs
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Create event
        UserEvent.objects.create(
            user=user,
            event_type=event_type,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            session_id=request.session.session_key or 'unknown',
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message
        )
        
    except Exception as e:
        # Silent failure
        import logging
        logger = logging.getLogger('analytics')
        logger.error(f"Decorator tracking error: {e}")


def _track_duration_async(request, event_name, duration_ms, view_kwargs):
    """Background duration tracking"""
    try:
        event_type = EventType.objects.filter(name=event_name).first()
        if not event_type:
            return
        
        user = request.user if request.user.is_authenticated else None
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        metadata = {
            'method': request.method,
            'path': request.path,
            'duration_ms': duration_ms,
        }
        
        UserEvent.objects.create(
            user=user,
            event_type=event_type,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            session_id=request.session.session_key or 'unknown',
            metadata=metadata,
            duration_ms=duration_ms,
            status='success'
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger('analytics')
        logger.error(f"Duration tracking error: {e}")


def _track_conversion_async(request, from_event, to_event, funnel_name, view_kwargs):
    """Background conversion tracking"""
    try:
        user = request.user if request.user.is_authenticated else None
        if not user:
            return  # Only track conversions for authenticated users
        
        # Find the "from" event in user's recent history (last 30 minutes)
        from_event_type = EventType.objects.filter(name=from_event).first()
        to_event_type = EventType.objects.filter(name=to_event).first()
        
        if not from_event_type or not to_event_type:
            return
        
        from datetime import timedelta
        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        
        recent_from_event = UserEvent.objects.filter(
            user=user,
            event_type=from_event_type,
            timestamp__gte=thirty_min_ago
        ).order_by('-timestamp').first()
        
        if recent_from_event:
            # Calculate conversion time
            conversion_time_ms = int((timezone.now() - recent_from_event.timestamp).total_seconds() * 1000)
            
            # Track the conversion event
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR', 'unknown')
            
            metadata = {
                'funnel_name': funnel_name,
                'from_event': from_event,
                'to_event': to_event,
                'conversion_time_ms': conversion_time_ms,
                'from_event_id': recent_from_event.id
            }
            
            UserEvent.objects.create(
                user=user,
                event_type=to_event_type,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                session_id=request.session.session_key or 'unknown',
                metadata=metadata,
                duration_ms=conversion_time_ms,
                status='success'
            )
        
    except Exception as e:
        import logging
        logger = logging.getLogger('analytics')
        logger.error(f"Conversion tracking error: {e}")


# Convenience decorators for common HCI events

def track_ai_chat(func):
    """Shortcut for tracking AI chat interactions"""
    return track_event('ai_chat_message', category='ai', resource_type='conversation', important=True)(func)


def track_pet_action(action_name):
    """Shortcut for tracking pet actions (feed, play, battle)"""
    def decorator(func):
        return track_event(action_name, category='pet', resource_type='pet', important=True)(func)
    return decorator


def track_recipe_view(func):
    """Shortcut for tracking recipe views"""
    return track_event('view_recipe_detail', category='recipe', resource_type='recipe')(func)


def track_store_interaction(func):
    """Shortcut for tracking store finder usage"""
    return track_event('find_store', category='shopping', resource_type='store', important=True)(func)


def track_review_creation(func):
    """Shortcut for tracking review creation"""
    return track_event('create_review', category='social', resource_type='review', important=True)(func)

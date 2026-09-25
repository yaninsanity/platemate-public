"""
Analytics Views - Frontend Event Tracking API
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import UserEvent, EventType, EventCategory
from .event_taxonomy import get_event_category
import json
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow both authenticated and anonymous users
def track_event(request):
    """
    Frontend event tracking endpoint
    
    POST /api/analytics/track/
    Body: {
        "event_name": "view_timezone_modal",
        "metadata": {
            "your_timezone": "America/Los_Angeles",
            "partner_timezone": "America/New_York",
            "partner_online": true,
            "time_difference_hours": 3
        },
        "duration_ms": 1500,  // optional
        "timestamp": "2025-10-13T12:34:56.789Z"  // optional
    }
    """
    try:
        event_name = request.data.get('event_name')
        metadata = request.data.get('metadata', {})
        duration_ms = request.data.get('duration_ms')
        event_timestamp = request.data.get('timestamp')
        
        logger.info(f'📊 [Analytics] Received track request: {event_name}')
        logger.info(f'📊 [Analytics] Metadata: {metadata}')
        
        if not event_name:
            return Response(
                {'error': 'event_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create event type
        category_name = get_event_category(event_name)
        category, _ = EventCategory.objects.get_or_create(
            name=category_name,
            defaults={
                'display_name': category_name.title(),
                'is_active': True
            }
        )
        
        event_type, _ = EventType.objects.get_or_create(
            name=event_name,
            defaults={
                'category': category,
                'display_name': event_name.replace('_', ' ').title(),
                'is_active': True
            }
        )
        
        # Parse timestamp if provided
        event_time = timezone.now()
        if event_timestamp:
            try:
                from django.utils.dateparse import parse_datetime
                parsed_time = parse_datetime(event_timestamp)
                if parsed_time:
                    event_time = parsed_time
            except:
                pass  # Use default timezone.now()
        
        # Extract resource info from metadata
        resource_type = metadata.get('resource_type', event_name)
        resource_id = metadata.get('resource_id')
        
        # Enhance metadata with request context
        enhanced_metadata = {
            **metadata,
            'path': request.path,
            'method': request.method,
            'referrer': request.META.get('HTTP_REFERER', ''),
        }
        
        # Create user event (support both authenticated and anonymous users)
        user_event = UserEvent.objects.create(
            user=request.user if request.user.is_authenticated else None,
            event_type=event_type,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=request.META.get('REMOTE_ADDR', ''),
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=enhanced_metadata,
            duration_ms=duration_ms,
            timestamp=event_time
        )
        
        # 🎯 Mark this request as explicitly tracked to prevent middleware double-tracking
        request._analytics_explicitly_tracked = True
        
        return Response({
            'success': True,
            'event_id': user_event.id,
            'event_name': event_name,
            'timestamp': user_event.timestamp.isoformat()
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        # Don't block user operations - log error silently
        logger.error(f'Analytics tracking error: {str(e)}', exc_info=True)
        
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

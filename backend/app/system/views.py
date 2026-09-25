from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import SystemConfig


@api_view(['GET'])
@permission_classes([AllowAny])
def system_config_view(request):
    config = SystemConfig.get_config()
    return Response({
        'ai_verification_enabled': config.ai_verification_enabled,
        'is_mock_mode': config.is_mock_mode(),
        'maintenance_mode': config.maintenance_mode,
        'nice_guy_card_mode': config.nice_guy_card_mode,
        'enable_reward_cooldown': config.enable_reward_cooldown,
        'reward_cooldown_hours': config.reward_cooldown_hours,
        'enable_analytics_tracking': config.enable_analytics_tracking,
        'pet_prompt_display_seconds': config.pet_prompt_display_seconds,
    })

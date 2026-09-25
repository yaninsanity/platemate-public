from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse, Http404, JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView,
)
import os

def download_cert(request):
    """提供SSL证书下载"""
    cert_path = os.path.join('/usr/src/app/certs', 'cert.pem')
    if os.path.exists(cert_path):
        response = FileResponse(open(cert_path, 'rb'), content_type='application/x-x509-ca-cert')
        response['Content-Disposition'] = 'attachment; filename="platemate.crt"'
        return response
    raise Http404(f"no certs: {cert_path}")

def health_check(request):
    """健康检查端点"""
    return JsonResponse({
        'status': 'healthy',
        'django_env': os.getenv('DJANGO_ENV', 'not_set'),
        'use_https': os.getenv('USE_HTTPS', 'false'),
        'production_host': os.getenv('PRODUCTION_HOST', 'not_set'),
        'cors_allow_all': getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False),
        'debug': getattr(settings, 'DEBUG', False),
    })

api_patterns = [
    path("admin/advanced_filters/", include("advanced_filters.urls")),
    path('users/',    include('users.urls',    namespace='users')),
    path('avatar/',   include('avatar.urls')),
    path('system/',   include('system.urls')),  # 🔧 System configuration
    path('analytics/', include(('analytics.urls', 'analytics'), namespace='analytics')),  # 📊 Event tracking
    path('recipes/',  include(('recipes.urls', 'recipes'), namespace='recipes')),
    path('petcare/',  include('petcare.urls',  namespace='petcare')),
    path("couplememory/", include("couplememory.urls", namespace="couplememory")),
    path("cookai/", include(("cookai.urls", "cookai"), namespace="cookai")),
    path('sms/', include('sms_service.urls')),
    path('health/', health_check, name='health_check'),  # 健康检查
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('api/',  include((api_patterns, 'api'))),     # ⬅️ 全 API 只走这一层
    path('certs/cert.pem', download_cert, name='download_cert'),  # 🔒 证书下载
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 生产环境静态文件配置
if settings.DEBUG or getattr(settings, 'DJANGO_ENV', 'dev') == 'prod':
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

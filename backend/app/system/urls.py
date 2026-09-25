from django.urls import path
from . import views

urlpatterns = [
    path('config/', views.system_config_view, name='system-config'),
]

"""
Analytics URLs - Frontend Event Tracking
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Frontend event tracking
    path('track/', views.track_event, name='track_event'),
]

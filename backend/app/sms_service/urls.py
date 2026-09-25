"""
URL configuration for SMS service.
"""

from django.urls import path
from . import views

app_name = 'sms_service'

urlpatterns = [
    # Core SMS/OTP functionality
    path('send/', views.SendSMSView.as_view(), name='send_sms'),
    path('bulk-send/', views.BulkSMSView.as_view(), name='bulk_sms'),

    # OTP functionality
    path('otp/send/', views.SendOTPView.as_view(), name='send_otp'),
    path('otp/verify/', views.VerifyOTPView.as_view(), name='verify_otp'),

    # User SMS history and notifications
    path('my-sms/', views.UserSMSHistoryView.as_view(), name='user_sms_history'),
    path('sms/<int:sms_id>/read/', views.MarkSMSReadView.as_view(), name='mark_sms_read'),
    path('sms/mark-all-read/', views.MarkAllSMSReadView.as_view(), name='mark_all_sms_read'),
    path('sms/unread-count/', views.UnreadSMSCountView.as_view(), name='unread_sms_count'),
]


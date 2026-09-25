"""
DRF API views for SMS service.
"""

import logging
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError

from .models import SMSRecord, OTPRecord
from .services import get_sms_service, get_otp_service
from .utils import get_client_ip
from .exceptions import (
    SMSSendError, OTPGenerationError, OTPVerificationError,
    OTPExpiredError, OTPMaxAttemptsError, InvalidPhoneNumberError
)
from .serializers import (
    # Request/Response serializers
    SendSMSRequestSerializer, SendSMSResponseSerializer,
    SendOTPRequestSerializer, SendOTPResponseSerializer,
    VerifyOTPRequestSerializer, VerifyOTPResponseSerializer,
    BulkSMSRequestSerializer, BulkSMSResponseSerializer,

    # User interface serializers
    UserSMSHistoryRequestSerializer, UserSMSHistoryResponseSerializer,
    UnreadCountResponseSerializer, MarkSMSReadResponseSerializer,
    MarkAllSMSReadResponseSerializer,

    # Model serializers
    SMSRecordSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────
# Core SMS/OTP API Views
# ────────────────────────────────────────────────────────────────

class SendSMSView(APIView):
    """Send SMS message."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendSMSRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = None

        # Get user if user_id provided
        if data.get('user_id'):
            try:
                user = User.objects.get(id=data['user_id'])
            except User.DoesNotExist:
                return Response(
                    {'success': False, 'message': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        try:
            sms_service = get_sms_service()
            record = sms_service.send_sms(
                phone_number=data['phone_number'],
                message=data['message'],
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            response_data = {
                'success': True,
                'message': 'SMS sent successfully',
                'sms_record': record
            }

            serializer = SendSMSResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except InvalidPhoneNumberError as e:
            return Response(
                {'success': False, 'message': f'Invalid phone number: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except SMSSendError as e:
            return Response(
                {'success': False, 'message': f'Failed to send SMS: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.exception("Unexpected error in SendSMSView")
            return Response(
                {'success': False, 'message': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SendOTPView(APIView):
    """Send OTP verification code."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = None

        # Get user if user_id provided
        if data.get('user_id'):
            try:
                user = User.objects.get(id=data['user_id'])
            except User.DoesNotExist:
                return Response(
                    {'success': False, 'message': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        try:
            otp_service = get_otp_service()
            record = otp_service.send_otp(
                phone_number=data['phone_number'],
                purpose=data.get('purpose', 'verification'),
                user=user,
                message_template=data.get('message_template'),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            response_data = {
                'success': True,
                'message': 'OTP sent successfully',
                'otp_record': record
            }

            serializer = SendOTPResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except InvalidPhoneNumberError as e:
            return Response(
                {'success': False, 'message': f'Invalid phone number: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except OTPGenerationError as e:
            return Response(
                {'success': False, 'message': f'Failed to send OTP: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.exception("Unexpected error in SendOTPView")
            return Response(
                {'success': False, 'message': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyOTPView(APIView):
    """Verify OTP code."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = None

        # Get user if user_id provided
        if data.get('user_id'):
            try:
                user = User.objects.get(id=data['user_id'])
            except User.DoesNotExist:
                return Response(
                    {'success': False, 'message': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        try:
            otp_service = get_otp_service()
            verified, message = otp_service.verify_otp(
                phone_number=data['phone_number'],
                otp_code=data['otp_code'],
                purpose=data.get('purpose'),
                user=user
            )

            response_data = {
                'success': True,
                'message': message,
                'verified': verified
            }

            serializer = VerifyOTPResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except (OTPVerificationError, OTPExpiredError, OTPMaxAttemptsError) as e:
            return Response(
                {'success': False, 'message': str(e), 'verified': False},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("Unexpected error in VerifyOTPView")
            return Response(
                {'success': False, 'message': 'Internal server error', 'verified': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkSMSView(APIView):
    """Send SMS to multiple users."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BulkSMSRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user_ids = data['user_ids']
        message = data['message']

        # Get users with phone numbers
        users = User.objects.filter(id__in=user_ids)

        sms_service = get_sms_service()
        success_count = 0
        failed_count = 0
        details = []

        for user in users:
            try:
                # Check if user has phone number
                if not hasattr(user, 'phone') or not user.phone:
                    details.append({
                        'user_id': user.id,
                        'username': user.username,
                        'success': False,
                        'error': 'No phone number'
                    })
                    failed_count += 1
                    continue

                record = sms_service.send_sms(
                    phone_number=user.phone,
                    message=message,
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )

                details.append({
                    'user_id': user.id,
                    'username': user.username,
                    'success': True,
                    'sms_record_id': record.id
                })
                success_count += 1

            except Exception as e:
                details.append({
                    'user_id': user.id,
                    'username': user.username,
                    'success': False,
                    'error': str(e)
                })
                failed_count += 1

        response_data = {
            'success': success_count > 0,
            'message': f'Sent SMS to {success_count} users, {failed_count} failed',
            'total_sent': success_count,
            'total_failed': failed_count,
            'details': details
        }

        serializer = BulkSMSResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ────────────────────────────────────────────────────────────────
# User SMS Interface Views
# ────────────────────────────────────────────────────────────────
class UserSMSHistoryView(APIView):
    """
    Get SMS history for the logged-in user.

    Query parameters (all optional):
      - status:   'pending' | 'success' | 'failed'
      - is_read:  'true' | 'false'
      - search:   substring to search in message content
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. 验证并提取所有可能的查询参数
        param_ser = UserSMSHistoryRequestSerializer(data=request.query_params)
        param_ser.is_valid(raise_exception=True)
        params = param_ser.validated_data

        # 2. base queryset, scoped by user only, with no default is_read filter
        qs = SMSRecord.objects.filter(user=request.user).order_by('-created_at')

        # 3. filter only when the raw query string actually carries the key
        qp = request.query_params
        if 'status' in qp:
            qs = qs.filter(status=params['status'])
        if 'is_read' in qp:
            qs = qs.filter(is_read=params['is_read'])
        if 'search' in qp:
            qs = qs.filter(message__icontains=params['search'])

        # 4. 统计
        total_count  = qs.count()
        unread_count = qs.filter(is_read=False, status='success').count()

        # 5. 序列化列表
        sms_data = SMSRecordSerializer(qs, many=True).data

        # 6. 返回完整 JSON
        return Response({
            'success'     : True,
            'sms_list'    : sms_data,
            'total_count' : total_count,
            'unread_count': unread_count,
        }, status=status.HTTP_200_OK)
class MarkSMSReadView(APIView):
    """Mark a specific SMS as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request, sms_id):
        try:
            sms = SMSRecord.objects.get(id=sms_id, user=request.user)
            sms.mark_as_read()

            response_data = {
                'success': True,
                'message': 'SMS marked as read'
            }

            serializer = MarkSMSReadResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except SMSRecord.DoesNotExist:
            return Response(
                {'success': False, 'message': 'SMS not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class MarkAllSMSReadView(APIView):
    """Mark all SMS for the user as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = SMSRecord.objects.filter(
            user=request.user,
            status='success',
            is_read=False
        ).update(is_read=True)

        response_data = {
            'success': True,
            'message': f'{count} SMS marked as read',
            'count': count
        }

        serializer = MarkAllSMSReadResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UnreadSMSCountView(APIView):
    """Get count of unread SMS for the user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = SMSRecord.get_unread_count(request.user)

        response_data = {
            'success': True,
            'unread_count': count
        }

        serializer = UnreadCountResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


"""
User API endpoints (English, i18n-ready).
All responses except /auth/login/ follow:

    {"detail": "...", "data": {...}}

Login returns {"token": "...", "detail": "..."} so
Pinia’s userStore can keep using data.token as before.
"""
import logging
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as gettext
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Couple
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    CoupleSerializer, JoinCoupleSerializer, LeaveCoupleSerializer,
)
from .exceptions import AlreadyInCouple, NotInCouple, InvalidInvite

logger = logging.getLogger(__name__)
User = get_user_model()

# ───────────── helpers ─────────────
def log_info(request, msg: str) -> None:
    who = request.user if request.user.is_authenticated else "Anon"
    logger.info("[%s] %s – %s", request.method, who, msg)


def ok(*, data=None, detail="OK", http=status.HTTP_200_OK) -> Response:
    """Envelope helper for non-login endpoints."""
    return Response({"detail": detail, "data": data}, status=http)

# ───────────── Auth ────────────────
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        log_info(request, "registration")
        resp = super().create(request, *args, **kwargs)
        user_dict = resp.data
        return ok(
            data={"id": user_dict.get("id"), "username": user_dict.get("username")},
            detail=gettext("Registration successful—now go find your soulmate!"),
            http=status.HTTP_201_CREATED,
        )

# ─────────────────────────── LoginView（JWT 版）─────────────────────────────
class LoginView(generics.GenericAPIView):
    """
    POST /users/auth/login/
    返回：
        {
            "token":   "<access_token>",   # 仍给 userStore.data.token 用
            "refresh": "<refresh_token>",  # 7 days valid; exchange it at /api/token/refresh/
            "detail":  "..."
        }
    """
    serializer_class     = LoginSerializer
    permission_classes   = [AllowAny]
    authentication_classes = []   # 避免 LoginSerializer 重复验证

    def post(self, request, *args, **kwargs):
        log_info(request, "login")
        ser = self.serializer_class(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user"]

        # 生成 JWT
        refresh = RefreshToken.for_user(user)
        access  = refresh.access_token

        try:
            from petcare.pet_message_service import refresh_user_pet_messages
            refresh_user_pet_messages(user, "jwt_login")
        except Exception as e:
            logger.error(f"Failed to refresh pet messages on login: {e}")

        return Response(
            {
                "token": str(access),      # ⬅️ 与旧字段名保持一致
                "refresh": str(refresh),
                "detail": gettext("Welcome back, %(name)s!") % {"name": user.username},
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────── LogoutView（JWT 版）────────────────────────────
class LogoutView(generics.GenericAPIView):
    """
    POST /users/auth/logout/
    建议前端请求体： { "refresh": "<refresh_token>" }
    returns 204 even without a refresh token, so the flow never stalls.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()   # blacklist the token; requires the token_blacklist app
            except TokenError:
                # 已失效 / 非法，照样算登出成功
                pass

        log_info(request, "logout (JWT)")
        return ok(detail=gettext("Logged out."), http=status.HTTP_204_NO_CONTENT)

# ───────────── Profile ─────────────
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

# ───────────── Couple ──────────────
class MyCoupleView(generics.RetrieveAPIView):
    serializer_class = CoupleSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        if not self.request.user.couple:
            raise NotInCouple()
        return self.request.user.couple


class CreateCoupleView(generics.GenericAPIView):
    serializer_class = CoupleSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.couple:
            raise AlreadyInCouple()
        couple = Couple.objects.create()
        couple.add_member(request.user)
        log_info(request, f"created couple {couple.code}")
        return ok(
            data=self.get_serializer(couple).data,
            detail=gettext("Couple created. Share your invite code!"),
            http=status.HTTP_201_CREATED,
        )


class JoinCoupleView(generics.CreateAPIView):
    serializer_class = JoinCoupleSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        code = request.data.get("code")
        try:
            couple = request.user.join_couple(code)
        except ValidationError:
            raise InvalidInvite()
        log_info(request, f"joined couple {code}")
        return ok(
            data=CoupleSerializer(couple, context={"request": request}).data,
            detail=gettext("Joined couple successfully!"),
        )


class LeaveCoupleView(generics.GenericAPIView):
    serializer_class = LeaveCoupleSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            request.user.leave_couple()
        except ValidationError:
            raise NotInCouple()
        log_info(request, "left couple")
        return ok(
            detail=gettext("Single again—good luck out there!"),
            http=status.HTTP_204_NO_CONTENT,
        )

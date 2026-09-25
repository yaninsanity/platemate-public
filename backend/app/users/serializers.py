# File: apps/users/serializers.py
from __future__ import annotations

from django.contrib.auth import get_user_model, authenticate
from django.contrib.sessions.models import Session
from django.utils import timezone
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from avatar.models import Avatar
from recipes.serializers import AbsoluteImageField

from .models import Couple

User = get_user_model()

# ───────────────────────── Auth ──────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username = validated_data["username"],
            email    = validated_data.get("email"),
            password = validated_data["password"],
        )
        Token.objects.create(user=user)          # issue initial token
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login (returns token in view)."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username = attrs.get("username"),
            password = attrs.get("password"),
        )
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        attrs["user"] = user
        return attrs


# ───────────────────────── User ──────────────────────────
class UserSerializer(serializers.ModelSerializer):
    # read-only helpers
    couple_code = serializers.SerializerMethodField(read_only=True)
    avatar_url  = serializers.SerializerMethodField(read_only=True)
    is_online   = serializers.SerializerMethodField(read_only=True)  # 🟢 在线状态

    # ★ 新增：可写头像文件；允许为空不上传
    avatar = serializers.ImageField(
        write_only=True, required=False, allow_null=True, use_url=False
    )

    class Meta:
        model  = User
        fields = [
            # core
            "id", "username", "email", "first_name", "last_name",
            # profile
            "bio", "birth_date", "age", "phone", "phone_verified",
            "timezone", "sms_opt_in", "email_opt_in", "address", "role",
            # avatar & couple
            "avatar",        # ← write-only
            "avatar_url",    # ← read-only
            "couple_code",
            # 🔐 account status & timestamps
            "is_active", "is_online", "last_login", "date_joined",
        ]
        read_only_fields = ["age", "avatar_url", "couple_code", "is_active", "is_online", "last_login", "date_joined"]

    # —— helpers ————————————————————————————————
    def get_couple_code(self, obj):
        return obj.couple.code if getattr(obj, "couple", None) else None
    
    def get_is_online(self, obj):
        """
        🟢 计算用户在线状态
        最佳实践：利用Django Session系统
        - purely whether a session is active, ignoring is_active
        - is_active由权限层处理，不应污染在线状态逻辑
        """
        # 检查是否有未过期的session
        active_sessions = Session.objects.filter(
            expire_date__gte=timezone.now()
        )
        
        for session in active_sessions:
            session_data = session.get_decoded()
            # 检查session是否属于这个用户
            if session_data.get('_auth_user_id') == str(obj.id):
                return True
        
        return False
    
    def get_avatar_url(self, obj):
            """
            Return user's avatar *relative* path, e.g.  /media/avatars/1/avatar.jpg
            This avoids leaking docker-internal host like  localhost:911.
            """
            avatar = (
                Avatar.objects.filter(user=obj, primary=True).first()
                or Avatar.objects.filter(user=obj).order_by("-date_uploaded").first()
            )
            if avatar and avatar.avatar:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(avatar.avatar.url).replace(request.get_host(), f"{request.get_host()}:911")
                return avatar.avatar.url
            return None

    # —— internal helper ————————————————————————————
    @staticmethod
    def _save_avatar(user: User, avatar_file):
        """
        Store new file into django-avatar and mark it primary.
        """
        if not avatar_file:
            return
        # reset previous primary
        Avatar.objects.filter(user=user, primary=True).update(primary=False)
        # create new primary avatar
        Avatar.objects.create(user=user, avatar=avatar_file, primary=True)

    # —— override create / update ———————————————————
    def create(self, validated_data):
        avatar_file = validated_data.pop("avatar", None)
        user = super().create(validated_data)
        if avatar_file is not None:
            self._save_avatar(user, avatar_file)
        return user

    def update(self, instance: User, validated_data):
        avatar_file = validated_data.pop("avatar", None)

        # 普通字段更新
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 保存头像
        if avatar_file is not None:
            self._save_avatar(instance, avatar_file)

        return instance


# ─────────────────────── Couple & misc ───────────────────
class CoupleSerializer(serializers.ModelSerializer):
    members     = UserSerializer(many=True, read_only=True)
    is_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Couple
        fields = ["id", "code", "name", "created_at", "is_complete", "members"]
        extra_kwargs = {"name": {"required": False, "allow_blank": True}}


class JoinCoupleSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=8)

    def validate_code(self, value):
        if not Couple.objects.filter(code=value).exists():
            raise serializers.ValidationError("Invalid couple code.")
        return value


class LeaveCoupleSerializer(serializers.Serializer):
    """No payload required – kept for symmetry with docs/UI."""
    pass

# cookai/api/serializers.py  ← drop-in replacement
from __future__ import annotations
import re, time
from typing import List

from django.core.files.storage import default_storage
from rest_framework import serializers

from cookai.models import AIPrompt, AIRequestLog


# ────────────────────────────────────────────────────────────
# helpers: support URL *or* upload
# ────────────────────────────────────────────────────────────
_URL_RE = re.compile(r"^https?://", re.I)


def _save_and_return_url(file_obj) -> str:
    path = default_storage.save(f"cookai_upload/{int(time.time())}_{file_obj.name}", file_obj)
    return default_storage.url(path)


class _ImageField(serializers.Field):
    """
    Accept either an absolute URL or an uploaded file; always return a URL string.
    """
    def to_internal_value(self, data):
        if hasattr(data, "read"):                    # InMemoryUploadedFile
            return _save_and_return_url(data)
        if isinstance(data, str) and _URL_RE.match(data):
            return data
        raise serializers.ValidationError("Must be an image URL or an uploaded file")

    def to_representation(self, value):
        return value


# ────────────────────────────────────────────────────────────
# meta serializers (unchanged)
# ────────────────────────────────────────────────────────────
class AIPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AIPrompt
        fields = (
            "id", "kind", "name", "template", "model_name",
            "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class AIRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AIRequestLog
        fields = (
            "id", "prompt", "prompt_name", "kind",
            "user", "couple", "request_payload",
            "response", "latency", "created_at",
        )
        read_only_fields = ("id", "created_at")


# ────────────────────────────────────────────────────────────
# 1) SCORE
# ────────────────────────────────────────────────────────────
class ScoreRequestSerializer(serializers.Serializer):
    image      = _ImageField(required=False)
    image_file = serializers.FileField(required=False, write_only=True)

    def validate(self, attrs):
        if not attrs.get("image") and not attrs.get("image_file"):
            raise serializers.ValidationError("Provide image URL or upload a file.")
        if "image_file" in attrs:                       # normalise -> image URL
            attrs["image"] = attrs.pop("image_file")
        return attrs


class ScoreResponseSerializer(serializers.Serializer):
    score  = serializers.FloatField(min_value=0.0, max_value=100.0)
    reason = serializers.CharField(max_length=512)


# ────────────────────────────────────────────────────────────
# 2) COMPARE
# ────────────────────────────────────────────────────────────
class CompareRequestSerializer(serializers.Serializer):
    image1      = _ImageField(required=False)
    image1_file = serializers.FileField(required=False, write_only=True)
    image2      = _ImageField(required=False)
    image2_file = serializers.FileField(required=False, write_only=True)

    def validate(self, attrs):
        # at least one input per image
        for k in ("image1", "image2"):
            if not attrs.get(k) and not attrs.get(f"{k}_file"):
                raise serializers.ValidationError({k: "URL or file required."})
            if f"{k}_file" in attrs:
                attrs[k] = attrs.pop(f"{k}_file")

        # different images check
        if attrs["image1"] == attrs["image2"]:
            raise serializers.ValidationError("image1 and image2 must differ.")
        return attrs


class CompareResponseSerializer(serializers.Serializer):
    winner = serializers.ChoiceField(choices=[0, 1, 2])
    image1 = serializers.DictField()
    image2 = serializers.DictField()


# ────────────────────────────────────────────────────────────
# 3) DETECT
# ────────────────────────────────────────────────────────────
class DetectRequestSerializer(serializers.Serializer):
    image = serializers.ImageField(required=False)  # 如果是上传图片
    image_url = serializers.URLField(required=False)  # 如果是 URL 图片
    target = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    def validate(self, data):
        if not data.get('image') and not data.get('image_url'):
            raise serializers.ValidationError("Either image or image_url is required.")
        return data



class DetectResponseSerializer(serializers.Serializer):
    detected = serializers.ListField(child=serializers.CharField(max_length=100))
    match    = serializers.BooleanField()
    confidence = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)
    message    = serializers.CharField(required=False, max_length=200)

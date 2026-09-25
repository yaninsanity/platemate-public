# cookai/views.py
import time
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from .client import CookAIClient
from .serializers import (
    ScoreRequestSerializer, ScoreResponseSerializer,
    CompareRequestSerializer, CompareResponseSerializer,
    DetectRequestSerializer, DetectResponseSerializer
)
from cookai.models import AIPrompt, AIRequestLog

logger = logging.getLogger(__name__)


class ScoreImageView(APIView):
    """
    API endpoint to score a single image.
    Supports either an image URL or an uploaded file (image_file).
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = ScoreRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        prompt = AIPrompt.objects.filter(
            kind=AIPrompt.KIND_SCORE, is_active=True
        ).first()
        start_ts = time.time()

        try:
            score, reason = CookAIClient.score_image(data["image"])
        except Exception as e:
            latency = time.time() - start_ts
            logger.exception("ScoreImageView failed")
            AIRequestLog.objects.log(
                prompt_obj=prompt,
                kind=AIPrompt.KIND_SCORE,
                user=request.user,
                request_payload={"image": str(data["image"])},
                response={"error": str(e)},
                latency=latency,
            )
            return Response(
                {"detail": "Kinny scoring service temporarily unavailable. Please try again.", "error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )

        latency = time.time() - start_ts
        AIRequestLog.objects.log(
            prompt_obj=prompt,
            kind=AIPrompt.KIND_SCORE,
            user=request.user,
            request_payload={"image": str(data["image"])},
            response={"score": score, "reason": reason},
            latency=latency,
        )

        return Response(
            ScoreResponseSerializer({"score": score, "reason": reason}).data,
            status=status.HTTP_200_OK
        )


class CompareImagesView(APIView):
    """
    API endpoint to compare two images and select a winner.
    Supports image1/image2 URLs or uploaded files image1_file/image2_file.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = CompareRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        prompt = AIPrompt.objects.filter(
            kind=AIPrompt.KIND_COMPARE, is_active=True
        ).first()
        start_ts = time.time()

        try:
            result = CookAIClient.compare_images(data["image1"], data["image2"])
        except Exception as e:
            latency = time.time() - start_ts
            logger.exception("CompareImagesView failed")
            AIRequestLog.objects.log(
                prompt_obj=prompt,
                kind=AIPrompt.KIND_COMPARE,
                user=request.user,
                request_payload={
                    "image1": str(data["image1"]),
                    "image2": str(data["image2"])
                },
                response={"error": str(e)},
                latency=latency,
            )
            return Response(
                {"detail": "Kinny comparison service temporarily unavailable. Please try again.", "error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )

        latency = time.time() - start_ts
        AIRequestLog.objects.log(
            prompt_obj=prompt,
            kind=AIPrompt.KIND_COMPARE,
            user=request.user,
            request_payload={
                "image1": str(data["image1"]),
                "image2": str(data["image2"])
            },
            response=result,
            latency=latency,
        )

        # Normalize result to include required keys for serializer
        normalized = {"winner": result.get("winner", 0)}
        if isinstance(result, dict):
            normalized["image1"] = result.get("image1", {})
            normalized["image2"] = result.get("image2", {})
        else:
            normalized["image1"] = {}
            normalized["image2"] = {}

        return Response(
            CompareResponseSerializer(normalized).data,
            status=status.HTTP_200_OK
        )


class DetectIngredientsView(APIView):
    """
    API endpoint to detect ingredients in an image.
    Supports either an image URL or an uploaded file (image_file).
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = DetectRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Determine the image source: file preferred over URL
        image_source = data.get("image") or data.get("image_url")
        targets = data.get("target", [])

        prompt = AIPrompt.objects.filter(
            kind=AIPrompt.KIND_DETECT, is_active=True
        ).first()
        start_ts = time.time()

        try:
            result = CookAIClient.detect_ingredients(
                image_source,
                targets
            )
        except Exception as e:
            latency = time.time() - start_ts
            logger.exception("DetectIngredientsView failed")
            AIRequestLog.objects.log(
                prompt_obj=prompt,
                kind=AIPrompt.KIND_DETECT,
                user=request.user,
                request_payload={
                    "image": str(image_source),
                    "targets": targets
                },
                response={"error": str(e)},
                latency=latency,
            )
            return Response(
                {"detail": "Kinny detection service temporarily unavailable. Please try again.", "error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )

        latency = time.time() - start_ts
        AIRequestLog.objects.log(
            prompt_obj=prompt,
            kind=AIPrompt.KIND_DETECT,
            user=request.user,
            request_payload={
                "image": str(image_source),
                "targets": targets
            },
            response=result,
            latency=latency,
        )

        return Response(DetectResponseSerializer(result).data, status=status.HTTP_200_OK)

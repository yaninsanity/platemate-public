# app/recipes/tasks.py
import time
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from .models import IngredientPhotoProof
from cookai.models import AIPrompt, AIRequestLog
from .client import CookAIClient

logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def async_score(self, image_url: str) -> dict:
    """
    async scoring task calling CookAIClient.score_image
    """
    start_ts = time.time()
    prompt = AIPrompt.objects.filter(kind=AIPrompt.KIND_SCORE, is_active=True).first()
    try:
        score, reason = CookAIClient.score_image(image_url)
        latency = time.time() - start_ts
        AIRequestLog.objects.log(
            prompt_obj=prompt,
            kind=AIPrompt.KIND_SCORE,
            user=None,  # 如果无用户上下文，可留空
            request_payload={"image": image_url},
            response={"score": score, "reason": reason},
            latency=latency,
        )
        return {"score": score, "reason": reason}
    except Exception as exc:
        logger.exception("async_score 调用失败")
        # 自动重试
        raise exc


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def detect_photo(self, proof_id: int) -> dict:
    """
    异步图像检测任务：
      1. 从数据库取 proof
      2. call OPENAI_BACKEND.detect_ingredients
      3. 更新 proof.detected, proof.match，并可选地标记 task 验证
      4. 记录日志到 AIRequestLog
    """
    start_ts = time.time()

    try:
        proof = IngredientPhotoProof.objects.select_related('task__ingredient').get(id=proof_id)
    except ObjectDoesNotExist:
        logger.error(f"detect_photo: 找不到 proof id={proof_id}")
        return {"error": "Proof not found"}

    image_url = settings.SITE_URL.rstrip('/') + proof.image.url  # 确保是完整 URL
    targets = [proof.task.ingredient.name]
    prompt = AIPrompt.objects.filter(kind=AIPrompt.KIND_DETECT, is_active=True).first()

    try:
        detected, match = settings.OPENAI_BACKEND.detect_ingredients(
            image_url,
            targets
        )
        # 更新 proof
        proof.detected = detected
        proof.match = match
        proof.verified_at = timezone.localtime(timezone.now()) if match else None
        proof.save(update_fields=['detected', 'match', 'verified_at'])

        # 如果匹配，标记任务
        if match:
            proof.task.verify(couple=proof.task.couple)

        latency = time.time() - start_ts
        # 记录日志
        AIRequestLog.objects.log(
            prompt_obj=prompt,
            kind=AIPrompt.KIND_DETECT,
            user=proof.uploader,
            request_payload={"image": image_url, "targets": targets},
            response={"detected": detected, "match": match},
            latency=latency,
        )

        return {"detected": detected, "match": match}

    except Exception as exc:
        latency = time.time() - start_ts
        logger.exception("detect_photo 调用失败")
        AIRequestLog.objects.log(
            prompt_obj=prompt,
            kind=AIPrompt.KIND_DETECT,
            user=proof.uploader,
            request_payload={"image": image_url, "targets": targets},
            response={"error": str(exc)},
            latency=latency,
        )
        # 任务失败时也把状态保存在 proof 中
        proof.error = str(exc)
        proof.save(update_fields=['error'])
        raise exc

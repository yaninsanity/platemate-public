"""System-level service utilities."""

from __future__ import annotations

import logging
import time
from typing import Dict, Iterable, List, Sequence

from django.db import OperationalError, ProgrammingError

from cookai.client import CookAIClient

from .models import SystemConfig

logger = logging.getLogger(__name__)


class MockAIService:
    """Deterministic mock implementation for ingredient detection.

    The mock service keeps client expectations aligned with the real API while
    guaranteeing fast, positive responses so product flows remain testable
    without external dependencies.
    """

    DEFAULT_CONFIDENCE = 0.93
    FALLBACK_CONFIDENCE = 0.62

    @classmethod
    def detect_ingredients(
        cls,
        image_url: str,
        targets: Sequence[str] | None = None,
        timeout: int | float = 5,
    ) -> Dict[str, object]:
        start = time.monotonic()
        normalized_targets = cls._normalize_targets(targets)

        match = bool(normalized_targets)
        detected: List[str] = []
        confidence = cls.DEFAULT_CONFIDENCE if match else cls.FALLBACK_CONFIDENCE

        if normalized_targets:
            detected.append(normalized_targets[0])

        # Add a light delay to emulate network latency but keep tests fast.
        simulated_latency = min(0.35, timeout / 10)
        time.sleep(simulated_latency)

        if match:
            message = (
                f"🎉 Kinny confirms it's {normalized_targets[0]}! "
                "Mock verification succeeded."
            )
        else:
            message = "🌟 Kinny couldn't see a specific ingredient, but keep going!"

        logger.debug(
            "Mock AI detection complete in %.3fs (targets=%s, match=%s)",
            time.monotonic() - start,
            normalized_targets,
            match,
        )

        return {
            "detected": detected,
            "match": match,
            "confidence": confidence,
            "message": message,
            "is_mock": True,
        }

    @staticmethod
    def _normalize_targets(targets: Iterable[str] | None) -> List[str]:
        if not targets:
            return []
        return [str(t).strip() for t in targets if str(t).strip()]


class RealAIService:
    """Proxy to the actual CookAI backend implementation."""

    @staticmethod
    def detect_ingredients(
        image_url: str,
        targets: Sequence[str] | None = None,
        timeout: int | float = 15,
    ) -> Dict[str, object]:
        response = CookAIClient.detect_ingredients(image_url, list(targets or []), timeout=int(timeout))
        response.setdefault("is_mock", False)
        return response


class AIServiceFactory:
    """Facade for selecting the correct AI verification service."""

    _cached_mode: bool | None = None

    @classmethod
    def is_using_mock(cls) -> bool:
        cls._refresh_mode()
        return not bool(cls._cached_mode)

    @classmethod
    def detect_ingredients(
        cls,
        image_url: str,
        targets: Sequence[str] | None = None,
        timeout: int | float = 15,
    ) -> Dict[str, object]:
        service = cls._select_service()
        return service.detect_ingredients(image_url, targets, timeout)  # type: ignore[arg-type]

    @classmethod
    def _refresh_mode(cls) -> None:
        try:
            cls._cached_mode = SystemConfig.is_ai_enabled()
        except (OperationalError, ProgrammingError):
            logger.warning("SystemConfig table unavailable – defaulting to mock AI mode")
            cls._cached_mode = False

    @classmethod
    def _select_service(cls):
        cls._refresh_mode()
        if cls._cached_mode:
            logger.info("AIServiceFactory using real AI backend")
            return RealAIService
        logger.info("AIServiceFactory using mock AI backend")
        return MockAIService

# cookai/client.py

import json, logging, time, requests, base64
from typing import Any, Dict, List, Optional, Tuple

from .backend import OpenAIBackend

logger = logging.getLogger(__name__)

class CookAIClient:
    """Facade used by other apps, e.g. recipes."""

    @staticmethod
    def score_image(url: str) -> Tuple[int, str]:
        """
        给单张图片打分，返回 (score, reason)
        """
        # OpenAIBackend 里对应的方法是 score_images
        return OpenAIBackend.score_images([url])

    @staticmethod
    def compare_images(url1: str, url2: str, recipe_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        对比两张图片，返回 {winner: int, reason: str}
        accepts a recipe context so judging follows the recipe instructions
        """
        return OpenAIBackend.compare_images(url1, url2, recipe_context)

    @staticmethod
    def detect_ingredients(
        url: str,
        targets: Optional[List[str]] = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        成分检测，返回包含detected, match, confidence, message的字典
        """
        # OpenAIBackend 里对应的方法是 detect_ingredients
        return OpenAIBackend.detect_ingredients(url, targets or [])

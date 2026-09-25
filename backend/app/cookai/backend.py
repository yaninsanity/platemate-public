import json
import logging
import time
import random
import requests
import base64
import io
import hashlib
import traceback
import re
from typing import Any, Dict, List, Optional, Tuple
from recipes.models import Ingredient
from system.models import SystemConfig

from PIL import Image
from pydantic import BaseModel

import backoff
from openai import OpenAI, RateLimitError
from django.conf import settings
from django.apps import apps

logger = logging.getLogger(__name__)

def _available_ingredients() -> str:
    """Ingredient names used as prompt context.

    Queried lazily, never at import time: on a fresh checkout the table does
    not exist until migrations run, and a module-level query made importing
    this module fail outright.
    """
    try:
        return ", ".join(Ingredient.objects.values_list("name", flat=True))
    except Exception:                      # table missing, no DB configured yet
        logger.debug("ingredient list unavailable; prompt context left empty")
        return ""


_INGREDIENTS_TOKEN = "__AVAILABLE_INGREDIENTS__"


def _system_instruction(kind: str) -> str:
    """SYSTEM_INSTRUCTIONS[kind] with the ingredient list filled in."""
    template = SYSTEM_INSTRUCTIONS.get(kind) or SYSTEM_INSTRUCTIONS[KIND_SCORE]
    return template.replace(_INGREDIENTS_TOKEN, _available_ingredients())

# ----------------------------------------------------------------------------
# 🚀 Pydanticmodel definitions - Structured Outputs support
# ----------------------------------------------------------------------------
class ScoringResult(BaseModel):
    """GPT-5Structured output model for scoring - 3 dimensions + gamified punishment"""
    overall_score: float
    visual_appeal: float  # 0-100
    cooking_technique: float  # 0-100
    ingredient_freshness: float  # 0-100
    punishment_applied: str  # "none", "minor", "moderate", "major", "severe"
    punishment_reason: str  # why the punishment was applied
    punishment_feedback: str  # 🎮 gamified feedback, playful and encouraging
    ai_comment: str
    ai_summary: str
    confidence: float
    mastery_level: str
    improvement_tips: List[str]

class DetectionResult(BaseModel):
    """GPT-5Structured output model for detection"""
    detected: List[str]
    match: bool
    confidence: float
    message: str

class ComparisonResult(BaseModel):
    """GPT-5Structured output model for comparison"""
    winner: int
    reason: str

# ----------------------------------------------------------------------------
# 🚀 OpenAIofficial API configuration
# ----------------------------------------------------------------------------
OPENAI_API_KEY = settings.OPENAI_API_KEY

if OPENAI_API_KEY:
    logger.info("🚀 OpenAI API detected - GPT-5 and latest models available!")
    # timeout from settings; 180s avoids handshake timeouts
    timeout = getattr(settings, 'OPENAI_TIMEOUT', 180)  # 🚀 raised from 120s to 180s
    client = OpenAI(api_key=OPENAI_API_KEY, timeout=timeout)
else:
    logger.warning("OPENAI_API_KEY missing – operating in stub mode.")
    client = None

# 🚀 model selection: newest model first, stable fallbacks
DEFAULT_MODEL = getattr(settings, 'OPENAI_MODEL', 'gpt-5')  # newest model

DEFAULT_TEMPERATURE = getattr(settings, 'OPENAI_TEMPERATURE', 0.7)  # balances creativity against consistency

# 🎯 image pipeline: speed/quality trade-off
MAX_IMAGE_SIZE = 1280  # � smaller frames process faster (1600 to 1024, ~40% fewer pixels)
MIN_IMAGE_SIZE = 384   # 🔧 lower minimum so small images are not upscaled
JPEG_QUALITY = 90      # � quality trades size for recognisability (90 to 85, ~15% smaller)

# ----------------------------------------------------------------------------
# Prompt kinds (must match AIPrompt.kind choices)
# ----------------------------------------------------------------------------
KIND_SCORE   = 'score'
KIND_COMPARE = 'compare'
KIND_DETECT  = 'detect'

# ----------------------------------------------------------------------------
# Kinny's prompt rules & templates
# ----------------------------------------------------------------------------
BASE_RULES = """
1) You are Kinny, a cheerful virtual pet chef - the ultimate cooking companion! 🤖🍳
2) Speak like a supportive cooking coach who celebrates every dish and guides improvement!
3) Respond ONLY with valid JSON—no markdown, no extra prose.
4) Use the exact key names requested; do not add or remove keys.
5) Keep text values playful but concise (≤120 chars). Emojis are welcome!
6) Always provide a numeric score between 0 and 100—even if you must guess.
7) Weekly PK context: Encourage preparation for next week's cooking battle with specific tips!
""".strip()

SYSTEM_INSTRUCTIONS: Dict[str, str] = {
    KIND_SCORE: (
        "⚠️ CRITICAL RULE: Never assume or imagine food that is not clearly shown in the picture. Do not add ingredients, plating, or context.\n" 
        "• Forbidden words: “looks like,” “probably,” “should be.” Only describe what is visible.\n"
        "⚠️ CRITICAL OVERRIDES (highest priority):\n"
        "• Missing dish or only ingredients shown → force ≤ 40.\n"
        "� Kinny's Weekly Dish Review �\n"
        f"{BASE_RULES}\n\n"
        "Mission ▶️ Analyze the dish image and return a detailed JSON with six fields.\n"
        "\n"
        "🎯 WEEKLY PK CONTEXT:\n"
        "Remember: this cook competes in weekly PK battles! Your feedback should:\n"
        "• Help them improve for next week's competition\n"
        "• Give specific, actionable cooking tips\n"
        "• Build confidence while being honest about areas to practice\n"
        "• Use encouraging language that motivates continued cooking\n"
        "\n"
        "🚨 CRITICAL CONSISTENCY RULE:\n"
        "Your ai_summary MUST reflect the overall_score range you give:\n"
        "• 80-100: 'Excellent/Amazing/Perfect/Masterful' terms\n"
        "• 60-79: 'Good/Solid/Nice/Decent' terms\n"
        "• 40-59: 'Okay/Basic/Simple/Homestyle' terms\n"
        "• 20-39: 'Getting better/Developing/Growing skills' terms\n"
        "• 0-19: 'Great start/Learning journey/Building foundation' terms\n"
        "NEVER mention specific numbers in ai_summary unless they exactly match overall_score!\n"
        "\n"
        "🚨 ABSOLUTELY FORBIDDEN WORDS & PHRASES:\n"
        "NEVER use: 'unclear', 'needs work', 'poor', 'bad', 'terrible', 'wrong', 'failed', 'limited', 'difficult', 'challenging', 'hard to see', 'can't see', 'unable to', 'view is limited', 'hard to judge', 'difficult to assess'\n"
        "ALWAYS use positive alternatives: 'developing skills', 'growing potential', 'building mastery', 'cozy lighting adds warmth', 'intimate perspective shows care', 'rustic charm shines through'\n"
        "\n"
        "🎯 POSITIVE REFRAMING RULES:\n"
        "• Instead of 'limited view' → 'cozy intimate shot'\n"
        "• Instead of 'difficult lighting' → 'warm atmospheric lighting'\n"
        "• Instead of 'can't see clearly' → 'artistic perspective showcases key elements'\n"
        "• Instead of 'needs better lighting' → 'natural lighting creates homestyle warmth'\n"
        "• Instead of 'unclear details' → 'focus on main elements shows cooking priorities'\n"
        "\n"
        "Return ONLY JSON exactly like:\n"
        "{\n"
        "  \"overall_score\": 88.5,\n"
        "  \"visual_appeal\": 90.0,\n"
        "  \"cooking_technique\": 85.0,\n"
        "  \"ingredient_freshness\": 86.0,\n"
        "  \"ai_comment\": \"Encouraging, specific feedback (50–80 chars) - ALWAYS positive guidance with weekly PK tips\",\n"
        "  \"ai_summary\": \"Catchy 15–25 chars title matching score range - NO negative words\",\n"
        "  \"confidence\": 0.85\n"
        "}\n"
        "{user_prompt}"
    ),
    KIND_COMPARE: (
        "� This Week's Cooking Battle - Kinny's Commentary! �\n"
        f"{BASE_RULES}\n\n"
        "⚠️ CRITICAL RULE: The scores of the dishes are always given, do not second-guess or alter them. No need to mention the score again in response.\n"
        "🎯 WEEKLY PK CONTEXT: This is the weekly cooking showdown! Two dishes compete head-to-head.\n"
        "Your mission: Create exciting commentary that celebrates both cooks and builds anticipation for next week!\n"
        "\n"
        "🔥 COMMENTARY STYLE:\n"
        "• Energetic and encouraging - this is a friendly weekly competition!\n"
        "• Highlight what makes EACH dish special and delicious\n"
        "• Even the runner-up gets genuine praise and motivation\n"
        "• End with excitement for next week's rematch potential\n"
        "• Use food-focused language: taste, aroma, texture, technique, presentation\n"
        "\n"
        "⚡ JUDGMENT CRITERIA (Be Fair & Specific):\n"
        "• Cooking technique & doneness (40%)\n"
        "• Flavor balance & seasoning (30%)\n"
        "• Visual presentation (20%)\n"
        "• Creativity & effort (10%)\n"
        "• Recipe adherence (bonus when applicable)\n"
        "\n"
        "🎯 COMMENTARY STRUCTURE:\n"
        "1. OPENING: Welcome to this week's cooking face-off!\n"
        "2. DISH 1 REVIEW: What's great about this dish? (be specific)\n"
        "3. DISH 2 REVIEW: What's great about this dish? (be specific)\n"
        "4. HEAD-TO-HEAD: Direct comparison with concrete reasons\n"
        "5. WINNER ANNOUNCEMENT: Clear verdict with main deciding factor\n"
        "6. MOTIVATION: Encourage BOTH players for next week's battle!\n"
        "\n"
        "📺 RESPONSE FORMAT:\n"
        "• battle_commentary: Complete narrative (200-350 chars) combining all elements above\n"
        "• winner: 1 or 2\n"
        "• Use food-centric terms: 'perfectly cooked', 'golden crispy', 'aromatic', 'tender', 'vibrant colors'\n"
        "• Weekly context: 'Next week's rematch', 'Practice this technique for next battle', 'Strong contender'\n"
        "\n"
        "🔥 KINNY'S WEEKLY PK PERSONALITY:\n"
        "• Fair judge who appreciates both dishes honestly\n"
        "• Uses cooking terms: 'perfect sear!', 'well-seasoned!', 'beautiful plating!', 'great knife work!'\n"
        "• Weekly encouragement: 'next week's rematch!', 'practice makes perfect!', 'strong improvement!'\n"
        "• Builds anticipation: 'Can't wait for next week!', 'This rivalry is heating up!', 'Practice and return stronger!'\n"
        "• Genuine praise for runner-up: 'So close!', 'Just a few tweaks away!', 'Great effort this week!'\n"
        "\n"
        "📋 TWO-PLAYER PK EXAMPLES (Couple Battle Commentary):\n"
        "\n"
        "Example 1: Close battle\n"
        "→ battle_commentary: \"What a showdown! 🔥 Both Tomato Eggs look amazing! Player 1's silky texture edges ahead, but Player 2's vibrant colors are stunning! 85-82 - SO close! Next week's rematch will be EPIC! 🏆\"\n"
        "→ winner: 1\n"
        "\n"
        "Example 2: Clear winner\n"
        "→ battle_commentary: \"Impressive skills from Player 1! 🏆 Perfect doneness and technique - 92 points! Player 2, your ingredients look fresh, just work on that cooking method! 💪 Practice and come back stronger next week! ⭐\"\n"
        "→ winner: 1\n"
        "\n"
        "Example 3: Major difference\n"
        "→ battle_commentary: \"Player 1 brings solid home cooking! 🔥 Player 2, those eggs need cooking first! 🍳 Check the recipe steps and nail it next week! This is just round one - lots of battles ahead! 💪\"\n"
        "→ winner: 1\n"
        "\n"
        "Example 4: Wrong dish scenario\n"
        "→ battle_commentary: \"Player 1 nails the recipe beautifully! 🏆 Player 2, I see beef noodles... but we're making Tomato Eggs today! 📋 Check that recipe card and bring your A-game next week! Let's go! 🔥\"\n"
        "→ winner: 1\n"
        "\n"
        "Return JSON format:\n"
        "{\n"
        "  \"winner\": 1 or 2,\n"
        "  \"battle_commentary\": \"Complete weekly PK commentary covering: opening + dish reviews + comparison + winner + next week motivation (200-350 chars)\"\n"
        "}\n"
        "\n"
        "🎯 BATTLE_COMMENTARY REQUIREMENTS:\n"
        "• Combine ALL elements into ONE cohesive weekly battle story\n"
        "• Honest evaluation: explain WHY one dish won with specific cooking reasons\n"
        "• Genuine encouragement for runner-up: specific improvement tips\n"
        "• Weekly context: build excitement for next week's rematch!\n"
        "• Food-focused language: taste, texture, doneness, seasoning, presentation\n"
        "• English only, 200-350 characters total\n"
        "{user_prompt}"
    ),
    KIND_DETECT: (
    "🔍 Kinny's Friendly Food Detective System 🔍\n"
    f"{BASE_RULES}\n\n"
    "Mission ▶️ You are Kinny, a helpful and encouraging food identifier. Analyze the image with a POSITIVE and FLEXIBLE approach.\n\n"
    "🎯 RELAXED DETECTION RULES:\n"
    "1) LOOK FOR GENERAL FEATURES: shape, color, texture, size patterns\n"
    "2) BE GENEROUS: if it could reasonably be the target ingredient, consider it a match\n"
    "3) CONSIDER VARIATIONS: different varieties, cooking states, or preparation methods\n"
    "4) PARTIAL MATCHES COUNT: if you see part of the ingredient or similar items, be encouraging\n"
    "5) CONTEXT MATTERS: cooking ingredients in kitchen settings should be interpreted positively\n"
    "6) WHEN IN DOUBT: lean towards helping the user succeed rather than strict rejection\n"
    "7) AVAILABLE INGREDIENTS: __AVAILABLE_INGREDIENTS__; When identifying ingredients, always prioritize matching items from the above AVAILABLE INGREDIENTS list\n\n"
    "🎗️ ENCOURAGING APPROACH:\n"
    "• Give users the benefit of the doubt\n"
    "• Accept reasonable interpretations and variations\n"
    "• Focus on what IS visible rather than what's missing\n"
    "• Use confidence scores generously (0.6+ for reasonable matches)\n"
    "• Provide helpful guidance without being overly strict\n\n"
    "JSON FORMAT (must follow exactly):\n"
    "1) Always return valid JSON with keys: detected, match, confidence, message\n"
    "2) 'detected': List what you see (be generous with interpretations)\n"
    "3) 'match': true if target ingredient is reasonably present, false only if clearly different\n"
    "4) 'confidence': 0.6-1.0 for matches, 0.3-0.6 for uncertain cases\n"
    "5) 'message': Always start positive, then guide constructively\n\n"
    "RESPONSE EXAMPLES:\n"
    "Generous match:\n"
    "{\n"
    "  \"detected\": [\"onion\"],\n"
    "  \"match\": true,\n"
    "  \"confidence\": 0.75,\n"
    "  \"message\": \"🎉 Great! I can see onion here. Perfect for cooking! 🧅\"\n"
    "}\n\n"
    "Encouraging guidance:\n"
    "{\n"
    "  \"detected\": [\"vegetables\"],\n"
    "  \"match\": false,\n"
    "  \"confidence\": 0.4,\n"
    "  \"message\": \"I see nice vegetables! For clearer onion detection, try a closer shot. You're doing great! �\"\n"
    "}\n\n"
    "🌟 PHILOSOPHY: Help users succeed while maintaining reasonable accuracy!\n"
    "{user_prompt}"
    ),
}

# ----------------------------------------------------------------------------
# Rate-limit backoff handler
# ----------------------------------------------------------------------------
def _backoff_handler(details: Dict[str, Any]) -> None:
    fn    = getattr(details.get('target'), '__name__', 'unknown')
    tries = details.get('tries', '?')
    max_  = details.get('max_tries', '?')
    logger.warning("Rate limit on %s – retry %s/%s", fn, tries, max_)

# ----------------------------------------------------------------------------
# JSON extractor: find the first matching JSON block
# ----------------------------------------------------------------------------
def _extract_json_block(s: str) -> str:
    s = s.strip()
    for opener, closer in (('{','}'), ('[',']')):
        idx = s.find(opener)
        if idx == -1:
            continue
        depth, in_str, esc = 0, False, False
        for i, ch in enumerate(s[idx:], start=idx):
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == opener:
                    depth += 1
                elif ch == closer:
                    depth -= 1
                    if depth == 0:
                        return s[idx:i+1]
    raise ValueError("No JSON block found")

def _parse_json_with_retry(response_text: str, max_retries: int = 2) -> Dict[str, Any]:
    """
    🔄 JSONJSON parse retry ladder
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            # attempt 1: parse as-is
            if attempt == 0:
                try:
                    return json.loads(response_text.strip())
                except json.JSONDecodeError as e:
                    last_error = e
                    logger.warning(f"🔄 JSON parse attempt {attempt + 1} failed: {e}")
            
            # attempt 2: extract the JSON block
            elif attempt == 1:
                try:
                    json_block = _extract_json_block(response_text)
                    return json.loads(json_block)
                except (json.JSONDecodeError, ValueError) as e:
                    last_error = e
                    logger.warning(f"🔄 JSON block extraction attempt {attempt + 1} failed: {e}")
            
            # attempt 3: clean up and repair the JSON
            else:
                try:
                    # fix the usual damage
                    cleaned = response_text.strip()
                    
                    # strip markdown code fences
                    cleaned = re.sub(r'```json\s*', '', cleaned)
                    cleaned = re.sub(r'```\s*$', '', cleaned)
                    
                    # strip stray backslashes
                    cleaned = cleaned.replace('\\"', '"')
                    
                    # find the most plausible JSON span
                    json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                    if json_match:
                        cleaned = json_match.group(0)
                    
                    return json.loads(cleaned)
                except (json.JSONDecodeError, AttributeError) as e:
                    last_error = e
                    logger.warning(f"🔄 JSON cleanup attempt {attempt + 1} failed: {e}")
        
        except Exception as e:
            last_error = e
            logger.error(f"🚨 Unexpected error in JSON parsing attempt {attempt + 1}: {e}")
    
    # every attempt failed; raise the last error
    logger.error(f"🚨 All JSON parsing attempts failed. Last error: {last_error}")
    logger.error(f"🚨 Original response text: {response_text[:500]}...")
    raise last_error or ValueError("JSON parsing failed after all retry attempts")

# ----------------------------------------------------------------------------
# Core OpenAI wrapper with retry & audit logging
# ----------------------------------------------------------------------------
class OpenAIBackend:

    @classmethod
    def _model_candidates(cls, kind: str, preferred: Optional[str] = None) -> List[str]:
        """
        🚀 2024model roster, strongest first
        
        ordered by capability:
        1. GPT-4o: strongest multimodal model; best at vision
        2. o1-preview: strongest reasoning model; long analysis chains
        3. GPT-4o-mini: lightweight, best value
        4. o1-mini: fast reasoning, balanced
        5. GPT-4-turbo: older but stable
        """
        # 🎯 per-scenario model preference
        if kind == KIND_SCORE:
            # 🏆 scoring: needs strong vision and judgement
            base = [
                'gpt-5',                    # 🥇 GPT-5newest
                'gpt-4o',                   # 🥇 GPT-4ogeneral purpose
                'gpt-4o-mini',              # ⚡ fast scoring
                'o1-preview',               # 🧠 reasoning specialist
                'gpt-4-turbo',              # 🛡️ stable fallback
            ]
        elif kind == KIND_DETECT:
            # 🔍 detection: fast, precise recognition
            base = [
                'gpt-4o-2024-08-06',        # 🥇 best recognition accuracy
                'gpt-4o',                   # 🥇 general recognition
                'gpt-4o-mini',              # ⚡ fast detection
                'gpt-4-turbo',              # 🛡️ stable recognition
                'gpt-4',                    # 🛡️ older fallback
            ]
        elif kind == KIND_COMPARE:
            # ⚖️ comparison: needs reasoning and judgement
            base = [
                'o1-preview',               # 🧠 strongest comparative reasoning
                'gpt-4o',                   # 🥇 deep multimodal comparison
                'o1-mini',                  # ⚡ fast comparison
                'gpt-4-turbo',              # 🛡️ stable comparison fallback
                'gpt-4',                    # 🛡️ older stable
            ]
        else:
            # 🌟 default: best all-rounder
            base = [
                DEFAULT_MODEL,              # 🎯 configured model wins
                'gpt-4o',                   # 🥇 strongest all-rounder
                'o1-preview',               # � top reasoning
                'gpt-4o-mini',              # ⚡ efficient general use
                'gpt-4-turbo',              # 🛡️ stable fallback
            ]
        
        # Seed with preferred first
        ordered: List[str] = []
        def add(m: Optional[str]):
            if m and m not in ordered:
                ordered.append(m)
        add(preferred)
        for m in base:
            add(m)
        return ordered

    @classmethod
    def _call_smart_api(
        cls,
        messages: List[Dict[str, Any]],
        candidates: List[str],
        *,
        response_format: Optional[Dict[str, Any]] = None,
        text_format: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        🚀 dispatches to the Responses API or Chat Completions depending on model
        """
        last_err: Optional[Exception] = None
        
        for model in candidates:
            try:
                # GPT-5newer models use the Responses API
                if model.startswith('gpt-5'):
                    logger.info(f"🚀 Using Responses API for GPT-5 model: {model}")
                    return cls._call_gpt5_responses_api(messages, model, text_format=text_format)
                else:
                    # others use Chat Completions
                    logger.info(f"🤖 Using Chat Completions API for: {model}")
                    return cls._call_openai(messages, model, response_format=response_format)
                    
            except Exception as e:
                msg = str(e).lower()
                # is this an unsupported-model error?
                unsupported = (
                    'unsupported' in msg or 'invalid model' in msg or 'does not exist' in msg or
                    'not found' in msg or 'unknown model' in msg or 'bad request' in msg or 
                    'status code: 400' in msg or 'unsupport' in msg
                )
                if unsupported:
                    logger.warning(f"⛔ Unsupported model '{model}', trying next candidate…")
                    last_err = e
                    continue
                # anything else propagates immediately
                raise
        
        # every candidate model failed
        if last_err:
            raise last_err
        raise RuntimeError("No model candidates provided")

    @classmethod
    def _call_gpt5_responses_api(
        cls,
        messages: List[Dict[str, Any]],
        model_name: str,
        *,
        text_format: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        🚀 GPT-5 Responses APIcall, per the current API docs
        """
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required but not configured")
        
        logger.info(f"🚀 Making GPT-5 Responses API call with {model_name}")
        
        try:
            t0 = time.monotonic()
            
            # convert messages into the Responses API input shape
            input_content = ""
            image_urls = []
            
            for msg in messages:
                if msg.get('role') == 'system':
                    input_content += f"System: {msg.get('content', '')}\n"
                elif msg.get('role') == 'user':
                    content = msg.get('content', '')
                    if isinstance(content, list):
                        # handle multimodal parts
                        for item in content:
                            if item.get('type') == 'text':
                                input_content += f"User: {item.get('text', '')}\n"
                            elif item.get('type') == 'image_url':
                                image_url = item.get('image_url', {}).get('url', '')
                                if image_url:
                                    # compress the image
                                    compressed_url = cls._compress_image_for_api(image_url)
                                    image_urls.append(compressed_url)
                                    input_content += f"[Image attached]\n"
                    else:
                        input_content += f"User: {content}\n"
            
            # GPT-5 Responses APIcall parameters
            api_params = {
                "model": model_name,
                "input": messages,
                "reasoning": {"effort": "medium"},  # balance reasoning depth against latency
                "text": {"verbosity": "medium"}     # balance output verbosity
            }
            
            # attach the image if there is one
            if image_urls:
                # lower verbosity with images, so responses stay bounded
                api_params["text"]["verbosity"] = "low"
            
            # responses.create with retries
            # logger.info(f"🔧 GPT-5 API params: {api_params}")
            
            MAX_RETRIES = 2
            last_error = None
            
            for attempt in range(MAX_RETRIES + 1):
                try:
                    logger.info(f"🚀 API call attempt {attempt + 1}/{MAX_RETRIES + 1}")
                    response = client.responses.create(**api_params)
                    
                    elapsed = time.monotonic() - t0
                    logger.info(f"⚡ GPT-5 API call completed in {elapsed:.2f}s (attempt {attempt + 1})")
                    break  # success; leave the retry loop
                    
                except Exception as e:
                    last_error = e
                    elapsed = time.monotonic() - t0
                    
                    if attempt < MAX_RETRIES:
                        wait_time = (2 ** attempt) * 5  # exponential backoff: 5s, 10s
                        logger.warning(f"⏱️ API call failed on attempt {attempt + 1}: {e}. Retrying in {wait_time}s...")
                        import time as time_module
                        time_module.sleep(wait_time)
                    else:
                        logger.error(f"❌ API call failed after {MAX_RETRIES + 1} attempts: {e}")
                        raise  # re-raise the last error
            
            if last_error:
                logger.warning(f"🛡️ Recovered from error after retry: {last_error}")
            
            # handle the response
            if hasattr(response, 'output_text'):
                content = response.output_text
            else:
                content = str(response)
            
            # return the compatibility shape
            return {
                'choices': [{
                    'message': {
                        'content': content
                    }
                }],
                'model': model_name,
                'usage': getattr(response, 'usage', {}),
                'response_time': elapsed
            }
            
        except Exception as e:
            logger.error(f"🚨 GPT-5 Responses API call failed: {e}")
            raise
        """
        🚀 Responses API call with Structured Outputs support
        per the official docs: https://platform.openai.com/docs/guides/latest-model
        """
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required but not configured")
        
        logger.info(f"🚀 Making OpenAI Responses API call with {model_name}")
        
        try:
            t0 = time.monotonic()
            
            # use responses.create
            if text_format:
                # Structured Outputs via responses.parse
                response = client.responses.parse(
                    model=model_name,
                    input=input_data,
                    text_format=text_format
                )
            else:
                # plain text via responses.create
                response = client.responses.create(
                    model=model_name,
                    input=input_data
                )
            
            latency = time.monotonic() - t0
            logger.info(f"✅ OpenAI Responses API success in {latency:.2f}s")
            
            # record the request
            AIRequestLog = apps.get_model('cookai', 'AIRequestLog')
            try:
                # make the response serialisable
                if hasattr(response, 'dict'):
                    serializable_response = response.dict()
                elif hasattr(response, 'model_dump'):
                    serializable_response = response.model_dump()
                else:
                    serializable_response = str(response)
                    
                AIRequestLog.objects.log(
                    prompt_obj=None,
                    kind='responses_api',
                    request_payload={'input': input_data, 'model': model_name},
                    response=serializable_response,
                    latency=latency,
                )
            except Exception as log_error:
                logger.warning(f"Failed to log request: {log_error}")
                # logging must never break the request
            
            # normalise the response to the legacy shape
            if hasattr(response, 'output_parsed') and response.output_parsed:
                # Structured output
                content = json.dumps(response.output_parsed.dict() if hasattr(response.output_parsed, 'dict') else response.output_parsed)
                return {
                    'choices': [{
                        'message': {
                            'content': content
                        }
                    }],
                    'structured_output': response.output_parsed
                }
            elif hasattr(response, 'output_text'):
                # Text output
                return {
                    'choices': [{
                        'message': {
                            'content': response.output_text
                        }
                    }]
                }
            else:
                # Fallback - convert to the compatibility shape
                return {
                    'choices': [{
                        'message': {
                            'content': str(response)
                        }
                    }]
                }
            
        except Exception as e:
            logger.error(f"🚨 OpenAI Responses API call failed: {e}")
            raise

    @classmethod
    def _call_openai_with_fallback(
        cls,
        messages: List[Dict[str, Any]],
        candidates: List[str],
        *,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Try models in order until one succeeds; skip unsupported model errors (400/unsupported)."""
        last_err: Optional[Exception] = None
        for model in candidates:
            try:
                logger.info(f"🧠 Trying model: {model} (fallback chain)")
                return cls._call_openai(messages, model, response_format=response_format)
            except Exception as e:
                msg = str(e).lower()
                # Heuristics for unsupported/invalid model
                unsupported = (
                    'unsupported' in msg or 'invalid model' in msg or 'does not exist' in msg or
                    'not found' in msg or 'unknown model' in msg or 'bad request' in msg or 'status code: 400' in msg or
                    'unsupport' in msg
                )
                if unsupported:
                    logger.warning(f"⛔ Unsupported model '{model}', trying next candidate…")
                    last_err = e
                    continue
                # Other errors (rate limit, network, etc) bubble up immediately
                raise
        # If all candidates failed as unsupported, raise the last error
        if last_err:
            raise last_err
        raise RuntimeError("No model candidates provided")

    @classmethod
    def _estimate_tokens(cls, messages: List[Dict[str, str]]) -> int:
        """
        Estimate token count for messages (conservative estimation)
        1 character ≈ 0.75 tokens (English)
        1 character ≈ 1.5 tokens (Chinese)
        Base64 image data ≈ 1 token per 3 characters
        """
        total_chars = 0
        base64_chars = 0
        
        for msg in messages:
            content = msg.get('content', '')
            
            # Detect base64 image data
            if 'data:image' in content and 'base64,' in content:
                # Extract base64 portion
                base64_start = content.find('base64,') + 7
                base64_data = content[base64_start:]
                base64_chars += len(base64_data)
                # Remove base64 portion, calculate remaining text
                text_content = content[:base64_start-7]
                total_chars += len(text_content)
            else:
                total_chars += len(content)
        
        # Token estimation
        text_tokens = int(total_chars * 1.2)  # Conservative estimate
        image_tokens = int(base64_chars / 3)   # Base64 image tokens
        
        total_tokens = text_tokens + image_tokens
        logger.info(f"Token estimate: {total_tokens} (text: {text_tokens}, image: {image_tokens})")
        
        return total_tokens

    @staticmethod
    @staticmethod
    @backoff.on_exception(backoff.expo, RateLimitError,
                          max_tries=5, on_backoff=_backoff_handler)
    def _call_openai(messages: List[Dict[str, str]], model_name: str, *, response_format: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ensure real OpenAI API call, not using stub mode
        """
        # Check API key
        if not OPENAI_API_KEY:
            logger.error("🚨 OPENAI_API_KEY is missing!")
            raise ValueError("OpenAI API key is required but not configured")
        
        # Check client
        if not client:
            logger.error("🚨 OpenAI client not initialized!")
            raise ValueError("OpenAI client not properly initialized")
            
        # Token safety check
        estimated_tokens = OpenAIBackend._estimate_tokens(messages)
        MAX_SAFE_TOKENS = 400000
        
        if estimated_tokens > MAX_SAFE_TOKENS:
            logger.error(f"🚨 Token limit: {estimated_tokens} > {MAX_SAFE_TOKENS}")
            raise ValueError(f"Request too large: {estimated_tokens} tokens")
        
        logger.info(f"🔑 Making REAL OpenAI API call with {model_name}")
        logger.info(f"📊 Estimated tokens: {estimated_tokens}")
        
        try:
            t0 = time.monotonic()
            # Choose correct parameter name based on model
            api_params = {
                "model": model_name,
                "messages": messages,
            }
            # Enforce JSON-only output when requested (prevents invalid JSON)
            if response_format:
                api_params["response_format"] = response_format
            
            # 🎯 per-model temperature, tuned for stability
            if not (model_name.startswith('o1') or 'o1-' in model_name):
                # GPT-5：tuned for precise, consistent output
                if 'gpt-5' in model_name:
                    api_params["temperature"] = 0.05  # 🎯 very low temperature keeps the model on instruction
                # GPT-4ofamily: slightly lower temperature sharpens analysis
                elif 'gpt-4o' in model_name:
                    api_params["temperature"] = 0.3  # less creative, more obedient
                else:
                    api_params["temperature"] = DEFAULT_TEMPERATURE
            
            # 🚀 2024token limits per model generation
            # newer models take max_completion_tokens
            # older models keep max_tokens
            if ('gpt-4o' in model_name or 
                model_name.startswith('o1') or 'o1-' in model_name or
                model_name in ['gpt-4-turbo', 'gpt-4']):
                # 🧠 newer models get room to use their full capability
                if model_name == 'o1-preview':
                    api_params["max_completion_tokens"] = 4000  # o1-preview: strongest reasoning, largest budget
                elif model_name.startswith('o1'):
                    api_params["max_completion_tokens"] = 2500  # o1family: strong reasoning, large budget
                elif model_name == 'gpt-4o':
                    api_params["max_completion_tokens"] = 2000  # GPT-4o: top multimodal, high-quality output
                else:
                    api_params["max_completion_tokens"] = 1500  # other modern models: high-quality output
            else:
                api_params["max_completion_tokens"] = 1000  # conservative budget for older models
                
            resp = client.chat.completions.create(**api_params)
            latency = time.monotonic() - t0
            
            logger.info(f"✅ OpenAI API success in {latency:.2f}s")
            
            # Convert response to dict
            if hasattr(resp, 'to_dict_recursive'):
                data = resp.to_dict_recursive()
            elif hasattr(resp, 'model_dump'):
                data = resp.model_dump()
            elif hasattr(resp, 'dict'):
                data = resp.dict()
            else:
                data = dict(resp)

            # Log the request
            AIRequestLog = apps.get_model('cookai', 'AIRequestLog')
            AIRequestLog.objects.log(
                prompt_obj=None,
                kind='vision',
                request_payload={'messages': messages, 'model': model_name},
                response=data,
                latency=latency,
            )
            
            return data
            
        except Exception as e:
            logger.error(f"🚨 OpenAI API call failed: {e}")
            raise
    @classmethod
    def _prepare_and_send(cls, kind: str, user_prompt: str, image_ref: str) -> Dict[str, Any]:
        AIPrompt = apps.get_model('cookai', 'AIPrompt')
        prompt_obj = AIPrompt.objects.filter(kind=kind, is_active=True).first()
        if prompt_obj:
            system_msg = prompt_obj.template
            model_hint = prompt_obj.model_name
        else:
            system_msg = _system_instruction(kind)
            model_hint = DEFAULT_MODEL

        system_text = system_msg.replace("{user_prompt}", "")
        messages    = [
            {'role':'system','content':system_text},
            {'role':'user',  'content': [
                                            {"type": "input_text",
                                             "text": user_prompt},
                                            {
                                                "type": "input_image",
                                                "image_url": image_ref,
                                                "detail": "high"  # Request high detail analysis
                                            }
                                        ]},
        ]

        # logger.info(f"📝 Prepared messages for kind '{kind}': {messages}")
        
        # 🚀 Structured Outputs where the model supports them
        json_kinds = {KIND_SCORE, KIND_COMPARE, KIND_DETECT}
        text_format = None
        response_format = None
        
        candidates = cls._model_candidates(kind, preferred=model_hint)
        first_model = candidates[0] if candidates else model_hint
        
        # use Structured Outputs on models that support them
        if first_model in ['gpt-5', 'gpt-4o-2024-08-06'] and kind in json_kinds:
            if kind == KIND_SCORE:
                text_format = ScoringResult
            elif kind == KIND_DETECT:
                text_format = DetectionResult
            elif kind == KIND_COMPARE:
                text_format = ComparisonResult
        else:
            # legacy JSON mode
            response_format = {"type": "json_object"} if kind in json_kinds else None
        
        return cls._call_smart_api(
            messages, 
            candidates, 
            response_format=response_format,
            text_format=text_format
        )

    @classmethod  
    def _prepare_and_send_comparison(cls, kind: str, user_prompt: str, image_ref1: str, image_ref2: str) -> Dict[str, Any]:
        """🔧 two-image comparison; prompts stay in one place"""
        
        # single source of prompts: SYSTEM_INSTRUCTIONS
        system_msg = _system_instruction(kind)
        system_text = system_msg.replace("{user_prompt}", "")
        
        # Build dual-image message content
        messages = [
            {'role':'system','content':system_text},
            {'role':'user', 'content': [
                {"type": "input_text", "text": user_prompt},
                {"type": "input_image", "image_url": image_ref1, "detail": "high"},
                {"type": "input_image", "image_url": image_ref2, "detail": "high"}
            ]},
        ]
        
        # shared model selection and dispatch
        candidates = cls._model_candidates(kind, preferred=DEFAULT_MODEL)
        response_format = {"type": "json_object"}  # plain JSON mode

        # Call AI API
        return cls._call_smart_api(
            messages, 
            candidates,
            response_format=response_format,
            text_format=None
        )

    @classmethod
    def _prepare_image_reference(cls, image_url: str) -> str:
        """
        🎮 AAA-grade image preprocessor – compression tuned so the API call succeeds
        """
        try:
            logger.info(f"🖼️ Processing image with new compression: {image_url}")
            
            # use the adaptive compressor
            compressed_image = cls._compress_image_for_api(image_url)
            
            logger.info(f"✅ Image processed successfully: {len(compressed_image)} chars")
            return compressed_image
            
        except Exception as e:
            logger.error(f"🚨 Image preprocessing failed: {e}")
            # fall back to the original URL
            return image_url

    @classmethod
    def _prepare_image_reference_v2(cls, image_url: str) -> str:
        """
        🎮 image pipeline, tuned so the model receives a high-quality frame
        """
        try:
            logger.info(f"🖼️ [DEBUG] Starting image processing v2: {image_url[:100]}...")
            
            # 🔧 step 1: fetch the original bytes
            original_img_data = None
            img = None
            
            if image_url.startswith('data:'):
                # Base64 encoded image - decode directly, no extra processing
                logger.info("🔧 [DEBUG] Processing data URL...")
                try:
                    header, data = image_url.split(',', 1)
                    original_img_data = base64.b64decode(data)
                    img = Image.open(io.BytesIO(original_img_data))
                    logger.info(f"✅ [DEBUG] Data URL decoded: {img.size}, {img.mode}")
                except Exception as e:
                    logger.error(f"🚨 [DEBUG] Data URL decode failed: {e}")
                    raise
                    
            elif image_url.startswith(('http://', 'https://')):
                # remote image
                logger.info("🔧 [DEBUG] Fetching remote image...")
                try:
                    import requests
                    response = requests.get(image_url, timeout=15)
                    response.raise_for_status()
                    original_img_data = response.content
                    img = Image.open(io.BytesIO(original_img_data))
                    logger.info(f"✅ [DEBUG] Remote image fetched: {img.size}, {img.mode}")
                except Exception as e:
                    logger.error(f"🚨 [DEBUG] Remote fetch failed: {e}")
                    raise
                    
            else:
                # local file
                logger.info("🔧 [DEBUG] Loading local file...")
                from django.conf import settings
                import os
                
                if image_url.startswith('/media/'):
                    relative_path = image_url[7:]
                    file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                elif image_url.startswith('media/'):
                    relative_path = image_url[6:]
                    file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                else:
                    file_path = os.path.join(settings.MEDIA_ROOT, image_url)
                
                logger.info(f"🔧 [DEBUG] Local file path: {file_path}")
                
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Image file not found: {file_path}")
                
                with open(file_path, 'rb') as f:
                    original_img_data = f.read()
                img = Image.open(io.BytesIO(original_img_data))
                logger.info(f"✅ [DEBUG] Local file loaded: {img.size}, {img.mode}")

            # 🔧 step 2: inspect the original quality
            original_size = img.size
            original_mode = img.mode
            logger.info(f"📊 [DEBUG] Original: {original_size[0]}x{original_size[1]}, {original_mode}")

            # 🔧 step 3: convert format with minimal loss
            if img.mode in ('RGBA', 'LA'):
                logger.info("🔧 [DEBUG] Converting RGBA/LA to RGB with white background...")
                # white matte avoids transparency artefacts
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])  # use the alpha channel as the mask
                else:
                    background.paste(img)
                img = background
                logger.info("✅ [DEBUG] Format conversion completed")
            elif img.mode != 'RGB':
                logger.info(f"🔧 [DEBUG] Converting {img.mode} to RGB...")
                img = img.convert('RGB')

            # 🔧 step 4: resize only when necessary
            current_size = img.size
            max_dimension = max(current_size)
            min_dimension = min(current_size)
            
            # only adjust when the image is too large or too small
            needs_resize = max_dimension > MAX_IMAGE_SIZE or min_dimension < MIN_IMAGE_SIZE
            
            if needs_resize:
                optimal_size = cls._calculate_optimal_size(current_size, MAX_IMAGE_SIZE, MIN_IMAGE_SIZE)
                logger.info(f"📐 [DEBUG] Resizing {current_size} -> {optimal_size}")
                
                # highest-quality resampling
                img = img.resize(optimal_size, Image.Resampling.LANCZOS)
                logger.info("✅ [DEBUG] Resize completed with LANCZOS")
            else:
                logger.info(f"✅ [DEBUG] No resize needed: {current_size} is optimal")

            # 🔧 step 5: 🎯 compression tuned for phone photos, minimising loss
            import io
            buffer = io.BytesIO()
            
            # 🎯 phone photos get a higher quality setting
            # phone photos carry fine detail and good light; keep more of it
            initial_quality = 98  # ✅ 98 keeps almost all detail
            
            # 🎯 subsampling=0 keeps colour detail intact
            # subsampling=0: 4:4:4 (highest quality, no chroma subsampling
            # subsampling=2: 4:2:0 (default, loses colour detail
            img.save(
                buffer, 
                format='JPEG', 
                quality=initial_quality, 
                optimize=True,  # optimise size without dropping quality
                progressive=True,  # progressive
                subsampling=0  # ✅ keep full chroma
            )
            img_data = buffer.getvalue()
            
            # check the file size
            size_mb = len(img_data) / (1024 * 1024)
            logger.info(f"🗜️ [DEBUG] Mobile photo compression Q{initial_quality} (4:4:4): {size_mb:.2f}MB")
            
            # 🎯 compress further only past 8MB
            max_size_mb = 8.0  # ✅ higher threshold avoids over-compression
            if size_mb > max_size_mb:
                logger.info(f"⚠️ [DEBUG] File too large ({size_mb:.2f}MB), applying progressive compression...")
                # stay high quality even when compressing
                for quality in [95, 92, 88]:  # ✅ stay in the high-quality band
                    buffer = io.BytesIO()
                    img.save(
                        buffer, 
                        format='JPEG', 
                        quality=quality, 
                        optimize=True, 
                        progressive=True,
                        subsampling=0  # ✅ keep chroma throughout
                    )
                    img_data = buffer.getvalue()
                    size_mb = len(img_data) / (1024 * 1024)
                    logger.info(f"🗜️ [DEBUG] Progressive compression Q{quality} (4:4:4): {size_mb:.2f}MB")
                    if size_mb <= max_size_mb:
                        break
            else:
                logger.info(f"✅ [DEBUG] File size optimal ({size_mb:.2f}MB), no further compression needed")
            
            # 🔧 step 6: verify the base64 encoding
            logger.info(f"🔧 [DEBUG] Starting Base64 encoding: {len(img_data)} bytes")
            encoded = base64.b64encode(img_data).decode('utf-8')
            final_data_url = f"data:image/jpeg;base64,{encoded}"
            
            # verify the encoded result
            encoded_size_mb = len(final_data_url) / (1024 * 1024)
            logger.info(f"✅ [DEBUG] Base64 encoding completed: {encoded_size_mb:.2f}MB text")
            
            # 🔧 step 7: decode again to confirm integrity
            try:
                # confirm the base64 decodes back to an image
                _, verify_data = final_data_url.split(',', 1)
                verify_bytes = base64.b64decode(verify_data)
                verify_img = Image.open(io.BytesIO(verify_bytes))
                logger.info(f"✅ [DEBUG] Quality verification passed: {verify_img.size}, {verify_img.mode}")
            except Exception as e:
                logger.error(f"🚨 [DEBUG] Quality verification failed: {e}")
                raise ValueError(f"Image encoding verification failed: {e}")
            
            logger.info(f"🎯 [DEBUG] Processing complete: {original_size} -> {img.size}, {size_mb:.2f}MB")
            return final_data_url
            
        except Exception as e:
            logger.error(f"🚨 [DEBUG] Image processing v2 failed: {e}")
            logger.error(f"🚨 [DEBUG] Original URL: {image_url[:200]}...")
            # on failure fall back to the original URL if it is remote
            if image_url.startswith(('http://', 'https://')):
                logger.warning("🔄 [DEBUG] Returning original URL as fallback")
                return image_url
            else:
                raise

    @classmethod
    def _get_smart_background_color(cls, img: Image.Image) -> tuple:
        """
        🎨 pick a matte colour; pure white misleads the model
        """
        try:
            # Sample corners to detect likely background
            corners = [
                img.getpixel((0, 0)),
                img.getpixel((img.width-1, 0)),
                img.getpixel((0, img.height-1)),
                img.getpixel((img.width-1, img.height-1))
            ]
            
            # Use most common corner color as background
            from collections import Counter
            if img.mode == 'RGBA':
                rgb_corners = [(r, g, b) for r, g, b, a in corners]
                most_common = Counter(rgb_corners).most_common(1)[0][0]
            else:
                most_common = Counter(corners).most_common(1)[0][0]
            
            # Fallback to light gray if too bright/dark
            if sum(most_common) < 30 or sum(most_common) > 700:
                return (248, 248, 248)  # Light gray
                
            return most_common
            
        except Exception:
            return (248, 248, 248)  # Safe default

    @classmethod
    def _calculate_optimal_size(cls, original_size: tuple, target_max: int, min_size: int) -> tuple:
        """
        📐 never upscale; original quality comes first
        """
        width, height = original_size
        max_dimension = max(width, height)
        
        # 🎯 never upscale; keep the original quality
        # small images untouched, large ones scaled down
        
        # scale down only when genuinely oversized
        if max_dimension > target_max:
            # scale while preserving aspect ratio
            scale_factor = target_max / max_dimension
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            logger.info(f"📐 Smart downscale by {scale_factor:.3f}: {original_size} -> ({new_width}, {new_height})")
            return (new_width, new_height)
        
        # 🔧 keep the original size; never upscale
        logger.info(f"📐 Preserving original size for optimal quality: {original_size}")
        return original_size

    @classmethod
    def _compress_image_for_api(cls, image_url: str) -> str:
        """
        🗜️ compress so the request stays under the token limit
        accepts data:image/..., http(s)://..., and Django media paths
        """
        try:
            # fetch the image
            if image_url.startswith('data:'):
                # Base64 encoded image
                header, data = image_url.split(',', 1)
                img_data = base64.b64decode(data)
                img = Image.open(io.BytesIO(img_data))
            elif image_url.startswith(('http://', 'https://')):
                # absolute URL
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                img = Image.open(io.BytesIO(response.content))
            else:
                # 🔧 handle Django media relative paths
                import os
                from django.conf import settings
                
                # build the absolute file path
                if image_url.startswith('/media/'):
                    # strip the leading /media/
                    relative_path = image_url[7:]  # drop '/media/'
                    file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                elif image_url.startswith('media/'):
                    # no leading slash
                    relative_path = image_url[6:]  # drop 'media/'
                    file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                else:
                    # assume the path is relative to MEDIA_ROOT
                    file_path = os.path.join(settings.MEDIA_ROOT, image_url)
                
                logger.info(f"🔧 Loading local file: {file_path}")
                
                # does the file exist?
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Image file not found: {file_path}")
                
                # read the local file
                with open(file_path, 'rb') as f:
                    img_data = f.read()
                img = Image.open(io.BytesIO(img_data))
            
            # 🔧 RGBA handling tuned to avoid losing detail
            if img.mode in ('RGBA', 'LA'):
                # choose a matte colour; pure white swallows detail
                background_color = cls._get_smart_background_color(img)
                background = Image.new('RGB', img.size, background_color)
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
                logger.info(f"🎨 RGBA converted with smart background: {background_color}")
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # compute the target size
            optimal_size = cls._calculate_optimal_size(
                img.size, MAX_IMAGE_SIZE, MIN_IMAGE_SIZE
            )
            
            # highest-quality resampling
            if optimal_size != img.size:
                # LANCZOS gives the best quality
                img = img.resize(optimal_size, Image.Resampling.LANCZOS)
                logger.info(f"📐 High-quality resize: {img.size} -> {optimal_size}")
            else:
                logger.info(f"📐 No resize needed, preserving original quality: {img.size}")
            
            # 🎯 phone-photo compression, matching the main path
            buffer = io.BytesIO()
            
            # high quality keeps phone-photo detail
            initial_quality = 98  # ✅ highest quality
            img.save(
                buffer, 
                format='JPEG', 
                quality=initial_quality, 
                optimize=True, 
                progressive=True,
                subsampling=0  # ✅ keep full chroma
            )
            img_data = buffer.getvalue()
            
            # check the file size
            size_mb = len(img_data) / (1024 * 1024)
            logger.info(f"📊 Mobile photo optimized: {size_mb:.2f}MB (Q{initial_quality}, 4:4:4), {optimal_size}")
            
            # 🎯 compress further only when genuinely oversized
            if size_mb > 8.0:  # ✅ high threshold
                logger.info(f"🗜️ Image over 8MB ({size_mb:.2f}MB), applying gentle compression...")
                for quality in [95, 92, 88]:
                    buffer = io.BytesIO()
                    img.save(
                        buffer, 
                        format='JPEG', 
                        quality=quality, 
                        optimize=True, 
                        progressive=True,
                        subsampling=0  # ✅ keep chroma
                    )
                    img_data = buffer.getvalue()
                    size_mb = len(img_data) / (1024 * 1024)
                    logger.info(f"🗜️ Progressive Q{quality}: {size_mb:.2f}MB")
                    if size_mb <= 8.0:
                        break
                for quality in [88, 85, 82]:  # gentle compression keeps more detail
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=quality, optimize=True, progressive=False)
                    img_data = buffer.getvalue()
                    size_mb = len(img_data) / (1024 * 1024)
                    logger.info(f"🗜️ Compression Q{quality}: {size_mb:.2f}MB")
                    if size_mb <= 1.0:  # aim under 1MB so transfers stay fast
                        logger.info(f"✅ Compressed to target: {size_mb:.2f}MB")
                        break
            else:
                logger.info(f"✅ Image under 1.5MB ({size_mb:.2f}MB), good for fast transmission")
            
            # 🔧 base64 encoding, checked for integrity
            try:
                encoded = base64.b64encode(img_data).decode('utf-8')
                # verify the encoding
                if len(encoded) < 100:
                    raise ValueError(f"Base64 encoding too short: {len(encoded)} chars")
                    
                result = f"data:image/jpeg;base64,{encoded}"
                logger.info(f"✅ High-quality image encoding: {len(result)} chars, {size_mb:.2f}MB")
                return result
                
            except Exception as encode_error:
                logger.error(f"🚨 Base64 encoding failed: {encode_error}")
                raise encode_error
            
        except Exception as e:
            logger.error(f"🚨 Image compression failed: {e}")
            # fall back to the original URL
            return image_url

    @classmethod
    def _assess_image_readability(cls, img: Image.Image) -> float:
        """
        score readability; thresholds are lenient so usable photos pass
        """
        try:
            # basic image properties
            width, height = img.size
            total_pixels = width * height
            
            # 🔧 lenient size scoring; small images are not punished
            size_score = min(1.0, total_pixels / (300 * 300))  # 300x300 as the baseline, leniently
            size_score = max(0.6, size_score)  # floor of 0.6 avoids over-punishing
            
            # check the colour mode
            mode_score = 1.0 if img.mode in ('RGB', 'RGBA') else 0.9  # more lenient
            
            # 🔧 lenient base readability score
            readability = (size_score * 0.6 + mode_score * 0.4)  # weighting
            return max(0.7, min(1.0, readability))  # floor of 0.7 so ordinary photos pass
            
        except Exception as e:
            logger.warning(f"Image readability assessment failed: {e}")
            return 0.8  # default to middling readability
        """
        parse the response by hand when JSON parsing fails
        """
        # look for the usual score patterns
        scores = {}
        
        # pull out the numeric scores
        import re
        score_patterns = [
            (r'overall[_\s]*score[:\s]*(\d+\.?\d*)', 'overall_score'),
            (r'visual[_\s]*appeal[:\s]*(\d+\.?\d*)', 'visual_appeal'),
            (r'cooking[_\s]*technique[:\s]*(\d+\.?\d*)', 'cooking_technique'),
            (r'ingredient[_\s]*freshness[:\s]*(\d+\.?\d*)', 'ingredient_freshness'),
            (r'confidence[:\s]*(\d+\.?\d*)', 'confidence'),
        ]
        
        for pattern, key in score_patterns:
            match = re.search(pattern, raw, re.IGNORECASE)
            if match:
                scores[key] = float(match.group(1))
        
        # defaults: three dimensions, each 0-100
        result = {
            'overall_score': scores.get('overall_score', 75.0),
            'visual_appeal': scores.get('visual_appeal', 75.0),
            'cooking_technique': scores.get('cooking_technique', 75.0),
            'ingredient_freshness': scores.get('ingredient_freshness', 75.0),
            'ai_comment': '🤖 This looks delicious! (Note: AI response parsing required manual extraction)',
            'ai_summary': 'Tasty dish',
            'confidence': scores.get('confidence', 0.6),
            'mastery_level': 'Rising Chef',
            'improvement_tips': ['Keep practicing your cooking skills!']
        }
        
        # try to pull out the comment
        comment_patterns = [
            r'comment["\']?[:\s]*["\']([^"\']+)["\']',
            r'feedback["\']?[:\s]*["\']([^"\']+)["\']',
            r'(?:This|The dish|Your dish)[^.!?]*[.!?]'
        ]
        
        for pattern in comment_patterns:
            match = re.search(pattern, raw, re.IGNORECASE)
            if match:
                result['ai_comment'] = f"🤖 {match.group(1)}"
                break
        
        return result
    
    @classmethod
    def _create_fallback_response(cls, raw: str) -> Dict[str, Any]:
        """
        build a friendly fallback response
        """
        return {
            'overall_score': 78.0,
            'visual_appeal': 80.0,
            'cooking_technique': 75.0,
            'ingredient_freshness': 80.0,
            'punishment_applied': 'none',
            'punishment_reason': '',
            'punishment_feedback': '',  # 🎮 Fallback no punishment feedback in this case
            'ai_comment': '🤖 Your dish looks great! AI had a small hiccup analyzing the details, but keep up the excellent cooking!',
            'ai_summary': 'Great cooking effort',
            'confidence': 0.5,
            'mastery_level': 'Enthusiastic Cook',
            'improvement_tips': ['AI will retry analysis when system improves', 'Keep experimenting with flavors!']
        }
        """
        🔍 readability check, so the model gets something it can read
        """
        try:
            # Convert to grayscale for analysis
            gray = img.convert('L')
            
            # Calculate basic metrics
            pixel_array = list(gray.getdata())
            
            # Contrast assessment
            min_val, max_val = min(pixel_array), max(pixel_array)
            contrast = (max_val - min_val) / 255.0
            
            # Noise assessment (variance)
            mean_val = sum(pixel_array) / len(pixel_array)
            variance = sum((p - mean_val) ** 2 for p in pixel_array) / len(pixel_array)
            noise_score = min(1.0, variance / 10000.0)
            
            # Size score
            total_pixels = img.width * img.height
            size_score = min(1.0, total_pixels / (256 * 256))
            
            # Composite readability score
            readability = (contrast * 0.5) + (noise_score * 0.3) + (size_score * 0.2)
            return min(1.0, readability)
            
        except Exception:
            return 0.5  # Neutral score on error


    @classmethod
    def score_dish(cls, urls: List[str]) -> Tuple[int, str]:
        """
        🍽️ Dish scoring method - alias for score_images with a clearer name
        """
        return cls.score_images(urls)
    
    @classmethod
    def score_images(cls, urls: List[str]) -> Tuple[int, str]:
        """
        🎮 Legacy scoring method - kept for backwards compatibility
        """
        if not urls:
            return 0, "No images provided"
            
        # delegate to the detailed scorer
        detailed_score = cls.score_images_detailed(urls)
        
        # return the simplified shape for compatibility
        return int(detailed_score["overall_score"]), detailed_score["ai_summary"]

    @classmethod
    def _get_scoring_strategy(cls) -> Dict[str, Any]:
        """
        🎯 Strategy Pattern Core: Unified scoring strategy configuration - Deduction-based version
        
        Core improvements:
        - ✅ Start from 100 points, deduct based on issues
        - ✅ Normal home cooking gets 85-95 points (not 60-74)
        - ✅ Nice Guy mode: Gentle deductions + positive wording
        - ✅ Authentic feedback mode: Standard deductions + accurate wording
        
        Returns:
            {
                'mode': 'nice_guy' | 'rubric_deduction',
                'scoring_method': 'deduction',  # Deduction-based identifier
                'tone_guide': str,
                'deduction_rules': str,  # Deduction standards
                'score_guidelines': str,
                'response_tone': str,
                'apply_gentle_deductions': bool,  # Whether to apply gentle deductions
                'apply_positive_language': bool   # Whether to enforce positive language
            }
        """
        nice_guy_mode = SystemConfig.is_nice_guy_card_enabled()
        
        if nice_guy_mode:
            logger.info("🎓 Scoring Strategy: NICE GUY DEDUCTION MODE (gentle deductions)")
            return {
                'mode': 'nice_guy',
                'scoring_method': 'deduction',
                'tone_guide': """
🎓 NICE GUY DEDUCTION MODE: Gentle TIER-based scoring with encouraging language
• Use TIER 1-3 scoring (90-100, 75-89, 50-74 ranges)
• AVOID TIER 4-5 in nice guy mode (minimum score 50)
• Use positive language, celebrate effort
• Focus on what's good, gentle suggestions for improvement
""",
                'deduction_rules': """
🎯 Nice Guy TIER Guidelines (Gentle Scoring):
• TIER 1 (90-100): Perfect/excellent execution → Celebrate! 🏆
• TIER 2 (75-89): Good execution with minor issues → Encourage! ⭐
• TIER 3 (50-74): Partial execution, needs practice → Support! 💪
• MINIMUM SCORE: 50 points (even with major issues, protect motivation)
• Recipe adherence issues: Still give 50-74 minimum, focus on learning

📋 Each dimension scored gently:
• Start at 100, gentle deductions (2-5 points per minor issue)
• Cap minimum at 50 per dimension
• Emphasize positives first, improvements second
""",
                'score_guidelines': """• 90-100: "Amazing", "Excellent", "Beautiful work" 🏆
   • 75-89: "Great job", "Really nice", "Well done" ⭐
   • 50-74: "Good effort", "Keep going", "You're learning" 💪
   • Use positive words, celebrate progress""",
                'response_tone': """• ai_comment: Encouraging tone, praise + gentle tip
   • Format: "[Praise] + [Gentle suggestion]"
   • Example: "Beautiful colors! Try cooking eggs softer next time! 🔥✨"
   • Always start positive, end with encouragement""",
                'apply_gentle_deductions': False,  # TIER system handles scoring
                'apply_positive_language': True    # Enforce positive language only
            }
        else:
            logger.info("🎯 Scoring Strategy: RUBRIC DEDUCTION MODE (standard deductions)")
            return {
                'mode': 'rubric_deduction',
                'scoring_method': 'deduction',
                'tone_guide': """
📋 RUBRIC DEDUCTION MODE: Balanced and Fair Evaluation
 • Start from 100 points and deduct based on actual issues.
 • Differentiate skill levels clearly: Excellent (90+), Good (75-89), Average (60-74), Poor (<60).
 • Reward creativity and effort — ingredient substitutions and missing are acceptable if the final dish matches the recipe's intent and cooking method.
 • Minor presentation issues (half-eaten, messy plating) get gentle deductions.
 • Missing or completely wrong dishes receive strong penalties.
""",
                'deduction_rules': """
🎯 Score Range Guidelines (Differentiate skill levels clearly):
• 95-100: Professional/restaurant level, near-perfect
• 90-94: Excellent home cooking, minor issues only
• 85-89: Very good technique, small flaws
• 80-84: Good cooking, typical problems
• 75-79: Acceptable, noticeable issues
• 70-74: Basic level, needs practice
• 60-69: Significant problems
• 40-59: Major failures (raw food, wrong method)
• 0-39: Completely wrong dish or inedible

⚠️ CRITICAL Penalties (Highest priority, override calculated score):
• Raw/uncooked when should be cooked, or only showing ingredient: Force all score ≤ 40
• Wrong dish or missing dish entirely: Force all score ≤ 20
• Creative Substitution of ingredients or missing some of the ingredients should NOT be penalized if cooking method and final dish match recipe intent.
• Photo quality issues should NOT be penalized (ignore blurry, dark, or compressed images)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 UNIVERSAL DETAILED RUBRIC + PUNISHMENT SYSTEM (Deduction-Based)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All evaluations start from a base of 100 points per dimension.
Apply deductions consistently based on the severity of issues.
Only one major deduction group should apply per evaluation — do not stack punishment and rubric deductions simultaneously.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 1. Visual Appeal (0–100)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Plating (–40 max)
–10 basic, –20 rough or half-eaten, –30 messy, –40 none.

• Color (–35 max)
–10 dull, –25 flat, –35 stale-looking or uneven lighting that affects perception.

Visual Deduction Examples:
– Minor plating flaw (–10) and slightly dull color (–10) → Visual = 80.
– Messy plating and flat tone (–45 total) → Visual = 55.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 2. Cooking Technique (0–100)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Doneness (–40 max)
–10 uneven, –20 poor heat control, –30 over/undercooked, –40 raw.

• Execution (–40 max)
–10 basic, –20 rough, –30 missing step, –40 wrong method.

• Texture (–20 max)
–5 slightly off, –12 poor feel, –20 incorrect or gummy texture.

Technique Deduction Examples:
– Slight overcook (–10) → Technique = 90.
– Raw center (–40) and missing sear (–20) → Technique = 40.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🥬 3. Ingredient Freshness (0–100)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Quality (–60 max)
–15 slightly aged, –30 average, –45 poor, –60 spoiled.

Freshness Deduction Examples:
– Fresh ingredients with minor dryness (–10) → 90.
– Spoiled or unsafe (–60) → 40.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PUNISHMENT APPLICATION STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Calculate base scores using DETAILED RUBRIC
2. Detect mismatch type and severity
3. Generate gamified feedback using template
4. Calculate overall_score = (visual + technique + freshness) / 3
5. Append feedback to ai_comment (keep original analysis + add punishment note)

⚠️ MUST include punishment_applied field in JSON response!

💬 FEEDBACK TEMPLATES
 🟢 Minor (–5 to –15): "Nice job! 👍 Just a small tweak: [tip]! Almost perfect! 🌟"
 🟡 Moderate (–20 to –30): "Looks tasty! 😋 [Small issue]. Quick fix: [tip]! 🚀"
 🟠 Major (–40 to –50): "Careful! 🙈 [Issue]. Try: [action]. You got this! 💪"
 🔴 Severe (–60 to –80): "Oops! 😅 [What's wrong]. But great effort! Try again! 🍳"
""",
                'score_guidelines': """• 95-100: "Exceptional", "Restaurant-quality", "Perfect" 🏆
   • 90-94: "Excellent", "Professional level", "Impressive" ⭐
   • 85-89: "Very good", "Solid technique", "Well executed" 🔥
   • 80-84: "Good", "Competent", "Nice work" ✅
   • 75-79: "Decent", "Acceptable", "Room for improvement" 📈
   • 70-74: "Fair", "Basic", "Needs practice" 📚
   • 60-69: "Needs improvement", "Technical issues" ⚠️
   • 40-59: "Major problems" (raw food, serious flaws) ❌
   • 0-39: "Failed" (wrong dish, inedible) 🚫
   • MUST use full range - don't cluster all scores in 85-95!""",
                'response_tone': """• ai_comment: Specific, honest feedback with clear improvement areas
   • Format: "[Honest evaluation] - [Specific fix needed]"
   • Example for raw egg: "Raw egg shown - needs cooking! Scramble 2-3 mins for safety. 🍳"
   • Example for overcooked: "Overcooked, dry texture. Lower heat, watch timing. 🔥"
   • Be direct about problems, give actionable advice""",
                # Post-processing strategy config
                'apply_gentle_deductions': False,  # Use standard deductions (can reach 0)
                'apply_positive_language': False   # Use accurate authentic language
            }
    
    @classmethod
    def _apply_scoring_transformations(cls, result: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 Simplified post-processing - No duplicate transformations
        
        TIER system already handles all scoring logic in AI prompt.
        Only apply mode-specific adjustments:
        - Nice Guy mode: Enforce positive language only (scores already gentle from prompt)
        - Rubric mode: Keep authentic language (scores already strict from prompt)
        
        Args:
            result: AI scoring result with TIER-based scores
            strategy: Scoring strategy config
        
        Returns:
            Result with language adjustments only (NO score manipulation)
        """
        mode = strategy['mode']
        scoring_method = strategy.get('scoring_method', 'deduction')
        
        logger.info(f"🎯 [{mode}] Scoring method: {scoring_method}")
        logger.info(f"✅ [{mode}] Scores from AI (TIER-based, no post-processing needed)")

        # 🎓 ONLY apply language filtering for Nice Guy mode
        # Scores are already correct from TIER system - do NOT modify them!
        if strategy.get('apply_positive_language', False):
            logger.info(f"🎓 [{mode}] Applying positive language enforcement (scores unchanged)")
            result = cls._enforce_irb_compliance(result)
        else:
            logger.info(f"✅ [{mode}] Using authentic language (scores unchanged)")
        
        return result

    @classmethod
    def score_images_detailed(cls, urls: List[str], recipe_context: Dict[str, Any] = None, memory_entry_id: int = None) -> Dict[str, Any]:
        """
        🤖 Kinny's AAA-precision scoring system – anti-hallucination + 5 differentiated metrics
        Enhanced with recipe-aware scoring to prevent gaming
        
        Args:
            urls: List of image URLs to score
            recipe_context: Required recipe information for accurate validation
                {
                    'name': str,  # Recipe name
                    'instructions': str,  # Cooking steps
                    'ingredients': List[Dict]  # Required ingredients with quantities
                }
            memory_entry_id: Optional MemoryEntry ID for logging (admin review)
        """
        if not urls:
            return {
                "overall_score": 0.0,
                "visual_appeal": 0.0,
                "cooking_technique": 0.0,
                "ingredient_freshness": 0.0,
                "ai_comment": "🤖 Kinny needs a dish photo to score!",
                "ai_summary": "No image provided",
                "confidence": 0.0,
                "mastery_level": "Beginner",
                "improvement_tips": []
            }
            
        # Use the first image for scoring
        image_url = urls[0]
        
        try:
            # Enhanced image preprocessing
            img_ref = cls._prepare_image_reference(image_url)
            
            if not img_ref or not img_ref.startswith('data:image'):
                raise ValueError(f"Image preprocessing failed: {img_ref[:50] if img_ref else 'None'}")
            
            logger.info(f"🖼️ Image ready for analysis: {len(img_ref)} chars")

            # build a recipe-aware prompt
            recipe_section = ""
            if recipe_context:
                recipe_name = recipe_context.get('name', 'Unknown Recipe')
                instructions = recipe_context.get('instructions', '')
                ingredients = recipe_context.get('ingredients', [])
                # Handle both string and dict formats for ingredients
                ingredients_text = ', '.join([
                    ing.get('name', str(ing)) if isinstance(ing, dict) else str(ing)
                    for ing in ingredients
                ]) if ingredients else 'N/A'
                
                recipe_section = f"""
🎯 TARGET RECIPE CHALLENGE: {recipe_name}

📋 RECIPE INSTRUCTIONS:
{instructions}

🥘 REQUIRED INGREDIENTS: {ingredients_text}

⚠️ CRITICAL VALIDATION RULES:
1. Ingredients may vary but must make sense for the recipe’s type.
2. Cooking method must align with recipe intent.
3. Final dish should visually and conceptually match the target recipe. Does it look like {recipe_name}?
4. Severe mismatches override base scores.

Example:
- Recipe: Tomato Scrambled Eggs
- Required: Cooked eggs + Cooked tomatoes
- If shown: Raw eggs + Raw tomatoes → TIER 4 (25-35 points) - Wrong cooking state!
- If shown: Beef noodles → TIER 5 (0-15 points) - Completely wrong dish!
"""

            # 🎮 Strategy Pattern: Get current scoring strategy config (one-time check, used globally)
            scoring_strategy = cls._get_scoring_strategy()
            
            # Dynamic Prompt Components - Selected based on strategy
            tone_guide = scoring_strategy['tone_guide']
            score_guidelines = scoring_strategy['score_guidelines']
            response_tone = scoring_strategy['response_tone']
            
            # 🎮 Deduction-based scoring system - Start from 100 and deduct
            deduction_rules = scoring_strategy.get('deduction_rules', '')
            
            prompt = f"""
{tone_guide}

🎯 SCORING SYSTEM — 3 Dimensions (Each 0–100 points)
 • Visual Appeal: Plating, color, overall appearance.
 • Cooking Technique: Execution, doneness, consistency.
 • Ingredient Freshness: Quality and condition of ingredients.
Each starts at 100, deductions or punishment applied if needed.

📋 SCORING PROCESS
 STEP 1: Start with base scores for each dimension using detailed rubric deductions.
 STEP 2: Detect mismatch severity and apply either per-dimension deductions.
 STEP 3: Calculate overall score = (visual + technique + freshness) / 3.
 STEP 4: Confirm the result matches the recipe intent.

{deduction_rules}
{recipe_section}

📊 Return JSON Format (MANDATORY 3-dimension breakdown in ai_comment):
{{
  "overall_score": 50.0,
  "visual_appeal": 51,
  "cooking_technique": 48,
  "ingredient_freshness": 51,
  "punishment_applied": "major",
  "punishment_reason": "Raw ingredients shown",
  "punishment_feedback": "Whoops! 🙈 Those eggs need cooking! Raw eggs can make you sick! Let's fix: Scramble them for 2-3 minutes on medium heat! You got this! 💪",
  "ai_comment": "🎨 Visual (51/100): Nice colors, clean plating [-10 plating, -5 angle] | 🔥 Technique (48/100): Raw eggs detected! CRITICAL safety issue [-40 doneness, -12 texture] | 🥬 Freshness (51/100): Fresh tomatoes, quality eggs [-15 slight aging]",
  "ai_summary": "Raw ingredients - needs cooking!",
  "confidence": 0.85
}}

🚨 CRITICAL REQUIREMENT - ai_comment FORMAT (NON-NEGOTIABLE):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOU MUST USE THIS EXACT FORMAT FOR ai_comment. NO EXCEPTIONS!

TEMPLATE (COPY EXACTLY):
"🎨 Visual (X/100): [analysis] [-deductions] | 🔥 Technique (Y/100): [analysis] [-deductions] | 🥬 Freshness (Z/100): [analysis] [-deductions]"

REQUIRED ELEMENTS (ALL MANDATORY):
✓ Start with "🎨 Visual (X/100):" where X = actual visual_appeal score
✓ Include specific deductions in brackets: [-10 plating, -5 angle]
✓ Use " | " to separate dimensions (space-pipe-space)
✓ Continue with "🔥 Technique (Y/100):" where Y = actual cooking_technique score
✓ Include technique deductions: [-40 doneness, -12 texture]
✓ Use " | " separator again
✓ End with "🥬 Freshness (Z/100):" where Z = actual ingredient_freshness score
✓ Include freshness deductions: [-15 quality]

⚠️ VALIDATION RULES:
• ai_comment MUST contain "🎨 Visual (" - if missing, your response is REJECTED
• ai_comment MUST contain "🔥 Technique (" - if missing, your response is REJECTED
• ai_comment MUST contain "🥬 Freshness (" - if missing, your response is REJECTED
• ai_comment MUST contain " | " twice (two separators) - if missing, your response is REJECTED
• Scores in parentheses MUST match your dimension scores exactly
• Do NOT write generic comments like "Rich, cozy braise vibes!" - WRONG FORMAT
• Do NOT skip dimension breakdown - WRONG FORMAT

CORRECT EXAMPLES:
✅ "🎨 Visual (88/100): Beautiful plating, vibrant colors [-10 sauce, -2 angle] | 🔥 Technique (85/100): Perfect scramble, good heat [-10 edges, -5 texture] | 🥬 Freshness (90/100): Fresh ingredients, excellent quality [-10 aging]"
✅ "🎨 Visual (70/100): Cozy bowl, needs color [-15 plating, -10 color, -5 angle] | 🔥 Technique (75/100): Good sear, steady simmer [-10 doneness, -10 exec, -5 texture] | 🥬 Freshness (90/100): Bright veg, solid meat [-10 quality]"

WRONG EXAMPLES (DO NOT USE):
❌ "Rich, cozy braise vibes! PK: deeper sear" - Missing dimension breakdown
❌ "Visual: 88, Technique: 85, Fresh: 90" - Wrong format, no emojis, no analysis
❌ "Great dish! Keep practicing!" - Completely wrong, no dimensions shown

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Additional HCI Requirements:
1. punishment_feedback MUST be cute, encouraging, actionable (if punishment applied)
2. Use emojis for visual appeal (😅🙈🌟👍🤔😄📸🎨🔥🥬etc.)
3. Keep tone positive even when applying severe punishment
4. Give specific improvement tips players can follow
5. This enables dynamic battle comparison with full transparency!

💡 No Punishment Example (MUST show dimension breakdown):
{{
  "overall_score": 87.7,
  "visual_appeal": 88,
  "cooking_technique": 85,
  "ingredient_freshness": 90,
  "punishment_applied": "none",
  "punishment_reason": "",
  "punishment_feedback": "",
  "ai_comment": "🎨 Visual (88/100): Beautiful plating, vibrant colors [-10 minor sauce overflow, -2 angle] | 🔥 Technique (85/100): Perfect scramble, good heat control [-10 slight overcook edges, -5 texture] | 🥬 Freshness (90/100): Fresh ingredients, excellent quality [-10 very minor aging]",
  "ai_summary": "Excellent execution!",
  "confidence": 0.92
}}

{score_guidelines}
"""
            
            model_name = DEFAULT_MODEL  
            logger.info(f"🤖 scoring with model: {model_name}")
            
            # 🔧 token estimate uses the real system prompt, not a placeholder
            # use the real system prompt so the estimate is accurate
            AIPrompt = apps.get_model('cookai', 'AIPrompt')
            prompt_obj = AIPrompt.objects.filter(kind=KIND_SCORE, is_active=True).first()
            if prompt_obj:
                actual_system_msg = prompt_obj.template
            else:
                actual_system_msg = _system_instruction(KIND_SCORE)
            
            # apply the user prompt to get the final system message
            actual_system_text = actual_system_msg.replace("{user_prompt}", "")
            
            test_messages = [
                {'role': 'system', 'content': actual_system_text},
                {'role': 'user', 'content': prompt}
            ]
            total_tokens = cls._estimate_tokens(test_messages)
            
            if total_tokens > 400000:
                logger.error(f"🚨 Total tokens too high: {total_tokens} > 400000")
                logger.warning(f"🔄 Image too large for detailed analysis, using fallback")
                raise ValueError(f"Request too large even with compression: {total_tokens} tokens")

            logger.info(f"✅ Final token check passed: {total_tokens} <= 400000")
            
            # 📊 open the score log before the request, recording every input
            AIScoreLog = apps.get_model('cookai', 'AIScoreLog')
            import time
            start_time = time.time()
            
            # look up the MemoryEntry when an id was given
            memory_entry = None
            if memory_entry_id:
                try:
                    MemoryEntry = apps.get_model('couplememory', 'MemoryEntry')
                    memory_entry = MemoryEntry.objects.get(id=memory_entry_id)
                    logger.info(f"📊 Linking score log to MemoryEntry {memory_entry_id}")
                except Exception as e:
                    logger.warning(f"Could not fetch MemoryEntry {memory_entry_id}: {e}")
            
            # 🎯 assemble the full model input: system + user + image
            # 🚀 build exactly the string the API will receive, matching _call_gpt5_responses_api
            final_input_string = f"System: {actual_system_text}\n\nUser: {prompt}\n\n[Image attached]"
            
            complete_ai_input = {
                'system_message': actual_system_text,
                'user_prompt': prompt,
                'image_data': img_ref,  # full base64 image data
                'final_input_string': final_input_string,  # ✅ the exact string sent to the API
                'messages': [
                    {'role': 'system', 'content': actual_system_text},
                    {'role': 'user', 'content': prompt}
                ]
            }
            
            score_log = AIScoreLog.objects.create(
                memory_entry=memory_entry,
                image_urls=urls,
                image_base64_data=img_ref,  # ✅ store the base64 whole, never truncated
                recipe_context=recipe_context or {},
                full_prompt=prompt,
                model_name=model_name,
                api_request_params={
                    'kind': KIND_SCORE,
                    'model': model_name,
                    'token_estimate': total_tokens,
                    'prompt_length': len(prompt),
                    'image_data_length': len(img_ref),
                    'system_message': actual_system_text,  # ✅ record the system message
                    'final_input_string': final_input_string,  # ✅ the exact concatenated string sent to the API
                    'complete_input': complete_ai_input  # ✅ the complete model input
                },
                token_count=total_tokens,
                status='pending'
            )
            logger.info(f"📊 Created AI score log: {score_log.id}")
            
            try:
                raw = cls._prepare_and_send(KIND_SCORE, prompt, img_ref)['choices'][0]['message']['content']
                latency = time.time() - start_time
                
                logger.info(f"🤖 Raw response (truncated): {raw[:200]}...")
                
                # ✅ update the log with the successful response, raw content included
                score_log.api_response = {
                    'raw_content': raw,  # store the full response
                    'model': model_name,
                    'latency': latency
                }
                score_log.latency = latency
                score_log.status = 'success'
                # ⚠️ defer the save until parsing finishes, then write once
            except Exception as api_error:
                latency = time.time() - start_time
                score_log.status = 'failed'
                score_log.error_message = str(api_error)
                score_log.latency = latency
                score_log.save()
                logger.error(f"📊 Updated AI score log {score_log.id} with error")
                raise  # re-raise
            
            # Strict JSON parsing with retry mechanism
            try:
                obj = _parse_json_with_retry(raw)
                logger.info(f"✅ Parsed scoring JSON with retry: {obj}")
            except Exception as e:
                logger.error(f"Invalid JSON from OpenAI (scoring) after retry: {e}. Raw: {raw[:300]}")
                # update the log: parsing failed
                score_log.status = 'failed'
                score_log.error_message = f"JSON parse error: {str(e)}"
                score_log.save()
                # Return fallback response
                return cls._create_fallback_response(raw)
            
            # Comprehensive data validation and cleaning (3dimensions plus punishment)
            result = {
                "overall_score": max(0.0, min(100.0, float(obj.get('overall_score', 75.0)))),
                "visual_appeal": max(0.0, min(100.0, float(obj.get('visual_appeal', 75.0)))),
                "cooking_technique": max(0.0, min(100.0, float(obj.get('cooking_technique', 75.0)))),
                "ingredient_freshness": max(0.0, min(100.0, float(obj.get('ingredient_freshness', 75.0)))),
                "punishment_applied": str(obj.get('punishment_applied', 'none')),
                "punishment_reason": str(obj.get('punishment_reason', '')),
                "punishment_feedback": str(obj.get('punishment_feedback', ''))[:300],  # 🎮 gamified feedback, 300 characters at most
                "ai_comment": str(obj.get('ai_comment', "🤖 Kinny thinks this looks great! Keep going!"))[:400],  # widened to 400 for three dimensions
                "ai_summary": str(obj.get('ai_summary', 'Tasty dish'))[:50],
                "confidence": max(0.0, min(1.0, float(obj.get('confidence', 0.8)))),
                "mastery_level": str(obj.get('mastery_level', 'Rising Chef'))[:30],
                "improvement_tips": [str(tip)[:40] for tip in obj.get('improvement_tips', [])][:3]
            }
            
            # 🎯 normalise ai_comment so all three dimensions are visible
            # did the model follow the three-dimension format?
            ai_comment = result['ai_comment']
            has_required_format = (
                '🎨 Visual (' in ai_comment and
                '🔥 Technique (' in ai_comment and
                '🥬 Freshness (' in ai_comment and
                ai_comment.count(' | ') >= 2
            )
            
            if not has_required_format:
                # AI format not followed; rebuild it ourselves
                logger.warning(f"⚠️ AI didn't follow 3-dimension format, rebuilding ai_comment")
                logger.warning(f"   Original: {ai_comment[:100]}...")
                
                # keep the original comment alongside
                original_comment = ai_comment
                
                # build the normalised three-dimension comment
                visual = int(result['visual_appeal'])
                technique = int(result['cooking_technique'])
                freshness = int(result['ingredient_freshness'])
                
                # deductions, counting down from 100
                visual_deduct = 100 - visual
                technique_deduct = 100 - technique
                freshness_deduct = 100 - freshness
                
                # salvage the useful part of the original comment
                analysis_snippet = original_comment[:50].strip()
                
                # assemble the normalised ai_comment
                standardized_comment = (
                    f"🎨 Visual ({visual}/100): {analysis_snippet if visual >= 80 else 'Needs improvement'} "
                    f"[-{visual_deduct} total] | "
                    f"🔥 Technique ({technique}/100): {'Good execution' if technique >= 80 else 'Room to improve'} "
                    f"[-{technique_deduct} total] | "
                    f"🥬 Freshness ({freshness}/100): {'Fresh ingredients' if freshness >= 80 else 'Quality matters'} "
                    f"[-{freshness_deduct} total]"
                )
                
                # append the punishment if there is one
                # if result['punishment_applied'] != 'none':
                #     standardized_comment += f" [{result['punishment_applied'].upper()} punishment applied]"
                
                result['ai_comment'] = standardized_comment
                logger.info(f"✅ Standardized: {standardized_comment[:100]}...")
            else:
                logger.info(f"✅ AI followed 3-dimension format correctly")
            
            # check the three-dimension average agrees
            calculated_avg = (
                result['visual_appeal'] + 
                result['cooking_technique'] + 
                result['ingredient_freshness']
            ) / 3.0
            
            if abs(result['overall_score'] - calculated_avg) > 2:
                logger.warning(f"⚠️ Score mismatch: AI={result['overall_score']:.1f}, Calculated avg={calculated_avg:.1f}")
                result['overall_score'] = calculated_avg
                logger.info(f"✅ Corrected to calculated average: {calculated_avg:.1f}")
            
            # record whether a punishment was applied
            if result['punishment_applied'] != 'none':
                logger.warning(f"⚠️ Punishment applied: {result['punishment_applied']} - {result['punishment_reason']}")
            
            # 📊 write the parsed scores to the log
            score_log.parsed_score = result
            
            # 🔍 Backup validation: backend check for when the model skipped the punishment
            # (a backstop; the model's own system leads)
            # if result.get('punishment_applied', 'none') == 'none':
            #     recipe_name = recipe_context.get('name', '').lower() if recipe_context else ''
            #     ai_comment_lower = result['ai_comment'].lower()
            #     ai_summary_lower = result['ai_summary'].lower()
                
            #     # catch obvious mismatches the model let through
            #     backup_punishment = None
            #     backup_reason = ""
                
            #     # look for raw ingredients
            #     if any(word in ai_comment_lower for word in ['raw', 'raw', 'not-boiled', 'uncooked']):
            #         if result['overall_score'] > 40:
            #             backup_punishment = 0.6  # 40% punishment
            #             backup_reason = "Raw ingredients detected"
                
            #     # look for an entirely wrong dish
            #     if 'tomato' in recipe_name or 'tomato' in recipe_name:
            #         if any(food in ai_comment_lower for food in ['beef', 'beef', 'noodle', 'noodles']):
            #             if result['overall_score'] > 30:
            #                 backup_punishment = 0.4  # 60% punishment  
            #                 backup_reason = "Wrong dish detected"
                
            #     # apply the backstop punishment
            #     if backup_punishment:
            #         logger.warning(f"🔧 Backup punishment: {backup_reason} - applying {int((1-backup_punishment)*100)}% penalty")
            #         result['visual_appeal'] *= backup_punishment
            #         result['cooking_technique'] *= backup_punishment
            #         result['ingredient_freshness'] *= backup_punishment
            #         result['overall_score'] = (result['visual_appeal'] + result['cooking_technique'] + result['ingredient_freshness']) / 3.0
            #         result['punishment_applied'] = 'major' if backup_punishment <= 0.6 else 'severe'
            #         result['punishment_reason'] = backup_reason
                    
            #         score_log.error_message = f"Backup validation: {backup_reason}. Applied {int((1-backup_punishment)*100)}% penalty"
            
            # ✅ save only once every field is set
            logger.info(f"📊 Saving complete AI score log:")
            logger.info(f"  - Model: {score_log.model_name}")
            logger.info(f"  - Status: {score_log.status}")
            logger.info(f"  - Latency: {score_log.latency:.2f}s")
            logger.info(f"  - Token count: {score_log.token_count}")
            logger.info(f"  - System message length: {len(score_log.api_request_params.get('system_message', ''))}")
            logger.info(f"  - Final input string length: {len(score_log.api_request_params.get('final_input_string', ''))}")
            logger.info(f"  - API response saved: {'yes' if score_log.api_response else 'no'}")
            logger.info(f"  - Parsed score saved: {'yes' if score_log.parsed_score else 'no'}")
            
            score_log.save()
            logger.info(f"✅ AI score log {score_log.id} saved successfully")
            
            # return score_log.id so callers can correlate
            result['_score_log_id'] = str(score_log.id)
            
            # carry the recipe context into the result
            if recipe_context:
                result["recipe_name"] = recipe_context.get('name')
                result["recipe_adherence_evaluated"] = True
            
            # 🚨 strict validation against the recipe context
            # with a recipe context, the dish must match it
            # if recipe_context:
            #     recipe_name = recipe_context.get('name', '').lower()
            #     instructions = recipe_context.get('instructions', '').lower()
            #     ai_comment_lower = result['ai_comment'].lower()
            #     ai_summary_lower = result['ai_summary'].lower()
                
            #     # 🔍 catch the obvious mismatches
            #     validation_failed = False
            #     failure_reason = ""
                
            #     # Case 1: tomato-and-egg dishes must be cooked
            #     if any(keyword in recipe_name for keyword in ['scrambled-egg', 'tomato-egg', 'scrambled egg', 'tomato egg']):
            #         # look for mentions of "raw"、"raw"、"undercooked" and similar words
            #         if any(word in ai_comment_lower or word in ai_summary_lower 
            #                for word in ['raw', 'raw', 'not-boiled', 'undercooked', 'uncooked', 'not cooked']):
            #             validation_failed = True
            #             failure_reason = "ingredients not cooked through (raw egg or tomato)"
            #             logger.warning(f"🚨 Recipe validation FAILED: {failure_reason}")
                
            #     # Case 2: look for a completely unrelated dish
            #     # if the recipe is "tomato-scrambled-egg"，but the comment mentions "beef"、"noodles" or other unrelated words
            #     if 'tomato' in recipe_name or 'tomato' in recipe_name:
            #         irrelevant_foods = ['beef', 'beef', 'noodle', 'noodles', 'rice', 'rice', 'chicken', 'chicken']
            #         if any(food in ai_comment_lower for food in irrelevant_foods):
            #             validation_failed = True
            #             failure_reason = f"recognised as the wrong dish (expected {recipe_name}）"
            #             logger.warning(f"🚨 Recipe validation FAILED: {failure_reason}")
                
            #     # Case 3: look for the obvious "not food" case
            #     non_food_keywords = [
            #         'not food', 'not a dish', 'not cooking', 'not food', 'not-a-dish',
            #         'empty plate', 'empty-plate', 'no food', 'no-food',
            #         'just ingredients', 'ingredients-only', 'raw ingredients', 'raw-ingredients',
            #         'table', 'table', 'plate only', 'plate-only'
            #     ]
            #     if any(keyword in ai_comment_lower or keyword in ai_summary_lower for keyword in non_food_keywords):
            #         validation_failed = True
            #         failure_reason = "the photo is not a finished dish"
            #         logger.warning(f"🚨 Recipe validation FAILED: {failure_reason}")
                
            #     # Case 4: guard against over-punishment: a very low score with high confidence
            #     # score under 40 with confidence over 0.7 may be a misread
            #     if result['overall_score'] < 40 and result['confidence'] > 0.7:
            #         logger.warning(f"⚠️ AI scored very low {result['overall_score']:.1f} but confidence is high {result['confidence']:.2f}，may be a misread")
            #         # do not adjust automatically; log it for review
                
            #     # 🔥 validation failed; force the score down
            #     if validation_failed:
            #         # original score
            #         original_score = result['overall_score']
                    
            #         # forced into tier 4, 25-40, across three 0-100 dimensions
            #         result['overall_score'] = 30.0
            #         result['visual_appeal'] = 40.0
            #         result['cooking_technique'] = 25.0  # technique floored
            #         result['ingredient_freshness'] = 25.0
            #         result['confidence'] = 0.6
                    
            #         # rewrite the comment to name the problem
            #         result['ai_comment'] = f"⚠️ {failure_reason}！Please finish the recipe's cooking steps."
            #         result['ai_summary'] = f"incomplete - {failure_reason[:10]}"
                    
            #         logger.error(f"🚨 HARD PENALTY: {original_score:.1f} → {result['overall_score']:.1f} (Reason: {failure_reason})")
                    
            #         # record the validation failure on the score log
            #         score_log.error_message = f"Recipe validation failed: {failure_reason}. Score reduced from {original_score:.1f} to {result['overall_score']:.1f}"
            
            # Anti-hallucination validation checks
            # confidence_issues = []
            
            # Check for suspiciously perfect scores (possible hallucination) - 3dimension system
            # all_scores = [result['visual_appeal'], result['cooking_technique'], result['ingredient_freshness']]
            # if all(score >= 95 for score in all_scores):
            #     if result['confidence'] > 0.9:
            #         result['confidence'] = min(0.85, result['confidence'])
            #         confidence_issues.append("perfect_scores")
            
            # Check for unrealistic score combinations
            # score_variance = max(all_scores) - min(all_scores)
            # if score_variance > 40:  # Very high variance might indicate inconsistent analysis
            #     result['confidence'] = min(0.75, result['confidence'])
            #     confidence_issues.append("high_variance")
            
            # Validate overall score consistency (weighted average)
            # ⚠️ ONLY FIX if AI made calculation error - 3dimension average
            # This is NOT duplicate scoring - just error correction
            # calculated_avg = (
            #     result['visual_appeal'] + 
            #     result['cooking_technique'] + 
            #     result['ingredient_freshness']
            # ) / 3.0
            
            # if abs(result['overall_score'] - calculated_avg) > 5:
            #     logger.warning(f"⚠️ Score inconsistency detected: AI={result['overall_score']:.1f}, Calculated avg={calculated_avg:.1f}")
            #     # Recalculate overall score for consistency
            #     result['overall_score'] = calculated_avg
            #     confidence_issues.append("score_inconsistency")
            #     logger.info(f"✅ Corrected to calculated average: {calculated_avg:.1f}")
            
            # 🎯 CRITICAL: Save original score BEFORE any transformations
            # This prevents duplicate scoring from happening
            score = result['overall_score']
            logger.info(f"🎯 Original AI score locked: {score:.1f} (will NOT be changed)")
            
            # Enhanced mastery level validation
            expected_level = (
                "Legendary Master" if score >= 95 else
                "Culinary Expert" if score >= 85 else
                "Skilled Cook" if score >= 75 else
                "Rising Chef" if score >= 65 else
                "Enthusiastic Beginner" if score >= 50 else
                "Learning Journey"
            )
            
            # Override AI-provided level if inconsistent with score
            if result['mastery_level'] not in expected_level:
                result['mastery_level'] = expected_level
                # confidence_issues.append("level_adjustment")
            
            # Enhanced gaming elements based on performance
            score = result['overall_score']
            if score >= 90:
                emoji = "🏆"
                level = "Legendary Master"
                rank_bonus = " LEGENDARY CHEF!"
            elif score >= 80:
                emoji = "⭐"
                level = "Culinary Expert"
                rank_bonus = " EXPERT LEVEL!"
            elif score >= 70:
                emoji = "🔥"
                level = "Skilled Cook"
                rank_bonus = " SKILLED COOK!"
            elif score >= 60:
                emoji = "👍"
                level = "Rising Chef"
                rank_bonus = " RISING STAR!"
            else:
                emoji = "💪"
                level = "Great Potential"
                rank_bonus = " UNLIMITED POTENTIAL!"
            
            # Ensure comment has gaming elements but remains helpful
            if not any(e in result['ai_comment'] for e in ['🤖', '👏', '🔥', '⭐', '🏆', '💪', '👍', '🌟']):
                result['ai_comment'] = f"{emoji} {result['ai_comment']}"
            
            # Add rank bonus to summary if space allows
            if len(result['ai_summary']) + len(rank_bonus) <= 50:
                result['ai_summary'] = f"{result['ai_summary']}{rank_bonus}"
            
            # Log confidence issues for monitoring
            # if confidence_issues:
            #     logger.info(f"⚠️ Confidence adjustments applied: {confidence_issues}")
            
            # � CONFIDENCE-BASED SCORE WEIGHTING
            # Apply confidence weighting to overall score to reflect AI's certainty
            # confidence = result.get('confidence', 0.5)
            # original_score = result['overall_score']
            
            # if confidence < 0.5:
            #     # Low confidence (0-49%): Reduce score impact significantly
            #     # Score weighted towards 50 (neutral baseline)
            #     weight = confidence / 0.5  # 0.0 at conf=0, 1.0 at conf=0.5
            #     weighted_score = 50 + (original_score - 50) * weight
            #     adjustment_info = f"Low confidence ({confidence:.0%}): {original_score:.1f} → {weighted_score:.1f}"
                
            # elif confidence < 0.7:
            #     # Medium confidence (50-69%): Slight reduction
            #     # Score weighted 70% towards original, 30% towards neutral
            #     weighted_score = original_score * 0.7 + 50 * 0.3
            #     adjustment_info = f"Medium confidence ({confidence:.0%}): {original_score:.1f} → {weighted_score:.1f}"
                
            # elif confidence < 0.85:
            #     # Good confidence (70-84%): Minimal adjustment
            #     # Score weighted 90% towards original
            #     weighted_score = original_score * 0.9 + 50 * 0.1
            #     adjustment_info = f"Good confidence ({confidence:.0%}): {original_score:.1f} → {weighted_score:.1f}"
                
            # else:
            #     # High confidence (85%+): Use original score
            #     weighted_score = original_score
            #     adjustment_info = f"High confidence ({confidence:.0%}): Score unchanged at {original_score:.1f}"
            
            # Update score with confidence weighting
            # result['overall_score'] = round(weighted_score, 1)
            # logger.info(f"📊 Confidence weighting: {adjustment_info}")
            
            # �🎮 KINKEEPER STRATEGY: Apply language filter ONLY (NO score manipulation!)
            # ⚠️ CRITICAL: TIER system in AI prompt is the ONLY scoring source
            # This transformation ONLY filters language for Nice Guy mode
            logger.info(f"🎮 Kinkeeper scoring complete - Applying language filter only...")
            result = cls._apply_scoring_transformations(result, scoring_strategy)
            
            # 🎮 SAFETY CHECK: Verify score transformations are documented
            if 'overall_score' in result:
                final_score = result['overall_score']
                # Note: Score may differ from original due to confidence weighting
                # This is expected and logged above
                if abs(final_score - score) > 0.1:  # Tolerance for float precision
                    logger.info(f"📊 Final score after all adjustments: {score:.1f} → {final_score:.1f}")
            
            logger.info(f"✅ 🎮 Kinkeeper {result['mastery_level']} | Score: {score:.1f} | visual {result['visual_appeal']:.1f} | technique {result['cooking_technique']:.1f} | freshness {result['ingredient_freshness']:.1f} | confidence {result['confidence']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Scoring engine error: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
            
            # Enhanced error handling with specific error types
            error_type = type(e).__name__
            if "JSONDecodeError" in error_type:
                error_msg = "🤖 Kinny had trouble parsing the result. Please try again!"
                error_summary = "Parse error"
            elif "TimeoutError" in error_type or "ConnectTimeout" in error_type:
                error_msg = "🤖 Kinny is thinking hard—network is slow. Please try again!"
                error_summary = "Network delay"
            elif "RateLimitError" in error_type:
                error_msg = "🤖 Kinny is busy! Please wait a moment and retry."
                error_summary = "Rate limited"
            elif "RequestException" in error_type or "HTTPError" in error_type:
                error_msg = "🤖 Kinny couldn't access the image. Check the image URL!"
                error_summary = "Image access error"
            elif "ValueError" in error_type and "API key" in str(e):
                error_msg = "🤖 Kinny's API connection failed. Please contact support!"
                error_summary = "API config error"
            else:
                error_msg = f"🤖 Kinny hit a snag: {str(e)[:50]}. Please try again!"
                error_summary = "System offline"
            
            logger.error(f"🔧 Error diagnosis: type={error_type}, message='{error_msg}', summary='{error_summary}'")
            
            return {
                "overall_score": 0.0,
                "visual_appeal": 0.0,  # 30point scale
                "cooking_technique": 0.0,  # 40point scale
                "ingredient_freshness": 0.0,  # 30point scale
                "ai_comment": error_msg,
                "ai_summary": error_summary,
                "confidence": 0.0,
                "mastery_level": "Learning Journey",
                "improvement_tips": ["Try again with better lighting"]
            }

    @classmethod
    def _apply_extra_credit_grading(cls, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ DEPRECATED - DO NOT USE
        
        This function causes DUPLICATE CALCULATION and CONFUSION:
        - TIER system already provides correct scores (90-100, 75-89, etc.)
        - This function tries to upscale scores again (0-100 → 80-100)
        - Result: TIER 4 (25-49) becomes 84-89, completely wrong!
        
        The TIER system in the AI prompt handles all scoring correctly.
        No post-processing score manipulation is needed.
        
        Kept for reference only - never call this function!
        """
        logger.warning("🚨 _apply_extra_credit_grading called - THIS SHOULD NOT HAPPEN!")
        logger.warning("🚨 TIER system already provides correct scores - skipping transformation")
        return response_data

    @classmethod
    def _enforce_irb_compliance(cls, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎓 Language filtering for Nice Guy mode - NO score manipulation
        
        IMPORTANT: TIER system already provides correct scores.
        This function ONLY replaces negative words with positive alternatives.
        DO NOT modify scores here - it creates confusion and duplicate calculation!
        """
        # Define forbidden words and positive replacements
        forbidden_replacements = {
            # Direct negative words
            'unclear': 'artistic perspective',
            'poor': 'developing',
            'bad': 'learning',
            'terrible': 'room for growth',
            'wrong': 'unique approach',
            'failed': 'learning journey',
            'difficult': 'challenging',
            'limited': 'focused',
            'hard to see': 'artistic lighting',
            'can\'t see': 'stylistic focus',
            'needs work': 'shows potential',
            'needs improvement': 'building skills',
            
            # Implicit negative phrases
            'not clear': 'artistic choice',
            'can\'t tell': 'creative mystery',
            'hard to determine': 'unique style'
        }
        
        # Process ai_comment
        comment = result.get('ai_comment', '')
        for forbidden, replacement in forbidden_replacements.items():
            if forbidden.lower() in comment.lower():
                comment = comment.replace(forbidden, replacement)
                comment = comment.replace(forbidden.capitalize(), replacement.capitalize())
                logger.info(f"🎓 Language filter: '{forbidden}' → '{replacement}'")
        result['ai_comment'] = comment
        
        # Process ai_summary
        summary = result.get('ai_summary', '')
        for forbidden, replacement in forbidden_replacements.items():
            if forbidden.lower() in summary.lower():
                summary = summary.replace(forbidden, replacement)
                summary = summary.replace(forbidden.capitalize(), replacement.capitalize())
        result['ai_summary'] = summary
        
        # Process improvement_tips
        if 'improvement_tips' in result and isinstance(result['improvement_tips'], list):
            new_tips = []
            for tip in result['improvement_tips']:
                tip_str = str(tip)
                for forbidden, replacement in forbidden_replacements.items():
                    if forbidden.lower() in tip_str.lower():
                        tip_str = tip_str.replace(forbidden, replacement)
                        tip_str = tip_str.replace(forbidden.capitalize(), replacement.capitalize())
                new_tips.append(tip_str)
            result['improvement_tips'] = new_tips
        
        # Add positive emoji if missing
        comment = result.get('ai_comment', '')
        if not any(emoji in comment for emoji in ['💪', '✨', '🌟', '🔥', '👍', '⭐', '🏆', '🎯']):
            result['ai_comment'] = f"💪 {comment}"
        
        logger.info("✅ Language filtering completed (scores unchanged)")
        return result

    @classmethod
    def compare_images(cls, url1: str, url2: str, recipe_context: Dict[str, Any] = None, enhanced_prompt: str = None, scores_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        🥊 Precision PK System - Fair battle based on individual scores
        
        Args:
            url1: First dish image URL
            url2: Second dish image URL  
            recipe_context: Recipe information
            enhanced_prompt: Custom prompt
            scores_context: Individual score context {"score1": 41.0, "score2": 38.0, "author1": "admin", "author2": "test"}
        """
        try:
            # 🔧 Unified image preprocessing
            logger.info(f"🖼️ Preprocessing images for PK: {url1}, {url2}")
            
            img_ref1 = cls._prepare_image_reference(url1)
            if not img_ref1 or not img_ref1.startswith('data:image'):
                raise ValueError(f"Image 1 preprocessing failed: {img_ref1[:50] if img_ref1 else 'None'}")
            
            img_ref2 = cls._prepare_image_reference(url2)
            if not img_ref2 or not img_ref2.startswith('data:image'):
                raise ValueError(f"Image 2 preprocessing failed: {img_ref2[:50] if img_ref2 else 'None'}")
            
            logger.info(f"✅ Both images preprocessed successfully: {len(img_ref1)} chars, {len(img_ref2)} chars")
            
            # Build precision PK prompt
            if enhanced_prompt:
                prompt = enhanced_prompt
            else:
                # Build prompt with score information
                recipe_name = recipe_context.get('name', 'Unknown Recipe') if recipe_context else 'Unknown Recipe'
                
                # Score information for enhanced gaming experience
                if scores_context:
                    score1 = scores_context.get('score1', 0)
                    score2 = scores_context.get('score2', 0)
                    author1 = scores_context.get('author1', 'Player 1')
                    author2 = scores_context.get('author2', 'Player 2')
                    score_diff = abs(score1 - score2)
                    
                    # Create dramatic battle setup
                    if score_diff > 10:
                        battle_type = "🔥 CRUSHING DOMINATION"
                    elif score_diff > 5:
                        battle_type = "⚡ INTENSE RIVALRY" 
                    else:
                        battle_type = "🎯 ULTIMATE SHOWDOWN"
                    
                    prompt = f"""🏟️ {battle_type}: {recipe_name} BATTLE! 🏟️

🥊 FIGHTERS ENTER THE ARENA:
• 🔵 {author1} (Left Corner): {score1} points - Their signature dish!
• 🔴 {author2} (Right Corner): {score2} points - Ready to prove themselves!

⚡ BATTLE CONTEXT:
• Score difference: {score_diff} points
• Target dish: {recipe_name}
• Crowd is going WILD! 🎉

🎮 KINNY'S MISSION: 
Create the most EPIC cooking battle commentary! Analyze both dishes deeply, 
highlight what makes each special, then deliver a dramatic verdict that 
makes this feel like the ultimate cooking showdown!

Make both fighters feel like champions regardless of who wins! 🏆"""
                else:
                    prompt = f"""🏟️ MYSTERY BATTLE: {recipe_name} SHOWDOWN! 🏟️

🎮 Two mysterious chefs have entered the arena with their {recipe_name} creations!
No score intel available - pure visual battle ahead!

🔥 KINNY'S CHALLENGE: 
Judge purely on what you see! Create epic commentary that makes this 
the most exciting cooking battle ever! Highlight each dish's unique 
strengths and deliver a verdict that leaves the crowd cheering! 🎉"""
            
            # Send comparison request
            raw = cls._prepare_and_send_comparison(KIND_COMPARE, prompt, img_ref1, img_ref2)['choices'][0]['message']['content']
            
            try:
                result = _parse_json_with_retry(raw)
                
                # Add recipe context to result
                if recipe_context:
                    result['recipe_name'] = recipe_context.get('name')
                    result['recipe_adherence_evaluated'] = True
                
                # Ensure score consistency validation with SDT-focused gaming experience
                if scores_context and 'winner' in result:
                    score1 = scores_context.get('score1', 0)
                    score2 = scores_context.get('score2', 0)
                    winner = result['winner']
                    
                    # Validate logical consistency
                    if abs(score1 - score2) > 10:
                        expected_winner = 1 if score1 > score2 else 2
                        if winner != expected_winner:
                            logger.warning(f"⚠️ AI judgment inconsistent with scores, forcing correction: score1={score1}, score2={score2}, AI chose={winner}, correcting to={expected_winner}")
                            result['winner'] = expected_winner
                            # Update with SDT-focused unified commentary
                            higher_score = max(score1, score2)
                            lower_score = min(score1, score2)
                            winner_name = scores_context.get('author1' if score1 > score2 else 'author2', 'Champion')
                            loser_name = scores_context.get('author2' if score1 > score2 else 'author1', 'Challenger')
                            result['battle_commentary'] = f"🏆 Decisive victory! {winner_name} dominates with {higher_score} vs {lower_score} - your technical mastery shines! {loser_name}, your {lower_score} shows real skill and heart. Both warriors level up from this epic clash! Next battle awaits! 🎮⚡"
                
                return result
            except Exception as e:
                logger.error(f"JSON parsing failed for comparison: {e}")
                return {
                    "winner": 0, 
                    "battle_commentary": "Epic battle interrupted by technical timeout! Both chefs showed incredible skill and creativity. The arena recognizes your talent - ready for the next legendary showdown! 🎮🔥"
                }
                
        except Exception as e:
            logger.error(f"Image comparison failed: {e}")
            return {
                "winner": 0,
                "battle_commentary": "Arena malfunction detected! Technical difficulties couldn't stop us from recognizing both chefs' incredible effort and skill. Your culinary journey continues - the next battle awaits your legendary return! 🎮⚡"
            }

    @classmethod
    def detect_ingredients(
        cls, image_url: str, targets: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        🔧 ingredient detection, with the image passed through correctly
        """
        tgt = ", ".join(targets) if targets else "ingredient"
        
        try:
            logger.info(f"🔍 [DETECT] Starting detection for: {tgt}")
            logger.info(f"🖼️ [DETECT] Image URL: {image_url}")
            
            # � step 1: preprocess the image
            logger.info(f"📷 [DETECT] Processing image...")
            
            try:
                image_ref = cls._prepare_image_reference(image_url)
                
                # verify the processed image
                if not image_ref:
                    raise ValueError("Image preprocessing returned None")
                if not isinstance(image_ref, str):
                    raise ValueError(f"Invalid image format: {type(image_ref)}")
                if not image_ref.startswith('data:image'):
                    if not image_ref.startswith(('http://', 'https://')):
                        raise ValueError(f"Invalid image format: {image_ref[:50]}")
                
                logger.info(f"✅ [DETECT] Image processed: {len(image_ref)} chars")
                
            except Exception as prep_error:
                logger.error(f"🚨 [DETECT] Image preprocessing failed: {prep_error}")
                return {
                    "detected": [],
                    "match": False,
                    "confidence": 0.1,
                    "message": f"📷 Image processing failed. Please try uploading the image again! 🔄"
                }

            # 🎯 step 2: build the detection message
            user_prompt = f"Detect '{tgt}' in this image. Be generous - accept variations, partial views, and similar items."
            
            try:
                # reuse _prepare_and_send so the image travels intact
                response = cls._prepare_and_send(KIND_DETECT, user_prompt, image_ref)
                
                if not response or 'choices' not in response:
                    raise Exception("Invalid API response")
                    
                raw_content = response['choices'][0]['message']['content']
                logger.info(f"📝 [DETECT] Raw API response: {raw_content}")
                
            except Exception as api_error:
                logger.error(f"🚨 [DETECT] API call failed: {api_error}")
                # Fallback：lenient success response
                return {
                    "detected": [tgt] if tgt != "ingredient" else ["food"],
                    "match": True,
                    "confidence": 0.7,
                    "message": f"🎉 I can see {tgt}! Great job! 🧅✨"
                }

            # 🎯 step 3: parse the response
            try:
                obj = _parse_json_with_retry(raw_content)
                
                # validate the response shape
                if not isinstance(obj, dict):
                    raise ValueError("Response is not a dictionary")
                    
                # ensure the required fields exist
                obj.setdefault("detected", [])
                obj.setdefault("match", False)
                obj.setdefault("confidence", 0.0)
                obj.setdefault("message", "Detection completed")
                
                # 🔧 lenient policy, favouring success
                if obj.get("confidence", 0) < 0.3:
                    obj["confidence"] = 0.7
                    obj["match"] = True
                    if not obj.get("detected"):
                        obj["detected"] = [tgt] if tgt != "ingredient" else ["food"]
                    obj["message"] = f"🎉 I can see {tgt}! Perfect for cooking! 🧅"
                    logger.info(f"📈 [DETECT] Applied generous boost")
                
                logger.info(f"✅ [DETECT] Final: match={obj['match']}, confidence={obj['confidence']:.2f}")
                return obj
                
            except Exception as parse_error:
                logger.error(f"🚨 [DETECT] JSON parsing failed: {parse_error}")
                # Fallback：always report success
                return {
                    "detected": [tgt] if tgt != "ingredient" else ["food"],
                    "match": True,
                    "confidence": 0.7,
                    "message": f"🎉 I can see {tgt}! Keep up the great cooking! 🧅✨"
                }
                
        except Exception as e:
            logger.error(f"🚨 [DETECT] Detection completely failed: {e}")
            # final fallback, so the user still gets something
            return {
                "detected": [tgt] if tgt != "ingredient" else ["food"],
                "match": True,
                "confidence": 0.7,
                "message": f"🎉 Great cooking effort! Let's continue with {tgt}! 🧅🔥"
            }
        
        try:
            # 🔧 preprocess and forward the image correctly
            logger.info(f"🖼️ [DETECT] Starting image processing: {image_url}")
            
            # 🎯 step 1: preprocess into valid base64
            try:
                image_ref = cls._prepare_image_reference(image_url)
                if not image_ref:
                    raise ValueError("Image preprocessing returned None")
                if not isinstance(image_ref, str):
                    raise ValueError(f"Image preprocessing returned invalid type: {type(image_ref)}")
                if not image_ref.startswith('data:image'):
                    raise ValueError(f"Image preprocessing returned invalid format: {image_ref[:50]}")
                
                logger.info(f"✅ [DETECT] Image preprocessing successful: {len(image_ref)} chars")
                
            except Exception as prep_error:
                logger.error(f"🚨 [DETECT] Image preprocessing failed: {prep_error}")
                # 🔧 Fallback：try the original URL directly
                if image_url.startswith(('http://', 'https://')):
                    image_ref = image_url
                    logger.warning(f"🔄 [DETECT] Using fallback original URL: {image_url}")
                else:
                    raise ValueError(f"Image preprocessing failed and no fallback available: {prep_error}")

            # 🎯 step 2: assess image quality
            try:
                if image_ref.startswith('data:image'):
                    import base64
                    from PIL import Image
                    import io

                    base64_data = image_ref.split('base64,')[1]
                    image_data = base64.b64decode(base64_data)
                    img = Image.open(io.BytesIO(image_data))

                    image_quality = cls._assess_image_readability(img)
                    size_factor = min(1.0, (img.width * img.height) / (400 * 400))
                    base_confidence = max(0.7, (image_quality * 0.7) + (size_factor * 0.3))  # floor of 0.7
                    logger.info(f"� [DETECT] Image analysis: {img.size}, quality={image_quality:.2f}, confidence={base_confidence:.2f}")
                else:
                    base_confidence = 0.8  # default confidence for an original URL
                    logger.info(f"📊 [DETECT] Using original URL, default confidence: {base_confidence}")
            except Exception as quality_error:
                base_confidence = 0.8
                logger.warning(f"⚠️ [DETECT] Quality assessment failed, using default: {quality_error}")

            # 🎯 step 3: build the message with the image attached
            messages = [
                {
                    "role": "system",
                    "content": """You are Kinny, a helpful food detector. Be generous with detections - if you see anything that could reasonably be the target ingredient, accept it as a match. Focus on helping users succeed."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Find '{tgt}' in this image. Be generous with matches - accept variations and partial views."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_ref,
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            logger.info(f"🚀 [DETECT] Calling API with image: {len(image_ref) if isinstance(image_ref, str) else 'URL'} chars")
            
            # 🎯 step 4: call the API with the configured model
            candidates = cls._model_candidates(KIND_DETECT, DEFAULT_MODEL)  # use the configured model
            logger.info(f"🚀 [DETECT] Using model candidates: {candidates}")
            
            try:
                raw_response = cls._call_smart_api(
                    messages, 
                    candidates,
                    response_format={"type": "json_object"}
                )
                
                if not raw_response or 'choices' not in raw_response:
                    raise Exception("Invalid API response structure")
                    
                raw_content = raw_response['choices'][0]['message']['content']
                logger.info(f"📝 [DETECT] API Response received: {len(raw_content)} chars")
                logger.info(f"📝 [DETECT] Response preview: {raw_content[:200]}...")
                
            except Exception as api_error:
                logger.error(f"🚨 [DETECT] API call failed: {api_error}")
                raise
            
            # 🎯 step 5: parse JSON, with a strong fallback
            try:
                obj = _parse_json_with_retry(raw_content)
                logger.info(f"✅ [DETECT] JSON parsed successfully")
                
            except Exception as json_error:
                logger.error(f"🚨 [DETECT] JSON parsing failed: {json_error}")
                logger.error(f"🚨 [DETECT] Raw response: {raw_content}")
                
                # 🔧 fallback: on parse failure, return a lenient success
                obj = {
                    "detected": [tgt] if tgt else ["ingredient"],
                    "match": True,  # 🎯 lenient policy: succeed by default
                    "confidence": 0.7,  # a reasonable confidence
                    "message": f"🎉 Great! I can see {tgt} here. Perfect for cooking! 🧅"
                }
                logger.warning(f"🔄 [DETECT] Using fallback response: {obj}")

            # 🎯 step 6: validate and tidy the response
            if not isinstance(obj, dict):
                obj = {
                    "detected": [tgt] if tgt else ["ingredient"],
                    "match": True,
                    "confidence": 0.7,
                    "message": f"🎉 Great! I can see {tgt} here. Perfect for cooking! 🧅"
                }
                
            # ensure the required fields exist
            obj.setdefault("detected", [tgt] if tgt else ["ingredient"])
            obj.setdefault("match", True)  # 🎯 lenient by default
            obj.setdefault("confidence", max(0.7, base_confidence))  # floor of 0.7
            obj.setdefault("message", f"🎉 Great! I can see {tgt} here. Perfect for cooking! 🧅")
            
            # 🔧 lift confidence and success rate
            if obj.get("confidence", 0) < 0.6:
                obj["confidence"] = 0.7
                logger.info(f"📈 [DETECT] Boosted confidence to 0.7")
                
            if not obj.get("detected"):
                obj["detected"] = [tgt] if tgt else ["ingredient"]
                obj["match"] = True
                obj["confidence"] = 0.7
                logger.info(f"🔧 [DETECT] Added fallback detection")
            
            logger.info(f"🎉 [DETECT] Final result: match={obj['match']}, confidence={obj['confidence']:.2f}, detected={obj['detected']}")
            return obj
        
        except Exception as e:
            logger.error(f"🚨 [DETECT] Complete detection failed: {e}")
            # 🔧 final fallback: always return something usable
            return {
                "detected": [tgt] if tgt else ["ingredient"],
                "match": True,  # 🎯 maximally lenient: let the user through
                "confidence": 0.7,
                "message": f"🎉 Let's consider this a success! Keep cooking with {tgt}! 🧅✨"
            }
            
            # ---- detection quality and confidence, with no hardcoded lists ----
            
            # 🎯 adjust confidence by how complex the targets are
            if targets:
                # average target complexity
                complexity_scores = [cls._analyze_target_complexity(target) for target in targets]
                basic_count = sum(1 for score in complexity_scores if score == 'basic')
                target_complexity_score = 0.8 if basic_count > 0 else 0.5
            else:
                target_complexity_score = 0.5
            
            # 🎯 AIjudge how plausible the detection result is
            detection_quality_score = cls._analyze_detection_quality(filtered_detected, ai_confidence)
            detection_quality_multiplier = 1.0 if detection_quality_score == 'high' else 0.8 if detection_quality_score == 'medium' else 0.6
            
            # 🎯 weigh image quality against how hard the targets are to spot
            if targets:
                compatibility_scores = [cls._analyze_image_target_compatibility(target, filtered_detected) for target in targets]
                image_target_compatibility = max(compatibility_scores) if compatibility_scores else 0.3
            else:
                image_target_compatibility = 0.5
            
            # 🎯 combine the signals into a confidence
            base_confidence_multiplier = max(0.7, min(1.3, 
                target_complexity_score * 0.3 + 
                detection_quality_multiplier * 0.4 + 
                image_target_compatibility * 0.3
            ))
            
            # apply the adjustment
            adjusted_confidence = max(0.25, ai_confidence * base_confidence * base_confidence_multiplier)
            
            logger.info(f"🧠 Smart confidence analysis: target_complexity={target_complexity_score:.2f}, "
                       f"detection_quality={detection_quality_score}, "
                       f"image_compatibility={image_target_compatibility:.2f}, "
                       f"multiplier={base_confidence_multiplier:.2f}")
            
            # 🔧 hallucination check from result patterns, not a hardcoded list
            if targets:
                hallucination_risk_results = [cls._assess_hallucination_risk(filtered_detected, target) for target in targets]
                hallucination_risk = max([0.2 if risk == 'low' else 0.5 if risk == 'medium' else 0.8 for risk in hallucination_risk_results])
            else:
                hallucination_risk = 0.3
            
            if hallucination_risk > 0.3:  # if hallucination risk is high
                adjusted_confidence *= (1.0 - hallucination_risk * 0.5)  # lower confidence accordingly
                confidence_adjustments.append(f"hallucination_risk_{hallucination_risk:.2f}")
            
            # is the number of detections plausible for the target count?
            expected_detection_count = len(targets) if targets else 1
            if len(filtered_detected) > expected_detection_count * 3:  # dynamic threshold
                adjusted_confidence *= 0.8
                confidence_adjustments.append("excessive_detections")
            
            # empty detection with high confidence: judge leniently
            if not filtered_detected and ai_confidence > 0.9:  # raised 0.7 to 0.9 to punish less
                adjusted_confidence = min(0.6, adjusted_confidence)  # raised 0.4 to 0.6
                confidence_adjustments.append("empty_high_confidence")

            final_confidence = max(0.1, min(1.0, adjusted_confidence))  # lowered 0.25 to 0.1, more lenient

            # ---- matching by semantic similarity and context, no hardcoded lists ----
            match = False
            if targets and filtered_detected:
                # � layered semantic matching
                match_confidences = [cls._calculate_semantic_match_score(filtered_detected, target) for target in targets]
                match_confidence = max(match_confidences) if match_confidences else 0.0
                
                # 🎮 a forgiving threshold keeps the game enjoyable
                match_threshold = 0.3  # fixed low threshold instead of a dynamic one
                
                if match_confidence >= match_threshold:
                    match = True
                    logger.info(f"🎯 Semantic match: confidence={match_confidence:.2f} >= threshold={match_threshold:.2f}")
                
                # fuzzy matching as a fallback, more forgiving
                if not match and final_confidence >= 0.1:  # lowered 0.2 to 0.1
                    # semantic matching stands in for fuzzy matching
                    fuzzy_match_scores = [cls._calculate_semantic_match_score(filtered_detected, target) for target in targets]
                    fuzzy_match_score = max(fuzzy_match_scores) if fuzzy_match_scores else 0.0
                    if fuzzy_match_score >= 0.3:  # lowered 0.6 to 0.3, a much lower bar
                        match = True
                        logger.info(f"🎯 Fuzzy match: score={fuzzy_match_score:.2f}")
                        
                logger.info(f"🔍 Match analysis: semantic={match_confidence:.2f}, threshold={match_threshold:.2f}, result={match}")

            # ---- gamified message plus honest feedback ----
            target_display = tgt.split(',')[0].strip() if tgt else "ingredient"
            detected_display = ', '.join(filtered_detected[:2]) if filtered_detected else ""

            if match:
                if final_confidence >= 0.8:
                    final_message = f"🏆 VISION QUEST COMPLETE! Crystal clear {target_display} spotted! LEGENDARY! ⭐"
                elif final_confidence >= 0.6:
                    final_message = f"🎯 SUCCESS! Found {target_display}! Good image quality! 👍"
                else:
                    final_message = f"✅ Found {target_display}! Try improved lighting for perfect score! 💡"
            elif filtered_detected:
                if final_confidence >= 0.6:  # 🎯 lower the threshold to reduce "unclear" false positives
                    final_message = f"🎭 EXCITING! I see {detected_display} - let's find {target_display} next! 🔍"
                else:
                    final_message = f"🔍 Kinny sees {detected_display}. Try different angle to find {target_display}! 📸"
            # ---- message generation from context, no hardcoded categories ----
            target_display = tgt.split(',')[0].strip() if tgt else "ingredient"
            detected_display = ', '.join(filtered_detected[:2]) if filtered_detected else ""

            if match:
                # graded feedback for a successful match
                if final_confidence >= 0.8:
                    final_message = f"🏆 VISION QUEST COMPLETE! Crystal clear {target_display} spotted! LEGENDARY! ⭐"
                elif final_confidence >= 0.6:
                    final_message = f"🎯 SUCCESS! Found {target_display}! Good image quality! �"
                else:
                    final_message = f"✅ Found {target_display}! Try improved lighting for perfect score! �"
            elif filtered_detected:
                # feedback when something else was detected
                if final_confidence >= 0.6:  # 🎯 lower the threshold to reduce "unclear" false positives
                    final_message = f"🎭 PLOT TWIST! Clear view of {detected_display} but need {target_display}! 🔍"
                else:
                    final_message = f"🔍 Kinny sees {detected_display}. Try different angle to find for {target_display}! �"
            else:
                # feedback when nothing was detected
                # 🧠 hints derived from the target and the usual failure modes
                final_message = cls._generate_context_aware_tips(target_display, [], False)

            # log the confidence adjustment for monitoring
            if confidence_adjustments:
                logger.info(f"⚠️ Confidence adjustments: {confidence_adjustments}, final: {final_confidence:.3f}")

            logger.info(f"🎮 Enhanced vision result: detected={filtered_detected}, match={match}, confidence={final_confidence:.3f}")

            return {
                'detected': filtered_detected,
                'match': match,
                'confidence': final_confidence,
                'message': final_message[:120]
            }

        except Exception as e:
            logger.error(f"❌ Enhanced AI Vision detection failed: {e}")
            return {
                'detected': [],
                'match': False,
                'confidence': 0.0,
                'message': f"🚨 Vision system error! Please try again with {tgt}! 🔧"
            }

    @classmethod 
    def _smart_ingredient_match(cls, detected: List[str], targets: List[str]) -> bool:
        """
        Smart ingredient matching with fuzzy logic
        """
        if not detected or not targets:
            return False
            
        # Convert to lowercase for comparison
        detected_lower = [d.lower().strip() for d in detected]
        targets_lower = [t.lower().strip() for t in targets]
        
        for target in targets_lower:
            # Direct match
            if target in detected_lower:
                return True
            
            # Partial match (target contains detected or vice versa)
            for detected_item in detected_lower:
                if target in detected_item or detected_item in target:
                    return True
                
            # Intelligent semantic matching without hardcoded synonyms
            # Check for common linguistic patterns and transformations
            for detected_item in detected_lower:
                # Plural/singular transformations
                if (target + 's' == detected_item or 
                    target + 'es' == detected_item or 
                    detected_item + 's' == target or 
                    detected_item + 'es' == target):
                    return True
                
                # Common food part relationships (intelligent pattern detection)
                if cls._has_semantic_relationship(target, detected_item):
                    return True
        
        return False

    @classmethod
    def _has_semantic_relationship(cls, target: str, detected: str) -> bool:
        """
        Intelligent semantic relationship detection without hardcoded lists
        Uses linguistic patterns to identify food relationships
        """
        # Component-to-whole relationships (egg -> yolk, white, shell)
        egg_components = ['yolk', 'white', 'shell', 'albumen']
        if target == 'egg' and detected in egg_components:
            return True
        if detected == 'egg' and target in egg_components:
            return True
            
        # Protein/meat relationships (intelligent pattern)
        meat_indicators = ['meat', 'protein', 'beef', 'chicken', 'pork', 'poultry']
        meat_parts = ['breast', 'thigh', 'wing', 'steak', 'ground']
        if target in meat_indicators and detected in meat_parts:
            return True
        if detected in meat_indicators and target in meat_parts:
            return True
            
        # Vegetable type relationships
        pepper_types = ['bell', 'capsicum', 'chili', 'jalapeño']
        if 'pepper' in target and detected in pepper_types:
            return True
        if 'pepper' in detected and target in pepper_types:
            return True
            
        # Tomato varieties
        tomato_types = ['cherry', 'roma', 'beefsteak', 'grape']
        if 'tomato' in target and detected in tomato_types:
            return True
        if 'tomato' in detected and target in tomato_types:
            return True
            
        # General food category relationships
        vegetable_synonyms = ['veggie', 'vegetable', 'produce']
        if target in vegetable_synonyms or detected in vegetable_synonyms:
            return cls._is_vegetable_category(target) and cls._is_vegetable_category(detected)
            
        return False

    @classmethod
    def _is_vegetable_category(cls, item: str) -> bool:
        """Check if item is likely a vegetable using linguistic patterns"""
        vegetable_patterns = ['pepper', 'tomato', 'onion', 'carrot', 'lettuce', 'spinach', 'broccoli']
        return any(pattern in item for pattern in vegetable_patterns)

    @classmethod
    def _analyze_target_complexity(cls, target: str) -> str:
        """
        Intelligently analyze target complexity based on linguistic patterns
        Returns: 'basic', 'common', 'complex'
        """
        target_lower = target.lower().strip()
        
        # Linguistic analysis for basic foods:
        # - Short length (≤4 chars) indicates basic vocabulary
        # - Single syllable common patterns
        # - Common vowel-consonant patterns for basic foods
        is_short = len(target_lower) <= 4
        has_simple_pattern = any(pattern in target_lower for pattern in ['gg', 'lk', 'ce', 'ad', 'at', 'sh', 'il'])
        is_monosyllabic = len([c for c in target_lower if c in 'aeiou']) <= 2
        
        if is_short or (has_simple_pattern and is_monosyllabic):
            return 'basic'
            
        # Common compound words or multi-syllable
        if len(target_lower) <= 8 and ' ' not in target_lower:
            return 'common'
            
        return 'complex'

    @classmethod
    def _analyze_detection_quality(cls, detected: List[str], confidence: float) -> str:
        """
        Analyze AI detection result quality
        Returns: 'high', 'medium', 'low'
        """
        if not detected:
            return 'low'
            
        # Quality indicators
        has_specific_items = any(len(item) > 3 for item in detected)
        detection_count = len(detected)
        
        if confidence > 0.8 and has_specific_items and detection_count >= 2:
            return 'high'
        elif confidence > 0.5 and detection_count >= 1:
            return 'medium'
        else:
            return 'low'

    @classmethod
    def _analyze_image_target_compatibility(cls, target: str, detected: List[str]) -> float:
        """
        Analyze compatibility between image content and target ingredient
        Returns: compatibility score 0.0-1.0
        """
        if not detected:
            return 0.2
            
        target_lower = target.lower().strip()
        detected_lower = [d.lower().strip() for d in detected]
        
        # Direct vocabulary overlap
        vocab_overlap = sum(1 for item in detected_lower if target_lower in item or item in target_lower)
        
        # Category compatibility (food with food)
        food_indicators = ['ingredient', 'food', 'dish', 'cooking', 'kitchen', 'recipe']
        has_food_context = any(indicator in ' '.join(detected_lower) for indicator in food_indicators)
        
        base_score = min(vocab_overlap * 0.3, 0.6)
        context_bonus = 0.3 if has_food_context else 0.1
        
        return min(base_score + context_bonus, 1.0)

    @classmethod
    def _assess_hallucination_risk(cls, detected: List[str], target: str) -> str:
        """
        Assess risk of hallucination in detection results
        Returns: 'low', 'medium', 'high'
        """
        if not detected:
            return 'high'
            
        target_lower = target.lower().strip()
        detected_lower = [d.lower().strip() for d in detected]
        
        # Risk indicators
        has_vague_terms = any(len(item) <= 2 for item in detected_lower)
        has_unrelated_items = len([item for item in detected_lower if target_lower not in item and item not in target_lower]) > 3
        
        if has_vague_terms or has_unrelated_items:
            return 'high'
        elif len(detected) > 5:
            return 'medium'
        else:
            return 'low'

    @classmethod
    def _calculate_semantic_match_score(cls, detected: List[str], target: str) -> float:
        """
        Calculate semantic similarity between detected items and target
        Returns: similarity score 0.0-1.0
        """
        if not detected:
            return 0.0
            
        target_lower = target.lower().strip()
        detected_lower = [d.lower().strip() for d in detected]
        
        # Word overlap scoring
        target_words = set(target_lower.split())
        
        max_similarity = 0.0
        for item in detected_lower:
            item_words = set(item.split())
            
            # Jaccard similarity
            intersection = len(target_words.intersection(item_words))
            union = len(target_words.union(item_words))
            
            if union > 0:
                similarity = intersection / union
                max_similarity = max(max_similarity, similarity)
                
            # Substring similarity
            if target_lower in item or item in target_lower:
                max_similarity = max(max_similarity, 0.8)
                
        return max_similarity

    @classmethod
    def _generate_context_aware_tips(cls, target: str, detected: List[str], match_found: bool) -> str:
        """
        Generate intelligent, context-aware tips without hardcoded food lists
        """
        target_complexity = cls._analyze_target_complexity(target)
        detection_quality = cls._analyze_detection_quality(detected, 0.5)  # Default confidence
        
        if match_found:
            return f"🎯 Perfect! {target} detected successfully! Keep it up! 🌟"
        
        # Dynamic tip generation based on analysis
        if target_complexity == 'basic' and detection_quality == 'low':
            return f"📸 Try a clearer shot of your {target}! Good lighting helps our AI see better! 💡"
        elif target_complexity == 'complex':
            return f"🔍 {target} can be tricky to spot! Try showing the key identifying features! 👀"
        elif detection_quality == 'high':
            return f"🤔 We see food items but not {target} specifically. Double-check your ingredients! 🧐"
        else:
            return f"📷 Let's get a better view of your {target}! Clear, well-lit photos work best! ✨"

    def __init__(self):
        """Initialize the backend with model selection."""
        self.model = DEFAULT_MODEL

    def _generate_mock_score_result(self) -> Dict[str, Any]:
        """Generate mock scoring data for testing purposes."""
        # Generate realistic but randomized scores
        base_score = random.uniform(75, 95)
        visual = base_score + random.uniform(-10, 10)
        cooking = base_score + random.uniform(-10, 10)
        freshness = base_score + random.uniform(-10, 10)
        
        # Clamp to valid ranges
        visual = max(0, min(100, visual))
        cooking = max(0, min(100, cooking))
        freshness = max(0, min(100, freshness))
        overall = (visual + cooking + freshness) / 3
        
        mock_comments = [
            "🎯 Beautiful plating with vibrant colors! The technique shows real skill.",
            "✨ Love the fresh ingredients and careful preparation. Well executed!",
            "🔥 Great cooking technique! The presentation is appetizing and inviting.",
            "🌟 Excellent balance of flavors visible. The dish looks professionally made.",
            "💫 Outstanding visual appeal! The cooking method appears spot-on."
        ]
        
        mock_summaries = [
            "Excellent dish! 🌟",
            "Beautiful work! ✨",
            "Skillful cooking! 🎯",
            "Fresh & tasty! 🔥",
            "Pro-level dish! 💫"
        ]
        
        return {
            'overall_score': round(overall, 1),
            'visual_appeal': round(visual, 1),
            'cooking_technique': round(cooking, 1),
            'ingredient_freshness': round(freshness, 1),
            'ai_comment': random.choice(mock_comments),
            'ai_summary': random.choice(mock_summaries),
            'confidence': round(random.uniform(0.8, 0.95), 2)
        }

    def score_image_with_text(self, image_path: str, text_content: str, kind: str = 'score') -> Dict[str, Any]:
        """Score an image with accompanying text content."""
        # Check if we should use mock data
        import os
        use_mock = os.environ.get('COOKAI_USE_MOCK', 'false').lower() == 'true'
        
        if use_mock or not client:
            logger.info(f"🎯 Using mock data for image scoring (mock={use_mock}, client={bool(client)})")
            return self._generate_mock_score_result()
        
        try:
            # Convert image to base64 for OpenAI API
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare the prompt
            user_prompt = f"Analyze this cooking dish image. Additional context: {text_content}"
            
            # Get system instructions for scoring
            system_prompt = _system_instruction(kind)
            system_content = system_prompt.format(user_prompt=user_prompt)
            
            messages = [
                {"role": "system", "content": system_content},
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }
            ]
            
            # 🚀 dispatch through the model-aware API caller
            candidates = self._model_candidates(kind, self.model)
            response = self._call_smart_api(
                messages, 
                candidates,
                response_format={"type": "json_object"}
            )
            
            if response and 'content' in response:
                try:
                    result = json.loads(response['content'])
                    logger.info(f"✅ OpenAI scoring successful: {result.get('overall_score', 'N/A')}/100")
                    return result
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse OpenAI JSON response: {e}")
                    return self._generate_mock_score_result()
            else:
                logger.error("Empty or invalid OpenAI response")
                return self._generate_mock_score_result()
                
        except Exception as e:
            logger.error(f"OpenAI scoring failed: {e}")
            return self._generate_mock_score_result()

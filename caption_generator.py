"""
ErosLab Caption Generator v3 (FINAL)
Персона + вариативность + вовлечение + стабильность
"""

import requests
import logging
import random
import urllib.parse
import os

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ==================== ПЕРСОНА ====================
PERSONA_LINES = [
    "Ты дерзкая, уверенная и слегка токсичная девушка.",
    "Ты говоришь так, будто уже всё видела и тебе скучно.",
    "Ты не просишь — ты провоцируешь.",
    "Ты играешь с вниманием, а не выпрашиваешь его.",
]

FORMAT_TYPES = ["single", "double", "dialog"]

ENGAGEMENT_LINES = [
    "И что дальше? 😈",
    "Оценка? 1–10",
    "Ты бы остановился?",
    "Продолжение хочешь?",
    "Слабовато или норм?",
]

NSFW_TRIGGER_TAGS = {
    "slut", "sex", "nude", "naked", "penis", "vagina", "cock",
    "pussy", "cum", "anal", "blowjob", "nsfw", "explicit", "porn",
    "hentai", "xxx", "nipple", "nipples", "breast", "breasts", "ass",
    "bondage", "bdsm", "fetish", "gangbang", "creampie", "ahegao",
    "spread_legs", "pussy_juice", "uncensored", "censored", "genitals"
}

# ==================== UTILS ====================
def _safe_tags(tags):
    return [t for t in tags if t.lower() not in NSFW_TRIGGER_TAGS]

def _is_valid_response(text):
    bad = ["I'm sorry", "I can't", "As an AI", "не могу"]
    return bool(text) and len(text) > 5 and not any(b in text for b in bad)

def maybe_add_engagement(text):
    if random.random() < 0.35:
        return text + "\n\n" + random.choice(ENGAGEMENT_LINES)
    return text

def trim_text(text, max_len=220):
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."

def add_noise(text):
    if random.random() < 0.2:
        text = text.replace("...", "..")
    if random.random() < 0.2:
        text = text.replace("😈", "😏")
    return text

# ==================== PROMPT ====================
def _build_prompt(tags):
    if not tags:
        return None

    persona = random.choice(PERSONA_LINES)
    format_type = random.choice(FORMAT_TYPES)

    if format_type == "single":
        format_instruction = "Напиши ОДНУ короткую строку."
    elif format_type == "double":
        format_instruction = "Напиши ДВЕ короткие строки."
    else:
        format_instruction = "Напиши короткий диалог из 2 реплик."

    tags_str = ", ".join(tags[:10])

    return f"""
{persona}

Ты пишешь короткие подписи к откровенным артам.

Стиль:
— намёк, а не прямое описание
— уверенность
— провокация
— минимум слов

Настроение: {tags_str}

{format_instruction}

Добавь 1-3 эмодзи.
Без объяснений.
"""

# ==================== API ====================
def _try_groq(prompt):
    if not GROQ_API_KEY:
        return None
    try:
        import json
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 120,
                "temperature": 0.95
            }),
            timeout=15
        )
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"].strip()
            if _is_valid_response(text):
                logger.info("Caption via Groq")
                return text
    except Exception as e:
        logger.error(f"Groq error: {e}")
    return None

def _try_pollinations(prompt):
    try:
        encoded = urllib.parse.quote(prompt)
        r = requests.get(f"https://text.pollinations.ai/{encoded}", timeout=20)
        if r.status_code == 200:
            text = r.text.strip()
            if _is_valid_response(text):
                logger.info("Caption via Pollinations")
                return text
    except Exception as e:
        logger.error(f"Pollinations error: {e}")
    return None

# ==================== MAIN ====================
def generate_caption(tags, rating, likes, **kwargs):
    if not tags:
        return ""

    prompt = _build_prompt(tags)

    text = _try_groq(prompt) or _try_pollinations(prompt)

    if not text:
        text = "Слишком тихо... и это настораживает 😏"

    text = trim_text(text)
    text = add_noise(text)
    text = maybe_add_engagement(text)

    safe_tags = _safe_tags(tags)
    if not safe_tags:
        safe_tags = tags[:5]

    hashtags = " ".join(f"#{t}" for t in safe_tags[:8])

    footer = "📢 @eroslabai\n💬 Предложка: @Haillord"

    return f"{text}\n\n{hashtags}\n\n{footer}"

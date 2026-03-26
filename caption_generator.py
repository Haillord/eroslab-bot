"""
Генератор описаний через Pollinations.ai (AI, без ключа)
"""

import requests
import logging
import random
import urllib.parse

logger = logging.getLogger(__name__)

# Теги, которые триггерят отказ у Pollinations — скрываем из промпта
NSFW_TRIGGER_TAGS = {
    "slut", "sex", "nude", "naked", "penis", "vagina", "cock",
    "pussy", "cum", "anal", "blowjob", "nsfw", "explicit", "porn",
    "hentai", "xxx", "nipple", "nipples", "breast", "breasts", "ass",
    "bondage", "bdsm", "fetish", "gangbang", "creampie", "ahegao",
    "spread_legs", "pussy_juice", "uncensored", "censored", "genitals"
}

# Шаблоны промптов — чередуем для разнообразия
PROMPT_TEMPLATES = [
    (
        "Ты автор горячего телеграм-канала. Напиши одно короткое соблазнительное "
        "предложение на русском языке для поста с аниме-артом. "
        "Не описывай внешность буквально. Передай настроение, желание, атмосферу. "
        "Вдохновение: {tags}. Добавь 1-2 эмодзи. Только текст, без кавычек."
    ),
    (
        "Придумай одну короткую дерзкую подпись на русском для аниме-поста в телеграме. "
        "Стиль: игривый, соблазнительный, с характером. "
        "Атмосфера: {tags}. Добавь эмодзи. Только текст ответа."
    ),
    (
        "Напиши одно предложение на русском — короткое, чувственное, с интригой. "
        "Как будто описываешь момент, от которого перехватывает дыхание. "
        "Настроение задают слова: {tags}. Добавь эмодзи. Без кавычек."
    ),
]

def generate_caption(tags, rating, likes):
    """Генерирует описание через Pollinations.ai"""

    if not tags:
        return fallback_caption(tags, rating, likes)

    # Фильтруем теги для промпта — AI их не увидит, но в пост они пойдут
    safe_tags = [t for t in tags if t.lower() not in NSFW_TRIGGER_TAGS]

    if not safe_tags:
        logger.info("No safe tags for AI, using fallback")
        return fallback_caption(tags, rating, likes)

    tags_str = ", ".join(safe_tags[:8])
    template = random.choice(PROMPT_TEMPLATES)
    prompt = template.format(tags=tags_str)

    # Метод 1: GET-запрос
    try:
        encoded = urllib.parse.quote(prompt)
        response = requests.get(
            f"https://text.pollinations.ai/{encoded}",
            timeout=30
        )

        if response.status_code == 200:
            ai_text = response.text.strip()

            if _is_valid_response(ai_text):
                if len(ai_text) > 250:
                    ai_text = ai_text[:250] + "..."
                logger.info("AI caption generated successfully (GET)")
                return _format_caption(ai_text, tags, rating, likes)
            else:
                logger.warning(f"AI refused: {ai_text[:80]}")

    except requests.exceptions.Timeout:
        logger.warning("GET timeout, trying POST...")
    except Exception as e:
        logger.warning(f"GET failed: {e}, trying POST...")

    # Метод 2: POST
    try:
        response = requests.post(
            "https://text.pollinations.ai/",
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "openai",
                "private": True
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            ai_text = response.text.strip()

            if _is_valid_response(ai_text):
                if len(ai_text) > 250:
                    ai_text = ai_text[:250] + "..."
                logger.info("AI caption generated successfully (POST)")
                return _format_caption(ai_text, tags, rating, likes)
            else:
                logger.warning(f"AI refused: {ai_text[:80]}")

    except requests.exceptions.Timeout:
        logger.warning("POST timeout, using fallback")
    except Exception as e:
        logger.error(f"POST failed: {e}")

    return fallback_caption(tags, rating, likes)


def _is_valid_response(text):
    """Проверяет что AI не отказал и вернул нормальный текст"""
    bad_phrases = ["I'm sorry", "I can't", "I cannot", "<!DOCTYPE", "<html"]
    return (
        text
        and len(text) > 5
        and not any(p in text for p in bad_phrases)
    )


def _format_caption(ai_text, tags, rating, likes):
    hashtags = " ".join(f"#{t}" for t in tags[:8])
    return (
        f"{ai_text}\n\n"
        f"{hashtags}\n\n"
        f"📢 @eroslabai"
    )

def fallback_caption(tags, rating, likes):
    tags_line = " ".join(f"#{t}" for t in tags[:8]) if tags else ""

    phrases = [
        "🔥 Горячий кадр для твоей ленты",
        "💖 Нежный образ с оттенком игривости",
        "🍑 Образ, который заставляет улыбнуться",
        "✨ Эстетика и соблазн в одном кадре",
        "💋 Когда искусство встречается с откровенностью",
        "🌟 Настроение поднимает этот пост",
        "🎀 Соблазнительный образ для настоящих ценителей",
        "🖤 Тот самый контент, ради которого ты здесь",
        "🌸 Откровенно и красиво — как ты любишь",
    ]

    return (
        f"{random.choice(phrases)}\n\n"
        f"{tags_line}\n\n"
        f"📢 @eroslabai"
    )
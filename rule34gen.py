import os
import random
import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger("ErosLab.Rule34Gen")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Referer": "https://rule34gen.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

# Основные теги для AI видео Rule34
DEFAULT_QUERIES = [
    "ai_generated", "ai_video", "animated", "3d", "rule34",
    "futa", "realistic", "hentai", "monster", "celebrity"
]

def fetch_rule34gen(
    query: str = None,
    limit: int = 60,
    page: int = 0,
    sort: str = "newest"   # newest, popular, top-rated, most-viewed
) -> List[Dict[str, Any]]:
    """
    Получает видео с rule34gen.com
    Возвращает список в формате, совместимом с rule34_api.py и civitai_bot.py
    """

    if query is None or not query.strip():
        query = random.choice(DEFAULT_QUERIES)

    logger.info(f"Rule34Gen → query='{query}', page={page}, limit={limit}, sort={sort}")

    # Попытка 1: Через внутренний API (самый предпочтительный)
    try:
        # Наиболее вероятные эндпоинты (на основе scrapers 2025-2026)
        possible_urls = [
            "https://rule34gen.com/api/search",
            "https://rule34gen.com/api/v1/search",
            "https://rule34gen.com/api/videos",
        ]

        params = {
            "q": query,
            "page": page,
            "limit": min(limit, 100),
            "sort": sort,           # newest / popular / top-rated / most-viewed
            "type": "video"
        }

        for base_url in possible_urls:
            r = requests.get(base_url, params=params, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                break
        else:
            raise Exception("All API endpoints failed")

        r.raise_for_status()
        data = r.json()

        # Возможные ключи с видео (разные версии сайта)
        videos = (
            data.get("videos") or
            data.get("results") or
            data.get("data") or
            data.get("items") or
            (data if isinstance(data, list) else [])
        )

        results: List[Dict[str, Any]] = []
        for v in videos[:limit]:
            if not isinstance(v, dict):
                continue

            vid_id = str(v.get("id") or v.get("video_id") or v.get("_id") or "")
            if not vid_id:
                continue

            file_url = v.get("video_url") or v.get("url") or v.get("file_url") or v.get("download_url")
            if not file_url or not str(file_url).startswith("http"):
                continue

            # Теги
            raw_tags = v.get("tags", [])
            if isinstance(raw_tags, str):
                tags = [t.strip() for t in raw_tags.split() if t.strip()]
            elif isinstance(raw_tags, list):
                tags = [str(t).strip() for t in raw_tags if str(t).strip()]
            else:
                tags = []

            results.append({
                "id":       f"r34gen_{vid_id}",
                "url":      str(file_url),
                "title":    v.get("title") or v.get("name") or "",
                "tags":     tags[:15],
                "likes":    int(v.get("views", 0) or v.get("score", 0) or v.get("likes", 0) or 0),
                "rating":   "XXX",
                "post_id":  vid_id,
                "source":   "rule34gen",
                "thumbnail": v.get("thumb") or v.get("preview") or v.get("thumbnail") or ""
            })

        logger.info(f"Rule34Gen: успешно получено {len(results)} видео (через API)")
        if results:
            return results

    except Exception as e:
        logger.warning(f"Rule34Gen API attempt failed: {e}")

    # Попытка 2: Fallback — можно расширить позже через yt-dlp или парсинг страниц
    logger.info("Rule34Gen: API не сработал, возвращаем пустой список")
    return []
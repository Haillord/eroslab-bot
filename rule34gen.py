import random
import logging
from typing import List, Dict, Any
import yt_dlp

logger = logging.getLogger("ErosLab.Rule34Gen")

# Популярные теги для AI видео Rule34
DEFAULT_QUERIES = [
    "ai_generated", "ai_video", "futa", "rule34", "3d", "animated",
    "monster", "celebrity", "hentai", "realistic"
]

def fetch_rule34gen(
    query: str = None,
    limit: int = 30,           # yt-dlp не любит большие лимиты
    sort: str = "newest"
) -> List[Dict[str, Any]]:
    """
    Получает видео с rule34gen.com через yt-dlp (самый стабильный способ)
    """
    if not query or not query.strip():
        query = random.choice(DEFAULT_QUERIES)

    logger.info(f"Rule34Gen → query='{query}', limit={limit}, sort={sort}")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,      # только метаданные, без скачивания
        'playlistend': limit,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Ищем по тегу на rule34gen.com
            url = f"https://rule34gen.com/search?q={query.replace(' ', '+')}"
            
            info = ydl.extract_info(url, download=False)
            
            entries = info.get('entries', []) if info else []
            
            results = []
            for entry in entries[:limit]:
                if not entry or not entry.get('url'):
                    continue
                    
                video_url = entry.get('url')
                video_id = entry.get('id') or entry.get('webpage_url').split('/')[-1]
                
                # Пытаемся получить прямую ссылку на видео
                try:
                    direct_info = ydl.extract_info(video_url, download=False)
                    direct_url = direct_info.get('url') or video_url
                except:
                    direct_url = video_url

                results.append({
                    "id":       f"r34gen_{video_id}",
                    "url":      direct_url,
                    "title":    entry.get('title', ''),
                    "tags":     [tag.strip() for tag in str(entry.get('description', '')).split() if tag.strip()][:12],
                    "likes":    int(entry.get('view_count', 0) or entry.get('like_count', 0) or 50),
                    "rating":   "XXX",
                    "post_id":  str(video_id),
                    "source":   "rule34gen",
                    "thumbnail": entry.get('thumbnail', '')
                })

            logger.info(f"Rule34Gen: успешно найдено {len(results)} видео через yt-dlp")
            return results

    except Exception as e:
        logger.error(f"Rule34Gen yt-dlp error: {e}")
        return []
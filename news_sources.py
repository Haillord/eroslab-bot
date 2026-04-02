"""
News feed sources for the ErosLab news poster.
Keep this list lightweight and easy to extend.
"""

from __future__ import annotations

import os


DEFAULT_NEWS_RSS_SOURCES = [
    # --- ОСНОВНЫЕ АГРЕГАТОРЫ (Релизы и Апдейты) ---
    "https://f95zone.to/forums/games.2/index.rss",       # Новые игры на F95
    "https://f95zone.to/forums/game-updates.8/index.rss", # Апдейты старых хитов
    "https://www.lewdgamer.com/feed/",                  # Главные новости NSFW-индустрии
    "https://nichegamer.com/tag/nsfw/feed/",            # Только NSFW раздел NicheGamer

    # --- ВИЗУАЛЬНЫЕ НОВЕЛЛЫ (VNs & Eroge) ---
    "https://blog.mangagamer.org/feed/",                # Официальный блог MangaGamer (лицензии/релизы)
    "https://jastusa.com/blog/feed",                    # Новости JAST USA
    "https://vnsnow.com/feed/",                         # Новости и обзоры визуаллок
    "https://vn-meido.com/forum/index.php?type=rss;action=.xml", # Сообщество по переводам и портам
    
    # --- REDDIT (Самое живое по теме модов и игр) ---
    "https://www.reddit.com/r/lewdgames/new/.rss",      # Обсуждение и поиск игр
    "https://www.reddit.com/r/nsfwgaming/new/.rss",     # Скриншоты и новости
    "https://www.reddit.com/r/adultgames/new/.rss",     # Прямо по адресу
    "https://www.reddit.com/r/ItchioNSFW/new/.rss",     # Самое свежее с Itch.io
    "https://www.reddit.com/r/SteamNSFW/new/.rss",      # Что вышло в Стиме без цензуры
    "https://www.reddit.com/r/symphonyoflewd/new/.rss", # Подборки и кураторство
    "https://www.reddit.com/r/HentaiGames/new/.rss",    # Чистый хентай
    "https://www.reddit.com/r/NSFW_Unity_Games/new/.rss", # Проекты на Unity (Patreon-стайл)

    # --- СЕКС-МОДЫ (Sex Mods / Customization) ---
    "https://www.reddit.com/r/sims4cc-nsfw/new/.rss",    # Моды для Симс (огромный пласт контента)
    "https://www.reddit.com/r/SkyrimNSFW/new/.rss",      # Моды на Скайрим (классика)
    "https://www.reddit.com/r/Cyberpunk衣/new/.rss",    # Моды на Киберпанк (если есть в RSS)
    "https://www.loverslab.com/files/rss/1-latest-files.xml", # САМЫЙ ТОП (Новинки с LoversLab)

    # --- ИГРОВЫЕ ПЛАТФОРМЫ (Тегированные) ---
    "https://itch.io/games/tag-adult.rss",
    "https://itch.io/games/tag-nsfw.rss",
    "https://itch.io/games/tag-erotic.rss",
    # --- ДОПОЛНИТЕЛЬНО ---
    "https://www.lewdgamereviews.com/feed/",
    "https://www.loverslab.com/files/rss/1-latest-files.xml", # ГЛАВНЫЙ по модам# Обзоры и аналитика
    "https://www.reddit.com/r/HentaiGames/new/.rss",
    "https://www.reddit.com/r/AdultGameReviews/new/.rss",
    "https://www.reddit.com/r/RenPy/new/.rss",
]


def _build_steam_sources() -> list[str]:
    """
    Builds Steam news RSS feeds from STEAM_APP_IDS env.
    Example: STEAM_APP_IDS="12345,67890"
    """
    raw = os.environ.get("STEAM_APP_IDS", "").strip()
    if not raw:
        return []

    result = []
    for part in raw.split(","):
        appid = part.strip()
        if not appid.isdigit():
            continue
        result.append(f"https://store.steampowered.com/feeds/news/app/{appid}/")
    return result


def get_news_sources() -> list[str]:
    """
    Returns deduplicated source list.
    Extra feeds can be appended with NEWS_RSS_EXTRA (comma-separated).
    """
    extra_raw = os.environ.get("NEWS_RSS_EXTRA", "").strip()
    extra = [x.strip() for x in extra_raw.split(",") if x.strip()]
    merged = _build_steam_sources() + DEFAULT_NEWS_RSS_SOURCES + extra

    seen = set()
    result = []
    for src in merged:
        if src not in seen:
            seen.add(src)
            result.append(src)
    return result

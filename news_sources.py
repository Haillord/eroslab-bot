"""
News feed sources for the ErosLab news poster.
Keep this list lightweight and easy to extend.
"""

from __future__ import annotations

import os


DEFAULT_NEWS_RSS_SOURCES = [
    # Core gaming + PC modding/news (filtered heavily in poster logic).
    "https://www.pcgamer.com/rss/",
    "https://www.rockpapershotgun.com/feed",
    "https://www.dsogaming.com/feed/",
    "https://www.pcgamesn.com/feed",
    "https://www.vg247.com/feed/",
    "https://www.gematsu.com/feed",
    "https://www.destructoid.com/feed/",
    "https://www.dualshockers.com/feed/",
    "https://www.nichegamer.com/feed/",
    "https://www.polygon.com/rss/index.xml",
    "https://kotaku.com/rss",
    # AI space (for "нейронки / tools / releases" bits).
    "https://www.marktechpost.com/feed/",
    "https://the-decoder.com/feed/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    # More niche / community-oriented sources for adult-game chatter.
    "https://www.reddit.com/r/lewdgames/new/.rss",
    "https://www.reddit.com/r/nsfwgaming/new/.rss",
    "https://www.reddit.com/r/visualnovels/new/.rss",
    "https://www.reddit.com/r/itchio/new/.rss",
    "https://www.reddit.com/r/Steam/new/.rss",
    # Communities that sometimes post adult VN/mod updates.
    "https://www.reddit.com/r/adultgames/new/.rss",
    "https://www.reddit.com/r/gamemods/new/.rss",
    # Itch adult tags (often contains VN/sim project updates).
    "https://itch.io/games/tag-adult.rss",
    "https://itch.io/games/tag-visual-novel.rss",
    "https://itch.io/games/tag-erotic.rss",
    "https://itch.io/games/tag-nsfw.rss",
    # Additional candidate feeds (some may be sparse, parser handles that).
    "https://f95zone.to/forums/games.2/index.rss",
    "https://f95zone.to/forums/game-updates.8/index.rss",
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

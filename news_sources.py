"""
News feed sources for the ErosLab news poster.
Keep this list lightweight and easy to extend.
"""

from __future__ import annotations

import os


DEFAULT_NEWS_RSS_SOURCES = [
    # General gaming + PC modding/news (filtered heavily in poster logic).
    "https://www.pcgamer.com/rss/",
    "https://www.rockpapershotgun.com/feed",
    "https://www.dsogaming.com/feed/",
    # AI space (for "нейронки / tools / releases" bits).
    "https://www.marktechpost.com/feed/",
    # More niche / community-oriented sources for adult-game chatter.
    "https://www.reddit.com/r/lewdgames/new/.rss",
    "https://www.reddit.com/r/nsfwgaming/new/.rss",
    # Itch adult tags (often contains VN/sim project updates).
    "https://itch.io/games/tag-adult.rss",
    "https://itch.io/games/tag-visual-novel.rss",
]


def get_news_sources() -> list[str]:
    """
    Returns deduplicated source list.
    Extra feeds can be appended with NEWS_RSS_EXTRA (comma-separated).
    """
    extra_raw = os.environ.get("NEWS_RSS_EXTRA", "").strip()
    extra = [x.strip() for x in extra_raw.split(",") if x.strip()]
    merged = DEFAULT_NEWS_RSS_SOURCES + extra

    seen = set()
    result = []
    for src in merged:
        if src not in seen:
            seen.add(src)
            result.append(src)
    return result

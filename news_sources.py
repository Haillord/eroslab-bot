"""
News feed sources for the ErosLab news poster.
Keep this list lightweight and easy to extend.
"""

from __future__ import annotations

import os


DEFAULT_NEWS_RSS_SOURCES = [
    # General gaming + PC modding/news (we filter by keywords later).
    "https://www.pcgamer.com/rss/",
    "https://www.rockpapershotgun.com/feed",
    "https://www.dsogaming.com/feed/",
    # AI space (for "нейронки / tools / releases" bits).
    "https://www.marktechpost.com/feed/",
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


import re
from typing import Any


def normalize_tag(tag: str) -> str:
    return str(tag).strip().lower().replace(" ", "_").replace("-", "_")


def clean_tags(tags, hashtag_stop_words: set[str]):
    clean = []
    seen = set()
    for t in tags:
        t = re.sub(r"[^\w]", "", normalize_tag(t))
        if re.search(r"\d+$", t):
            continue
        if t and t not in hashtag_stop_words and t not in seen and 3 <= len(t) <= 30:
            clean.append(t)
            seen.add(t)
    return clean


def extract_tags_from_item(
    item: dict[str, Any],
    hashtag_stop_words: set[str],
    logger=None,
    debug_logs: bool = False,
):
    raw_tags = []

    civitai_tags = item.get("tags", [])
    if civitai_tags:
        for t in civitai_tags:
            name = t.get("name", "") if isinstance(t, dict) else str(t)
            if name:
                raw_tags.append(name)
        if logger and debug_logs:
            logger.debug(f"CivitAI tags found: {len(raw_tags)}")

    if not raw_tags:
        prompt = item.get("meta", {}).get("prompt", "") if item.get("meta") else ""
        if prompt:
            tokens = re.split(r"[,\(\)\[\]|<>]+", prompt)
            for token in tokens:
                token = token.strip()
                if token:
                    raw_tags.append(token)
            if logger and debug_logs:
                logger.debug(f"Parsed {len(raw_tags)} tokens from meta.prompt")
        else:
            if logger and debug_logs:
                logger.debug("No tags and no prompt available")

    return clean_tags(raw_tags, hashtag_stop_words)


def to_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def extract_civitai_likes(item: dict[str, Any]):
    stats = item.get("stats") or {}
    stats_total = 0
    if isinstance(stats, dict):
        for key, value in stats.items():
            key_lower = str(key).lower()
            if "count" in key_lower:
                stats_total += to_int(value, 0)

    candidates = [
        stats.get("likeCount"),
        stats.get("heartCount"),
        stats.get("reactionCount"),
        stats.get("favoriteCount"),
        stats_total,
        item.get("likeCount"),
        item.get("heartCount"),
        item.get("reactionCount"),
    ]
    numeric = [to_int(v, 0) for v in candidates]
    return max(numeric) if numeric else 0

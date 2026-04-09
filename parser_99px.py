"""
Парсер обоев с 99px.ru для ErosLab Wallpapers Bot
Возвращает items в том же формате что fetch_wallhaven
"""

import logging
import re
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE = "https://wallpapers.99px.ru"

NSFW_KEYWORDS = {"обнаженн"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": BASE,
}


def _parse_page(url: str) -> list[dict]:
    """Парсит одну страницу листинга и возвращает список items."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"99px fetch error {url}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    items = []

    for link in soup.select("a[href*='/wallpapers/']"):
        href = link.get("href", "")

        if not re.search(r"/wallpapers/\d+", href):
            continue

        m = re.search(r"/wallpapers/(\d+)", href)
        if not m:
            continue
        item_id_num = m.group(1)
        item_id = f"99px_{item_id_num}"

        img = link.find("img")
        title = ""
        if img:
            title = img.get("alt", "").strip() or img.get("title", "").strip()

        # Чистим "Обои на рабочий стол " из начала alt
        title = re.sub(r"^обои на рабочий стол\s*", "", title, flags=re.IGNORECASE).strip()

        # Фильтр NSFW по названию
        if any(kw in title.lower() for kw in NSFW_KEYWORDS):
            continue

        tags = [t for t in re.split(r"[\s,]+", title.lower()) if len(t) > 2] if title else []

        items.append({
            "id":        item_id,
            "url":       f"{BASE}/wallpapers/download/{item_id_num}/",
            "page_url":  href if href.startswith("http") else BASE + href,
            "tags":      tags[:10],
            "likes":     0,
            "rating":    "safe",
            "mime":      "image/jpeg",
            "createdAt": None,
            "source":    "99px",
        })

    logger.info(f"99px parsed {len(items)} items from {url}")
    return items


def fetch_99px(max_pages: int = 5) -> list[dict]:
    """
    Основная функция — совместима с fetch_wallhaven.
    Возвращает список items готовых к публикации.
    """
    all_items = []

    for base_url in [f"{BASE}/new/", f"{BASE}/best/"]:
        for page in range(1, max_pages + 1):
            url = base_url if page == 1 else f"{base_url}?page={page}"
            page_items = _parse_page(url)
            if not page_items:
                break
            all_items.extend(page_items)

    # Убираем дубли по id
    seen = set()
    unique = []
    for item in all_items:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    logger.info(f"99px total unique items: {len(unique)}")
    return unique
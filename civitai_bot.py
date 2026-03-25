"""
ErosLab Bot — GitHub Actions Edition
Запускается один раз, постит одно фото/видео и завершается.
Расписание управляется через GitHub Actions cron.
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import re
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import telegram
from telegram import Bot

# ╔══════════════════════════════════════════════════════╗
# ║   НАСТРОЙКИ — берутся из переменных окружения       ║
# ║   (GitHub Actions Secrets)                          ║
# ╚══════════════════════════════════════════════════════╝

TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN",  "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@eroslabai")
ADMIN_USER_ID       = int(os.environ.get("ADMIN_USER_ID",   "0"))
CIVITAI_API_KEY     = os.environ.get("CIVITAI_API_KEY",     "")
WATERMARK_TEXT      = "@eroslabai"

MIN_LIKES   = 30
MIN_WIDTH   = 512
MIN_HEIGHT  = 512
FETCH_LIMIT = 100

HISTORY_FILE = "posted_ids.json"
HASHES_FILE  = "posted_hashes.json"
STATS_FILE   = "stats.json"

BLACKLIST_TAGS = {
    "gore", "guro", "scat", "vore", "snuff", "necrophilia",
    "bestiality", "zoo", "loli", "shota", "child", "minor",
    "underage", "infant", "toddler",
}

HASHTAG_STOP_WORDS = {
    "score", "source", "rating", "version", "step", "steps", "cfg", "seed",
    "sampler", "model", "lora", "vae", "clip", "unet", "fp16", "safetensors",
    "checkpoint", "embedding", "none", "null", "true", "false", "and", "the",
    "for", "with", "masterpiece", "best", "quality", "high", "ultra", "detail",
    "detailed", "8k", "4k", "hd", "resolution", "simple", "background",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ╔══════════════════════════════════════════════════════╗
# ║                 ХРАНЕНИЕ ДАННЫХ                     ║
# ╚══════════════════════════════════════════════════════╝

def load_json(path, default):
    if Path(path).exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

posted_ids    = set(load_json(HISTORY_FILE, []))
posted_hashes = set(load_json(HASHES_FILE,  []))
stats         = load_json(STATS_FILE, {"total_posts": 0, "sources": {}, "top_tags": {}})

def save_all():
    save_json(HISTORY_FILE, list(posted_ids))
    save_json(HASHES_FILE,  list(posted_hashes))
    save_json(STATS_FILE,   stats)

# ╔══════════════════════════════════════════════════════╗
# ║              ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ                ║
# ╚══════════════════════════════════════════════════════╝

def clean_tags(tags):
    clean, seen = [], set()
    for t in tags:
        t = re.sub(r"[^\w]", "", t.strip().lower().replace(" ", "_").replace("-", "_"))
        if t and t not in HASHTAG_STOP_WORDS and t not in seen and 3 <= len(t) <= 30:
            clean.append(t)
            seen.add(t)
    return clean

def has_blacklisted(tags):
    return bool(set(t.lower() for t in tags) & BLACKLIST_TAGS)

def download(url):
    try:
        r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.content
    except Exception as e:
        logger.error(f"Скачивание: {e}")
        return None

def is_duplicate(data):
    h = hashlib.md5(data).hexdigest()
    if h in posted_hashes:
        return True
    posted_hashes.add(h)
    return False

def check_resolution(data):
    try:
        img = Image.open(BytesIO(data))
        w, h = img.size
        return w >= MIN_WIDTH and h >= MIN_HEIGHT
    except Exception:
        return True

def add_watermark(data, text):
    try:
        img = Image.open(BytesIO(data)).convert("RGBA")
        w, h = img.size
        layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw  = ImageDraw.Draw(layer)
        fsize = max(24, int(w * 0.045))
        font  = None
        for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                   "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
            try:
                font = ImageFont.truetype(fp, fsize)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x, y = w-tw-24, h-th-24
        draw.text((x+2, y+2), text, font=font, fill=(0,0,0,160))
        draw.text((x,   y),   text, font=font, fill=(255,255,255,230))
        out = BytesIO()
        Image.alpha_composite(img, layer).convert("RGB").save(out, format="JPEG", quality=92)
        return out.getvalue()
    except Exception as e:
        logger.error(f"Watermark: {e}")
        return data

def build_caption(item):
    tags  = item["tags"]
    likes = item["likes"]
    src   = item["source"]
    htags = " ".join(f"#{t}" for t in tags) if tags else "#nsfw #ai #art"
    return f"{htags}\n\n❤️ {likes} реакций • {src}\n📢 {WATERMARK_TEXT}"

# ╔══════════════════════════════════════════════════════╗
# ║                   ИСТОЧНИКИ                         ║
# ╚══════════════════════════════════════════════════════╝

def fetch_civitai():
    params = {
        "limit": FETCH_LIMIT, "nsfw": "X",
        "sort":   random.choice(["Most Reactions", "Most Comments", "Newest"]),
        "period": random.choice(["Day", "Week", "Month"]),
    }
    try:
        r = requests.get("https://civitai.com/api/v1/images", params=params,
                         headers={"Authorization": f"Bearer {CIVITAI_API_KEY}"}, timeout=15)
        r.raise_for_status()
        result = []
        for item in r.json().get("items", []):
            likes = item.get("stats", {}).get("likeCount", 0) + item.get("stats", {}).get("heartCount", 0)
            if likes < MIN_LIKES:
                continue
            tags = clean_tags(_civitai_tags(item))
            if has_blacklisted(tags):
                continue
            result.append({"id": f"civitai_{item['id']}", "url": item.get("url",""),
                           "tags": tags[:12], "likes": likes, "source": "CivitAI"})
        logger.info(f"CivitAI: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"CivitAI: {e}")
        return []

def _civitai_tags(item):
    raw = item.get("tags", [])
    if raw:
        return [t.get("name","") if isinstance(t, dict) else str(t) for t in raw]
    prompt = (item.get("meta") or {}).get("prompt", "")
    if prompt:
        parts = re.split(r"[,|]", prompt)
        return [re.sub(r"[<>(){}\[\]\\/*\d]+","",p).strip().lower().replace(" ","_") for p in parts[:20]]
    return []

def fetch_rule34():
    try:
        r = requests.get("https://api.rule34.xxx/index.php", timeout=15, params={
            "page":"dapi","s":"post","q":"index","limit":FETCH_LIMIT,
            "tags":"ai_generated score:>10","json":1})
        r.raise_for_status()
        result = []
        for item in (r.json() or []):
            tags = clean_tags(item.get("tags","").split())
            if has_blacklisted(tags):
                continue
            result.append({"id": f"rule34_{item['id']}", "url": item.get("file_url",""),
                           "tags": tags[:12], "likes": item.get("score",0), "source": "Rule34"})
        result.sort(key=lambda x: x["likes"], reverse=True)
        logger.info(f"Rule34: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Rule34: {e}")
        return []

def fetch_danbooru():
    try:
        r = requests.get("https://danbooru.donmai.us/posts.json", timeout=15, params={
            "tags":"rating:explicit ai-generated order:score",
            "limit":FETCH_LIMIT, "page": random.randint(1,5)})
        r.raise_for_status()
        result = []
        for item in (r.json() or []):
            if item.get("is_banned") or item.get("is_deleted"):
                continue
            url = item.get("file_url") or item.get("large_file_url","")
            if not url:
                continue
            tags = clean_tags((item.get("tag_string_general","") + " " + item.get("tag_string_character","")).split())
            if has_blacklisted(tags):
                continue
            result.append({"id": f"danbooru_{item['id']}", "url": url,
                           "tags": tags[:12],
                           "likes": item.get("score",0) + item.get("fav_count",0),
                           "source": "Danbooru"})
        result.sort(key=lambda x: x["likes"], reverse=True)
        logger.info(f"Danbooru: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Danbooru: {e}")
        return []

def fetch_gelbooru():
    try:
        r = requests.get("https://gelbooru.com/index.php", timeout=15, params={
            "page":"dapi","s":"post","q":"index","json":1,
            "tags":"ai-generated rating:explicit sort:score",
            "limit":FETCH_LIMIT, "pid": random.randint(0,10)})
        r.raise_for_status()
        data  = r.json()
        items = data.get("post",[]) if isinstance(data, dict) else (data or [])
        result = []
        for item in items:
            tags = clean_tags(item.get("tags","").split())
            if has_blacklisted(tags):
                continue
            result.append({"id": f"gelbooru_{item['id']}", "url": item.get("file_url",""),
                           "tags": tags[:12], "likes": item.get("score",0), "source": "Gelbooru"})
        result.sort(key=lambda x: x["likes"], reverse=True)
        logger.info(f"Gelbooru: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Gelbooru: {e}")
        return []

SOURCES = [fetch_civitai, fetch_rule34, fetch_danbooru, fetch_gelbooru]

def fetch_and_pick():
    random.shuffle(SOURCES)
    for fetcher in SOURCES:
        items = fetcher()
        fresh = [i for i in items if i["id"] not in posted_ids]
        if fresh:
            fresh.sort(key=lambda x: x["likes"], reverse=True)
            return fresh[0]
    return None

# ╔══════════════════════════════════════════════════════╗
# ║                     MAIN                            ║
# ╚══════════════════════════════════════════════════════╝

async def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не задан!")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    me  = await bot.get_me()
    logger.info(f"Бот: @{me.username} → {TELEGRAM_CHANNEL_ID}")

    item = fetch_and_pick()
    if not item:
        logger.error("Не найдено подходящего медиа ни в одном источнике")
        return

    url  = item["url"]
    data = download(url)
    if not data:
        return

    if is_duplicate(data):
        logger.warning("Дубликат по хэшу, пропускаем")
        save_all()
        return

    is_video = any(url.endswith(e) for e in (".mp4", ".webm", ".gif"))
    if not is_video and not check_resolution(data):
        logger.warning("Маленькое разрешение, пропускаем")
        return

    caption = build_caption(item)

    try:
        if is_video:
            await bot.send_video(chat_id=TELEGRAM_CHANNEL_ID, video=BytesIO(data),
                                 caption=caption, supports_streaming=True)
        else:
            await bot.send_photo(chat_id=TELEGRAM_CHANNEL_ID,
                                 photo=BytesIO(add_watermark(data, WATERMARK_TEXT)),
                                 caption=caption)

        posted_ids.add(item["id"])
        stats["total_posts"] = stats.get("total_posts", 0) + 1
        stats["sources"][item["source"]] = stats["sources"].get(item["source"], 0) + 1
        for tag in item["tags"]:
            stats["top_tags"][tag] = stats["top_tags"].get(tag, 0) + 1
        save_all()

        kind = "🎬 видео" if is_video else "🖼 фото"
        logger.info(f"✅ {kind} [{item['source']}] ❤️{item['likes']}")

    except telegram.error.TelegramError as e:
        logger.error(f"Telegram: {e}")


if __name__ == "__main__":
    asyncio.run(main())

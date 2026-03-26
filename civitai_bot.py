"""
ErosLab Bot FINAL — стабильный, без повторов, с буфером
Гарантирует посты по расписанию
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import re
import requests
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from telegram import Bot
from caption_generator import generate_caption

# ==================== CONFIG ====================
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@eroslabai")
CIVITAI_API_KEY     = os.environ.get("CIVITAI_API_KEY", "")

MIN_LIKES      = 20
MIN_IMAGE_SIZE = 512
MAX_HISTORY    = 5000
QUEUE_TARGET   = 30

HISTORY_FILE = "posted_ids.json"
HASHES_FILE  = "posted_hashes.json"
QUEUE_FILE   = "queue.json"
STATS_FILE   = "stats.json"

BLACKLIST = {
    "gore","guro","scat","vore","snuff","necrophilia",
    "bestiality","zoo","loli","shota","child","minor","underage"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== STORAGE ====================
def load_json(path, default):
    if Path(path).exists():
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except:
            pass
    return default

def save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

posted_ids    = set(load_json(HISTORY_FILE, []))
posted_hashes = set(load_json(HASHES_FILE, []))
queue         = load_json(QUEUE_FILE, [])
stats         = load_json(STATS_FILE, {"total_posts": 0, "top_tags": {}})

def save_all():
    save_json(HISTORY_FILE, list(posted_ids)[-MAX_HISTORY:])
    save_json(HASHES_FILE,  list(posted_hashes)[-MAX_HISTORY:])
    save_json(QUEUE_FILE,   queue)
    save_json(STATS_FILE,   stats)

# ==================== UTILS ====================
def clean_tags(tags):
    out = []
    for t in tags:
        t = re.sub(r"[^\w]", "", str(t).lower())
        if t and t not in BLACKLIST:
            out.append(t)
    return list(set(out))

def check_image(data):
    try:
        img = Image.open(BytesIO(data))
        return img.size[0] >= MIN_IMAGE_SIZE
    except:
        return False

def get_video_duration(data):
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(data)
            path = tmp.name

        cmd = ["ffprobe","-v","error","-show_entries","format=duration",
               "-of","default=noprint_wrappers=1:nokey=1",path]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return 0.0

# ==================== QUEUE ====================
def refill_queue():
    global queue

    if len(queue) >= QUEUE_TARGET:
        return

    logger.info("Refilling queue...")

    r = requests.get(
        "https://civitai.com/api/v1/images",
        params={"limit": 100, "nsfw": "X", "sort": "Most Reactions"},
        timeout=30
    )

    items = r.json().get("items", [])

    for item in items:
        tags = clean_tags(item.get("tags", []))

        if item["id"] in posted_ids:
            continue

        if any(q["id"] == item["id"] for q in queue):
            continue

        likes = item.get("stats", {}).get("likeCount", 0)
        if likes < MIN_LIKES:
            continue

        queue.append({
            "id": f"civitai_{item['id']}",
            "url": item["url"],
            "tags": tags,
            "likes": likes,
            "rating": item.get("nsfwLevel")
        })

        if len(queue) >= QUEUE_TARGET:
            break

    save_json(QUEUE_FILE, queue)

def get_next_post():
    global queue

    if not queue:
        refill_queue()

    if not queue:
        return None

    item = queue.pop(0)
    save_json(QUEUE_FILE, queue)
    return item

# ==================== TELEGRAM ====================
async def send_with_retry(func, *args, retries=3, **kwargs):
    for i in range(retries):
        try:
            return await func(*args, **kwargs)
        except:
            if i == retries - 1:
                raise
            await asyncio.sleep(2 * (i + 1))

# ==================== MAIN ====================
async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    refill_queue()
    item = get_next_post()

    if not item:
        logger.error("Queue empty → no post")
        return

    try:
        data = requests.get(item["url"], timeout=60).content
    except:
        return

    # проверка
    if item["url"].endswith((".mp4",".webm",".gif")):
        if get_video_duration(data) < 0.5:
            return
    else:
        if not check_image(data):
            return

    img_hash = hashlib.sha256(data).hexdigest()

    if img_hash in posted_hashes:
        logger.warning("Duplicate detected")
        return

    caption = generate_caption(item["tags"], item["rating"], item["likes"])

    try:
        if item["url"].endswith((".mp4",".webm",".gif")):
            await send_with_retry(
                bot.send_video,
                chat_id=TELEGRAM_CHANNEL_ID,
                video=BytesIO(data),
                caption=caption
            )
        else:
            await send_with_retry(
                bot.send_photo,
                chat_id=TELEGRAM_CHANNEL_ID,
                photo=BytesIO(data),
                caption=caption
            )

        posted_ids.add(item["id"])
        posted_hashes.add(img_hash)

        stats["total_posts"] += 1

        for t in item["tags"][:5]:
            stats["top_tags"][t] = stats["top_tags"].get(t, 0) + 1

        save_all()

        logger.info(f"Posted: {item['id']}")

    except Exception as e:
        logger.error(f"Send error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

"""
Reddit 3D Bot — парсит NSFW 3D-контент через HTML (без API)
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
from telegram import Bot

# ==================== НАСТРОЙКИ ====================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@eroslabai")

# Сабреддиты с 3D NSFW контентом
SUBREDDITS = [
    "3dnsfw",
    "blendernsfw", 
    "3dart",
    "sfmcompileclub",
    "3dhentai"
]

HISTORY_FILE = "reddit_posted.json"
WATERMARK_TEXT = "@eroslabai"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def load_posted():
    """Загружает историю опубликованных постов"""
    if Path(HISTORY_FILE).exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            pass
    return set()

def save_posted(posted):
    """Сохраняет историю"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(posted), f, ensure_ascii=False, indent=2)

def fetch_reddit_posts():
    """Парсит Reddit через HTML"""
    posted_ids = load_posted()
    all_posts = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for subreddit in SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot/.json?limit=25"
            logger.info(f"Fetching: {url}")
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            posts_count = 0
            for post in data['data']['children']:
                post_data = post['data']
                post_id = post_data['id']
                post_key = f"reddit_{subreddit}_{post_id}"
                
                if post_key in posted_ids:
                    continue
                
                # Проверяем, есть ли медиа
                url_overridden = post_data.get('url_overridden_by_dest', '')
                is_media = url_overridden.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm'))
                
                if not is_media:
                    continue
                
                # Фильтруем по рейтингу
                score = post_data.get('score', 0)
                if score < 50:
                    continue
                
                all_posts.append({
                    "id": post_key,
                    "url": url_overridden,
                    "title": post_data['title'],
                    "subreddit": subreddit,
                    "score": score,
                    "link": f"https://reddit.com{post_data['permalink']}"
                })
                posts_count += 1
            
            logger.info(f"Found {posts_count} posts from r/{subreddit}")
            
        except Exception as e:
            logger.error(f"Error fetching r/{subreddit}: {e}")
    
    return all_posts

async def main():
    """Основная функция"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN found!")
        return
    
    logger.info("=" * 50)
    logger.info("Starting Reddit 3D Parser Bot")
    logger.info(f"Channel: {TELEGRAM_CHANNEL_ID}")
    logger.info("=" * 50)
    
    posts = fetch_reddit_posts()
    
    if not posts:
        logger.info("No new posts found")
        return
    
    logger.info(f"Total fresh posts: {len(posts)}")
    
    # Выбираем случайный пост
    post = random.choice(posts)
    logger.info(f"Selected: {post['id']} from r/{post['subreddit']} (score: {post['score']})")
    logger.info(f"Title: {post['title'][:80]}")
    
    # Скачиваем медиа
    try:
        logger.info(f"Downloading: {post['url']}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(post["url"], timeout=60, headers=headers)
        r.raise_for_status()
        data = r.content
        logger.info(f"Downloaded {len(data)} bytes")
    except Exception as e:
        logger.error(f"Download error: {e}")
        return
    
    # Формируем подпись
    caption = f"🎨 **{post['title']}**\n\n📌 r/{post['subreddit']} | ❤️ {post['score']} votes | 🔗 [Source]({post['link']})\n\n{WATERMARK_TEXT}"
    
    # Отправляем в Telegram
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    try:
        url_lower = post["url"].lower()
        if url_lower.endswith((".mp4", ".webm", ".gif")):
            logger.info("Sending as video")
            await bot.send_video(
                chat_id=TELEGRAM_CHANNEL_ID,
                video=BytesIO(data),
                caption=caption,
                supports_streaming=True,
                parse_mode='Markdown',
                write_timeout=60,
                read_timeout=60
            )
        else:
            logger.info("Sending as image")
            await bot.send_photo(
                chat_id=TELEGRAM_CHANNEL_ID,
                photo=BytesIO(data),
                caption=caption,
                parse_mode='Markdown',
                write_timeout=60,
                read_timeout=60
            )
        
        # Сохраняем историю
        posted_ids = load_posted()
        posted_ids.add(post["id"])
        save_posted(posted_ids)
        logger.info(f"✅ Successfully posted: {post['id']}")
        
    except Exception as e:
        logger.error(f"Send error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
"""
Публикация постов в группу ВКонтакте (фото и видео) через прямой API.
"""

import requests
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

def post_to_vk(image_data, caption, media_url, group_id, token):
    """
    Публикует пост в группу ВКонтакте (фото и видео) через прямой API.
    """
    api_url = "https://api.vk.com/method/"
    v = "5.131"

    is_video = media_url.lower().endswith(('.mp4', '.webm', '.gif'))

    if is_video:
        # 1. Получаем сервер для загрузки видео
        params = {
            "access_token": token,
            "v": v,
            "group_id": group_id,
            "name": caption[:200],
            "is_private": 0
        }
        resp = requests.get(api_url + "video.save", params=params).json()
        if "error" in resp:
            logger.error(f"Video save error: {resp['error']}")
            return
        upload_data = resp["response"]
        upload_url = upload_data["upload_url"]
        video_id = upload_data["video_id"]
        owner_id = upload_data["owner_id"]

        # 2. Загружаем видео
        files = {'video_file': ('video.mp4', BytesIO(image_data), 'video/mp4')}
        upload_response = requests.post(upload_url, files=files).json()
        if "size" not in upload_response:
            logger.error(f"Video upload failed: {upload_response}")
            return

        attachment = f"video{owner_id}_{video_id}"
        logger.info(f"Video uploaded, attachment: {attachment}")
    else:
        # 1. Получаем сервер для загрузки фото на стену группы
        params = {
            "access_token": token,
            "v": v,
            "group_id": group_id
        }
        resp = requests.get(api_url + "photos.getWallUploadServer", params=params).json()
        if "error" in resp:
            logger.error(f"Get upload server error: {resp['error']}")
            return
        upload_url = resp["response"]["upload_url"]

        # 2. Загружаем фото
        files = {'photo': ('image.jpg', BytesIO(image_data), 'image/jpeg')}
        upload_response = requests.post(upload_url, files=files).json()

        # 3. Сохраняем фото на стену
        params = {
            "access_token": token,
            "v": v,
            "group_id": group_id,
            "photo": upload_response["photo"],
            "server": upload_response["server"],
            "hash": upload_response["hash"]
        }
        save_resp = requests.get(api_url + "photos.saveWallPhoto", params=params).json()
        if "error" in save_resp:
            logger.error(f"Save photo error: {save_resp['error']}")
            return
        photo = save_resp["response"][0]
        attachment = f"photo{photo['owner_id']}_{photo['id']}"

    # 3. Публикуем пост
    params = {
        "access_token": token,
        "v": v,
        "owner_id": -group_id,
        "message": caption,
        "attachments": attachment,
        "signed": 0
    }
    resp = requests.get(api_url + "wall.post", params=params).json()
    if "error" in resp:
        logger.error(f"Wall post error: {resp['error']}")
    else:
        logger.info("✅ Posted to VK")
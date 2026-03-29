#!/usr/bin/env python3
"""
Модуль для наложения водяных знаков на изображения
"""

import logging
from PIL import Image, ImageDraw, ImageFont
import io

logger = logging.getLogger(__name__)

def add_watermark(image_data: bytes, text: str = "@eroslabai", 
                 opacity: float = 0.3, font_size_ratio: float = 0.04) -> bytes:
    """
    Накладывает водяной знак на изображение
    
    Args:
        image_data: Исходные данные изображения
        text: Текст водяного знака
        opacity: Прозрачность (0.0 - 1.0)
        font_size_ratio: Размер шрифта относительно высоты изображения
    
    Returns:
        bytes: Изображение с водяным знаком
    """
    try:
        # Загружаем изображение
        image = Image.open(io.BytesIO(image_data)).convert("RGBA")
        width, height = image.size
        
        # Создаем прозрачный слой для водяного знака
        watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        # Определяем размер шрифта
        font_size = max(20, int(height * font_size_ratio))
        
        # Пытаемся загрузить шрифт
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Получаем размер текста
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Позиция: нижний правый угол с отступом
        margin = 20
        x = width - text_width - margin
        y = height - text_height - margin
        
        # Цвет текста: белый с прозрачностью
        text_color = (255, 255, 255, int(255 * opacity))
        
        # Рисуем текст
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Накладываем водяной знак
        result = Image.alpha_composite(image, watermark_layer)
        
        # Конвертируем обратно в bytes
        output = io.BytesIO()
        if image.mode in ('RGBA', 'LA') or 'transparency' in image.info:
            result.save(output, format='PNG', optimize=True)
        else:
            result.convert('RGB').save(output, format='JPEG', quality=95, optimize=True)
        
        logger.info(f"Watermark added: {text} (opacity: {opacity*100}%)")
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Watermark error: {e}")
        return image_data  # Возвращаем оригинальное изображение при ошибке

def should_add_watermark(url: str) -> bool:
    """
    Проверяем, нужно ли добавлять водяной знак
    
    Args:
        url: URL изображения
    
    Returns:
        bool: True если нужно добавить водяной знак
    """
    # Добавляем водяной знак только для изображений, не для видео
    video_extensions = (".mp4", ".webm", ".gif")
    return not url.lower().endswith(video_extensions)


if __name__ == "__main__":
    # Тестирование
    import requests
    
    test_url = "https://example.com/test-image.jpg"
    
    try:
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            watermarked = add_watermark(response.content)
            with open("test_watermarked.png", "wb") as f:
                f.write(watermarked)
            print("✅ Watermark test successful")
        else:
            print("❌ Failed to download test image")
    except Exception as e:
        print(f"❌ Test failed: {e}")
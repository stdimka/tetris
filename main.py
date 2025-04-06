from PIL import Image, ImageDraw, ImageFont
import re
from collections import Counter
import os

# Настройки
FONT_PATH = "simsun.ttc"  # Убедитесь, что путь к шрифту корректный
FONT_SIZE = 17
IMAGE_SIZE = (30, 30)
BG_COLOR = (255, 255, 255)  # Белый фон
OUTPUT_DIR = "glyphs"

# Стандартные цвета Tetris
TETRIS_COLORS = [
    (0, 255, 255),   # I - голубой
    (128, 0, 128),   # T - фиолетовый
    (255, 255, 0),   # O - желтый
    (0, 255, 0),     # S - зеленый
    (255, 0, 0),     # Z - красный
    (0, 0, 255),     # L - синий
    (255, 165, 0)    # J - оранжевый
]

# Пример текста
text = """
这是一个简单的例子。我们使用Python来统计汉字出现的频率。
"""

# Извлекаем иероглифы
chars = re.findall(r'[\u4e00-\u9fff]', text)
counter = Counter(chars)

# Создаем папку для сохранения
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Инициализируем шрифт
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

# Генерируем изображения
for idx, (char, count) in enumerate(counter.items()):
    # Выбираем цвет из списка TETRIS_COLORS (по индексу символа)
    text_color = TETRIS_COLORS[idx % len(TETRIS_COLORS)]  # Циклический выбор цвета

    image = Image.new("RGB", IMAGE_SIZE, BG_COLOR)
    draw = ImageDraw.Draw(image)

    # Исправленный блок расчета размера текста
    text_bbox = draw.textbbox((0, 0), char, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    position = (
        (IMAGE_SIZE[0] - text_width) // 2,
        (IMAGE_SIZE[1] - text_height) // 2
    )

    draw.text(position, char, font=font, fill=text_color)
    filename = f"{ord(char):04x}_{char}.png"
    image.save(os.path.join(OUTPUT_DIR, filename))
    print(f"Сохранено: {filename} ({count} раз)")
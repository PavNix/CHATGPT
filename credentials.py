import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Перевірка існування файлу .env
if not os.path.exists(".env"):
    logger.error("Файл .env не знайдено. Перевірте його наявність!")
    raise FileNotFoundError("Файл .env не знайдено. Перевірте його наявність!")

# Завантаження змінних із файлу .env
load_dotenv()
logger.info(".env файл завантажено.")

# Отримання токенів
CHATGPT_TOKEN = os.getenv("CHATGPT_TOKEN", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Перевірка наявності токенів
if not CHATGPT_TOKEN or not BOT_TOKEN:
    logger.error("Необхідно вказати коректні токени у файлі .env")
    raise ValueError("Необхідно вказати коректні токени у файлі .env")
logger.info("Токени завантажено успішно.")

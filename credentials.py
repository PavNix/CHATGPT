import os
from dotenv import load_dotenv

# Перевірка існування файлу .env
if not os.path.exists(".env"):
    raise FileNotFoundError("Файл .env не знайдено. Перевірте його наявність!")

# Завантаження змінних із файлу .env
load_dotenv()

# Отримання токенів
CHATGPT_TOKEN = os.getenv("CHATGPT_TOKEN", "").strip()
ORGANIZATION = os.getenv("ORGANIZATION", "").strip()
PROJECT_ID = os.getenv("PROJECT_ID", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Перевірка наявності токенів
if not CHATGPT_TOKEN or not BOT_TOKEN:
    raise ValueError("Необхідно вказати коректні токени у файлі .env")

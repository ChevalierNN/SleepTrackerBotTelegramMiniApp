import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Mini App — публичный HTTPS URL
WEBAPP_URL: str = os.getenv("WEBAPP_URL", "http://localhost:8085").rstrip("/")

# Локальный сервер для раздачи Mini App
SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8085"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден! Создайте файл .env и укажите BOT_TOKEN=ваш_токен")

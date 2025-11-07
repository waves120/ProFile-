
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "").strip()
    db_url: str = os.getenv("DB_URL", "sqlite+aiosqlite:///./data/bot.db")

settings = Settings()
if not settings.bot_token:
    raise RuntimeError("BOT_TOKEN не задан в .env")

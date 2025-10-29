import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment (.env)")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "video_bot")

# Platforms & modes
PLATFORM_TIKTOK = "tiktok"
PLATFORM_YOUTUBE = "youtube"
MODE_VIDEO = "video"
MODE_AUDIO = "audio"

# Qualities (fallback options if probing fails)
QUALITY_BEST = "best"
QUALITY_LIST_DEFAULT = ["2160p","1440p","1080p","720p","480p","360p","240p","144p"]

# Soft limit for Telegram files (~1.9GB). Telegram hard limit is ~2GB for many clients.
TELEGRAM_SOFT_LIMIT = 1900 * 1024 * 1024

# Concurrency: only a few downloads at a time
GLOBAL_CONCURRENCY = 3

# URL detection
URL_REGEX = r"https?://\S+"

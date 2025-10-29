import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in .env")

# platforms & modes
PLATFORM_TIKTOK = "tiktok"
PLATFORM_YOUTUBE = "youtube"
MODE_VIDEO = "video"
MODE_AUDIO = "audio"

# qualities
QUALITY_BEST = "best"
QUALITY_1080P = "1080p"
QUALITY_720P = "720p"
QUALITY_480P = "480p"
QUALITY_ORDER = [QUALITY_1080P, QUALITY_720P, QUALITY_480P, QUALITY_BEST]

# Увеличенный лимит для больших видео
MAX_BOT_FILE_SIZE = 1800 * 1024 * 1024  # ~1.8GB

URL_REGEX = r"https?://\S+"

GLOBAL_CONCURRENCY = 3

# GIF'ы для уведомлений (рабочие проверенные ссылки)
SUCCESS_GIFS = [
	"https://i.gifer.com/embedded/download/7TyW.gif",
	"https://i.gifer.com/embedded/download/7pld.gif",
	"https://i.gifer.com/embedded/download/7nUZ.gif",
]

WORKING_GIFS = [
	"https://i.gifer.com/embedded/download/ZKZx.gif",
	"https://i.gifer.com/embedded/download/ZXDX.gif",
]

# Файл для отзывов
REVIEWS_FILE = Path("reviews.txt")

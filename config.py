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

# GIF'ы для уведомлений
SUCCESS_GIFS = [
    "https://media.tenor.com/LXf4rKIRbkIAAAAC/success.gif",
    "https://media.tenor.com/eyZk4aVqE0gAAAAC/ok-yes.gif",
    "https://media.tenor.com/6gT7U4wA0U0AAAAC/check-mark.gif",
    "https://media.tenor.com/3O0mZcp8k7wAAAAC/success-celebrate.gif",
    "https://media.tenor.com/0QVtYHfdn0kAAAAC/verified.gif",
    "https://media.tenor.com/6Gd1pIzc1JkAAAAC/done-task.gif",
    "https://media.tenor.com/2q1cQ5Q5Q5QAAAAC/success-rocket.gif",
    "https://media.tenor.com/9Q1Q1Q1Q1Q1AAAAC/approved.gif"
]

WORKING_GIFS = [
    "https://media.tenor.com/1cQw6cZ6p6wAAAAC/loading.gif",
    "https://media.tenor.com/UnFx-k_lSckAAAAC/amalie-steiness.gif",
    "https://media.tenor.com/5oQjX1Q1Q1QAAAAC/loading-waiting.gif",
    "https://media.tenor.com/3Q1Q1Q1Q1Q1AAAAC/spinner.gif",
    "https://media.tenor.com/7Q1Q1Q1Q1Q1AAAAC/processing.gif",
    "https://media.tenor.com/8Q1Q1Q1Q1Q1AAAAC/loading-bar.gif",
    "https://media.tenor.com/4Q1Q1Q1Q1Q1AAAAC/hourglass.gif",
    "https://media.tenor.com/2Q1Q1Q1Q1Q1AAAAC/working.gif"
]

# Файл для отзывов
REVIEWS_FILE = Path("reviews.txt")

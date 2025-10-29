# Telegram Downloader Bot (YouTube + TikTok + Shorts/Reels/VK/X via yt-dlp)

Minimal UX:
- Send a link → choose 🎬 Video or 🎧 Audio → (for video) choose real qualities → get file.
- No reply keyboards, no spam.
- Retry (3x) per backend, then failover to next backend (yt-dlp → pytube → savefrom).
- Size soft-limit check; hint to lower quality or audio if too big for Telegram.

## Local run
```bash
pip install -r requirements.txt
cp .env.example .env  # put your BOT_TOKEN
python bot.py
```

## Render.com deploy
1. New Web Service → connect this repo / upload ZIP → set **Environment** to Python.
2. Build command: `pip install -r requirements.txt`
3. Start command: `python bot.py`
4. Add env var `BOT_TOKEN` with your token.
5. (Optional) Add `LOG_LEVEL=INFO`.
> Polling is used (no public URL required). For webhook deploy, adapt to FastAPI easily.

## Commands
- `/start` — clean start
- `/reset` — clear state
- `/help` — brief help

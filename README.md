## Telegram Video Downloader Bot (TikTok + YouTube)

A Python Telegram bot that downloads videos from TikTok (without watermark when available) and YouTube, with user-selectable quality.

### Features

- TikTok and YouTube downloading via `yt-dlp`
- TikTok: requests no-watermark downloads when available
- Quality selection: Original (best), 1080p, 720p, 480p
- Uses `.env` for bot token

### Requirements

- Python 3.10+
- A Telegram Bot Token from `@BotFather`

### Setup

1. Clone or open this project.
2. Create a `.env` file in the project root:
   ```env
   BOT_TOKEN=123456:ABC-YourTelegramBotToken
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

### Usage

- Start the bot: `/start`
- Choose a platform (TikTok or YouTube)
- Choose quality
- Send the video URL
- Bot returns the video if size allows. If too large for Telegram limits, try a lower quality.

### Notes

- Telegram bots have file size limits. If a selected quality exceeds the limit, the bot will ask to choose a lower quality.
- TikTok no-watermark is attempted using `yt-dlp` extractor arguments and is subject to availability per video.

### License

MIT

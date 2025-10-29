import asyncio, re, logging
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from config import *
from keyboards import mode_kb, quality_kb_from, review_optin_kb
from downloader import BACKENDS, DownloadRequest, list_available_qualities
from db import save_download, save_review

logger = logging.getLogger("bot")
URL_RE = re.compile(URL_REGEX, re.IGNORECASE)
active_tasks = {}
global_semaphore = asyncio.Semaphore(GLOBAL_CONCURRENCY)

class State:
    def __init__(self):
        self.platform = None
        self.mode = None
        self.quality = None
        self.pending_url = None
        self.available_qualities = []
        self.awaiting_review = False
        self.last_action = None

def get_state(context: ContextTypes.DEFAULT_TYPE) -> State:
    st = context.user_data.get("state")
    if not st:
        st = State()
        context.user_data["state"] = st
    return st

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Я помогу скачать медиа с YouTube и TikTok.\n\n"
        "Что умею:\n"
        "• Загрузка видео и аудио с YouTube/TikTok\n\n"
        "Инструкция:\n"
        "Отправьте ссылку на видео, и я помогу вам скачать медиа."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь ссылку на видео — я помогу скачать 📥 (YouTube/TikTok)")

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Сбросил! Отправь новую ссылку 🚀")

async def on_review_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, val: str):
    st = get_state(context)
    if val == "yes":
        st.awaiting_review = True
        await update.callback_query.message.reply_text("Напишите короткий отзыв (3–200 символов) 💙")
    else:
        st.awaiting_review = False
        await update.callback_query.message.reply_text("Окей, в следующий раз 🙂")
    context.user_data["state"] = st

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    st = get_state(context)

    if st.awaiting_review:
        if 3 <= len(text) <= 200 and not text.startswith("/"):
            user_id = update.effective_user.id if update.effective_user else "?"
            action = st.last_action or "unknown"
            save_review({"userId": user_id, "action": action, "text": text})
            p = Path("reviews.txt"); prev = p.read_text(encoding="utf-8") if p.exists() else ""
            prev += f"\n[{datetime.now().isoformat()}] user={user_id} action={action}: {text}"
            p.write_text(prev, encoding="utf-8")
            await update.message.reply_text("Спасибо за отзыв! 💛")
        st.awaiting_review = False
        context.user_data["state"] = st
        return

    if URL_RE.search(text):
        if "youtu" in text:
            st.platform = PLATFORM_YOUTUBE
        elif "tiktok" in text:
            st.platform = PLATFORM_TIKTOK
        else:
            await update.message.reply_text("Пока поддерживаю только YouTube и TikTok 🙏")
            return
        st.pending_url = text
        context.user_data["state"] = st
        await update.message.reply_text("Что хотите скачать? 🎧 Аудио или 📹 Видео?", reply_markup=mode_kb())
        return

    await update.message.reply_text("Отправь ссылку 😌")

async def on_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    st = get_state(context)
    st.mode = mode
    url = st.pending_url
    chat_id = update.effective_chat.id
    if not url:
        await context.bot.send_message(chat_id, "Сначала отправь ссылку 🙂")
        return

    if mode == MODE_AUDIO:
        await context.bot.send_message(chat_id, "🎧 Конвертирую в MP3 (320 kbps)…")
        st.last_action = f"{st.platform}:{mode}:request"
        context.user_data["state"] = st
        await _download(update, context, url)
        return

    try:
        quals = list_available_qualities(url, st.platform) or QUALITY_LIST_DEFAULT
        st.available_qualities = quals
        st.last_action = f"{st.platform}:{mode}:qualities_listed"
        context.user_data["state"] = st
        await update.callback_query.message.reply_text("Доступные качества (динамически):", reply_markup=quality_kb_from(quals))
    except Exception as e:
        logger.warning("list qualities failed: %s", e)
        await update.callback_query.message.reply_text("Не получилось определить качество. Выберите из стандартных.",
                                                       reply_markup=quality_kb_from(QUALITY_LIST_DEFAULT))

async def on_quality(update: Update, context: ContextTypes.DEFAULT_TYPE, q: str):
    st = get_state(context)
    st.quality = q
    st.last_action = f"{st.platform}:{st.mode}:quality={q}"
    context.user_data["state"] = st
    await _download(update, context, st.pending_url)

async def _download(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    user_id = update.effective_user.id if update.effective_user else 0
    chat_id = update.effective_chat.id
    if user_id in active_tasks:
        await context.bot.send_message(chat_id, "⏳ Уже качаю! /reset чтобы отменить")
        return

    async with global_semaphore:
        task = asyncio.current_task(); active_tasks[user_id] = task
        st = get_state(context)
        try:
            await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
            req = DownloadRequest(url=url, platform=st.platform, mode=st.mode, quality=st.quality or QUALITY_BEST)
            last_err = None
            for backend in BACKENDS:
                for attempt in range(1, 4):
                    try:
                        res = await asyncio.to_thread(backend.download, req)
                        if req.mode == MODE_AUDIO:
                            await context.bot.send_audio(chat_id, res.file_path.open('rb'), caption="🎵 Готово!")
                            st.last_action = f"{st.platform}:audio:success"
                        else:
                            if res.file_path.suffix.lower() in {".mp4",".mov",".m4v",".webm",".mkv"}:
                                await context.bot.send_video(chat_id, res.file_path.open('rb'), supports_streaming=True, caption="🎬 Готово!")
                            else:
                                await context.bot.send_document(chat_id, res.file_path.open('rb'), caption="📦 Готово!")
                            st.last_action = f"{st.platform}:video:{st.quality or 'best'}:success"
                        save_download({
                            "userId": user_id,
                            "platform": st.platform,
                            "mode": st.mode,
                            "quality": st.quality or "best",
                            "url": url,
                            "backend": backend.name,
                            "filename": res.filename,
                            "filesize": res.file_path.stat().st_size if res.file_path.exists() else None,
                        })
                        context.user_data["state"] = st
                        await context.bot.send_message(chat_id, "Оставите отзыв? 📝", reply_markup=review_optin_kb())
                        return
                    except Exception as e:
                        last_err = e
                        continue
            st.last_action = f"{st.platform}:{st.mode}:error"
            context.user_data["state"] = st
            await context.bot.send_message(chat_id, f"❌ Ошибка загрузки 😢\nПопробуйте другую ссылку или качество.\n\nПодробности: {last_err}")
            await context.bot.send_message(chat_id, "Хотите оставить отзыв? 📝", reply_markup=review_optin_kb())
        finally:
            active_tasks.pop(user_id, None)

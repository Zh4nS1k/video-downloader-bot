import asyncio, re, logging, time
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from config import *
from keyboards import *
from downloader import BACKENDS, DownloadRequest

# Красивое логирование с эмодзи
logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s ✨ [%(levelname)s] %(message)s",
)
logger = logging.getLogger("bot")

URL_RE = re.compile(URL_REGEX, re.IGNORECASE)
active_tasks = {}
global_semaphore = asyncio.Semaphore(GLOBAL_CONCURRENCY)

class State:
	def __init__(self):
		self.platform = None
		self.mode = None
		self.quality = None
		self.menu_msg_id = None
		self.awaiting_review = False

def get_state(context: ContextTypes.DEFAULT_TYPE) -> State:
	st = context.user_data.get("state")
	if not st:
		st = State()
		context.user_data["state"] = st
	return st

async def _edit_or_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, kb=None, include_reply=True):
	"""Редактируем одно меню-сообщение; если нет — создаём. Добавляем reply_kb для "прилипания"."""
	st = get_state(context)
	chat = update.effective_chat
	reply_kb_v = reply_kb() if include_reply else None
	if st.menu_msg_id:
		try:
			await context.bot.edit_message_text(
				text=text, chat_id=chat.id, message_id=st.menu_msg_id, reply_markup=kb
			)
			if include_reply and update.message:
				await update.message.reply_text("Используйте клавиатуру ниже ⬇️", reply_markup=reply_kb_v)
			return
		except Exception:
			st.menu_msg_id = None
	msg = await context.bot.send_message(chat_id=chat.id, text=text, reply_markup=kb)
	st.menu_msg_id = msg.message_id
	if include_reply and update.message:
		await update.message.reply_text("Используйте клавиатуру ниже ⬇️", reply_markup=reply_kb_v)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	st = get_state(context)
	st.platform = st.mode = st.quality = None
	st.menu_msg_id = None
	logger.info("🚀 /start user=%s", update.effective_user.id if update.effective_user else "?")
	logo_path = Path("logo.png")
	greet = (
		"Привет! 👋😄\n"
		"Я помогу скачать видео 🎬 и аудио 🎵 из TikTok и YouTube в лучшем качестве.\n"
		"Просто пришлите ссылку!"
	)
	if logo_path.exists():
		try:
			await update.message.reply_photo(photo=logo_path.open('rb'), caption=greet, reply_markup=reply_kb())
		except Exception:
			await update.message.reply_text(greet, reply_markup=reply_kb())
	else:
		await update.message.reply_text(greet, reply_markup=reply_kb())
	await _edit_or_send(update, context, "Выберите платформу ⬇️", platform_kb())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
	logger.info("❓ /help user=%s", update.effective_user.id if update.effective_user else "?")
	await _edit_or_send(update, context,
		"💡 Подсказка: выбери Платформу → Режим → Качество (для видео) → отправь ссылку. Меню ниже.",
		menu_kb()
	)

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
	logger.info("🔄 /reset user=%s", update.effective_user.id if update.effective_user else "?")
	context.user_data["state"] = State()
	await _edit_or_send(update, context, "✅ Сброс настроек. Выбери платформу:", platform_kb())

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
	logger.info("📋 /menu user=%s", update.effective_user.id if update.effective_user else "?")
	await _edit_or_send(update, context, "✨ Меню:", menu_kb())

async def on_platform(update: Update, context: ContextTypes.DEFAULT_TYPE, platform: str):
	st = get_state(context)
	st.platform = platform
	st.mode = None
	st.quality = None
	logger.info("🎯 platform=%s user=%s", platform, update.effective_user.id if update.effective_user else "?")
	await _edit_or_send(update, context, f"Платформа: {platform.upper()} ✅\nВыбери режим:", mode_kb())

async def on_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
	st = get_state(context)
	st.mode = mode
	st.quality = None
	logger.info("🎛 mode=%s user=%s", mode, update.effective_user.id if update.effective_user else "?")
	if mode == MODE_AUDIO:
		await _edit_or_send(update, context, f"Режим: 🎵 MP3 ✅\nОтправь ссылку!", menu_kb())
	else:
		await _edit_or_send(update, context, f"Режим: 🎬 Видео ✅\nВыбери качество:", quality_kb())

async def on_quality(update: Update, context: ContextTypes.DEFAULT_TYPE, quality: str):
	st = get_state(context)
	st.quality = quality
	quality_label = "Оригинал" if quality == QUALITY_BEST else quality
	logger.info("🎚 quality=%s user=%s", quality_label, update.effective_user.id if update.effective_user else "?")
	await _edit_or_send(update, context,
		f"Качество: {quality_label} ✅\nТеперь отправь ссылку.", menu_kb()
	)

async def on_menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
	logger.info("📋 menu=%s user=%s", action, update.effective_user.id if update.effective_user else "?")
	if action == "platform":
		await _edit_or_send(update, context, "Выбери платформу:", platform_kb()); return
	if action == "mode":
		await _edit_or_send(update, context, "Выбери режим:", mode_kb()); return
	if action == "quality":
		await _edit_or_send(update, context, "Выбери качество:", quality_kb()); return
	if action == "help":
		await _edit_or_send(update, context, "Пришлите ссылку TikTok/YouTube. В Меню можно поменять всё необходимое.", menu_kb()); return
	if action == "reset":
		await reset_cmd(update, context); return

async def on_more_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str):
	if choice == "yes":
		await update.callback_query.edit_message_text("Отправьте следующую ссылку ✨", reply_markup=menu_kb())
		if update.callback_query.message:
			await update.callback_query.message.reply_text("Используйте клавиатуру ниже ⬇️", reply_markup=reply_kb())
	else:
		await update.callback_query.edit_message_text("Спасибо, что пользуетесь ботом! 💙", reply_markup=menu_kb())
		if update.callback_query.message:
			await update.callback_query.message.reply_text("Используйте клавиатуру ниже ⬇️", reply_markup=reply_kb())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
	text = (update.message.text or "").strip()
	if not text:
		return
	st = get_state(context)

	# Обработка отзыва
	if st.awaiting_review:
		try:
			reviews_path = Path(REVIEWS_FILE)
			if reviews_path.exists():
				content = reviews_path.read_text(encoding="utf-8")
			else:
				content = ""
			user_id = update.effective_user.id if update.effective_user else "?"
			content += f"\n[{datetime.now().isoformat()}] user={user_id}: {text}\n"
			reviews_path.write_text(content, encoding="utf-8")
		except Exception as e:
			logger.error("❌ Ошибка сохранения отзыва: %s", e)
		st.awaiting_review = False
		context.user_data["state"] = st
		await update.message.reply_text("Спасибо за отзыв! 💙", reply_markup=reply_kb())
		await update.message.reply_text("Хотите скачать ещё что-то?", reply_markup=more_kb())
		return

	if URL_RE.search(text):
		if not st.platform:
			await _edit_or_send(update, context, "Сначала выбери платформу:", platform_kb()); return
		if not st.mode:
			await _edit_or_send(update, context, "Выбери режим:", mode_kb()); return
		if st.mode != MODE_AUDIO and not st.quality:
			await _edit_or_send(update, context, "Выбери качество:", quality_kb()); return
		await _download(update, context, text)
		return

	low = text.lower()
	if "help" in low or "помо" in low:
		await help_cmd(update, context); return
	if "menu" in low or "меню" in low:
		await menu_cmd(update, context); return
	if "reset" in low or "сброс" in low:
		await reset_cmd(update, context); return

	await _edit_or_send(update, context, "Пришли ссылку или открой меню:", menu_kb())

async def _download(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
	user_id = update.effective_user.id if update.effective_user else 0
	if user_id in active_tasks:
		await _edit_or_send(update, context, "У тебя уже есть активная загрузка. /cancel чтобы отменить.", menu_kb())
		return
	async with global_semaphore:
		task = asyncio.current_task()
		if task:
			active_tasks[user_id] = task
		st = get_state(context)
		anim_msg = None
		status_msg = None
		start_ts = time.monotonic()
		try:
			# Анимация скачивания
			work_gif = WORKING_GIFS[int(time.time()) % len(WORKING_GIFS)]
			try:
				anim_msg = await update.message.reply_animation(animation=work_gif, caption="Скачиваю… ⏳")
			except Exception:
				pass
			await context.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_VIDEO)
			status_msg = await update.message.reply_text("Готовлю загрузку…", reply_markup=menu_kb())
			await update.message.reply_text("Используйте клавиатуру ниже ⬇️", reply_markup=reply_kb())

			req = DownloadRequest(url=url, platform=st.platform, mode=st.mode, quality=st.quality or QUALITY_BEST)
			logger.info("⬇️ download start url=%s platform=%s quality=%s mode=%s user=%s", url, st.platform, st.quality, st.mode, user_id)

			last_err = None
			for backend in BACKENDS:
				try:
					est = backend.probe(req)
					if st.mode == MODE_VIDEO and est and est > MAX_BOT_FILE_SIZE:
						await _edit_or_send(update, context,
							f"⚠️ Файл будет ~{est/1024/1024:.1f}MB (>лимита). Снизь качество или выбери MP3.",
							too_big_kb()
						)
						return
					res = backend.download(req)
					if st.mode == MODE_VIDEO and res.file_path.stat().st_size > MAX_BOT_FILE_SIZE:
						res.file_path.unlink(missing_ok=True)
						await _edit_or_send(update, context,
							"⚠️ Файл вышел больше лимита TG. Снизь качество или MP3.", too_big_kb())
						return

					dl_time = time.monotonic() - start_ts
					logger.info("✅ downloaded file=%s size=%sB in %.2fs", res.filename, res.file_path.stat().st_size, dl_time)

					await status_msg.edit_text("Загружаю в Telegram… 📤")
					upload_start = time.monotonic()

					# Отправка файла
					if st.mode == MODE_AUDIO:
						await update.message.reply_audio(audio=res.file_path.open('rb'), filename=res.filename, caption="Готово! 🎵")
					else:
						if res.filename.lower().endswith((".mp4",".mov",".m4v",".webm",".mkv")):
							await update.message.reply_video(video=res.file_path.open('rb'), supports_streaming=True, caption="Готово! 🎬")
						else:
							await update.message.reply_document(document=res.file_path.open('rb'), filename=res.filename, caption="Готово! 📦")

					upload_time = time.monotonic() - upload_start
					total_time = time.monotonic() - start_ts
					logger.info("📤 uploaded in %.2fs (total %.2fs)", upload_time, total_time)

					# GIF успеха
					try:
						succ_gif = SUCCESS_GIFS[int(time.time()) % len(SUCCESS_GIFS)]
						await update.message.reply_animation(animation=succ_gif, caption="Спасибо, что пользуетесь ботом! 💙")
					except Exception as e:
						logger.warning("⚠️ Не удалось отправить GIF: %s", e)

					# Запрос отзыва
					await update.message.reply_text("Пожалуйста, оставьте короткий отзыв 📝 — это займёт 5 секунд!", reply_markup=reply_kb())
					st.awaiting_review = True
					context.user_data["state"] = st

					# Вопрос "скачать еще"
					await update.message.reply_text("Хотите скачать ещё что-то?", reply_markup=more_kb())
					await update.message.reply_text("Используйте клавиатуру ниже ⬇️", reply_markup=reply_kb())
					return
				except Exception as e:
					last_err = e
					logger.warning("⚠️ backend %s failed: %s", backend.name, str(e))
					continue

			await _edit_or_send(update, context, f"❌ Ошибка: {last_err}", menu_kb())
		finally:
			active_tasks.pop(user_id, None)
			try:
				if anim_msg:
					await anim_msg.delete()
				if status_msg:
					await status_msg.delete()
			except Exception:
				pass

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id if update.effective_user else 0
	t = active_tasks.get(user_id)
	if t and not t.done():
		t.cancel()
		logger.info("⛔ cancel user=%s", user_id)
		await update.message.reply_text("⛔️ Отменил.", reply_markup=reply_kb())
	else:
		await update.message.reply_text("Нет активной загрузки.", reply_markup=reply_kb())

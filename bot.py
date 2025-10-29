import logging, re
from telegram.ext import (
	Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from config import BOT_TOKEN
from handlers import (
	start, help_cmd, reset_cmd, menu_cmd,
	on_platform, on_mode, on_quality, on_menu_action,
	handle_text, cancel_cmd, on_more_choice
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s ✨ [%(levelname)s] %(message)s")
logger = logging.getLogger("bot")

def main():
	app = Application.builder().token(BOT_TOKEN).build()

	async def _set_commands(a):
		await a.bot.set_my_commands([
			("start","Старт"),
			("help","Помощь"),
			("menu","Меню"),
			("reset","Сброс"),
			("cancel","Отменить загрузку"),
		])
	app.post_init = _set_commands

	app.add_handler(CallbackQueryHandler(lambda u,c: on_platform(u,c,u.callback_query.data.split(":")[1]), pattern=r"^platform:"))
	app.add_handler(CallbackQueryHandler(lambda u,c: on_mode(u,c,u.callback_query.data.split(":")[1]), pattern=r"^mode:"))
	app.add_handler(CallbackQueryHandler(lambda u,c: on_quality(u,c,u.callback_query.data.split(":")[1]), pattern=r"^quality:"))
	app.add_handler(CallbackQueryHandler(lambda u,c: on_menu_action(u,c,u.callback_query.data.split(":")[1]), pattern=r"^menu:"))
	app.add_handler(CallbackQueryHandler(lambda u,c: on_more_choice(u,c,u.callback_query.data.split(":")[1]), pattern=r"^more:"))

	app.add_handler(CommandHandler("start", start))
	app.add_handler(CommandHandler("help", help_cmd))
	app.add_handler(CommandHandler("menu", menu_cmd))
	app.add_handler(CommandHandler("reset", reset_cmd))
	app.add_handler(CommandHandler("cancel", cancel_cmd))

	app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

	logger.info("🤖 Bot starting…")
	app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()

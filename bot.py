import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import BotCommand
from config import BOT_TOKEN, LOG_LEVEL
from handlers import start, help_cmd, reset_cmd, handle_text, on_mode, on_quality, on_review_choice

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
                    format="%(asctime)s ✨ [%(levelname)s] %(message)s")
logger = logging.getLogger("bot")

def _val(data: str) -> str:
    return (data or "").partition(":")[2]

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    async def _set_cmds(a: Application):
        await a.bot.set_my_commands([
            BotCommand("start", "Старт"),
            BotCommand("help", "Помощь"),
            BotCommand("reset", "Сброс")
        ])
    app.post_init = _set_cmds

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))

    app.add_handler(CallbackQueryHandler(lambda u,c: on_mode(u,c,_val(u.callback_query.data)), pattern=r"^mode:"))
    app.add_handler(CallbackQueryHandler(lambda u,c: on_quality(u,c,_val(u.callback_query.data)), pattern=r"^quality:"))
    app.add_handler(CallbackQueryHandler(lambda u,c: on_review_choice(u,c,_val(u.callback_query.data)), pattern=r"^review:"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🤖 Bot starting…")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()

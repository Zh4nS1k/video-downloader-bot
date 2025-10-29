from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import MODE_AUDIO, MODE_VIDEO

def mode_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🎬 Видео", callback_data=f"mode:{MODE_VIDEO}"),
        InlineKeyboardButton("🎧 Аудио (MP3)", callback_data=f"mode:{MODE_AUDIO}"),
    ]])

def quality_kb_from(qualities):
    rows, row = [], []
    for q in qualities:
        row.append(InlineKeyboardButton(q, callback_data=f"quality:{q}"))
        if len(row) == 3:
            rows.append(row); row = []
    if row: rows.append(row)
    return InlineKeyboardMarkup(rows)

def review_optin_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Да, оставить отзыв", callback_data="review:yes"),
        InlineKeyboardButton("❌ Нет", callback_data="review:no")
    ]])

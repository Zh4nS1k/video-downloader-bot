from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import *

def reply_kb() -> ReplyKeyboardMarkup:
	return ReplyKeyboardMarkup(
		[
			[KeyboardButton("📋 Меню"), KeyboardButton("❓ Помощь")],
			[KeyboardButton("🔄 Сброс"), KeyboardButton("🎵 Аудио MP3"), KeyboardButton("🎬 Видео")],
		],
		resize_keyboard=True,
		one_time_keyboard=False,
	)

def platform_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("YouTube", callback_data=f"platform:{PLATFORM_YOUTUBE}"),
        InlineKeyboardButton("TikTok",  callback_data=f"platform:{PLATFORM_TIKTOK}"),
    ]])

def mode_kb() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup([[
		InlineKeyboardButton("🎬 Видео", callback_data=f"mode:{MODE_VIDEO}"),
		InlineKeyboardButton("🎵 Аудио (MP3)", callback_data=f"mode:{MODE_AUDIO}"),
	]])

def quality_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Original (Best)", callback_data=f"quality:{QUALITY_BEST}")],
            [
                InlineKeyboardButton("1080p", callback_data=f"quality:{QUALITY_1080P}"),
                InlineKeyboardButton("720p",  callback_data=f"quality:{QUALITY_720P}"),
                InlineKeyboardButton("480p",  callback_data=f"quality:{QUALITY_480P}"),
            ],
        ]
    )

def menu_kb() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(
		[
			[
				InlineKeyboardButton("Платформа", callback_data="menu:platform"),
				InlineKeyboardButton("Режим",     callback_data="menu:mode"),
			],
			[
				InlineKeyboardButton("Качество",  callback_data="menu:quality"),
				InlineKeyboardButton("Помощь", callback_data="menu:help"),
			],
			[InlineKeyboardButton("Сброс", callback_data="menu:reset")],
		]
	)

def too_big_kb() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup([[
		InlineKeyboardButton("⬇️ Ниже качество", callback_data="menu:quality"),
		InlineKeyboardButton("🎵 Переключиться на MP3",  callback_data=f"mode:{MODE_AUDIO}"),
	]])

def more_kb() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup([[
		InlineKeyboardButton("Да, ещё! ✨", callback_data="more:yes"),
		InlineKeyboardButton("Нет, спасибо 😊", callback_data="more:no"),
	]])

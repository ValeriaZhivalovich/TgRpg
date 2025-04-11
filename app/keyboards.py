from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup 
from aiogram.utils.keyboard import InlineKeyboardBuilder


menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📜 Список задач"),
            KeyboardButton(text="🏆 Профиль")
        ],
        [
            KeyboardButton(text="🎒 Инвентарь"),
            KeyboardButton(text="⚔️ Навыки")
        ]
    ],
    resize_keyboard=True
)


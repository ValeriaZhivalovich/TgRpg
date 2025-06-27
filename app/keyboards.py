from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup 
from aiogram.utils.keyboard import InlineKeyboardBuilder


menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📜 Список задач"),
            KeyboardButton(text="🧝‍♀️ Профиль")
        ],
        [
            KeyboardButton(text="⚖️ Рынок"),
            KeyboardButton(text="⚔️ Боссы/Квесты")
        ],
        [
            KeyboardButton(text="⚙️ Настройки")
        ]
    ],
    resize_keyboard=True
)

profile = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏹 Навыки"),
            KeyboardButton(text="🏆 Достижения")
        ],
        [
            KeyboardButton(text="🎒 Инвентарь"),
            KeyboardButton(text="🐶 Питомцы")
        ]
    ],
    resize_keyboard=True
)

tasks = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ Текущие"),
            KeyboardButton(text="❌ Завершенные")
        ],
        [
            KeyboardButton(text="📝 Создать задачу"),
        ]
    ],
    resize_keyboard=True
)

active_task = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="❌ Удалить"),
            KeyboardButton(text="⭕️ Изменить")
        ],
    ],
    resize_keyboard=True
)

market = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✨ Зелья"),
            KeyboardButton(text="🐶 Питомцы")
        ],
        [
            KeyboardButton(text="🎟 Билеты"),
        ]
    ],
    resize_keyboard=True
)


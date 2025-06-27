from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup 
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery


menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📜 Список задач", callback_data = 'tasks' ),
            KeyboardButton(text="🧝‍♀️ Профиль", callback_data='profile')
        ],
        [
            KeyboardButton(text="⚖️ Рынок", callback_data = 'market'),
            KeyboardButton(text="⚔️ Боссы/Квесты", callback_data = 'boss')
        ],
        [
            KeyboardButton(text="⚙️ Настройки", callback_data = 'options')
        ]
    ],
    resize_keyboard=True
)

profile_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🏹 Навыки", callback_data = 'skills'),
            InlineKeyboardButton(text="🏆 Достижения", callback_data = 'achievements')
        ],
        [
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data = 'inventory'),
            InlineKeyboardButton(text="🐶 Питомцы", callback_data = 'my_pets')
        ]
    ],
    resize_keyboard=True
)

tasks_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Текущие", callback_data = 'active_task'),
            InlineKeyboardButton(text="❌ Завершенные", callback_data = 'complite_task')
        ],
        [
            InlineKeyboardButton(text="📝 Создать задачу", callback_data = 'creste_task'),
        ]
    ],
    resize_keyboard=True
)

active_task_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Удалить", callback_data = 'delete_active_task'),
            InlineKeyboardButton(text="⭕️ Изменить", callback_data = 'change_active_task')
        ],
    ],
    resize_keyboard=True
)

market_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✨ Зелья", callback_data = 'market_potion'),
            InlineKeyboardButton(text="🐶 Питомцы", callback_data = 'market_pets')
        ],
        [
            InlineKeyboardButton(text="🎟 Билеты", callback_data = 'market_ticket'),
        ]
    ],
    resize_keyboard=True
)

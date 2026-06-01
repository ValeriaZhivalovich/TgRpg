from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📋 Квесты"),
            KeyboardButton(text="🧝‍♀️ Профиль"),
        ],
        [
            KeyboardButton(text="🛒 Магазин"),
            KeyboardButton(text="🐾 Питомцы"),
        ],
        [
            KeyboardButton(text="📝 Заметки"),
            KeyboardButton(text="⚙️ Настройки"),
        ],
    ],
    resize_keyboard=True
)

main_menu_btn = InlineKeyboardButton(text="◀ Главное меню", callback_data='main_menu')
back_btn = InlineKeyboardButton(text="◀ Назад", callback_data='set_back')

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[main_menu_btn]])

# === Profile ===

profile_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🏹 Навыки", callback_data='skills'),
            InlineKeyboardButton(text="🏆 Достижения", callback_data='achievements'),
        ],
        [
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data='inventory'),
            InlineKeyboardButton(text="🐶 Питомцы", callback_data='my_pets'),
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data='stats_charts'),
        ],
        [main_menu_btn],
    ]
)

# === Tasks / Quests ===

tasks_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Текущие", callback_data='active_task'),
            InlineKeyboardButton(text="❌ Завершённые", callback_data='complete_task'),
        ],
        [
            InlineKeyboardButton(text="📝 Создать квест", callback_data='create_task'),
            main_menu_btn,
        ],
    ]
)

# === Market ===

market_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✨ Зелья", callback_data='market_potion'),
            InlineKeyboardButton(text="🐶 Питомцы", callback_data='market_pets'),
        ],
        [
            InlineKeyboardButton(text="📜 Свитки", callback_data='market_scroll'),
            InlineKeyboardButton(text="🍖 Корм", callback_data='market_food'),
        ],
        [main_menu_btn],
    ]
)

# === Pets ===

pets_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [main_menu_btn],
    ]
)

# === Class selection ===

class_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🗡️ Авантюрист", callback_data='class_Авантюрист'),
            InlineKeyboardButton(text="🔮 Маг", callback_data='class_Маг'),
        ],
        [
            InlineKeyboardButton(text="⚔️ Воин", callback_data='class_Воин'),
            InlineKeyboardButton(text="💰 Торговец", callback_data='class_Торговец'),
        ],
        [
            InlineKeyboardButton(text="🏹 Следопыт", callback_data='class_Следопыт'),
        ],
    ]
)

skip_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Пропустить", callback_data='skip')],
    ]
)

confirm_reg_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ В путь!", callback_data='reg_confirm'),
            InlineKeyboardButton(text="❌ Заново", callback_data='reg_restart'),
        ]
    ]
)

# === Quest creation keyboards ===

quest_difficulty_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🌟 Easy", callback_data='qdiff_easy'),
            InlineKeyboardButton(text="⚡ Normal", callback_data='qdiff_normal'),
            InlineKeyboardButton(text="🔥 Hard", callback_data='qdiff_hard'),
        ]
    ]
)

quest_type_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📌 Разовый", callback_data='qtype_once'),
            InlineKeyboardButton(text="🔄 Повторяющийся", callback_data='qtype_repeat'),
        ]
    ]
)

quest_deadline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🚫 Без дедлайна", callback_data='qdeadline_skip'),
        ],
        [
            InlineKeyboardButton(text="📅 1 день", callback_data='qdeadline_1'),
            InlineKeyboardButton(text="📅 3 дня", callback_data='qdeadline_3'),
            InlineKeyboardButton(text="📅 7 дней", callback_data='qdeadline_7'),
        ]
    ]
)

quest_confirm_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data='qconfirm_yes'),
            InlineKeyboardButton(text="❌ Отмена", callback_data='qconfirm_no'),
        ]
    ]
)

# === Timer selection ===

quest_timer_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🚫 Без таймера", callback_data='qtimer_skip'),
        ],
        [
            InlineKeyboardButton(text="⏱ 5 мин", callback_data='qtimer_5'),
            InlineKeyboardButton(text="⏱ 10 мин", callback_data='qtimer_10'),
            InlineKeyboardButton(text="⏱ 15 мин", callback_data='qtimer_15'),
        ],
        [
            InlineKeyboardButton(text="⏱ 30 мин", callback_data='qtimer_30'),
            InlineKeyboardButton(text="⏱ 60 мин", callback_data='qtimer_60'),
        ],
        [
            InlineKeyboardButton(text="✏️ Своё", callback_data='qtimer_custom'),
        ],
    ]
)

# === Settings ===

settings_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🌟 Easy", callback_data='settings_diff_easy'),
            InlineKeyboardButton(text="⚡ Normal", callback_data='settings_diff_normal'),
            InlineKeyboardButton(text="🔥 Hard", callback_data='settings_diff_hard'),
        ],
        [
            InlineKeyboardButton(text="🔔 Уведомления", callback_data='notif_toggle'),
        ],
        [main_menu_btn],
    ]
)

# === ISEKAI NARRATIVE — System Voice ===
# Все сообщения бота в стиле «попаданец в другой мир».
# System — безликий голос в голове Героя.

# ──────────────────────────────────────────────
# REGISTRATION
# ──────────────────────────────────────────────

def start_new(name_raw: str) -> str:
    return (
        "👋 <b>Неизвестный сигнал. Сканирование души...</b>\n\n"
        f"Ты — {name_raw}. Твой профиль не обнаружен в архиве Системы.\n\n"
        "Ты помнишь, кто ты? Мир за гранью ждёт ответа.\n"
        "<b>Назови своё имя, Герой.</b>"
    )


def start_return(name: str) -> str:
    return (
        f"⚡ <b>Возвращение зафиксировано.</b>\n\n"
        f"Система опознаёт тебя, <b>{name}</b>.\n"
        "Поток реальности вновь связан. Добро пожаловать обратно."
    )


def reg_name_long() -> str:
    return "❌ Слишком длинное имя. Максимум 50 символов. Попробуй ещё раз:"


def reg_ask_lastname() -> str:
    return (
        "Принято. Архив обновлён.\n\n"
        "Теперь скажи, какая у тебя <b>фамилия</b>?\n"
        "(или нажми «Пропустить», если в твоём мире её нет)"
    )


def reg_lastname_long() -> str:
    return "❌ Слишком длинная фамилия. Максимум 150 символов."


def reg_ask_class() -> str:
    return (
        "🛡️ <b>Выбери свой класс:</b>\n\n"
        "Каждый класс определяет твой путь в этом мире.\n\n"
        "🗡️ <b>Авантюрист</b> — сбалансирован, 100 HP / 50 EP\n"
        "🔮 <b>Маг</b> — высокий запас энергии, 70 HP / 80 EP\n"
        "⚔️ <b>Воин</b> — крепкое здоровье, 130 HP / 30 EP\n"
        "💰 <b>Торговец</b> — начинаешь с 50 золота, 90 HP / 50 EP\n"
        "🏹 <b>Следопыт</b> — вынослив и быстр, 100 HP / 60 EP"
    )


def reg_ask_avatar() -> str:
    return (
        "🎭 Отправь <b>emoji</b> для аватара.\n"
        "(или нажми «Пропустить» — Система выберет сама)"
    )


def reg_avatar_long() -> str:
    return "❌ Слишком длинный аватар. Отправь один emoji или короткий символ:"


def reg_summary(avatar: str, full_name: str, class_name: str, hp: int, ep: int, gold: int) -> str:
    return (
        "📋 <b>Сводка персонажа:</b>\n\n"
        f"{avatar} <b>{full_name}</b>\n"
        f"🛡️ Класс: {class_name}\n"
        f"❤ HP: {hp}\n"
        f"⚡ EP: {ep}\n"
        f"💰 Золото: {gold}\n\n"
        "<b>Система подтверждает создание персонажа?</b>"
    )


def reg_confirm(full_name: str, class_name: str) -> str:
    return (
        "✅ <b>Регистрация завершена.</b>\n\n"
        f"Система приветствует тебя, {full_name}.\n"
        f"Твой класс: {class_name}. Уровень: 1.\n\n"
        "Ты открываешь глаза в новом мире. Вокруг — неизведанные земли.\n"
        "Где-то вдалеке слышен гул древней магии...\n\n"
        "<i>Голос Системы затихает, но ты чувствуешь — она рядом.</i>"
    )


def reg_restart() -> str:
    return (
        "🔄 <b>Пересоздание персонажа.</b>\n\n"
        "Поток реальности перематывается назад...\n"
        "<b>Назови своё имя, Герой.</b>"
    )


# ──────────────────────────────────────────────
# PROFILE
# ──────────────────────────────────────────────

def profile_not_found() -> str:
    return "❌ Твой профиль не найден в архиве Системы. Используй /start."


def character_not_found() -> str:
    return "❌ Персонаж не найден. Возможно, поток реальности разорван. Используй /start."


def profile_stats(avatar: str, name: str, class_name: str, level: int,
                  energy: int, max_energy: int, hp: int, max_hp: int,
                  xp: int, xp_next: int, gold: int) -> str:
    return (
        f"{avatar} <b>{name}</b>\n"
        f"🛡️ Класс: {class_name}\n"
        f"📊 Уровень: {level}\n"
        f"⚡ Энергия: {energy}/{max_energy}\n"
        f"❤ Здоровье: {hp}/{max_hp}\n"
        f"✨ Опыт: {xp}/{xp_next}\n"
        f"💰 Золото: {gold}"
    )


def skills_empty() -> str:
    return (
        "🔮 <b>Навыки ещё не раскрыты.</b>\n\n"
        "Выполняй задания с привязкой к навыку, чтобы прокачать их.\n"
        "Система фиксирует каждое твоё действие."
    )


def skills_list(text: str) -> str:
    return f"🔮 <b>Твои навыки:</b>\n\n{text}"


def achievements_empty() -> str:
    return "🏆 Достижений пока нет. Система следит за каждым твоим шагом."


def achievements_list(text: str) -> str:
    return f"🏆 <b>Достижения:</b>\n\n{text}"


def new_achievement(name: str, description: str) -> str:
    return (
        f"🏆 <b>Достижение разблокировано!</b>\n\n"
        f"{name}\n"
        f"{description}\n\n"
        f"Система отмечает твой подвиг."
    )


def inventory_empty() -> str:
    return "🎒 Инвентарь пуст. Добывай трофеи в испытаниях!"


def inventory_text(text: str) -> str:
    return f"🎒 <b>Инвентарь:</b>\n\n{text}"


# ──────────────────────────────────────────────
# NAVIGATION
# ──────────────────────────────────────────────

def tasks_menu() -> str:
    return "📋 Система открывает список заданий. Выбери категорию:"


def market_welcome() -> str:
    return (
        "🛍 <b>Рынок</b>\n\n"
        "Смертные и маги торгуют здесь своими товарами.\n"
        "Трать золото с умом, Герой."
    )


def bosses_placeholder() -> str:
    return (
        "👹 <b>Боссы ещё не появились.</b>\n\n"
        "Тьма сгущается где-то вдали. Система готовит испытания..."
    )


def deadline_reminder(title: str, hours_left: int) -> str:
    return (
        f"⌛ <b>Дедлайн приближается!</b>\n\n"
        f"Задание «{title}» нужно сдать через <b>{hours_left} ч.</b>\n"
        f"Система напоминает: время уходит."
    )


def recurring_reminder(title: str) -> str:
    return (
        f"🔄 <b>Привычка ждёт!</b>\n\n"
        f"Повторяющееся задание «{title}» ещё не выполнено сегодня.\n"
        f"Система верит в твою дисциплину."
    )


def notifications_on() -> str:
    return "🔔 Уведомления включены. Система будет напоминать о дедлайнах."


def notifications_off() -> str:
    return "🔕 Уведомления отключены. Система замолкает."


def settings_menu(current_diff: str, notifications: bool = True) -> str:
    diff_names = {'easy': '🌟 Easy', 'normal': '⚡ Normal', 'hard': '🔥 Hard'}
    label = diff_names.get(current_diff, current_diff)
    notif_label = "🔔 Вкл" if notifications else "🔕 Выкл"
    return (
        "⚙️ <b>Настройки Системы</b>\n\n"
        f"🌀 Сложность квеста по умолчанию:\n"
        f"   {label}\n\n"
        f"🔔 Уведомления: {notif_label}\n\n"
        "<i>Уведомления напоминают о дедлайнах и привычках.</i>"
    )


def settings_updated(difficulty: str) -> str:
    diff_names = {'easy': '🌟 Easy', 'normal': '⚡ Normal', 'hard': '🔥 Hard'}
    label = diff_names.get(difficulty, difficulty)
    return (
        f"✅ Параметры Системы обновлены.\n"
        f"Сложность по умолчанию: {label}"
    )


# ──────────────────────────────────────────────
# ITEMS & SHOP
# ──────────────────────────────────────────────

def shop_empty(title: str) -> str:
    return f"{title} пока отсутствуют. Торговцы ещё не доставили товар."


def shop_list(title: str, text: str) -> str:
    return f"<b>{title}</b>\n\n{text}"


def shop_buy_error() -> str:
    return "❌ Ошибка транзакции. Система не может обработать запрос."


def shop_bought(name: str, gold_left: int) -> str:
    return (
        f"✅ <b>Покупка совершена!</b>\n\n"
        f"«{name}» перемещён в твой инвентарь.\n"
        f"💰 Осталось: {gold_left} золота\n\n"
        "Сделку зафиксировала сама Система."
    )


def pet_shop_empty() -> str:
    return "🐶 Питомцы пока недоступны. Система ищет подходящих зверей..."


def pet_adopted(name: str, description: str, gold_left: int) -> str:
    return (
        f"🎉 <b>{name} доверяет тебе!</b>\n\n"
        f"{description}\n\n"
        f"💰 Осталось: {gold_left} золота\n"
        "🐾 Загляни в профиль, чтобы призвать спутника."
    )


def pet_activated(name: str) -> str:
    return (
        f"✅ <b>{name} призван!</b>\n\n"
        "Он выходит из тени и встаёт рядом с тобой.\n"
        "Система чувствует его присутствие. Связь установлена."
    )


def no_active_pet() -> str:
    return "❌ Нет активного питомца. Призови питомца в профиле."


def item_used(name: str, messages: list[str]) -> str:
    return f"✅ <b>«{name}» использован!</b>\n\n" + "\n".join(messages)


# ──────────────────────────────────────────────
# QUESTS — General
# ──────────────────────────────────────────────

def cancel_none() -> str:
    return "❌ Нет активного действия для отмены."


def cancel_ok() -> str:
    return "⏹ Действие отменено. Система возвращается в режим ожидания."


# ──────────────────────────────────────────────
# QUESTS — Creation
# ──────────────────────────────────────────────

def quest_create_start() -> str:
    return (
        "📝 <b>Создание нового задания.</b>\n\n"
        "Система ждёт название твоей миссии:"
    )


def quest_title_long() -> str:
    return "❌ Слишком длинное название. Максимум 100 символов. Попробуй ещё раз:"


def quest_ask_description() -> str:
    return (
        "📖 Добавь <b>описание</b> к заданию (необязательно).\n"
        "Опиши контекст или детали миссии.\n\n"
        "Или нажми «Пропустить»."
    )


def quest_description_long() -> str:
    return "❌ Слишком длинное описание. Максимум 255 символов."


def quest_ask_difficulty(current: str = 'easy') -> str:
    diff_names = {'easy': '🌟 Easy', 'normal': '⚡ Normal', 'hard': '🔥 Hard'}
    label = diff_names.get(current, current)
    return (
        "Выбери <b>сложность</b> задания:\n\n"
        "🌟 Easy — рутинная задача, без таймера\n"
        "⚡ Normal — средняя сложность (таймер 5 мин)\n"
        "🔥 Hard — серьёзное испытание (таймер 10 мин + подтверждение)\n\n"
        f"🌀 <i>Текущая по умолчанию: {label}</i>"
    )


def quest_ask_type() -> str:
    return "Это задание будет <b>разовым</b> или <b>повторяющимся</b>?"


def quest_ask_skill() -> str:
    return "🎯 К какому <b>навыку</b> относится это задание?"


def quest_ask_deadline() -> str:
    return "У этого задания есть <b>дедлайн</b>?"


def quest_summary(title: str, description: str, difficulty: str, quest_type: str, skill: str,
                  deadline: str, xp: int, gold: int) -> str:
    desc = f"\n📖 {description}\n" if description else ""
    return (
        "📋 <b>Сводка задания:</b>\n\n"
        f"Название: {title}"
        f"{desc}"
        f"\nСложность: {difficulty}\n"
        f"Тип: {quest_type}\n"
        f"Навык: {skill}\n"
        f"Дедлайн: {deadline}\n\n"
        f"🎁 Награда: {xp} XP, {gold} золота\n\n"
        "<b>Подтверждаешь?</b>"
    )


def quest_accepted(emoji: str, title: str, description: str, skill: str, hint: str) -> str:
    desc = f"\n📖 <i>{description}</i>" if description else ""
    skill_line = f"{skill}\n" if skill else ""
    return (
        f"{emoji} <b>Задание принято!</b>\n\n"
        f"Система зарегистрировала миссию:\n"
        f"«{title}»"
        f"{desc}\n"
        f"{skill_line}"
        f"Срок выполнения зафиксирован.{hint}"
    )


def quest_recurring_hint() -> str:
    return "\n\n🔄 Это задание будет повторяться ежедневно. Система ждёт подвиг каждый день!"


def quest_timer_hint(minutes: int) -> str:
    return f"\n\n⏱ Таймер установлен на <b>{minutes} мин.</b> Не забудь запустить его, когда приступишь."


def quest_hint_hard() -> str:
    return "\n\n📝 После завершения потребуется заметка или фото."


def quest_ask_timer() -> str:
    return (
        "⏱ <b>Таймер</b>\n\n"
        "Сколько минут длится это задание?\n"
        "Чем дольше — тем выше награда: +2✨ +1💰 за каждую минуту.\n\n"
        "Выбери готовый вариант или введи своё число (до 180)."
    )


def quest_timer_custom() -> str:
    return "⏱ Введи количество минут (целое число, от 1 до 180):"


def quest_timer_invalid() -> str:
    return "❌ Некорректное значение. Введи число от 1 до 180 или нажми «Без таймера»."


def quest_cancelled() -> str:
    return "⏹ Создание отменено. Система ждёт новых указаний."


# ──────────────────────────────────────────────
# QUESTS — Active List
# ──────────────────────────────────────────────

def profile_err() -> str:
    return "❌ Профиль не найден в архиве Системы."


def active_empty() -> str:
    return "📭 <b>Активных заданий нет.</b>\nСистема в режиме ожидания. Создай новую миссию."


def active_list(text: str) -> str:
    return f"📋 <b>Активные задания:</b>\n\n{text}"


# ──────────────────────────────────────────────
# QUESTS — Timer
# ──────────────────────────────────────────────

def start_none() -> str:
    return "⏹ Нет заданий, которые можно запустить.\nВсе Normal/Hard миссии уже запущены или отсутствуют."


def start_choose() -> str:
    return "Выбери задание для запуска таймера:"


def start_already() -> str:
    return "❌ Это задание уже запущено или недоступно."


def timer_started(title: str, minutes: int) -> str:
    return (
        f"▶️ <b>Таймер запущен!</b>\n\n"
        f"«{title}»\n"
        f"⏳ {minutes} мин. Система наблюдает."
    )


# ──────────────────────────────────────────────
# QUESTS — Complete
# ──────────────────────────────────────────────

def finish_none() -> str:
    return (
        "⏳ Нет заданий, готовых к сдаче.\n"
        "Normal/Hard миссии нужно сначала запустить и дождаться таймера."
    )


def finish_choose() -> str:
    return "✅ Выбери задание для завершения:"


def finish_own() -> str:
    return "❌ Это не твоё задание, Герой. Система не обманешь."


def finish_timer() -> str:
    return "⏳ Таймер ещё не истёк. Система наблюдает."


def finish_hard_ask() -> str:
    return (
        "📝 <b>Hard-задание требует подтверждения.</b>\n\n"
        "Отправь заметку или фото, чтобы Система засчитала выполнение:\n"
        "(текст или фото)"
    )


def reward_completed(title: str, xp: int, gold: int, skill: str,
                     streak: str, level: int) -> str:
    return (
        f"✅ <b>Задание выполнено!</b>\n\n"
        f"«{title}» — завершено.\n\n"
        f"🎁 +{xp} XP\n"
        f"💰 +{gold} золота"
        f"{skill}"
        f"{streak}\n"
        f"📊 Уровень: {level}"
    )


def reward_recurring() -> str:
    return "🔄 Привычка остаётся активной. Завтра Система снова ждёт твоего подвига."


def level_up(new_level: int) -> str:
    return (
        f"⬆️⬆️⬆️ <b>РАНГ ПОВЫШЕН!</b> ⬆️⬆️⬆️\n\n"
        f"Система фиксирует твой рост, Герой.\n"
        f"Ты достиг <b>{new_level} уровня</b>.\n\n"
        f"Мир чувствует изменения в тебе. Силы прибывают."
    )


# ──────────────────────────────────────────────
# QUESTS — Delete & Completed
# ──────────────────────────────────────────────

def delete_choose() -> str:
    return "Выбери задание для удаления:"


def delete_none() -> str:
    return "📭 Нет активных заданий для удаления."


def delete_ok() -> str:
    return "🗑 Задание удалено. Система очищает записи."


def delete_not_found() -> str:
    return "❌ Задание не найдено или не принадлежит тебе."


def completed_empty() -> str:
    return "📜 Завершённых заданий пока нет.\nСистема ждёт твоих первых побед."


def completed_list(text: str) -> str:
    return f"✅ <b>Завершённые задания:</b>\n\n{text}"


def completed_last() -> str:
    return "\n📜 Показаны последние 10."


# ──────────────────────────────────────────────
# NOTES
# ──────────────────────────────────────────────

def notes_empty() -> str:
    return (
        "📝 <b>Заметок пока нет.</b>\n\n"
        "Создай первую! Заметки также автоматически появляются при выполнении Hard-заданий.\n"
        "Система записывает всё, что ты считаешь важным."
    )


def edit_choose() -> str:
    return "✏️ Выбери задание для редактирования:"


def edit_difficulty_prompt() -> str:
    return "🎯 Выбери новую сложность:\n\nНаграда будет пересчитана автоматически."


def edit_deadline_prompt() -> str:
    return "📅 Выбери новый дедлайн:"


def notes_none_more() -> str:
    return "📝 Больше заметок нет. Архив пуст."


def notes_list(text: str) -> str:
    return text


def notes_detail(date: str, quest: str, text: str) -> str:
    return f"📝 <b>Заметка от {date}</b>{quest}\n\n{text}"


def notes_new_start() -> str:
    return (
        "📝 <b>Новая запись в дневнике</b>\n\n"
        "Напиши текст заметки или отправь фото с подписью.\n"
        "Система сохранит это в архиве."
    )


def notes_saved() -> str:
    return "✅ <b>Заметка сохранена!</b> Информация зафиксирована в архиве Системы."


def notes_photo_text() -> str:
    return "Фото-подтверждение"


# ──────────────────────────────────────────────
# ERRORS
# ──────────────────────────────────────────────

def error_access() -> str:
    return "❌ Ошибка доступа. Система блокирует запрос."


def error_not_found() -> str:
    return "❌ Объект не найден в архиве Системы."


def error_invalid_id() -> str:
    return "❌ Некорректный идентификатор. Система не может обработать запрос."


def error_task_gone() -> str:
    return "❌ Это задание уже недоступно. Возможно, оно уже завершено или удалено."


def error_quest_fail() -> str:
    return "❌ Ошибка при завершении задания. Система сбита с толку."


def error_navigation() -> str:
    return "❌ Ошибка навигации. Система не может определить направление."


# ──────────────────────────────────────────────
# PETS
# ──────────────────────────────────────────────

def pets_empty() -> str:
    return (
        "🐾 Питомцев пока нет.\n"
        "Загляни на рынок — возможно, кто-то ждёт именно тебя."
    )


def pets_list(text: str) -> str:
    return f"<b>🐾 Твои питомцы:</b>\n\n{text}"


def companion_found(name: str, description: str) -> str:
    return (
        f"🐾 <b>Новый спутник!</b>\n\n"
        f"{name} присоединился к тебе в награду.\n"
        f"{description}"
    )


def secret_pet_found(name: str, description: str) -> str:
    return (
        f"🐌 <b>Секретный питомец найден!</b>\n\n"
        f"«{name}» присоединился к тебе.\n"
        f"{description}"
    )


def note_to_quest_choose() -> str:
    return "📝 Выбери квест, к которому хочешь добавить заметку:"


def note_to_quest_start() -> str:
    return "📝 <b>Заметка к квесту</b>\n\nНапиши текст заметки:"


def no_active_quests_for_note() -> str:
    return "📭 Нет активных квестов для заметки."


def choose_action() -> str:
    return (
        "⚡ <b>Главное меню</b>\n\n"
        "Выбери раздел:"
    )


def main_menu_text() -> str:
    return (
        "⚡ <b>Главное меню</b>\n\n"
        "📋 <b>Квесты</b> — управление заданиями\n"
        "🧝‍♀️ <b>Профиль</b> — статистика и достижения\n"
        "🛒 <b>Магазин</b> — зелья, питомцы, свитки\n"
        "🐾 <b>Питомцы</b> — твои спутники\n"
        "📝 <b>Заметки</b> — записки Системе\n"
        "⚙️ <b>Настройки</b> — сложность и уведомления"
    )

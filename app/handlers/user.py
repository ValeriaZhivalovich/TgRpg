import os
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.request import *
import app.keyboards as kb

router = Router()


class Reg(StatesGroup):
    name = State()
    last_name = State()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user = await set_user(message.from_user.id)
    if user:
        await message.answer(
            f"С возвращением, <b>{user.username}!</b> 🎮\n"
            "Вы готовы продолжить своё путешествие?",
            parse_mode="HTML",
            reply_markup=kb.menu_kb
        )
        await state.clear()
    else:
        await message.answer(
            f"Приветствую, путник {message.from_user.username}! 🌟\n\n"
            "Я — Хранитель Гильдии Приключений. Чтобы начать ваш путь, "
            "мне нужно узнать немного о вас.\n\n"
            "Как вас <b>зовут</b>? 📝",
            parse_mode="HTML"
        )
        await state.set_state(Reg.name)

@router.message(Reg.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Reg.last_name)
    await message.answer(
        "Хорошо, запомнил ваше имя. Теперь скажите, какая у вас <b>фамилия</b>? 🏛️",
        parse_mode="HTML"
    )

@router.message(Reg.last_name)
async def reg_lastname(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    data = await state.get_data()
    await add_user(
        tg_id=message.from_user.id,
        name=data['name'],
        last_name=data['last_name'],
    )
    await state.clear()
    await message.answer(
        "Отлично! Теперь вы официально зарегистрированы как искатель приключений! 🎉\n"
        "Ваше имя занесено в Базу Гильдии. Что дальше?\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=kb.menu_kb
    )



# === Главное меню ===
@router.message(F.text == "🧝‍♀️ Профиль")
async def show_profile(message: Message):
    tg_id = message.from_user.id

    user = await set_user(tg_id)

    if not user:
        await message.answer("❌ Ваш профиль не найден. Используйте /start чтобы зарегистрироваться.")
        return

    stats_text = (
        f"🧙‍♂️ <b>Ваш герой</b>\n"
        f"Уровень: {user.level}\n"
        f"⚡ Энергия: {user.energy}/50\n"
        f"❤ Здоровье: {user.hp}/100\n"
        f"✨ Опыт: {user.xp}/{user.level * 100}\n"
        f"💰 Золото: {user.gold}"
    )

    await message.answer(stats_text,parse_mode="HTML", reply_markup=kb.profile_kb)


# === Подменю профиля ===
@router.callback_query(F.data == 'skills')
async def show_skills(call: CallbackQuery):
    await call.message.edit_text("🔮 Здесь будут ваши навыки...")


@router.callback_query(F.data == 'achievements')
async def show_achievements(call: CallbackQuery):
    await call.message.edit_text("🏆 Вы пока ничего не достигли...")


@router.callback_query(F.data == 'inventory')
async def show_inventory(call: CallbackQuery):
    tg_id = call.from_user.id

    async with async_session() as session:
        user = await set_user(tg_id)

        if not user:
            await call.message.answer("❌ Ваш профиль не найден. Используйте /start чтобы зарегистрироваться.")
            return

        inventory_items = await get_inventory(user.id)

        if not inventory_items:
            await call.message.edit_text("🎒 Ваш инвентарь пуст...")
            return

        inventory_text = "🎒 <b>Ваш инвентарь:</b>\n\n"
        for inv_item in inventory_items:
            item = inv_item.item  # ✅ Теперь это Item, а inv_item — InventoryItem
            status = "одет" if inv_item.equipped else "не одет"
            inventory_text += (
                f"▫️ <b>{item.name}</b> x{inv_item.quantity}\n"
                f"   — {item.description or 'Без описания'}\n"
                f"   — Статус: {status}\n\n"
            )

    await call.message.edit_text(inventory_text, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == 'my_pets')
async def show_pets(call: CallbackQuery):
    await call.message.edit_text("🐶 У вас нет питомцев...")


# === Кнопка "Список задач" ===
@router.message(F.text == "📜 Список задач")
async def show_tasks_menu(message: Message):
    await message.answer("📋 Выберите тип задач:", reply_markup=kb.tasks_kb)


# === Подменю задач ===
@router.callback_query(F.data == 'active_task')
async def show_active_tasks(call: CallbackQuery):
    await call.message.edit_text("✅ Активные задачи:\n— Почистить зубы\n— Сделать зарядку", reply_markup=kb.active_task_kb)


@router.callback_query(F.data == 'complite_task')
async def show_completed_tasks(call: CallbackQuery):
    await call.message.edit_text("❌ Завершённых задач пока нет.", reply_markup=kb.tasks_kb)


@router.callback_query(F.data == 'creste_task')
async def create_new_task(call: CallbackQuery):
    await call.message.edit_text("📝 Введите название новой задачи...")


# === Подменю активной задачи ===
@router.callback_query(F.data == 'delete_active_task')
async def delete_task(call: CallbackQuery):
    await call.message.edit_text("🗑 Задача удалена.", reply_markup=kb.tasks_kb)


@router.callback_query(F.data == 'change_active_task')
async def edit_task(call: CallbackQuery):
    await call.message.edit_text("✍️ Введите новое описание задачи...")


# === Кнопка "Рынок" ===
@router.message(F.text == "⚖️ Рынок")
async def show_market(message: Message):
    await message.answer("🛍 Добро пожаловать на рынок!", reply_markup=kb.market_kb)


# === Подменю рынка ===
@router.callback_query(F.data == 'market_potion')
async def show_potions(call: CallbackQuery):
    await call.message.edit_text("🧪 Зелья:\n— Зелье энергии (+10)\n— Зелье здоровья (+10)")


@router.callback_query(F.data == 'market_pets')
async def show_pets_shop(call: CallbackQuery):
    await call.message.edit_text("🐶 Питомцы:\n— Котик\n— Щенок\n— Черепашка")


@router.callback_query(F.data == 'market_ticket')
async def show_tickets(call: CallbackQuery):
    await call.message.edit_text("🎟 Билеты:\n— На турнир\n— В подземелье")


# === Кнопка "Боссы/Квесты" ===
@router.message(F.text == "⚔️ Боссы/Квесты")
async def show_bosses(message: Message):
    await message.answer("👹 Здесь будут боссы и квесты!")


# === Кнопка "Настройки" ===
@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    await message.answer("🛠 Здесь будут настройки!")




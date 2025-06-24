import os
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.request import set_user, add_user
from app.database.logic import complete_task, add_skill_xp 
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
            f"С возвращением, <b>{user.name}!</b> 🎮\n"
            "Вы готовы продолжить своё путешествие?",
            parse_mode="HTML",
            reply_markup=kb.menu
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
        reply_markup=kb.menu
    )

@router.message(Command("complete"))
async def cmd_complete(message: types.Message, session: AsyncSession):
    task_id = int(message.text.split()[1])  # Получаем ID задачи из сообщения
    result = await complete_task(session, task_id)
    await message.answer(result)

@router.message(Command("add_skill"))
async def cmd_add_skill(message: types.Message, session: AsyncSession):
    _, skill_name, xp = message.text.split()
    xp = int(xp)
    result = await add_skill_xp(session, message.from_user.id, skill_name, xp)
    await message.answer(result)




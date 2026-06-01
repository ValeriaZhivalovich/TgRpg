from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.database.request import get_user, get_notes, get_note_by_id, create_note, check_achievements
import app.keyboards as kb
import app.texts as txt

router = Router()


NOTES_PER_PAGE = 5


class NewNote(StatesGroup):
    text = State()


@router.message(Command('notes'))
async def cmd_notes(message: Message):
    await show_notes_page(message, 0)


@router.message(F.text == "📝 Заметки")
async def notes_button(message: Message):
    await show_notes_page(message, 0)


def build_notes_text_and_buttons(notes, page: int, has_more: bool):
    text = "📝 <b>Твои заметки:</b>\n\n"
    for i, note in enumerate(notes, 1 + page * NOTES_PER_PAGE):
        date = note.created_at.strftime("%d.%m %H:%M")
        preview = note.text[:60] + "..." if len(note.text) > 60 else note.text
        quest_title = f" [{note.quest.title}]" if note.quest else ""
        photo_mark = " 📷" if note.photo_id else ""
        text += f"{i}. <b>{date}</b>{quest_title}{photo_mark}\n   {preview}\n\n"

    text += "🔍 Нажми на номер, чтобы прочитать полностью."

    buttons = []
    for j, note in enumerate(notes, 1 + page * NOTES_PER_PAGE):
        buttons.append([InlineKeyboardButton(text=f"{j}", callback_data=f"note_{note.id}_{page}")])

    buttons.append([InlineKeyboardButton(text="✏️ Новая заметка", callback_data='new_note')])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀ Назад", callback_data=f"notes_page_{page - 1}"))
    if has_more:
        nav.append(InlineKeyboardButton(text="Далее ▶", callback_data=f"notes_page_{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="🏠 Меню", callback_data='notes_menu')])
    return text, buttons


async def show_notes_page(message: Message, page: int):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(txt.profile_not_found())
        return

    notes = await get_notes(user.id, limit=NOTES_PER_PAGE + 1, offset=page * NOTES_PER_PAGE)
    if not notes:
        if page == 0:
            empty_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Создать заметку", callback_data='new_note')],
                [InlineKeyboardButton(text="🏠 Меню", callback_data='notes_menu')],
            ])
            await message.answer(txt.notes_empty(), parse_mode="HTML", reply_markup=empty_kb)
        else:
            await message.answer(txt.notes_none_more())
        return

    has_more = len(notes) > NOTES_PER_PAGE
    notes = notes[:NOTES_PER_PAGE]
    text, buttons = build_notes_text_and_buttons(notes, page, has_more)
    await message.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith('notes_page_'))
async def notes_page_cb(call: CallbackQuery):
    try:
        page = int(call.data.replace('notes_page_', ''))
    except ValueError:
        await call.message.edit_text(txt.error_navigation())
        await call.answer()
        return

    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.error_access())
        await call.answer()
        return

    notes = await get_notes(user.id, limit=NOTES_PER_PAGE + 1, offset=page * NOTES_PER_PAGE)
    if not notes:
        await call.message.edit_text(txt.notes_none_more())
        await call.answer()
        return

    has_more = len(notes) > NOTES_PER_PAGE
    notes = notes[:NOTES_PER_PAGE]
    text, buttons = build_notes_text_and_buttons(notes, page, has_more)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()


@router.callback_query(F.data.startswith('note_'))
async def note_detail_cb(call: CallbackQuery):
    parts = call.data.split('_')
    try:
        note_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        await call.message.edit_text(txt.error_invalid_id())
        await call.answer()
        return

    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.error_access())
        await call.answer()
        return

    note = await get_note_by_id(note_id, user_id=user.id)
    if not note:
        await call.message.edit_text(txt.error_not_found())
        await call.answer()
        return

    date = note.created_at.strftime("%d.%m.%Y %H:%M")
    quest_info = f"\n📌 Квест: {note.quest.title}" if note.quest else ""

    text = txt.notes_detail(date, quest_info, note.text)

    buttons = [
        [InlineKeyboardButton(text="◀ Назад к списку", callback_data=f"notes_page_{page}")],
    ]

    if note.photo_id:
        await call.message.delete()
        await call.message.answer_photo(
            photo=note.photo_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    else:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()


# === New standalone note ===

@router.callback_query(F.data == 'new_note')
async def new_note_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(NewNote.text)
    await call.message.edit_text(txt.notes_new_start(), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data='new_note_cancel')]
        ])
    )
    await call.answer()


@router.message(NewNote.text)
async def new_note_text(message: Message, state: FSMContext):
    if not message.text and not message.photo:
        await message.answer(txt.error_invalid_id())
        return

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(txt.error_access())
        await state.clear()
        return

    text = message.text or message.caption or txt.notes_photo_text()
    photo_id = message.photo[-1].file_id if message.photo else None

    await create_note(user_id=user.id, text=text, photo_id=photo_id)
    await state.clear()
    await message.answer(txt.notes_saved(), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Все заметки", callback_data='notes_all')],
            [InlineKeyboardButton(text="🏠 Меню", callback_data='notes_menu')],
        ])
    )

    new_ach = await check_achievements(user.id)
    for ach in new_ach:
        await message.answer(
            txt.new_achievement(ach.name, ach.description),
            parse_mode="HTML"
        )


@router.callback_query(F.data == 'new_note_cancel')
async def new_note_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(txt.choose_action(), reply_markup=kb.menu_kb)
    await call.answer()


@router.callback_query(F.data == 'notes_all')
async def notes_all_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_notes_page(call.message, 0)


@router.callback_query(F.data == 'notes_menu')
async def notes_back_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(txt.choose_action(), reply_markup=kb.menu_kb)
    await call.answer()

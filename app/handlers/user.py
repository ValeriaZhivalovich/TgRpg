import html
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.database.request import (
    get_user, add_user, get_character, award_pet,
    get_all_achievements, get_user_achievements,
    update_default_difficulty, get_achievement_progress,
    set_notifications_pref, get_notifications_pref,
    get_active_tasks, get_user_pets, get_user_skills,
    get_inventory, CLASS_STATS,
)
from app.handlers.quests import build_task_status
import app.keyboards as kb
import app.texts as txt

router = Router()


class Reg(StatesGroup):
    name = State()
    last_name = State()
    class_name = State()
    avatar = State()


def _profile_text(character) -> str:
    safe_name = html.escape(character.name)
    avatar = character.avatar or "🧝"
    cls = character.class_name
    max_hp = CLASS_STATS.get(cls, {}).get('hp', 100)
    max_ep = CLASS_STATS.get(cls, {}).get('energy', 50)
    xp_needed = character.level * 100
    return (
        f"{avatar} <b>{safe_name}</b> — {cls}\n\n"
        f"Уровень: {character.level}  ✨ {character.xp}/{xp_needed}\n"
        f"❤️ HP: {character.hp}/{max_hp}  ⚡ EP: {character.energy}/{max_ep}\n"
        f"💰 Золото: {character.gold}\n"
        f"🎯 Режим: {character.difficulty}"
    )


# === Start / Menu ===

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    user = await get_user(message.from_user.id)
    if user:
        character = await get_character(user.id)
        await message.answer(
            txt.start_return(html.escape(character.name)),
            parse_mode="HTML", reply_markup=kb.menu_kb
        )
        await message.answer(txt.main_menu_text(), parse_mode="HTML")
    else:
        await message.answer(
            txt.start_new(message.from_user.username),
            parse_mode="HTML"
        )
        await state.set_state(Reg.name)


@router.message(Command('menu'))
async def cmd_menu(message: Message):
    await message.answer(txt.main_menu_text(), parse_mode="HTML", reply_markup=kb.menu_kb)


@router.callback_query(F.data == 'main_menu')
async def main_menu_cb(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(txt.main_menu_text(), parse_mode="HTML", reply_markup=kb.menu_kb)
    await call.answer()


@router.callback_query(F.data == 'set_back')
async def settings_back_cb(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(txt.main_menu_text(), parse_mode="HTML", reply_markup=kb.menu_kb)
    await call.answer()


# === Registration ===

@router.message(Reg.name)
async def reg_name(message: types.Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer(txt.reg_name_long())
        return
    await state.update_data(name=message.text)
    await state.set_state(Reg.last_name)
    await message.answer(txt.reg_ask_lastname(), parse_mode="HTML", reply_markup=kb.skip_kb)


@router.message(Reg.last_name)
async def reg_lastname(message: types.Message, state: FSMContext):
    if len(message.text) > 150:
        await message.answer(txt.reg_lastname_long())
        return
    await state.update_data(last_name=message.text)
    await ask_class(message, state)


@router.callback_query(Reg.last_name, F.data == 'skip')
async def reg_skip_lastname(call: CallbackQuery, state: FSMContext):
    await state.update_data(last_name=None)
    await call.message.delete()
    await ask_class(call.message, state)
    await call.answer()


async def ask_class(message: types.Message, state: FSMContext):
    await state.set_state(Reg.class_name)
    await message.answer(txt.reg_ask_class(), parse_mode="HTML", reply_markup=kb.class_kb)


@router.callback_query(Reg.class_name, F.data.startswith('class_'))
async def reg_class(call: CallbackQuery, state: FSMContext):
    class_name = call.data.replace('class_', '')
    await state.update_data(class_name=class_name)
    await state.set_state(Reg.avatar)
    await call.message.edit_text(txt.reg_ask_avatar(), parse_mode="HTML", reply_markup=kb.skip_kb)
    await call.answer()


@router.message(Reg.avatar)
async def reg_avatar(message: types.Message, state: FSMContext):
    avatar = message.text.strip()
    if len(avatar) > 10:
        await message.answer(txt.reg_avatar_long())
        return
    await state.update_data(avatar=avatar)
    await show_reg_summary(message, state)


@router.callback_query(Reg.avatar, F.data == 'skip')
async def reg_skip_avatar(call: CallbackQuery, state: FSMContext):
    await state.update_data(avatar=None)
    await call.message.delete()
    await show_reg_summary(call.message, state)
    await call.answer()


async def show_reg_summary(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name', '???')
    last_name = data.get('last_name')
    class_name = data.get('class_name', 'Авантюрист')
    avatar = data.get('avatar')
    stats = CLASS_STATS.get(class_name, CLASS_STATS['Авантюрист'])
    if not avatar:
        avatar = stats['avatar']
    full_name = f"{name} {last_name}" if last_name else name
    summary = txt.reg_summary(avatar, full_name, class_name, stats['hp'], stats['energy'], stats['gold'])
    await state.update_data(avatar=avatar, full_name=full_name)
    await message.answer(summary, parse_mode="HTML", reply_markup=kb.confirm_reg_kb)


@router.callback_query(F.data == 'reg_confirm')
async def reg_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await add_user(
        tg_id=call.from_user.id,
        name=data['name'],
        last_name=data.get('last_name'),
        class_name=data['class_name'],
        avatar=data.get('avatar'),
    )
    await state.clear()
    starter_pet = await award_pet(user.id, 1)
    pet_note = ""
    if starter_pet:
        pet_note = f"\n\n🐾 Стартовый питомец «{starter_pet.name}» уже ждёт тебя!"
    await call.message.edit_text(
        txt.reg_confirm(data['full_name'], data['class_name']) + pet_note,
        parse_mode="HTML"
    )
    await call.message.answer(txt.main_menu_text(), parse_mode="HTML", reply_markup=kb.menu_kb)
    await call.answer()


@router.callback_query(F.data == 'reg_restart')
async def reg_restart(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(txt.start_new(call.from_user.username), parse_mode="HTML")
    await state.set_state(Reg.name)
    await call.answer()


# === Profile ===

@router.message(F.text == "🧝‍♀️ Профиль")
@router.message(Command('profile'))
async def profile_show(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(txt.profile_err())
        return
    character = await get_character(user.id)
    await message.answer(_profile_text(character), parse_mode="HTML", reply_markup=kb.profile_kb)


# === Achievements ===

@router.callback_query(F.data == 'achievements')
async def show_achievements(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return
    all_ach = await get_all_achievements()
    user_ach = await get_user_achievements(user.id)
    earned_ids = {ua.achievement_id for ua in user_ach}
    progress = await get_achievement_progress(user.id)
    lines = ["<b>🏆 Достижения</b>\n"]
    for ach in all_ach:
        icon = "✅" if ach.id in earned_ids else ach.emoji
        if ach.id in earned_ids:
            ua = next(u for u in user_ach if u.achievement_id == ach.id)
            lines.append(f"{icon} <b>{ach.name}</b> — {ua.achieved_at.strftime('%d.%m.%Y')}")
        else:
            cur = progress.get(ach.condition_type, 0)
            lines.append(f"{icon} {ach.name} — <i>{cur}/{ach.condition_value}</i>")
    await call.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=kb.main_menu_kb())
    await call.answer()


# === Tasks / Quests ===

@router.message(F.text == "📋 Квесты")
async def quests_menu(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(txt.profile_err())
        return
    tasks = await get_active_tasks(user.id)
    if not tasks:
        await message.answer(txt.active_empty(), parse_mode="HTML", reply_markup=kb.tasks_kb)
        return
    task_lines = "\n".join(f"{i}. {build_task_status(t)}" for i, t in enumerate(tasks, 1))
    await message.answer(txt.active_list(task_lines), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Старт", callback_data='start_task_list'),
             InlineKeyboardButton(text="✅ Завершить", callback_data='finish_task')],
            [InlineKeyboardButton(text="❌ Удалить", callback_data='delete_active_task'),
             InlineKeyboardButton(text="📝 Заметка", callback_data='note_quest_list')],
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data='edit_task_list'),
             kb.main_menu_btn],
        ]))


# === Settings ===

@router.message(F.text == "⚙️ Настройки")
async def settings_open(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(txt.profile_err())
        return
    notif = await get_notifications_pref(message.from_user.id)
    await message.answer(txt.settings_menu(user.mode, notif), parse_mode="HTML", reply_markup=kb.settings_kb)


@router.callback_query(F.data.startswith('settings_diff_'))
async def settings_set_difficulty(call: CallbackQuery):
    diff = call.data.replace('settings_diff_', '')
    await update_default_difficulty(call.from_user.id, diff)
    await call.message.edit_text(txt.settings_updated(diff), parse_mode="HTML", reply_markup=kb.settings_kb)
    await call.answer()


@router.callback_query(F.data == 'notif_toggle')
async def settings_toggle_notifications(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return
    current = await get_notifications_pref(call.from_user.id)
    await set_notifications_pref(call.from_user.id, not current)
    status = txt.notifications_on() if not current else txt.notifications_off()
    await call.message.edit_text(status, parse_mode="HTML", reply_markup=kb.settings_kb)
    await call.answer()


# === Shop ===

@router.message(F.text == "🛒 Магазин")
async def shop_menu(message: Message):
    await message.answer(txt.market_welcome(), parse_mode="HTML", reply_markup=kb.market_kb)


# === Pets ===

@router.message(F.text == "🐾 Питомцы")
async def pets_menu(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(txt.profile_err())
        return
    pets = await get_user_pets(user.id)
    if not pets:
        await message.answer(txt.pets_empty(), parse_mode="HTML", reply_markup=kb.pets_kb)
        return
    lines = []
    for up in pets:
        active_tag = " ⚡" if up.active else ""
        pet_name = up.pet.name if up.pet else "???"
        pet_emoji = up.pet.emoji if up.pet and up.pet.emoji else "🐾"
        lines.append(f"{pet_emoji} <b>{pet_name}</b> lv.{up.level} xp:{up.xp}{active_tag}")
    await message.answer(
        txt.pets_list("\n".join(lines)),
        parse_mode="HTML", reply_markup=kb.pets_kb
    )


@router.callback_query(F.data == 'my_pets')
async def my_pets_cb(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return
    pets = await get_user_pets(user.id)
    if not pets:
        await call.message.edit_text(txt.pets_empty(), parse_mode="HTML", reply_markup=kb.pets_kb)
        await call.answer()
        return
    lines = []
    for up in pets:
        active_tag = " ⚡" if up.active else ""
        pet_name = up.pet.name if up.pet else "???"
        pet_emoji = up.pet.emoji if up.pet and up.pet.emoji else "🐾"
        lines.append(f"{pet_emoji} <b>{pet_name}</b> lv.{up.level} xp:{up.xp}{active_tag}")
    await call.message.edit_text(
        txt.pets_list("\n".join(lines)),
        parse_mode="HTML", reply_markup=kb.pets_kb
    )
    await call.answer()


# === notes handled in notes.py via reply button ===


# === Placeholder handlers for unhandled callbacks ===

@router.callback_query(F.data == 'skills')
async def skills_cb(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return
    skills = await get_user_skills(user.id)
    if not skills:
        await call.message.edit_text(txt.skills_empty(), parse_mode="HTML", reply_markup=kb.profile_kb)
        await call.answer()
        return
    lines = ["🔮 <b>Твои навыки:</b>"]
    for us in skills:
        skill_name = us.skill.skill_name if us.skill else f"ID:{us.skill_id}"
        lines.append(f"• {skill_name} — ур.{us.level} ({us.xp} XP)")
    await call.message.edit_text(
        "\n".join(lines), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[kb.main_menu_btn]])
    )
    await call.answer()


@router.callback_query(F.data == 'inventory')
async def inventory_cb(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return
    items = await get_inventory(user.id)
    if not items:
        await call.message.edit_text(txt.inventory_empty(), parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[kb.main_menu_btn]]))
        await call.answer()
        return
    lines = ["🎒 <b>Инвентарь:</b>"]
    for inv in items:
        item_name = inv.item.name if inv.item else "???"
        lines.append(f"• {item_name} x{inv.quantity}")
    await call.message.edit_text(
        "\n".join(lines), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[kb.main_menu_btn]])
    )
    await call.answer()


@router.callback_query(F.data == 'stats_charts')
async def stats_charts_cb(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return
    from app.stats import chart_completed_daily, chart_xp_daily, chart_difficulty_pie, chart_skills
    charts = [
        await chart_completed_daily(user.id),
        await chart_xp_daily(user.id),
        await chart_difficulty_pie(user.id),
        await chart_skills(user.id),
    ]
    media = types.MediaGroup()
    for buf in charts:
        media.attach_photo(types.BufferedInputFile(buf.read(), filename="chart.png"))
    await call.message.delete()
    await call.message.answer_media_group(media=media)
    await call.message.answer(txt.main_menu_text(), parse_mode="HTML", reply_markup=kb.menu_kb)
    await call.answer()


# === Market placeholders ===

@router.callback_query(F.data.startswith('market_'))
async def market_placeholder(call: CallbackQuery):
    await call.message.edit_text(txt.market_welcome(), parse_mode="HTML", reply_markup=kb.market_kb)
    await call.answer()

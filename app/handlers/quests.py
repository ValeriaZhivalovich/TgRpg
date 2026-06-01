from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.database.request import (
    get_user, get_character, create_task, get_active_tasks, get_completed_tasks,
    get_task_by_id, get_skill_by_id, start_task, complete_task, complete_recurring_task, delete_task,
    get_all_skills, add_xp_and_gold, add_skill_xp, create_note,
    get_timer_remaining, is_completed_today, can_complete,
    check_achievements, give_pet_quest_xp, award_pet, get_pet_by_achievement,
    get_user_pets, update_task_fields,
)
from app.constants import (
    Difficulty, TaskType, TaskStatus,
    REWARD_MAP, DIFF_EMOJIS, DIFF_NAMES, TYPE_NAMES,
)
import app.keyboards as kb
import app.texts as txt
from datetime import datetime, timedelta

router = Router()


# === Cancel FSM ===

@router.message(Command('cancel'))
async def cmd_cancel(message: Message, state: FSMContext):
    if await state.get_state() is None:
        await message.answer(txt.cancel_none())
        return
    await state.clear()
    await message.answer(txt.cancel_ok(), reply_markup=kb.menu_kb)


# === Create Quest FSM ===

class CreateQuest(StatesGroup):
    title = State()
    description = State()
    difficulty = State()
    quest_type = State()
    skill = State()
    deadline = State()
    timer = State()
    confirm = State()


class HardNote(StatesGroup):
    waiting_note = State()
    task_id = State()


class QuestNote(StatesGroup):
    waiting_text = State()
    task_id = State()


@router.callback_query(F.data == 'create_task')
async def quest_create_start_cb(call: CallbackQuery, state: FSMContext):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return
    await state.update_data(default_difficulty=user.mode)
    await call.message.edit_text(txt.quest_create_start(), parse_mode="HTML")
    await state.set_state(CreateQuest.title)
    await call.answer()


@router.message(Command('new_quest'))
async def quest_create_start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(txt.profile_err())
        return
    await state.update_data(default_difficulty=user.mode)
    await message.answer(txt.quest_create_start(), parse_mode="HTML")
    await state.set_state(CreateQuest.title)


@router.message(CreateQuest.title)
async def quest_title(message: Message, state: FSMContext):
    if len(message.text) > 100:
        await message.answer(txt.quest_title_long())
        return
    data = await state.get_data()
    await state.update_data(title=message.text)
    await state.set_state(CreateQuest.description)
    await message.answer(txt.quest_ask_description(), parse_mode="HTML", reply_markup=kb.skip_kb)


@router.message(CreateQuest.description)
async def quest_description(message: Message, state: FSMContext):
    if len(message.text) > 255:
        await message.answer(txt.quest_description_long())
        return
    await state.update_data(description=message.text)
    await ask_difficulty(message, state)


@router.callback_query(CreateQuest.description, F.data == 'skip')
async def quest_skip_description(call: CallbackQuery, state: FSMContext):
    await state.update_data(description=None)
    await call.message.delete()
    await ask_difficulty(call.message, state)
    await call.answer()


async def ask_difficulty(message: Message, state: FSMContext):
    data = await state.get_data()
    default_diff = data.get('default_difficulty', 'easy')
    await state.update_data(difficulty=default_diff)
    await state.set_state(CreateQuest.difficulty)
    await message.answer(txt.quest_ask_difficulty(default_diff), parse_mode="HTML", reply_markup=kb.quest_difficulty_kb)


@router.callback_query(CreateQuest.difficulty, F.data.in_({'qdiff_easy', 'qdiff_normal', 'qdiff_hard'}))
async def quest_difficulty(call: CallbackQuery, state: FSMContext):
    diff_map = {'qdiff_easy': 'easy', 'qdiff_normal': 'normal', 'qdiff_hard': 'hard'}
    difficulty = diff_map[call.data]
    await state.update_data(difficulty=difficulty)
    await state.set_state(CreateQuest.quest_type)
    await call.message.edit_text(txt.quest_ask_type(), parse_mode="HTML", reply_markup=kb.quest_type_kb)
    await call.answer()


@router.callback_query(CreateQuest.quest_type, F.data.in_({'qtype_once', 'qtype_repeat'}))
async def quest_type(call: CallbackQuery, state: FSMContext):
    type_map = {'qtype_once': 'одноразовая', 'qtype_repeat': 'повторяющаяся'}
    quest_type = type_map[call.data]
    await state.update_data(quest_type=quest_type)
    await state.set_state(CreateQuest.skill)

    skills = await get_all_skills()
    skill_buttons = [
        [InlineKeyboardButton(text=s.skill_name, callback_data=f"qskill_{s.id}")]
        for s in skills
    ]
    skill_kb = InlineKeyboardMarkup(inline_keyboard=skill_buttons)
    await call.message.edit_text(txt.quest_ask_skill(), parse_mode="HTML", reply_markup=skill_kb)
    await call.answer()


@router.callback_query(CreateQuest.skill, F.data.startswith('qskill_'))
async def quest_skill(call: CallbackQuery, state: FSMContext):
    try:
        skill_id = int(call.data.replace('qskill_', ''))
    except ValueError:
        await call.message.edit_text(txt.error_invalid_id())
        await call.answer()
        return
    await state.update_data(skill_id=skill_id)
    await state.set_state(CreateQuest.deadline)
    await call.message.edit_text(txt.quest_ask_deadline(), parse_mode="HTML", reply_markup=kb.quest_deadline_kb)
    await call.answer()


@router.callback_query(CreateQuest.deadline, F.data.in_({'qdeadline_skip', 'qdeadline_1', 'qdeadline_3', 'qdeadline_7'}))
async def quest_deadline(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    title = data['title']
    difficulty = data['difficulty']
    quest_type = data['quest_type']
    description = data.get('description')

    xp, gold = REWARD_MAP.get(difficulty, (10, 5))

    deadline = None
    deadline_text = "🚫 Без дедлайна"
    if call.data != 'qdeadline_skip':
        try:
            days = int(call.data.replace('qdeadline_', ''))
        except ValueError:
            await call.message.edit_text(txt.error_invalid_id())
            await call.answer()
            return
        deadline = datetime.now() + timedelta(days=days)
        deadline_text = f"📅 {days} дн."

    skill_id = data.get('skill_id')
    skill_name = "🎯 Без навыка"
    if skill_id:
        skill = await get_skill_by_id(skill_id)
        if skill:
            skill_name = skill.skill_name

    await state.update_data(deadline=deadline)
    await state.set_state(CreateQuest.timer)
    await call.message.edit_text(txt.quest_ask_timer(), parse_mode="HTML", reply_markup=kb.quest_timer_kb)
    await call.answer()


@router.callback_query(CreateQuest.timer, F.data.startswith('qtimer_'))
async def quest_timer(call: CallbackQuery, state: FSMContext):
    val = call.data.replace('qtimer_', '')
    if val == 'custom':
        await call.message.edit_text(txt.quest_timer_custom(), parse_mode="HTML")
        await state.set_state(CreateQuest.timer)
        return

    timer_min = int(val) if val != 'skip' else 0
    await _finish_quest_timer(call, state, timer_min)


@router.message(CreateQuest.timer)
async def quest_timer_custom(message: Message, state: FSMContext):
    try:
        timer_min = int(message.text.strip())
        if timer_min < 0 or timer_min > 180:
            await message.answer(txt.quest_timer_invalid())
            return
    except ValueError:
        await message.answer(txt.quest_timer_invalid())
        return
    await _finish_quest_timer(message, state, timer_min)


async def _finish_quest_timer(source, state, timer_min: int):
    await state.update_data(timer_minutes=timer_min)
    data = await state.get_data()
    title = data['title']
    difficulty = data['difficulty']
    quest_type = data['quest_type']
    description = data.get('description')

    base_xp, base_gold = REWARD_MAP.get(difficulty, (10, 5))
    bonus_xp = timer_min * 2
    bonus_gold = timer_min
    total_xp = base_xp + bonus_xp
    total_gold = base_gold + bonus_gold

    deadline_text = "🚫 Без дедлайна"
    if data.get('deadline'):
        days = (data['deadline'] - datetime.now()).days
        deadline_text = f"📅 {days} дн."

    skill_id = data.get('skill_id')
    skill_name = "🎯 Без навыка"
    if skill_id:
        skill = await get_skill_by_id(skill_id)
        if skill:
            skill_name = skill.skill_name

    timer_text = f"⏱ {timer_min} мин" if timer_min else "🚫 Без таймера"

    summary = txt.quest_summary(
        title, description or "",
        DIFF_NAMES.get(difficulty, difficulty),
        TYPE_NAMES.get(quest_type, quest_type),
        skill_name, deadline_text, total_xp, total_gold
    )
    summary += f"\n⏱ Таймер: {timer_text}"
    summary += f"\n\n<i>➕ бонус за таймер: +{bonus_xp}✨ +{bonus_gold}💰</i>" if timer_min else ""

    if isinstance(source, CallbackQuery):
        await source.message.edit_text(summary, parse_mode="HTML", reply_markup=kb.quest_confirm_kb)
        await source.answer()
    else:
        await source.answer(summary, parse_mode="HTML", reply_markup=kb.quest_confirm_kb)

    await state.set_state(CreateQuest.confirm)


@router.callback_query(CreateQuest.confirm, F.data == 'qconfirm_yes')
async def quest_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await state.clear()
        return

    task = await create_task(
        user_id=user.id,
        title=data['title'],
        difficulty=data['difficulty'],
        task_type=data['quest_type'],
        deadline=data.get('deadline'),
        skill_id=data.get('skill_id'),
        description=data.get('description'),
        timer_minutes=data.get('timer_minutes', 0),
    )
    await state.clear()

    hint = ""
    if data['quest_type'] == 'повторяющаяся':
        hint = txt.quest_recurring_hint()
    timer_min = data.get('timer_minutes', 0)
    if timer_min:
        hint += txt.quest_timer_hint(timer_min) if timer_min else ""
    if data['difficulty'] == 'hard':
        hint += txt.quest_hint_hard()

    skill_name = ""
    if data.get('skill_id'):
        skill = await get_skill_by_id(data['skill_id'])
        if skill:
            skill_name = f"\n🎯 Навык: {skill.skill_name}"

    emoji = DIFF_EMOJIS.get(data['difficulty'], '📋')

    await call.message.edit_text(
        txt.quest_accepted(emoji, data['title'], data.get('description') or "",
                           skill_name, hint),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(CreateQuest.confirm, F.data == 'qconfirm_no')
async def quest_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(txt.quest_cancelled())
    await call.answer()


# === Active tasks list with statuses ===

def build_task_status(task) -> str:
    emoji = DIFF_EMOJIS.get(task.difficulty, '📋')
    skill_tag = f" [{task.skill.skill_name}]" if task.skill_id and task.skill else ""
    desc_tag = " 📖" if task.description else ""

    if task.type == 'повторяющаяся':
        done_today = is_completed_today(task)
        streak_tag = f" 🔥x{task.streak}" if task.streak else ""
        if done_today:
            return f"{emoji} {task.title}{skill_tag}{desc_tag} ✅{streak_tag}"
        if not task.timer_minutes:
            return f"{emoji} {task.title}{skill_tag}{desc_tag}{streak_tag}"
        if not task.started_at:
            return f"{emoji} {task.title}{skill_tag}{desc_tag}  ⏹{streak_tag}"
        remaining = get_timer_remaining(task)
        if remaining > 0:
            return f"{emoji} {task.title}{skill_tag}{desc_tag}  ⏳ {remaining} мин{streak_tag}"
        return f"{emoji} {task.title}{skill_tag}{desc_tag}  ✅{streak_tag}"

    if not task.timer_minutes:
        return f"{emoji} {task.title}{skill_tag}{desc_tag}"
    if not task.started_at:
        return f"{emoji} {task.title}{skill_tag}{desc_tag}  ⏹"
    remaining = get_timer_remaining(task)
    if remaining > 0:
        return f"{emoji} {task.title}{skill_tag}{desc_tag}  ⏳ {remaining} мин"
    return f"{emoji} {task.title}{skill_tag}{desc_tag}  ✅"


@router.callback_query(F.data == 'active_task')
async def show_active_tasks(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        return

    tasks = await get_active_tasks(user.id)
    if not tasks:
        await call.message.edit_text(txt.active_empty(), parse_mode="HTML", reply_markup=kb.tasks_kb)
        return

    task_lines = ""
    for i, t in enumerate(tasks, 1):
        task_lines += f"{i}. {build_task_status(t)}\n"

    text = txt.active_list(task_lines)

    actions_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="▶️ Старт", callback_data='start_task_list'),
            InlineKeyboardButton(text="✅ Завершить", callback_data='finish_task'),
        ],
        [
            InlineKeyboardButton(text="❌ Удалить", callback_data='delete_active_task'),
            InlineKeyboardButton(text="📝 Заметка", callback_data='note_quest_list'),
        ],
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data='edit_task_list'),
        ],
    ])
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=actions_kb)
    await call.answer()


# === Start task (timer) ===

@router.callback_query(F.data == 'start_task_list')
async def start_task_list(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        return

    tasks = await get_active_tasks(user.id)
    startable = [t for t in tasks if t.timer_minutes and not t.started_at]
    if not startable:
        await call.message.edit_text(
            txt.start_none(),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ Назад к списку", callback_data='active_task')]
            ])
        )
        await call.answer()
        return

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"▶️ {t.title}", callback_data=f"start_{t.id}")]
        for t in startable
    ])
    await call.message.edit_text(txt.start_choose(), reply_markup=inline_kb)
    await call.answer()


@router.callback_query(F.data.startswith('start_'))
async def start_task_cb(call: CallbackQuery):
    try:
        task_id = int(call.data.replace('start_', ''))
    except ValueError:
        await call.message.edit_text(txt.error_invalid_id())
        await call.answer()
        return
    task = await get_task_by_id(task_id)
    if not task or task.status != 'active' or task.started_at:
        await call.message.edit_text(txt.start_already())
        await call.answer()
        return

    await start_task(task_id)
    timer_min = task.timer_minutes

    await call.message.edit_text(
        txt.timer_started(task.title, timer_min),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ К списку квестов", callback_data='active_task')]
        ])
    )
    await call.answer()


# === Complete task ===

@router.callback_query(F.data == 'finish_task')
async def finish_task_list(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        return

    tasks = await get_active_tasks(user.id)
    completable = [t for t in tasks if can_complete(t)]
    if not completable:
        await call.message.edit_text(
            txt.finish_none(),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ К списку квестов", callback_data='active_task')]
            ])
        )
        return

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ {t.title}", callback_data=f"done_{t.id}")]
        for t in completable
    ])
    await call.message.edit_text(txt.finish_choose(), reply_markup=inline_kb)
    await call.answer()


@router.message(Command('done'))
async def cmd_done(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(txt.profile_err())
        return

    tasks = await get_active_tasks(user.id)
    completable = [t for t in tasks if can_complete(t)]
    if not completable:
        await message.answer(txt.finish_none())
        return

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ {t.title}", callback_data=f"done_{t.id}")]
        for t in completable
    ])
    await message.answer(txt.finish_choose(), reply_markup=inline_kb)


@router.callback_query(F.data.startswith('done_'))
async def complete_task_cb(call: CallbackQuery, state: FSMContext):
    try:
        task_id = int(call.data.replace('done_', ''))
    except ValueError:
        await call.message.edit_text(txt.error_invalid_id())
        await call.answer()
        return
    task = await get_task_by_id(task_id)
    if not task or task.status != 'active':
        await call.message.edit_text(txt.error_task_gone())
        await call.answer()
        return

    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return

    if task.user_id != user.id:
        await call.message.edit_text(txt.finish_own())
        await call.answer()
        return

    if not can_complete(task):
        await call.message.edit_text(txt.finish_timer())
        await call.answer()
        return

    # Hard mode: ask for note/photo first
    if task.difficulty == 'hard':
        await state.update_data(hard_task_id=task_id)
        await state.set_state(HardNote.waiting_note)
        await call.message.edit_text(txt.finish_hard_ask(), parse_mode="HTML")
        await call.answer()
        return

    await complete_and_reward(call.message, task, user.id)
    await call.answer()


# === Hard mode: note/photo submission ===

@router.message(HardNote.waiting_note, F.photo)
async def hard_note_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data['hard_task_id']
    task = await get_task_by_id(task_id)

    if not task or task.status != 'active':
        await message.answer(txt.error_task_gone())
        await state.clear()
        return

    user = await get_user(message.from_user.id)
    if not user or task.user_id != user.id:
        await message.answer(txt.error_access())
        await state.clear()
        return

    caption = message.caption or txt.notes_photo_text()
    photo_id = message.photo[-1].file_id
    await create_note(user_id=user.id, text=caption, quest_id=task_id, photo_id=photo_id)
    await state.clear()
    await complete_and_reward(message, task, user.id)


@router.message(HardNote.waiting_note, F.text)
async def hard_note_text(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data['hard_task_id']
    task = await get_task_by_id(task_id)

    if not task or task.status != 'active':
        await message.answer(txt.error_task_gone())
        await state.clear()
        return

    user = await get_user(message.from_user.id)
    if not user or task.user_id != user.id:
        await message.answer(txt.error_access())
        await state.clear()
        return

    await create_note(user_id=user.id, text=message.text, quest_id=task_id)
    await state.clear()
    await complete_and_reward(message, task, user.id)


# === Edit quest ===

@router.callback_query(F.data == 'edit_task_list')
async def edit_task_list(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return

    tasks = await get_active_tasks(user.id)
    if not tasks:
        await call.message.edit_text(txt.active_empty(), parse_mode="HTML", reply_markup=kb.tasks_kb)
        await call.answer()
        return

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✏️ {t.title}", callback_data=f"edittask_{t.id}")]
        for t in tasks
    ])
    await call.message.edit_text(txt.edit_choose(), reply_markup=inline_kb)
    await call.answer()


@router.callback_query(F.data.startswith('edittask_'))
async def edit_task_menu(call: CallbackQuery):
    try:
        task_id = int(call.data.replace('edittask_', ''))
    except ValueError:
        await call.message.edit_text(txt.error_invalid_id())
        await call.answer()
        return

    task = await get_task_by_id(task_id)
    if not task:
        await call.message.edit_text(txt.error_task_gone())
        await call.answer()
        return

    user = await get_user(call.from_user.id)
    if not user or task.user_id != user.id:
        await call.message.edit_text(txt.error_access())
        await call.answer()
        return

    desc = f"\n📖 {task.description}" if task.description else ""
    deadline_str = task.deadline.strftime("%d.%m.%y") if task.deadline else "🚫 нет"
    text = (
        f"✏️ <b>{task.title}</b>{desc}\n\n"
        f"🎯 Сложность: {DIFF_NAMES.get(task.difficulty, task.difficulty)}\n"
        f"📅 Дедлайн: {deadline_str}"
    )

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Сложность", callback_data=f"editdiff_{task.id}")],
        [InlineKeyboardButton(text="📅 Дедлайн", callback_data=f"editdead_{task.id}")],
        [InlineKeyboardButton(text="◀ Назад", callback_data='edit_task_list')],
    ])
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=inline_kb)
    await call.answer()


@router.callback_query(F.data.startswith('editdiff_'))
async def edit_task_difficulty(call: CallbackQuery):
    task_id = int(call.data.replace('editdiff_', ''))
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌟 Easy", callback_data=f"setdiff_{task_id}_easy"),
            InlineKeyboardButton(text="⚡ Normal", callback_data=f"setdiff_{task_id}_normal"),
            InlineKeyboardButton(text="🔥 Hard", callback_data=f"setdiff_{task_id}_hard"),
        ]
    ])
    await call.message.edit_text(txt.edit_difficulty_prompt(), parse_mode="HTML", reply_markup=inline_kb)
    await call.answer()


@router.callback_query(F.data.startswith('setdiff_'))
async def edit_task_difficulty_set(call: CallbackQuery):
    parts = call.data.split('_')
    task_id = int(parts[1])
    new_diff = parts[2]
    xp, gold = REWARD_MAP.get(new_diff, (10, 5))
    task = await update_task_fields(task_id, difficulty=new_diff, reward_xp=xp, reward_gold=gold)
    if task:
        await call.message.edit_text(
            f"✅ Сложность изменена на {DIFF_NAMES.get(new_diff, new_diff)}.\n"
            f"💰 Награда пересчитана: +{xp}✨ / +{gold}💰",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ Назад", callback_data=f"edittask_{task_id}")]
            ])
        )
    else:
        await call.message.edit_text(txt.error_task_gone())
    await call.answer()


@router.callback_query(F.data.startswith('editdead_'))
async def edit_task_deadline(call: CallbackQuery):
    task_id = int(call.data.replace('editdead_', ''))
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Без дедлайна", callback_data=f"setdead_{task_id}_skip")],
        [
            InlineKeyboardButton(text="📅 1 день", callback_data=f"setdead_{task_id}_1"),
            InlineKeyboardButton(text="📅 3 дня", callback_data=f"setdead_{task_id}_3"),
            InlineKeyboardButton(text="📅 7 дней", callback_data=f"setdead_{task_id}_7"),
        ]
    ])
    await call.message.edit_text(txt.edit_deadline_prompt(), parse_mode="HTML", reply_markup=inline_kb)
    await call.answer()


@router.callback_query(F.data.startswith('setdead_'))
async def edit_task_deadline_set(call: CallbackQuery):
    parts = call.data.split('_')
    task_id = int(parts[1])
    val = parts[2]

    if val == 'skip':
        deadline = None
        label = "🚫 без дедлайна"
    else:
        days = int(val)
        deadline = datetime.now() + timedelta(days=days)
        label = f"📅 {days} дн."

    task = await update_task_fields(task_id, deadline=deadline)
    if task:
        await call.message.edit_text(
            f"✅ Дедлайн изменён: {label}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ Назад", callback_data=f"edittask_{task_id}")]
            ])
        )
    else:
        await call.message.edit_text(txt.error_task_gone())
    await call.answer()


async def complete_and_reward(message: Message, task, user_id: int):
    is_recurring = task.type == 'повторяющаяся'

    if is_recurring:
        completed = await complete_recurring_task(task.id)
        streak_text = f"\n🔥 Серия: {completed.streak} дн." if completed.streak else ""
    else:
        completed = await complete_task(task.id)
        streak_text = ""

    if not completed:
        await message.answer(txt.error_quest_fail())
        return

    base_xp = completed.reward_xp
    base_gold = completed.reward_gold

    # Streak bonus
    streak_bonus_text = ""
    if is_recurring and completed.streak and completed.streak > 1:
        daily_bonus_gold = min(completed.streak, 10)
        base_gold += daily_bonus_gold
        streak_bonus_text = f"\n🔥 Бонус серии: +{daily_bonus_gold}💰"
        if completed.streak % 10 == 0:
            big_bonus = 50 + completed.streak * 5
            base_gold += big_bonus
            base_xp += big_bonus
            streak_bonus_text += f"\n🎁 <b>Юбилей!</b> +{big_bonus}💰 +{big_bonus}✨"

    pets = await get_user_pets(user_id)
    active_pet = next((up for up in pets if up.active), None)
    xp_bonus_pct = (active_pet.pet.stat_bonus or {}).get('xp_bonus', 0) if active_pet else 0
    if xp_bonus_pct:
        bonus_xp = round(base_xp * xp_bonus_pct / 100)
        base_xp += bonus_xp

    result = await add_xp_and_gold(user_id, base_xp, base_gold)
    char = result['character']

    skill_text = ""
    if completed.skill_id:
        sk_result = await add_skill_xp(user_id, completed.skill_id, base_xp)
        skill_text = f"\n🎯 Навык: +{base_xp} XP (ур. {sk_result['new_level']})"
        if sk_result['leveled_up']:
            skill_text += " ⬆️"

    pet_msgs = []
    if completed.skill_id:
        pet_msgs = await give_pet_quest_xp(user_id, completed.skill_id, base_xp)

    reward_msg = txt.reward_completed(
        completed.title, completed.reward_xp, completed.reward_gold,
        skill_text, streak_text, char.level
    ) + streak_bonus_text

    await message.answer(reward_msg, parse_mode="HTML")

    for pm in pet_msgs:
        await message.answer(pm, parse_mode="HTML")

    if is_recurring:
        await message.answer(txt.reward_recurring(), parse_mode="HTML")

    if result['leveled_up']:
        lvl = result['new_level']
        lvl_msg = txt.level_up(lvl)
        if result['level_gold']:
            lvl_msg += f"\n💰 +{result['level_gold']} золота за повышение ранга!"
        await message.answer(lvl_msg, parse_mode="HTML")

    new_ach = await check_achievements(user_id)
    for ach in new_ach:
        await message.answer(
            txt.new_achievement(ach.name, ach.description),
            parse_mode="HTML"
        )
        reward_pet = await get_pet_by_achievement(ach.code)
        if reward_pet:
            await message.answer(
                txt.companion_found(reward_pet.name, reward_pet.description),
                parse_mode="HTML"
            )

    easter = ['слизень', 'slime', '🐌', 'слизня']
    if any(w in completed.title.lower() for w in easter):
        slime_pet = await award_pet(user_id, 5)
        if slime_pet:
            await message.answer(
                txt.secret_pet_found(slime_pet.name, slime_pet.description),
                parse_mode="HTML"
            )


# === Voluntary note to quest ===

@router.callback_query(F.data == 'note_quest_list')
async def note_quest_list(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return

    tasks = await get_active_tasks(user.id)
    if not tasks:
        await call.message.edit_text(
            txt.no_active_quests_for_note(),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ Назад", callback_data='active_task')]
            ])
        )
        await call.answer()
        return

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📝 {t.title}", callback_data=f"nq_{t.id}")]
        for t in tasks
    ])
    await call.message.edit_text(
        txt.note_to_quest_choose(),
        reply_markup=inline_kb
    )
    await call.answer()


@router.callback_query(F.data.startswith('nq_'))
async def note_quest_start(call: CallbackQuery, state: FSMContext):
    try:
        task_id = int(call.data.replace('nq_', ''))
    except ValueError:
        await call.message.edit_text(txt.error_invalid_id())
        await call.answer()
        return

    await state.update_data(quest_note_task_id=task_id)
    await state.set_state(QuestNote.waiting_text)
    await call.message.edit_text(
        txt.note_to_quest_start(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(QuestNote.waiting_text)
async def note_quest_text(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get('quest_note_task_id')
    if not task_id:
        await message.answer(txt.error_not_found())
        await state.clear()
        return

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(txt.profile_err())
        await state.clear()
        return

    if message.photo:
        text = message.caption or txt.notes_photo_text()
        photo_id = message.photo[-1].file_id
        await create_note(user_id=user.id, text=text, quest_id=task_id, photo_id=photo_id)
    else:
        await create_note(user_id=user.id, text=message.text, quest_id=task_id)
    await state.clear()
    await message.answer(
        txt.notes_saved(),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Все заметки", callback_data='notes_all')],
        ])
    )

    new_ach = await check_achievements(user.id)
    for ach in new_ach:
        await message.answer(
            txt.new_achievement(ach.name, ach.description),
            parse_mode="HTML"
        )


# === Delete task ===

@router.callback_query(F.data == 'delete_active_task')
async def delete_active_task(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        return

    tasks = await get_active_tasks(user.id)
    if not tasks:
        await call.message.edit_text(txt.delete_none())
        return

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🗑 {t.title}", callback_data=f"del_{t.id}")]
        for t in tasks
    ])
    await call.message.edit_text(txt.delete_choose(), reply_markup=inline_kb)
    await call.answer()


@router.callback_query(F.data.startswith('del_'))
async def delete_task_cb(call: CallbackQuery):
    try:
        task_id = int(call.data.replace('del_', ''))
    except ValueError:
        await call.message.edit_text(txt.error_invalid_id())
        await call.answer()
        return

    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        await call.answer()
        return

    deleted = await delete_task(task_id, user.id)
    if not deleted:
        await call.message.edit_text(txt.delete_not_found())
        await call.answer()
        return

    await call.message.edit_text(txt.delete_ok())
    await call.answer()


# === Completed tasks ===

@router.callback_query(F.data == 'complete_task')
async def show_completed_tasks(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(txt.profile_err())
        return

    tasks = await get_completed_tasks(user.id)
    if not tasks:
        await call.message.edit_text(txt.completed_empty(), parse_mode="HTML")
        return

    task_lines = ""
    for i, t in enumerate(tasks[-10:], 1):
        emoji = DIFF_EMOJIS.get(t.difficulty, '📋')
        skill_tag = f" [{t.skill.skill_name}]" if t.skill_id and t.skill else ""
        task_lines += f"{i}. {emoji} {t.title}{skill_tag}\n"
    task_lines += txt.completed_last()

    await call.message.edit_text(txt.completed_list(task_lines), parse_mode="HTML")
    await call.answer()

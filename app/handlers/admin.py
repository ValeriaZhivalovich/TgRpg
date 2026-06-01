from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from app.database.models import User, Character, Task, Note
from app.constants import TaskStatus
from sqlalchemy import select, func
from app.database.request import connection
import html
from logs.logger_config import logger

router = Router()

ADMIN_IDS = []


def set_admin_ids(ids: list[int]):
    global ADMIN_IDS
    ADMIN_IDS = ids


def is_admin(tg_id: int) -> bool:
    return tg_id in ADMIN_IDS


@router.message(Command('admin'))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = await _gather_stats()

    text = (
        f"🛡️ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: {stats['users']}\n"
        f"📋 Квестов активных: {stats['active_tasks']}\n"
        f"✅ Квестов завершено: {stats['completed_tasks']}\n"
        f"📝 Заметок: {stats['notes']}\n"
        f"⚙️ Режимы: {stats['mode_breakdown']}\n\n"
        f"<b>Команды:</b>\n"
        f"<code>/admin_users</code> — список пользователей\n"
        f"<code>/admin_user &lt;id&gt;</code> — профиль пользователя\n"
        f"<code>/admin_broadcast &lt;текст&gt;</code> — рассылка\n"
        f"<code>/admin_reseed</code> — перезаливка seed-данных"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command('admin_users'))
async def cmd_admin_users(message: Message):
    if not is_admin(message.from_user.id):
        return

    users = await _get_all_users()
    if not users:
        await message.answer("❌ Нет пользователей.")
        return

    text = "<b>👥 Все пользователи:</b>\n\n"
    for u, c in users:
        name = html.escape(c.name) if c else f"ID {u.id}"
        mode = u.mode.upper()
        text += f"• <code>{u.tg_id}</code> — {name} (ур.{c.level if c else '?'}) [{mode}]\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command('admin_user'))
async def cmd_admin_user(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    if not command.args:
        await message.answer("Укажи tg_id: <code>/admin_user 123456789</code>", parse_mode="HTML")
        return

    try:
        tg_id = int(command.args.strip())
    except ValueError:
        await message.answer("❌ Некорректный ID.")
        return

    info = await _get_user_info(tg_id)
    if not info:
        await message.answer("❌ Пользователь не найден.")
        return

    u, c, task_count, note_count = info
    name = html.escape(c.name) if c else "?"
    text = (
        f"👤 <b>{name}</b>\n"
        f"ID: <code>{u.tg_id}</code>\n"
        f"Дата: {u.created_at.strftime('%d.%m.%Y')}\n"
        f"Режим: {u.mode}\n"
        f"Уведомления: {'🔔' if u.notifications else '🔕'}\n"
    )
    if c:
        text += (
            f"Класс: {c.class_name} | Ур.{c.level}\n"
            f"❤ {c.hp}/{c.max_hp} | ⚡ {c.energy}/{c.max_energy}\n"
            f"💰 {c.gold} | ✨ {c.xp}\n"
        )
    text += f"📋 Квестов: {task_count} | 📝 Заметок: {note_count}"
    await message.answer(text, parse_mode="HTML")


@router.message(Command('admin_broadcast'))
async def cmd_admin_broadcast(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    if not command.args:
        await message.answer("Укажи текст рассылки: <code>/admin_broadcast Привет всем!</code>", parse_mode="HTML")
        return

    text = command.args.strip()
    users = await _get_all_users()
    sent = 0
    failed = 0

    status_msg = await message.answer(f"📨 Рассылка запущена... 0/{len(users)}")
    for i, (u, _) in enumerate(users):
        try:
            await message.bot.send_message(
                u.tg_id,
                f"📢 <b>Системное сообщение</b>\n\n{text}",
                parse_mode="HTML"
            )
            sent += 1
        except Exception as e:
            logger.error(f"Broadcast failed to {u.tg_id}: {e}")
            failed += 1
        if i % 10 == 0:
            await status_msg.edit_text(f"📨 Рассылка... {i}/{len(users)}")

    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена</b>\n"
        f"Отправлено: {sent}\n"
        f"Ошибок: {failed}",
        parse_mode="HTML"
    )


@router.message(Command('admin_reseed'))
async def cmd_admin_reseed(message: Message):
    if not is_admin(message.from_user.id):
        return

    from app.database.request import seed_skills, seed_items, seed_pets, seed_achievements
    await seed_skills()
    await seed_items()
    await seed_pets()
    await seed_achievements()
    await message.answer("✅ Seed-данные перезалиты (пропущены уже существующие).")


# === Internal helpers ===

@connection
async def _gather_stats(session):
    users = await session.scalar(select(func.count(User.id)))
    active_tasks = await session.scalar(
        select(func.count(Task.id)).where(Task.status == TaskStatus.ACTIVE)
    )
    completed_tasks = await session.scalar(
        select(func.count(Task.id)).where(Task.status == TaskStatus.COMPLETED)
    )
    notes = await session.scalar(select(func.count(Note.id)))

    modes = await session.execute(
        select(User.mode, func.count(User.id)).group_by(User.mode)
    )
    mode_parts = []
    for row in modes:
        emoji = {'easy': '🌟', 'normal': '⚡', 'hard': '🔥'}.get(row[0], '❓')
        mode_parts.append(f"{emoji} {row[0]}: {row[1]}")
    mode_breakdown = " | ".join(mode_parts) if mode_parts else "—"

    return {
        'users': users or 0,
        'active_tasks': active_tasks or 0,
        'completed_tasks': completed_tasks or 0,
        'notes': notes or 0,
        'mode_breakdown': mode_breakdown,
    }


@connection
async def _get_all_users(session):
    result = await session.execute(
        select(User, Character).outerjoin(Character, User.id == Character.user_id)
        .order_by(User.created_at.desc())
    )
    return result.all()


@connection
async def _get_user_info(session, tg_id: int):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if not user:
        return None
    char = await session.scalar(
        select(Character).where(Character.user_id == user.id)
    )
    task_count = await session.scalar(
        select(func.count(Task.id)).where(Task.user_id == user.id)
    )
    note_count = await session.scalar(
        select(func.count(Note.id)).where(Note.user_id == user.id)
    )
    return user, char, task_count or 0, note_count or 0

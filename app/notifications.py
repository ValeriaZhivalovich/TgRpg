import asyncio
from datetime import datetime, timedelta
from logs.logger_config import logger
from app.database.models import async_session
from app.database.models import User, Task
from app.database.request import is_completed_today
from app.constants import TaskStatus
from sqlalchemy import select
import app.texts as txt

CHECK_INTERVAL = 900

_last_notified = {}

async def check_deadlines(bot):
    global _last_notified
    while True:
        now = datetime.now()
        today_key = now.date().isoformat()
        try:
            async with async_session() as session:
                deadline_soon = now + timedelta(hours=24)
                result = await session.execute(
                    select(User).where(User.notifications == True)
                )
                users = result.scalars().all()

                for user in users:
                    tasks = await session.execute(
                        select(Task).where(
                            Task.user_id == user.id,
                            Task.status == TaskStatus.ACTIVE,
                            Task.deadline.isnot(None),
                            Task.deadline > now,
                            Task.deadline <= deadline_soon,
                        )
                    )
                    for task in tasks.scalars().all():
                        key = f"deadline_{task.id}_{today_key}"
                        if key in _last_notified:
                            continue
                        hours_left = int((task.deadline - now).total_seconds() / 3600)
                        try:
                            await bot.send_message(
                                user.tg_id,
                                txt.deadline_reminder(task.title, hours_left),
                                parse_mode="HTML"
                            )
                            _last_notified[key] = True
                        except Exception as e:
                            logger.error(f"Deadline reminder error for user {user.tg_id}: {e}")

                    recurring = await session.execute(
                        select(Task).where(
                            Task.user_id == user.id,
                            Task.type == 'recurring',
                            Task.status == TaskStatus.ACTIVE,
                        )
                    )
                    for task in recurring.scalars().all():
                        key = f"recurring_{task.id}_{today_key}"
                        if key in _last_notified:
                            continue
                        if not is_completed_today(task):
                            try:
                                await bot.send_message(
                                    user.tg_id,
                                    txt.recurring_reminder(task.title),
                                    parse_mode="HTML"
                                )
                                _last_notified[key] = True
                            except Exception as e:
                                logger.error(f"Recurring reminder error for user {user.tg_id}: {e}")
        except Exception as e:
            logger.error(f"Notification check error: {e}")

        # Prune old keys
        _last_notified = {k: v for k, v in _last_notified.items() if today_key in k}
        await asyncio.sleep(CHECK_INTERVAL)

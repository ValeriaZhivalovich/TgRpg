import os
from logs.logger_config import logger
from dotenv import load_dotenv

import asyncio
from aiogram import Bot, Dispatcher

from app.handlers.user import router as user_router
from app.handlers.quests import router as quests_router
from app.handlers.notes import router as notes_router
from app.handlers.admin import router as admin_router, set_admin_ids
from app.database.models import async_main
from app.database.request import seed_skills, seed_items, seed_pets, seed_achievements
from app.notifications import check_deadlines
from app.middleware import ThrottlingMiddleware

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    logger.error("Токен не найден! .env файл")
    raise ValueError("Токен бота не найден!")

ADMIN_IDS = []
raw = os.getenv("ADMIN_IDS")
if raw:
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ADMIN_IDS.append(int(part))

async def main():
    await async_main()
    await seed_skills()
    await seed_items()
    await seed_pets()
    await seed_achievements()

    set_admin_ids(ADMIN_IDS)

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.message.middleware(ThrottlingMiddleware())
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(quests_router)
    dp.include_router(notes_router)

    notify_task = asyncio.create_task(check_deadlines(bot))

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка во время работы бота: {e}")
    finally:
        notify_task.cancel()
        await bot.session.close()
        logger.info("Сессия бота закрыта.")

if __name__ == "__main__":
    try:
        logger.info("Бот запущен")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Бот отключен")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
import asyncio
from aiogram import BaseMiddleware
from aiogram.types import Message
from logs.logger_config import logger

RATE_LIMIT = 1.0
_rate_store = {}


class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        user_id = event.from_user.id
        now = asyncio.get_running_loop().time()

        last = _rate_store.get(user_id, 0)
        if now - last < RATE_LIMIT:
            logger.debug(f"Throttled user {user_id}")
            return

        _rate_store[user_id] = now

        # Prune stale entries (every 100 events)
        if len(_rate_store) > 1000:
            cutoff = now - 10
            for uid in list(_rate_store.keys()):
                if _rate_store[uid] < cutoff:
                    del _rate_store[uid]

        return await handler(event, data)

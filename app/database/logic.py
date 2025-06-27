from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import *
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload


async def get_user_by_tg_id(tg_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalars().first()
        return user


async def get_inventory(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(InventoryItem)
            .options(joinedload(InventoryItem.item))  # ✅ Подгружаем item сразу
            .where(InventoryItem.user_id == user_id)
        )
        return result.unique().scalars().all()

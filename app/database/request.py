from app.database.models import async_session
from app.database.models import User
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload



def connection(func):
    async def wrapper(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return wrapper


@connection 
async def set_user(session, tg_id): 
    user = await session.scalar(select(User).where(User.tg_id == tg_id))

    if not user:
        return False
    else:
        return user


@connection
async def add_user(session, tg_id, name, last_name, contact=None):
    new_user = User(
        tg_id=tg_id,
        username=name,
        last_name=last_name
    )
    session.add(new_user)
    await session.commit()
    return new_user


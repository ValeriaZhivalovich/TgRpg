from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import *
from sqlalchemy.future import select

# Логика выполнения задачи
async def complete_task(session: AsyncSession, task_id: int):
    task = await session.get(Task, task_id)
    if not task:
        return "Задача не найдена."

    # Если задача одноразовая
    if task.periodicity == "одноразовая":
        task.completed = True
        # Начисляем награду
        user = await session.get(User, task.user_id)
        user.xp += task.reward_xp
        user.gold += task.reward_gold
        await session.delete(task)  # Удаляем задачу
    else:
        # Если задача повторяемая
        task.streak += 1
        task.completed = True
        # Начисляем награду
        user = await session.get(User, task.user_id)
        user.xp += task.reward_xp
        user.gold += task.reward_gold

    await session.commit()
    return "Задача выполнена!"

# Логика добавления опыта к навыку
async def add_skill_xp(session: AsyncSession, user_id: int, skill_name: str, xp: int):
    skill = await session.query(Skill).filter_by(user_id=user_id, skill_name=skill_name).first()
    if not skill:
        # Если навыка нет, создаем его
        skill = Skill(user_id=user_id, skill_name=skill_name, xp=0, level=1)
        session.add(skill)

    # Добавляем опыт
    skill.xp += xp
    # Проверяем, нужно ли повысить уровень
    if skill.xp >= skill.level * 100:  # Пример: 100 XP на уровень
        skill.level += 1
        skill.xp = 0

    await session.commit()
    return f"Навык '{skill_name}' повышен до уровня {skill.level}!"

async def get_user_by_tg_id(tg_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalars().first()
        return user

# Добавление нового пользователя
async def add_user(tg_id: int, name: str, last_name: str, session: AsyncSession):
    new_user = User(
        tg_id=tg_id,
        name=name,
        last_name=last_name,
        hp=100,
        level=1,
        xp=0,
        gold=0
    )
    session.add(new_user)
    await session.commit()
from sqlalchemy import ForeignKey, String, BigInteger, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# URL для подключения к базе данных
URL = os.getenv('SQLALCHEMY_URL')

# Создание асинхронного движка
engine = create_async_engine(url=URL)

# Создание фабрики сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name:Mapped[str] = mapped_column(String(150), nullable=True)
    hp: Mapped[int] = mapped_column(Integer, default=100)  # Здоровье
    energy: Mapped[int] = mapped_column(Integer, default=50)  # Энергия
    level: Mapped[int] = mapped_column(Integer, default=1)  # Уровень
    xp: Mapped[int] = mapped_column(Integer, default=0)  # Опыт
    gold: Mapped[int] = mapped_column(Integer, default=0)  # Золото


class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)
    comment: Mapped[str] = mapped_column(String(255), nullable=True)  # Комментарий к задаче
    periodicity: Mapped[str] = mapped_column(String(50), default="одноразовая")  # Периодичность
    streak: Mapped[int] = mapped_column(Integer, default=0)  # Серия выполнений подряд
    completed: Mapped[bool] = mapped_column(Boolean, default=False)  # Выполнена ли задача?
    reward_xp: Mapped[int] = mapped_column(Integer, default=10)  # Награда за выполнение (опыт)
    reward_gold: Mapped[int] = mapped_column(Integer, default=5)  # Награда за выполнение (золото)

class Skill(Base):
    __tablename__ = 'skills'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(50), nullable=False)  # Название навыка
    xp: Mapped[int] = mapped_column(Integer, default=0)  # Опыт в навыке
    level: Mapped[int] = mapped_column(Integer, default=1)  # Уровень навыка
    
# Асинхронная функция для создания таблиц
async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
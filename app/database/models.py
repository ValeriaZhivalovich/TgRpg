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

    inventory: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="user")

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
    skill_id: Mapped[int] = mapped_column(ForeignKey('skills.id'), nullable=False)

class Skill(Base):
    __tablename__ = 'skills'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    skill_name: Mapped[str] = mapped_column(String(50), nullable=False)  # Название навыка 
    level_max: Mapped[int] = mapped_column(Integer, default=1)

class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    item_type: Mapped[str] = mapped_column(String(30), nullable=True)
    effect: Mapped[dict] = mapped_column(String(150), nullable=True) 

    users: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="item")

class Pet(Base):
    __tablename__ = 'pets'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    stat_bonus: Mapped[dict] = mapped_column(String(255), nullable=True)  


class UserSkill(Base):
    __tablename__ = 'user_skills'
    
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'),primary_key=True, nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey('skills.id'),primary_key=True, nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0)  # Опыт в навыке
    level: Mapped[int] = mapped_column(Integer, default=1)  # Уровень навыка


class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="inventory")
    item: Mapped["Item"] = relationship("Item", back_populates="users")


class UserPet(Base):
    __tablename__ = 'user_pets'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    pet_id: Mapped[int] = mapped_column(ForeignKey('pets.id'), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    

# Асинхронная функция для создания таблиц
async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
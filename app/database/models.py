from sqlalchemy import ForeignKey, String, BigInteger, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv('SQLALCHEMY_URL')

engine = create_async_engine(url=URL)

async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    mode: Mapped[str] = mapped_column(String(20), default='easy')
    notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    character: Mapped["Character"] = relationship("Character", back_populates="user", uselist=False)
    inventory: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="user")
    pets: Mapped[list["UserPet"]] = relationship("UserPet", back_populates="user")


class Character(Base):
    __tablename__ = 'characters'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    class_name: Mapped[str] = mapped_column(String(30), default='Авантюрист')
    avatar: Mapped[str] = mapped_column(String(10), default='🧙')
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    gold: Mapped[int] = mapped_column(Integer, default=0)
    hp: Mapped[int] = mapped_column(Integer, default=100)
    max_hp: Mapped[int] = mapped_column(Integer, default=100)
    energy: Mapped[int] = mapped_column(Integer, default=50)
    max_energy: Mapped[int] = mapped_column(Integer, default=50)

    user: Mapped["User"] = relationship("User", back_populates="character")


class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default='easy')
    type: Mapped[str] = mapped_column(String(30), default='одноразовая')
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='active')
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey('skills.id'), nullable=True)
    reward_xp: Mapped[int] = mapped_column(Integer, default=10)
    reward_gold: Mapped[int] = mapped_column(Integer, default=5)
    timer_minutes: Mapped[int] = mapped_column(Integer, default=0)
    last_completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    streak: Mapped[int] = mapped_column(Integer, default=0)

    skill: Mapped["Skill"] = relationship("Skill", lazy="joined")


class Note(Base):
    __tablename__ = 'notes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    quest_id: Mapped[int] = mapped_column(ForeignKey('tasks.id'), nullable=True)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    photo_id: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    quest: Mapped["Task"] = relationship("Task", lazy="joined")


class Skill(Base):
    __tablename__ = 'skills'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    skill_name: Mapped[str] = mapped_column(String(50), nullable=False)
    level_max: Mapped[int] = mapped_column(Integer, default=1)


class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    item_type: Mapped[str] = mapped_column(String(30), nullable=True)
    price: Mapped[int] = mapped_column(Integer, default=0)
    effect: Mapped[dict] = mapped_column(JSON, nullable=True)

    users: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="item")


class Pet(Base):
    __tablename__ = 'pets'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[int] = mapped_column(Integer, default=0)
    stat_bonus: Mapped[dict] = mapped_column(JSON, nullable=True)
    skill_ids: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(20), default='shop')
    achievement_code: Mapped[str] = mapped_column(String(50), nullable=True)


class UserSkill(Base):
    __tablename__ = 'user_skills'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True, nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey('skills.id'), primary_key=True, nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)

    skill: Mapped["Skill"] = relationship("Skill", lazy="joined")


class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="inventory")
    item: Mapped["Item"] = relationship("Item", back_populates="users")


class UserPet(Base):
    __tablename__ = 'user_pets'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    pet_id: Mapped[int] = mapped_column(ForeignKey('pets.id'), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship("User", back_populates="pets")
    pet: Mapped["Pet"] = relationship("Pet", lazy="joined")


class Achievement(Base):
    __tablename__ = 'achievements'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    emoji: Mapped[str] = mapped_column(String(10), default='🏆')
    condition_type: Mapped[str] = mapped_column(String(30), nullable=False)
    condition_value: Mapped[int] = mapped_column(Integer, default=1)


class UserAchievement(Base):
    __tablename__ = 'user_achievements'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    achievement_id: Mapped[int] = mapped_column(ForeignKey('achievements.id'), nullable=False)
    achieved_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

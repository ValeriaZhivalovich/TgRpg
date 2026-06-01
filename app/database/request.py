from app.database.models import (
    async_session, User, Character, Task, Note, Skill, Item, Pet,
    UserSkill, InventoryItem, UserPet, Achievement, UserAchievement,
)
from app.constants import Difficulty, TaskType, TaskStatus, REWARD_MAP
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timedelta


def connection(func):
    async def wrapper(*args, **kwargs):
        async with async_session() as session:
            try:
                return await func(session, *args, **kwargs)
            except Exception:
                await session.rollback()
                raise
    return wrapper


# === Users & Characters ===

@connection
async def get_user(session, tg_id: int) -> User | None:
    return await session.scalar(select(User).where(User.tg_id == tg_id))


CLASS_STATS = {
    'Авантюрист': {'hp': 100, 'energy': 50, 'gold': 0, 'avatar': '🗡️'},
    'Маг':        {'hp': 70,  'energy': 80, 'gold': 0, 'avatar': '🔮'},
    'Воин':       {'hp': 130, 'energy': 30, 'gold': 0, 'avatar': '⚔️'},
    'Торговец':   {'hp': 90,  'energy': 50, 'gold': 50, 'avatar': '💰'},
    'Следопыт':   {'hp': 100, 'energy': 60, 'gold': 0, 'avatar': '🏹'},
}


@connection
async def add_user(session, tg_id, name, last_name=None, class_name='Авантюрист', avatar=None):
    user = User(
        tg_id=tg_id,
        username=name,
        last_name=last_name or name,
    )
    session.add(user)
    await session.flush()

    stats = CLASS_STATS.get(class_name, CLASS_STATS['Авантюрист'])
    if not avatar:
        avatar = stats['avatar']

    character = Character(
        user_id=user.id,
        name=name,
        last_name=last_name,
        class_name=class_name,
        avatar=avatar,
        hp=stats['hp'],
        max_hp=stats['hp'],
        energy=stats['energy'],
        max_energy=stats['energy'],
        gold=stats['gold'],
    )
    session.add(character)
    await session.commit()
    return user


@connection
async def update_default_difficulty(session, tg_id: int, difficulty: str):
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if not user:
        return False
    user.mode = difficulty
    await session.commit()
    return True


@connection
async def get_character(session, user_id: int):
    character = await session.scalar(
        select(Character).where(Character.user_id == user_id)
    )
    return character


@connection
async def update_character_stats(session, user_id: int, **kwargs):
    await session.execute(
        update(Character).where(Character.user_id == user_id).values(**kwargs)
    )
    await session.commit()


@connection
async def get_user_with_character(session, tg_id: int):
    user = await session.scalar(
        select(User).options(selectinload(User.character)).where(User.tg_id == tg_id)
    )
    return user


@connection
async def get_inventory(session, user_id: int):
    result = await session.scalars(
        select(InventoryItem).options(joinedload(InventoryItem.item)).where(InventoryItem.user_id == user_id)
    )
    return result.unique().all()


# === Timer config ===

def get_timer_remaining(task) -> int:
    if not task.started_at or not task.timer_minutes:
        return 0
    elapsed = (datetime.now() - task.started_at).total_seconds() / 60
    return max(0, round(task.timer_minutes - elapsed))


def is_completed_today(task) -> bool:
    if not task.last_completed_at:
        return False
    return task.last_completed_at.date() == datetime.now().date()


def can_complete(task) -> bool:
    if task.type == TaskType.RECURRING and is_completed_today(task):
        return False
    if not task.timer_minutes:
        return True
    if not task.started_at:
        return False
    return get_timer_remaining(task) == 0


# === Skills ===

DEFAULT_SKILLS = [
    {'name': '💻 Разработка', 'emoji': '💻'},
    {'name': '📚 Обучение', 'emoji': '📚'},
    {'name': '💪 Здоровье', 'emoji': '💪'},
    {'name': '🎨 Творчество', 'emoji': '🎨'},
    {'name': '🏠 Бытовое', 'emoji': '🏠'},
    {'name': '🎯 Без навыка', 'emoji': '🎯'},
]


@connection
async def seed_skills(session):
    existing = await session.scalars(select(Skill))
    if existing.first():
        return
    for s in DEFAULT_SKILLS:
        session.add(Skill(skill_name=s['name']))
    await session.commit()


@connection
async def get_all_skills(session):
    result = await session.scalars(select(Skill))
    return result.all()


@connection
async def get_skill_by_id(session, skill_id: int):
    return await session.scalar(select(Skill).where(Skill.id == skill_id))


@connection
async def get_user_skills(session, user_id: int):
    result = await session.scalars(
        select(UserSkill).where(UserSkill.user_id == user_id)
        .order_by(UserSkill.level.desc(), UserSkill.xp.desc())
    )
    return result.all()


@connection
async def get_or_create_user_skill(session, user_id: int, skill_id: int):
    us = await session.scalar(
        select(UserSkill).where(
            UserSkill.user_id == user_id, UserSkill.skill_id == skill_id
        )
    )
    if not us:
        us = UserSkill(user_id=user_id, skill_id=skill_id, xp=0, level=1)
        session.add(us)
        await session.commit()
    return us


@connection
async def add_skill_xp(session, user_id: int, skill_id: int, xp: int) -> dict:
    us = await get_or_create_user_skill(session, user_id, skill_id)
    us.xp += xp
    leveled = False
    while us.xp >= us.level * 100:
        us.xp -= us.level * 100
        us.level += 1
        leveled = True
    await session.commit()
    return {'leveled_up': leveled, 'new_level': us.level, 'user_skill': us}


# === Quests (Tasks) ===

@connection
async def create_task(session, user_id: int, title: str, difficulty: str = Difficulty.EASY,
                      task_type: str = TaskType.ONCE, deadline: datetime = None,
                      skill_id: int = None, description: str = None,
                      timer_minutes: int = 0) -> Task:
    base_xp, base_gold = REWARD_MAP.get(difficulty, (10, 5))
    total_xp = base_xp + timer_minutes * 2
    total_gold = base_gold + timer_minutes

    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        difficulty=difficulty,
        type=task_type,
        deadline=deadline,
        status=TaskStatus.ACTIVE,
        skill_id=skill_id,
        reward_xp=total_xp,
        reward_gold=total_gold,
        timer_minutes=timer_minutes,
    )
    session.add(task)
    await session.commit()
    return task


@connection
async def get_active_tasks(session, user_id: int):
    result = await session.scalars(
        select(Task).where(Task.user_id == user_id, Task.status == TaskStatus.ACTIVE)
    )
    return result.all()


@connection
async def get_completed_tasks(session, user_id: int):
    result = await session.scalars(
        select(Task).where(Task.user_id == user_id, Task.status == TaskStatus.COMPLETED)
    )
    return result.all()


@connection
async def get_task_by_id(session, task_id: int):
    return await session.scalar(select(Task).where(Task.id == task_id))


@connection
async def start_task(session, task_id: int):
    task = await session.scalar(select(Task).where(Task.id == task_id))
    if not task or task.status != TaskStatus.ACTIVE:
        return None
    task.started_at = datetime.now()
    await session.commit()
    return task


@connection
async def get_notes(session, user_id: int, limit: int = 10, offset: int = 0):
    result = await session.scalars(
        select(Note).where(Note.user_id == user_id)
        .order_by(Note.created_at.desc())
        .limit(limit).offset(offset)
    )
    return result.all()


@connection
async def get_note_by_id(session, note_id: int, user_id: int = None):
    query = select(Note).where(Note.id == note_id)
    if user_id:
        query = query.where(Note.user_id == user_id)
    return await session.scalar(query)


@connection
async def create_note(session, user_id: int, text: str, quest_id: int = None, photo_id: str = None):
    note = Note(
        user_id=user_id,
        quest_id=quest_id,
        text=text,
        photo_id=photo_id,
    )
    session.add(note)
    await session.commit()
    return note


@connection
async def complete_task(session, task_id: int):
    task = await session.scalar(select(Task).where(Task.id == task_id))
    if not task:
        return None
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now()
    await session.commit()
    return task


@connection
async def update_task_fields(session, task_id: int, **kwargs):
    task = await session.scalar(select(Task).where(Task.id == task_id))
    if not task:
        return None
    for key, value in kwargs.items():
        if hasattr(task, key):
            setattr(task, key, value)
    await session.commit()
    return task


@connection
async def complete_recurring_task(session, task_id: int):
    task = await session.scalar(select(Task).where(Task.id == task_id))
    if not task:
        return None

    now = datetime.now()
    task.completed_at = now

    if task.last_completed_at:
        if task.last_completed_at.date() == (now - timedelta(days=1)).date():
            task.streak += 1
        else:
            task.streak = 1
    else:
        task.streak = 1

    task.last_completed_at = now
    await session.commit()
    return task


@connection
async def delete_task(session, task_id: int, user_id: int):
    task = await session.scalar(select(Task).where(Task.id == task_id, Task.user_id == user_id))
    if not task:
        return False
    await session.delete(task)
    await session.commit()
    return True


# === Items / Shop ===

SEED_ITEMS = [
    {'name': '💚 Малое зелье здоровья', 'description': '+30 HP', 'item_type': 'potion', 'price': 10, 'effect': {'hp': 30}},
    {'name': '❤️ Большое зелье здоровья', 'description': '+75 HP', 'item_type': 'potion', 'price': 25, 'effect': {'hp': 75}},
    {'name': '💧 Зелье энергии', 'description': '+20 EP', 'item_type': 'potion', 'price': 10, 'effect': {'energy': 20}},
    {'name': '✨ Эликсир энергии', 'description': '+50 EP', 'item_type': 'potion', 'price': 25, 'effect': {'energy': 50}},
    {'name': '📜 Свиток опыта', 'description': '+50 XP персонажу', 'item_type': 'scroll', 'price': 20, 'effect': {'xp': 50}},
    {'name': '📜 Свиток мудрости', 'description': '+100 XP персонажу', 'item_type': 'scroll', 'price': 40, 'effect': {'xp': 100}},
    {'name': '🧀 Лакомство', 'description': '+25 XP питомцу', 'item_type': 'pet_food', 'price': 8, 'effect': {'pet_xp': 25}},
    {'name': '🥩 Стейк', 'description': '+50 XP питомцу', 'item_type': 'pet_food', 'price': 15, 'effect': {'pet_xp': 50}},
    {'name': '🍖 Большой стейк', 'description': '+100 XP питомцу', 'item_type': 'pet_food', 'price': 30, 'effect': {'pet_xp': 100}},
]


@connection
async def seed_items(session):
    existing = await session.scalars(select(Item))
    if existing.first():
        return
    for data in SEED_ITEMS:
        session.add(Item(**data))
    await session.commit()


@connection
async def get_items_by_type(session, item_type: str):
    result = await session.scalars(
        select(Item).where(Item.item_type == item_type)
    )
    return result.all()


@connection
async def get_item_by_id(session, item_id: int):
    return await session.scalar(select(Item).where(Item.id == item_id))


@connection
async def buy_item(session, user_id: int, item_id: int) -> dict:
    character = await session.scalar(
        select(Character).where(Character.user_id == user_id)
    )
    item = await session.scalar(select(Item).where(Item.id == item_id))
    if not character or not item:
        return {'success': False, 'error': '❌ Персонаж или товар не найден.'}
    if character.gold < item.price:
        return {'success': False, 'error': '❌ Недостаточно золота.'}

    character.gold -= item.price

    existing = await session.scalar(
        select(InventoryItem).where(
            InventoryItem.user_id == user_id,
            InventoryItem.item_id == item_id,
        )
    )
    if existing:
        existing.quantity += 1
    else:
        session.add(InventoryItem(user_id=user_id, item_id=item_id, quantity=1))

    await session.commit()
    return {'success': True, 'item': item, 'gold_left': character.gold}


@connection
async def use_consumable(session, user_id: int, inv_item_id: int) -> dict:
    inv = await session.scalar(
        select(InventoryItem).options(joinedload(InventoryItem.item)).where(
            InventoryItem.id == inv_item_id, InventoryItem.user_id == user_id
        )
    )
    if not inv:
        return {'success': False, 'error': '❌ Предмет не найден.'}

    char = await session.scalar(select(Character).where(Character.user_id == user_id))
    if not char:
        return {'success': False, 'error': '❌ Персонаж не найден.'}

    effect = inv.item.effect or {}
    messages = []

    if 'hp' in effect:
        old = char.hp
        char.hp = min(char.hp + effect['hp'], char.max_hp)
        messages.append(f"❤ HP: {old} → {char.hp}")
    if 'energy' in effect:
        old = char.energy
        char.energy = min(char.energy + effect['energy'], char.max_energy)
        messages.append(f"⚡ EP: {old} → {char.energy}")
    if 'xp' in effect:
        messages.append(f"✨ +{effect['xp']} XP к персонажу")
        char.xp += effect['xp']
        while char.xp >= char.level * 100:
            char.xp -= char.level * 100
            char.level += 1
            messages.append(f"⬆️ Уровень {char.level}!")
    if 'pet_xp' in effect:
        active_pet = await session.scalar(
            select(UserPet).options(joinedload(UserPet.pet)).where(
                UserPet.user_id == user_id, UserPet.active == True
            )
        )
        if not active_pet:
            return {'success': False, 'error': '❌ Нет активного питомца. Призови питомца в профиле.'}
        old_lvl = active_pet.level
        active_pet.xp = getattr(active_pet, 'xp', 0) + effect['pet_xp']
        while active_pet.xp >= active_pet.level * 50:
            active_pet.xp -= active_pet.level * 50
            active_pet.level += 1
        leveled = active_pet.level > old_lvl
        bonus_str = ", ".join(f"{k}={round(v * (1 + (active_pet.level - 1) * 0.2))}" for k, v in (active_pet.pet.stat_bonus or {}).items())
        messages.append(f"🐾 {active_pet.pet.name}: +{effect['pet_xp']} XP (ур.{old_lvl} → ур.{active_pet.level})")
        if leveled:
            messages.append(f"⬆️ {active_pet.pet.name} повышен! Бонусы: {bonus_str}")

    inv.quantity -= 1
    if inv.quantity <= 0:
        await session.delete(inv)
    await session.commit()
    return {'success': True, 'messages': messages, 'item_name': inv.item.name, 'character': char}


# === Pets ===

SEED_PETS = [
    {'name': '🐱 Котик',      'description': 'Мурлыкает и греет душу. +5 HP',     'price': 30, 'stat_bonus': {'hp': 5},     'skill_ids': [1, 5], 'source': 'shop',       'achievement_code': None},
    {'name': '🐶 Щенок',      'description': 'Верный друг. +5 EP',                 'price': 30, 'stat_bonus': {'energy': 5}, 'skill_ids': [2, 3], 'source': 'shop',       'achievement_code': None},
    {'name': '🦊 Лисёнок',    'description': 'Хитрый малый. +5% к XP за квесты',   'price': 0,  'stat_bonus': {'xp_bonus': 5}, 'skill_ids': [2, 4], 'source': 'achievement', 'achievement_code': 'ten_quests'},
    {'name': '🐉 Дракончик',  'description': 'Редкий зверь. +10 HP, +5 EP',        'price': 0,  'stat_bonus': {'hp': 10, 'energy': 5}, 'skill_ids': [1, 2, 3, 4, 5], 'source': 'achievement', 'achievement_code': 'streak_7'},
    {'name': '🐌 Слизень',    'description': 'Странный, но свой. Не даёт бонусов, но Система его зачем-то добавила.', 'price': 0, 'stat_bonus': {}, 'skill_ids': [], 'source': 'easter_egg', 'achievement_code': None},
]


@connection
async def seed_pets(session):
    existing = await session.scalars(select(Pet))
    if existing.first():
        return
    for data in SEED_PETS:
        session.add(Pet(**data))
    await session.commit()


@connection
async def get_all_pets(session):
    result = await session.scalars(select(Pet))
    return result.all()


@connection
async def get_shop_pets(session):
    result = await session.scalars(
        select(Pet).where(Pet.source == 'shop').order_by(Pet.price)
    )
    return result.all()


@connection
async def get_user_pets(session, user_id: int):
    result = await session.scalars(
        select(UserPet).options(joinedload(UserPet.pet)).where(UserPet.user_id == user_id)
    )
    return result.all()


@connection
async def adopt_pet(session, user_id: int, pet_id: int) -> dict:
    character = await session.scalar(select(Character).where(Character.user_id == user_id))
    pet = await session.scalar(select(Pet).where(Pet.id == pet_id))
    if not character or not pet:
        return {'success': False, 'error': '❌ Персонаж или питомец не найден.'}
    if character.gold < pet.price:
        return {'success': False, 'error': '❌ Недостаточно золота.'}

    already = await session.scalar(
        select(UserPet).where(UserPet.user_id == user_id, UserPet.pet_id == pet_id)
    )
    if already:
        return {'success': False, 'error': '❌ Этот питомец уже у тебя есть.'}

    character.gold -= pet.price
    session.add(UserPet(user_id=user_id, pet_id=pet_id, active=False, level=1))
    await session.commit()
    return {'success': True, 'pet': pet, 'gold_left': character.gold}


@connection
async def activate_pet(session, user_id: int, user_pet_id: int) -> dict:
    pets = await session.scalars(select(UserPet).where(UserPet.user_id == user_id))
    target = None
    for up in pets:
        if up.id == user_pet_id:
            up.active = True
            target = up
        else:
            up.active = False
    if not target:
        return {'success': False, 'error': '❌ Питомец не найден.'}
    await session.commit()
    return {'success': True, 'pet': target.pet}


@connection
async def get_pet_by_achievement(session, achievement_code: str) -> Pet | None:
    return await session.scalar(
        select(Pet).where(Pet.achievement_code == achievement_code)
    )


@connection
async def give_pet_quest_xp(session, user_id: int, skill_id: int, xp: int) -> list[str]:
    active_pet = await session.scalar(
        select(UserPet).options(joinedload(UserPet.pet)).where(
            UserPet.user_id == user_id, UserPet.active == True
        )
    )
    if not active_pet:
        return []
    if skill_id not in (active_pet.pet.skill_ids or []):
        return []
    old_lvl = active_pet.level
    active_pet.xp = getattr(active_pet, 'xp', 0) + xp
    while active_pet.xp >= active_pet.level * 50:
        active_pet.xp -= active_pet.level * 50
        active_pet.level += 1
    await session.commit()
    msgs = [f"🐾 {active_pet.pet.name}: +{xp} XP за квест"]
    if active_pet.level > old_lvl:
        bonus_str = ", ".join(f"{k}={round(v * (1 + (active_pet.level - 1) * 0.2))}" for k, v in (active_pet.pet.stat_bonus or {}).items())
        msgs.append(f"⬆️ {active_pet.pet.name} повышен до ур.{active_pet.level}! Бонусы: {bonus_str}")
    return msgs


@connection
async def award_pet(session, user_id: int, pet_id: int) -> Pet | None:
    already = await session.scalar(
        select(UserPet).where(UserPet.user_id == user_id, UserPet.pet_id == pet_id)
    )
    if already:
        return None
    session.add(UserPet(user_id=user_id, pet_id=pet_id, active=False, level=1))
    await session.commit()
    pet = await session.scalar(select(Pet).where(Pet.id == pet_id))
    return pet


# === Achievements ===

SEED_ACHIEVEMENTS = [
    {'code': 'first_quest',     'name': '🎯 Первый шаг',       'description': 'Завершить первый квест',               'condition_type': 'quests_total', 'condition_value': 1},
    {'code': 'ten_quests',      'name': '🔥 Трудоголик',       'description': 'Завершить 10 квестов',                 'condition_type': 'quests_total', 'condition_value': 10},
    {'code': 'hard_mode',       'name': '💀 Хардкорщик',       'description': 'Завершить квест в Hard-режиме',        'condition_type': 'quests_hard',  'condition_value': 1},
    {'code': 'streak_7',        'name': '📅 Неделя',           'description': 'Достичь серии в 7 дней подряд',         'condition_type': 'streak',       'condition_value': 7},
    {'code': 'level_5',         'name': '⬆️ Адепт',            'description': 'Достичь 5 уровня',                      'condition_type': 'level',        'condition_value': 5},
    {'code': 'level_10',        'name': '⬆️ Мастер',           'description': 'Достичь 10 уровня',                     'condition_type': 'level',        'condition_value': 10},
    {'code': 'five_notes',      'name': '📝 Летописец',        'description': 'Создать 5 заметок',                     'condition_type': 'notes',        'condition_value': 5},
    {'code': 'pet_friend',      'name': '🐾 Друг зверей',      'description': 'Завести питомца',                       'condition_type': 'pets',         'condition_value': 1},
    {'code': 'first_pet',       'name': '🐾 Друг зверей',      'description': 'Завести первого питомца',               'condition_type': 'pets',         'condition_value': 1},
]


@connection
async def seed_achievements(session):
    existing = await session.scalars(select(Achievement))
    if existing.first():
        return
    for a in SEED_ACHIEVEMENTS:
        session.add(Achievement(**a))
    await session.commit()


@connection
async def get_user_achievements(session, user_id: int):
    result = await session.scalars(
        select(UserAchievement).options(joinedload(UserAchievement.achievement))
        .where(UserAchievement.user_id == user_id)
    )
    return result.all()


@connection
async def get_all_achievements(session):
    result = await session.scalars(select(Achievement))
    return result.all()


@connection
async def award_achievement(session, user_id: int, achievement_id: int) -> Achievement | None:
    existing = await session.scalar(
        select(UserAchievement).where(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id,
        )
    )
    if existing:
        return None
    session.add(UserAchievement(user_id=user_id, achievement_id=achievement_id))
    await session.commit()
    ach = await session.scalar(select(Achievement).where(Achievement.id == achievement_id))
    return ach


@connection
async def check_achievements(session, user_id: int) -> list[Achievement]:
    character = await session.scalar(select(Character).where(Character.user_id == user_id))
    if not character:
        return []

    new_achievements = []
    all_achievements = await session.scalars(select(Achievement))
    existing_ua = await session.scalars(
        select(UserAchievement).where(UserAchievement.user_id == user_id)
    )
    earned_ids = {ua.achievement_id for ua in existing_ua}

    # Compute current stats
    completed_tasks = await session.scalars(
        select(Task).where(Task.user_id == user_id, Task.status == TaskStatus.COMPLETED)
    )
    completed_list = completed_tasks.all() if completed_tasks else []
    total_quests_count = len(completed_list)
    hard_count = len([t for t in completed_list if t.difficulty == Difficulty.HARD])

    recurring = await session.scalars(
        select(Task).where(Task.user_id == user_id, Task.type == TaskType.RECURRING)
    )
    max_streak = max((t.streak for t in recurring or []), default=0)

    all_notes = await session.scalars(
        select(Note).where(Note.user_id == user_id)
    )
    notes_count = len(all_notes.all() if all_notes else [])

    user_pets = await session.scalars(
        select(UserPet).where(UserPet.user_id == user_id)
    )
    pets_count = len(user_pets.all() if user_pets else [])

    for ach in all_achievements:
        if ach.id in earned_ids:
            continue

        met = False
        if ach.condition_type == 'quests_total':
            met = total_quests_count >= ach.condition_value
        elif ach.condition_type == 'quests_hard':
            met = hard_count >= ach.condition_value
        elif ach.condition_type == 'streak':
            met = max_streak >= ach.condition_value
        elif ach.condition_type == 'level':
            met = character.level >= ach.condition_value
        elif ach.condition_type == 'notes':
            met = notes_count >= ach.condition_value
        elif ach.condition_type == 'pets':
            met = pets_count >= ach.condition_value

        if met:
            awarded = await award_achievement(session, user_id, ach.id)
            if awarded:
                new_achievements.append(awarded)
                reward_pet = await get_pet_by_achievement(session, ach.code)
                if reward_pet:
                    await award_pet(session, user_id, reward_pet.id)

    return new_achievements


@connection
async def get_achievement_progress(session, user_id: int) -> dict[str, int]:
    character = await session.scalar(select(Character).where(Character.user_id == user_id))
    if not character:
        return {}

    completed_tasks = await session.scalars(
        select(Task).where(Task.user_id == user_id, Task.status == TaskStatus.COMPLETED)
    )
    completed_list = completed_tasks.all() if completed_tasks else []
    total_quests = len(completed_list)
    hard_count = len([t for t in completed_list if t.difficulty == Difficulty.HARD])

    recurring = await session.scalars(
        select(Task).where(Task.user_id == user_id, Task.type == TaskType.RECURRING)
    )
    max_streak = max((t.streak for t in recurring or []), default=0)

    all_notes = await session.scalars(select(Note).where(Note.user_id == user_id))
    notes_count = len(all_notes.all() if all_notes else [])

    user_pets = await session.scalars(select(UserPet).where(UserPet.user_id == user_id))
    pets_count = len(user_pets.all() if user_pets else [])

    return {
        'quests_total': total_quests,
        'quests_hard': hard_count,
        'streak': max_streak,
        'level': character.level,
        'notes': notes_count,
        'pets': pets_count,
    }


# === XP & Level-up ===

# === User settings ===

@connection
async def get_notifications_pref(session, tg_id: int) -> bool:
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if not user:
        return False
    return user.notifications


@connection
async def set_notifications_pref(session, tg_id: int, enabled: bool) -> bool:
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    if not user:
        return False
    user.notifications = enabled
    await session.commit()
    return True


@connection
async def add_xp_and_gold(session, user_id: int, xp: int, gold: int) -> dict:
    character = await session.scalar(
        select(Character).where(Character.user_id == user_id)
    )
    if not character:
        return {'leveled_up': False, 'new_level': None, 'level_gold': 0, 'character': None}

    character.xp += xp
    character.gold += gold

    leveled_up = False
    new_level = character.level
    level_gold = 0

    while character.xp >= character.level * 100:
        character.xp -= character.level * 100
        character.level += 1
        leveled_up = True
        new_level = character.level
        bonus = new_level * 10
        character.gold += bonus
        level_gold += bonus

    await session.commit()
    return {
        'leveled_up': leveled_up,
        'new_level': new_level,
        'level_gold': level_gold,
        'character': character,
    }

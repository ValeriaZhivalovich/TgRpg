import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from app.database.models import UserSkill, Task
from app.constants import TaskStatus
from sqlalchemy import select
from app.database.request import connection
from sqlalchemy.orm import joinedload

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 120

COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FF8C42', '#6C5B7B']

def _get_buffer(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', facecolor='#1a1a2e')
    buf.seek(0)
    plt.close(fig)
    return buf


@connection
async def get_completed_tasks_daily(session, user_id: int, days: int = 7):
    since = datetime.now() - timedelta(days=days)
    result = await session.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.status == TaskStatus.COMPLETED,
            Task.completed_at >= since,
        )
    )
    return result.scalars().all()


@connection
async def get_xp_earned_daily(session, user_id: int, days: int = 7):
    since = datetime.now() - timedelta(days=days)
    result = await session.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.status == TaskStatus.COMPLETED,
            Task.completed_at >= since,
        )
    )
    tasks = result.scalars().all()
    daily_xp = defaultdict(int)
    for t in tasks:
        date_key = t.completed_at.date().isoformat() if t.completed_at else None
        if date_key:
            daily_xp[date_key] += t.reward_xp
    return daily_xp


@connection
async def get_user_skill_data(session, user_id: int):
    result = await session.execute(
        select(UserSkill).options(joinedload(UserSkill.skill)).where(
            UserSkill.user_id == user_id
        )
    )
    return result.scalars().all()


async def chart_completed_daily(user_id: int, days: int = 14) -> io.BytesIO:
    tasks = await get_completed_tasks_daily(user_id, days)
    dates = [(datetime.now() - timedelta(days=i)).date().isoformat() for i in range(days - 1, -1, -1)]
    counts = Counter(t.completed_at.date().isoformat() for t in tasks if t.completed_at)
    values = [counts.get(d, 0) for d in dates]
    labels = [d[-5:] for d in dates]

    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')
    ax.bar(range(len(dates)), values, color='#4ECDC4', width=0.6)
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(labels, rotation=45, ha='right', color='white', fontsize=8)
    ax.set_ylabel('Квестов', color='white', fontsize=9)
    ax.set_title('📊 Завершённые квесты по дням', color='white', fontsize=11, pad=10)
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('#2d2d44')
    ax.set_ylim(0, max(values) * 1.3 + 0.5 if values and max(values) > 0 else 2)
    for i, v in enumerate(values):
        if v > 0:
            ax.text(i, v + 0.1, str(v), ha='center', color='white', fontsize=8)
    plt.tight_layout()
    return _get_buffer(fig)


async def chart_xp_daily(user_id: int, days: int = 14) -> io.BytesIO:
    daily_xp = await get_xp_earned_daily(user_id, days)
    dates = [(datetime.now() - timedelta(days=i)).date().isoformat() for i in range(days - 1, -1, -1)]
    values = [daily_xp.get(d, 0) for d in dates]
    labels = [d[-5:] for d in dates]

    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')
    bars = ax.bar(range(len(dates)), values, color='#FF6B6B', width=0.6)
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(labels, rotation=45, ha='right', color='white', fontsize=8)
    ax.set_ylabel('XP', color='white', fontsize=9)
    ax.set_title('✨ Полученный опыт по дням', color='white', fontsize=11, pad=10)
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('#2d2d44')
    ax.set_ylim(0, max(values) * 1.3 + 1 if values and max(values) > 0 else 10)
    for i, v in enumerate(values):
        if v > 0:
            ax.text(i, v + 0.5, str(v), ha='center', color='white', fontsize=8, rotation=90)
    plt.tight_layout()
    return _get_buffer(fig)


async def chart_difficulty_pie(user_id: int) -> io.BytesIO:
    tasks = await get_completed_tasks_daily(user_id, 365)
    counts = Counter(t.difficulty for t in tasks)
    labels_map = {'easy': 'Easy', 'normal': 'Normal', 'hard': 'Hard'}
    colors_map = {'easy': '#4ECDC4', 'normal': '#FFEAA7', 'hard': '#FF6B6B'}

    labels = [labels_map.get(k, k) for k in ('easy', 'normal', 'hard') if counts.get(k, 0) > 0]
    sizes = [counts.get(k, 0) for k in ('easy', 'normal', 'hard') if counts.get(k, 0) > 0]
    colors = [colors_map.get(k, '#999') for k in ('easy', 'normal', 'hard') if counts.get(k, 0) > 0]

    if not sizes:
        labels = ['Нет данных']
        sizes = [1]
        colors = ['#333']

    fig, ax = plt.subplots(figsize=(4, 3.5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct='%1.0f%%',
        startangle=90, textprops={'color': 'white', 'fontsize': 9},
        pctdistance=0.75
    )
    for t in autotexts:
        t.set_color('white')
        t.set_fontsize(8)
    ax.set_title('Сложность квестов', color='white', fontsize=11, pad=10)
    plt.tight_layout()
    return _get_buffer(fig)


async def chart_skills(user_id: int) -> io.BytesIO:
    skills_data = await get_user_skill_data(user_id)
    if not skills_data:
        fig, ax = plt.subplots(figsize=(6, 2.5))
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        ax.text(0.5, 0.5, '🔮 Навыки ещё не раскрыты', ha='center', va='center',
                color='white', fontsize=12, transform=ax.transAxes)
        ax.axis('off')
        plt.tight_layout()
        return _get_buffer(fig)

    names = []
    xp_values = []
    levels = []
    colors = COLORS[:len(skills_data)]
    for us in skills_data:
        skill_name = us.skill.skill_name if us.skill else f'Навык {us.skill_id}'
        names.append(skill_name)
        xp_values.append(us.xp + (us.level - 1) * 100)
        levels.append(us.level)

    fig, ax = plt.subplots(figsize=(7, 3.5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')
    bars = ax.barh(range(len(names)), xp_values, color=colors, height=0.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, color='white', fontsize=9)
    ax.set_xlabel('Всего XP', color='white', fontsize=9)
    ax.set_title('🔮 Прокачка навыков', color='white', fontsize=11, pad=10)
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('#2d2d44')
    for i, (bar, lvl) in enumerate(zip(bars, levels)):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f'ур.{lvl}', va='center', color='white', fontsize=8)
    plt.tight_layout()
    return _get_buffer(fig)

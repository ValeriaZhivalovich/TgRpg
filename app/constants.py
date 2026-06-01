from enum import StrEnum


class Difficulty(StrEnum):
    EASY = 'easy'
    NORMAL = 'normal'
    HARD = 'hard'


class TaskType(StrEnum):
    ONCE = 'одноразовая'
    RECURRING = 'повторяющаяся'


class TaskStatus(StrEnum):
    ACTIVE = 'active'
    COMPLETED = 'completed'


REWARD_MAP = {
    Difficulty.EASY: (10, 5),
    Difficulty.NORMAL: (20, 10),
    Difficulty.HARD: (30, 15),
}

DIFF_EMOJIS = {
    Difficulty.EASY: '🌟',
    Difficulty.NORMAL: '⚡',
    Difficulty.HARD: '🔥',
}

DIFF_NAMES = {
    Difficulty.EASY: '🌟 Easy',
    Difficulty.NORMAL: '⚡ Normal',
    Difficulty.HARD: '🔥 Hard (с заметкой)',
}

TYPE_NAMES = {
    TaskType.ONCE: '📌 Разовый',
    TaskType.RECURRING: '🔄 Повторяющийся',
}

TIMER_MINUTES = {
    Difficulty.EASY: 0,
    Difficulty.NORMAL: 5,
    Difficulty.HARD: 10,
}

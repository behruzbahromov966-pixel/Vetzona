"""FSM holatlari (tsikl importlarni oldini olish uchun alohida)."""

from aiogram.fsm.state import State, StatesGroup


class AiChatState(StatesGroup):
    active = State()

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BUTTON_END_AI_CHAT = "Ai chat tugatish ❌"


def get_ai_chat_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BUTTON_END_AI_CHAT)]],
        resize_keyboard=True,
    )

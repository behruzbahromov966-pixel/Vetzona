from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_role_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Shifokor"), KeyboardButton(text="Oddiy foydalanuvchi")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

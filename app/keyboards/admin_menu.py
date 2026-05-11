from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BUTTON_VIEW_USERS = "Foydalanuvchilarni ko'rish 📋"
BUTTON_VIEW_DOCTORS = "Doktorlarni ko'rish 📋"
BUTTON_VIEW_REFERRALS = "Murojaatlarni ko'rish 📋"
BUTTON_VIEW_PHARMACIES = "Dorixonalarni ko'rish 📋"
BUTTON_ADD_PHARMACY = "Dorixona qo'shish ➕"
BUTTON_REMOVE_PHARMACY = "Dorixona o'chirish ✖️"
BUTTON_BACK = "Ortga 🔙"


def get_admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BUTTON_VIEW_USERS),
                KeyboardButton(text=BUTTON_VIEW_DOCTORS),
                KeyboardButton(text=BUTTON_VIEW_REFERRALS),
            ],
            [
                KeyboardButton(text=BUTTON_VIEW_PHARMACIES),
                KeyboardButton(text=BUTTON_ADD_PHARMACY),
                KeyboardButton(text=BUTTON_REMOVE_PHARMACY),
            ],
            [KeyboardButton(text=BUTTON_BACK)],
        ],
        resize_keyboard=True,
    )

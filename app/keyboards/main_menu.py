from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BUTTON_AI_CHAT = "Ai chat"
BUTTON_DOCTOR_CONTACT = "Doktorga murojaat 📞"
BUTTON_PHARMACIES = "Dorixonalar ro'yxati 📋"
BUTTON_COOPERATION = "Hamkorlik bo'yicha murojaat 📞"
BUTTON_ADMIN_PANEL = "Admin paneli 🔒"


def get_main_menu(is_admin: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BUTTON_AI_CHAT), KeyboardButton(text=BUTTON_DOCTOR_CONTACT)],
        [KeyboardButton(text=BUTTON_PHARMACIES), KeyboardButton(text=BUTTON_COOPERATION)],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=BUTTON_ADMIN_PANEL)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

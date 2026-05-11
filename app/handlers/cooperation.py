from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.keyboards.main_menu import BUTTON_COOPERATION
from app.texts.uz import COOPERATION_CAPTION_HTML_TEMPLATE
from app.utils.tg_username import public_telegram_username
from config import Settings

router = Router()

COOPERATION_APPLY_BUTTON_TEXT = "✉️ Adminga yozish"


async def present_cooperation(message: Message, settings: Settings) -> None:
    """Hamkorlik bo'limi matni + ixtiyoriy rasm + admin bilan bog'lanish tugmasi."""
    phone = escape(settings.cooperation_phone or "")
    username = public_telegram_username(settings.admin_username)

    if username:
        tg_line = f'Telegram: <a href="https://t.me/{username}">@{escape(username)}</a>'
        apply_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=COOPERATION_APPLY_BUTTON_TEXT,
                        url=f"https://t.me/{username}",
                    )
                ]
            ]
        )
    else:
        raw_u = (settings.admin_username or "").strip()
        hint = (
            f"<i>ADMIN_USERNAME noto'g'ri yoki bo'sh: <code>{escape(raw_u[:80])}</code>. "
            "To'g'ri ochiq username (5–32 belgi) kiriting.</i>\n"
            if raw_u
            else "<i>Telegram: admin username (.env → ADMIN_USERNAME) yo'q — telefon orqali bog'laning.</i>"
        )
        tg_line = hint
        apply_kb = None

    caption = COOPERATION_CAPTION_HTML_TEMPLATE.format(phone=phone, tg_line=tg_line)

    image_url = (settings.cooperation_image_url or "").strip()
    if image_url:
        try:
            await message.answer_photo(
                photo=image_url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=apply_kb,
            )
            return
        except TelegramBadRequest:
            await message.answer(
                "<i>Rasm yuklanmadi, matn ko'rsatilmoqda.</i>\n\n" + caption,
                parse_mode="HTML",
                reply_markup=apply_kb,
            )
            return

    await message.answer(caption, parse_mode="HTML", reply_markup=apply_kb)


@router.message(F.text == BUTTON_COOPERATION)
async def cooperation_info(message: Message, settings: Settings) -> None:
    await present_cooperation(message, settings)

from aiogram import F, Router
from aiogram.types import Message

from app.db import Database
from app.keyboards.main_menu import BUTTON_PHARMACIES
from app.texts.uz import NO_PHARMACY_TEXT, PHARMACY_LIST_INTRO_HTML
from app.utils.pharmacy_display import send_pharmacy_list

router = Router()


async def present_pharmacy_catalog(message: Message, db: Database) -> None:
    """Barcha dorixonalar (bazada nechta bo'lsa) ketma-ket yuboriladi."""
    pharmacies = await db.get_pharmacies()
    if not pharmacies:
        await message.answer(NO_PHARMACY_TEXT)
        return

    await message.answer(
        PHARMACY_LIST_INTRO_HTML.format(n=len(pharmacies)),
        parse_mode="HTML",
    )
    await send_pharmacy_list(
        message,
        pharmacies,
        show_pharmacy_id=False,
        show_index=True,
        for_public=True,
    )


@router.message(F.text == BUTTON_PHARMACIES)
async def list_pharmacies(message: Message, db: Database) -> None:
    await present_pharmacy_catalog(message, db)

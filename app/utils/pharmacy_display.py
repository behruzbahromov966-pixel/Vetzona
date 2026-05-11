"""Dorixona ro'yxatini HTML caption + rasm (URL yoki file_id) bilan yuborish."""

from __future__ import annotations

import asyncio
import logging
from html import escape
from urllib.parse import quote_plus

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

logger = logging.getLogger(__name__)

# Bir xil chatda juda ko'p xabar — FloodControl uchun qisqa pauza
_PHARMACY_SEND_DELAY_SEC = 0.04
# Telegram: photo caption maks. ~1024 belgi (HTML)
_MAX_CAPTION_LEN = 1020


def _trim_caption(html: str) -> str:
    if len(html) <= _MAX_CAPTION_LEN:
        return html
    return html[: _MAX_CAPTION_LEN - 40] + "\n\n<i>… Matn qisqartirildi.</i>"


async def send_pharmacy_list(
    message: Message,
    pharmacies: list[tuple],
    *,
    show_pharmacy_id: bool = False,
    show_index: bool = False,
    for_public: bool = False,
) -> None:
    """
    show_pharmacy_id: admin uchun bazadagi ID.
    show_index: foydalanuvchiga 1/n tartib ko'rsatish.
    for_public: umumiy uslub (rasm yo'qligi haqida ehtiyotkor yozuv).
    """
    total = len(pharmacies)
    for idx, (pharmacy_id, name, phone, address, image_url, admin_note) in enumerate(
        pharmacies, start=1
    ):
        safe_address = address or ""
        maps_url = (
            "https://www.google.com/maps/search/?api=1&query="
            f"{quote_plus(safe_address)}"
        )
        maps_link_html = (
            f'<a href="{escape(maps_url, quote=True)}">📌 Manzilni xaritada ochish</a>'
        )
        en = escape(name or "")
        ep = escape(phone or "")
        ea = escape(safe_address)

        note_block = ""
        if admin_note:
            note_block = f"\n\n📝 <b>Qo'shimcha ma'lumot</b>\n{escape(admin_note)}"

        id_block = f"<code>ID: {pharmacy_id}</code>\n\n" if show_pharmacy_id else ""

        index_block = ""
        if show_index:
            index_block = f"<i>#{idx} / {total}</i>\n\n"

        raw_url = (image_url or "").strip()
        has_photo = bool(raw_url)

        if for_public and not has_photo:
            visual_note = "\n\n<i>🖼 Ushbu manzil uchun rasm hali biriktirilmagan.</i>"
        elif not for_public and not has_photo:
            visual_note = "\n\n🖼 <i>Rasm biriktirilmagan</i>"
        else:
            visual_note = ""

        caption = _trim_caption(
            f"{id_block}"
            f"{index_block}"
            f"🏪 <b>{en}</b>\n"
            f"📞 <b>Telefon:</b> <code>{ep}</code>\n"
            f"📍 <b>Manzil:</b> {ea}\n"
            f"{maps_link_html}"
            f"{note_block}"
            f"{visual_note}"
        )

        try:
            if has_photo:
                await message.answer_photo(
                    photo=raw_url,
                    caption=caption,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
            else:
                await message.answer(caption, parse_mode="HTML", disable_web_page_preview=True)
        except TelegramBadRequest as exc:
            logger.warning("Pharmacy card send failed id=%s: %s", pharmacy_id, exc)
            err_short = escape(str(exc)[:180])
            await message.answer(
                f"⚠️ <b>#{idx}</b> — <i>{en}</i>\n"
                f"<i>Bu manzil yuborilmadi (Telegram xatosi). Keyinroq admin tekshirsin.</i>\n"
                f"<code>{err_short}</code>",
                parse_mode="HTML",
            )

        if idx < total:
            await asyncio.sleep(_PHARMACY_SEND_DELAY_SEC)

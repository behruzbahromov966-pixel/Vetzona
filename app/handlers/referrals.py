import asyncio
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.db import Database
from app.fsm import AiChatState
from app.handlers.cooperation import present_cooperation
from app.handlers.pharmacies import present_pharmacy_catalog
from app.keyboards.ai_chat import get_ai_chat_keyboard
from app.keyboards.main_menu import (
    BUTTON_ADMIN_PANEL,
    BUTTON_AI_CHAT,
    BUTTON_COOPERATION,
    BUTTON_DOCTOR_CONTACT,
    BUTTON_PHARMACIES,
    get_main_menu,
)
from app.handlers.admin import admin_login_start
from app.texts.uz import (
    AI_PROMPT_TEXT,
    DOCTOR_REFERRAL_PROMPT_TEXT,
    DOCTOR_REFERRAL_RECEIVED_TEXT,
    DOCTOR_REFERRAL_TO_DOCTORS_TEMPLATE,
)
from config import Settings


router = Router()

_log = logging.getLogger(__name__)

ACCEPT_REFERRAL_PREFIX = "accept_referral:"
ACCEPT_BUTTON_TEXT = "Qabul qilish✅"


class ReferralState(StatesGroup):
    waiting_for_text = State()


def _is_fully_registered(user: tuple | None) -> bool:
    if not user:
        return False
    _, full_name, phone, role, *_ = user
    return bool(full_name and phone and role)


def _parse_referral_id(callback_data: str) -> int | None:
    if not callback_data.startswith(ACCEPT_REFERRAL_PREFIX):
        return None
    raw = callback_data[len(ACCEPT_REFERRAL_PREFIX) :]
    if not raw.isdigit():
        return None
    return int(raw)


@router.message(F.text == BUTTON_DOCTOR_CONTACT)
async def doctor_referral_start(
    message: Message, state: FSMContext, db: Database
) -> None:
    # Works for both normal users and doctors. We only require the user to be registered.
    user = await db.get_user(message.from_user.id)
    if not _is_fully_registered(user):
        await message.answer(
            "Iltimos, avval /start orqali ro'yxatdan o'ting.",
            reply_markup=get_main_menu(is_admin=False),
        )
        return

    await state.set_state(ReferralState.waiting_for_text)
    await message.answer(DOCTOR_REFERRAL_PROMPT_TEXT, reply_markup=None)


@router.message(ReferralState.waiting_for_text, F.text)
async def doctor_referral_send(
    message: Message,
    state: FSMContext,
    db: Database,
    settings: Settings,
) -> None:
    data = await db.get_user(message.from_user.id)
    if not _is_fully_registered(data):
        await state.clear()
        await message.answer("Iltimos, avval /start orqali ro'yxatdan o'ting.")
        return

    _, full_name, phone, _, *_ = data
    referral_text = (message.text or "").strip()

    if referral_text == BUTTON_COOPERATION:
        await state.clear()
        await present_cooperation(message, settings)
        return
    if referral_text == BUTTON_PHARMACIES:
        await state.clear()
        await present_pharmacy_catalog(message, db)
        return
    if referral_text == BUTTON_AI_CHAT:
        await state.clear()
        await state.set_state(AiChatState.active)
        await message.answer(AI_PROMPT_TEXT, reply_markup=get_ai_chat_keyboard())
        return
    if referral_text == BUTTON_ADMIN_PANEL:
        await state.clear()
        await admin_login_start(message, state)
        return

    if referral_text == BUTTON_DOCTOR_CONTACT:
        await message.answer(DOCTOR_REFERRAL_PROMPT_TEXT)
        return
    if not referral_text:
        await message.answer(DOCTOR_REFERRAL_PROMPT_TEXT)
        return

    referral_request_id = await db.create_referral_request(
        from_user_id=message.from_user.id, referral_text=referral_text
    )

    doctors = await db.get_doctors()
    if not doctors:
        await state.clear()
        await message.answer(DOCTOR_REFERRAL_RECEIVED_TEXT, reply_markup=get_main_menu(is_admin=message.from_user.id in settings.admin_ids))
        return

    # Send the request to every doctor and remember their message_id for future edits.
    sent_count = 0
    for doctor_id, _doctor_full_name, _doctor_phone in doctors:
        accept_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=ACCEPT_BUTTON_TEXT, callback_data=f"{ACCEPT_REFERRAL_PREFIX}{referral_request_id}")]
            ]
        )
        text_to_doctors = DOCTOR_REFERRAL_TO_DOCTORS_TEMPLATE.format(
            referral_text=referral_text,
            full_name=full_name or "-",
            phone=phone or "-",
        )
        try:
            sent = await message.bot.send_message(
                chat_id=doctor_id, text=text_to_doctors, reply_markup=accept_kb
            )
            await db.add_referral_message(referral_request_id, doctor_id, sent.message_id)
            sent_count += 1
        except TelegramBadRequest as exc:
            _log.warning("Shifokor %s ga yuborib bo'lmadi: %s", doctor_id, exc)
        await asyncio.sleep(0.05)

    await state.clear()
    is_adm = message.from_user.id in settings.admin_ids
    if sent_count == 0:
        await message.answer(
            "Hozir hech qaysi shifokorga yuborib bo'lmadi (botni bloklagan yoki chat topilmadi). "
            "Keyinroq qayta urinib ko'ring yoki admin bilan bog'laning.",
            reply_markup=get_main_menu(is_admin=is_adm),
        )
        return

    extra = f"\n\n<i>Yuborildi: {sent_count}/{len(doctors)} shifokor.</i>" if sent_count < len(doctors) else ""
    await message.answer(
        f"{DOCTOR_REFERRAL_RECEIVED_TEXT}{extra}",
        parse_mode="HTML",
        reply_markup=get_main_menu(is_admin=is_adm),
    )


@router.callback_query(F.data.startswith(ACCEPT_REFERRAL_PREFIX))
async def doctor_referral_accept(callback: CallbackQuery, db: Database) -> None:
    referral_id = _parse_referral_id(callback.data or "")
    if referral_id is None:
        await callback.answer()
        return

    doctor_id = callback.from_user.id
    doctor = await db.get_user(doctor_id)
    if not doctor or doctor[3] != "doctor":
        await callback.answer("Faqat shifokorlar qabul qila oladi.", show_alert=False)
        return

    accepted_now = await db.try_accept_referral(referral_id, doctor_id)
    await callback.answer("Qabul qilindi", show_alert=False)

    # Birinchi qabul: faqat qabul qilgan shifokorda xabar qoladi, boshqalarda o'chiriladi.
    referral_messages = await db.get_referral_messages(referral_id)
    if not referral_messages:
        return

    if accepted_now:
        for msg_doctor_id, message_id in referral_messages:
            if msg_doctor_id == doctor_id:
                try:
                    await callback.bot.edit_message_reply_markup(
                        chat_id=msg_doctor_id,
                        message_id=message_id,
                        reply_markup=None,
                    )
                except TelegramBadRequest:
                    pass
            else:
                try:
                    await callback.bot.delete_message(chat_id=msg_doctor_id, message_id=message_id)
                except TelegramBadRequest:
                    pass
    else:
        for msg_doctor_id, message_id in referral_messages:
            if msg_doctor_id != doctor_id:
                continue
            try:
                await callback.bot.delete_message(chat_id=msg_doctor_id, message_id=message_id)
            except TelegramBadRequest:
                pass
            break


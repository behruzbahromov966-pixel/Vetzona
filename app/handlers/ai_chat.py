from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.db import Database
from app.fsm import AiChatState
from app.handlers.cooperation import present_cooperation
from app.handlers.pharmacies import present_pharmacy_catalog
from app.keyboards.ai_chat import BUTTON_END_AI_CHAT, get_ai_chat_keyboard
from app.keyboards.main_menu import (
    BUTTON_ADMIN_PANEL,
    BUTTON_AI_CHAT,
    BUTTON_COOPERATION,
    BUTTON_DOCTOR_CONTACT,
    BUTTON_PHARMACIES,
    get_main_menu,
)
from app.services.gemini_service import GeminiService
from app.texts.uz import AI_CHAT_ENDED_TEXT, AI_PROMPT_TEXT
from config import Settings

from app.handlers.admin import admin_login_start
from app.handlers.referrals import doctor_referral_start


router = Router()


@router.message(F.text == BUTTON_AI_CHAT)
async def open_ai_chat(message: Message, state: FSMContext) -> None:
    await state.set_state(AiChatState.active)
    await message.answer(AI_PROMPT_TEXT, reply_markup=get_ai_chat_keyboard())


@router.message(
    AiChatState.active,
    F.text.in_(
        {
            BUTTON_PHARMACIES,
            BUTTON_COOPERATION,
            BUTTON_DOCTOR_CONTACT,
            BUTTON_ADMIN_PANEL,
        }
    ),
)
async def ai_chat_exit_via_main_menu(
    message: Message,
    state: FSMContext,
    db: Database,
    settings: Settings,
) -> None:
    """AI chat ichida bosh menyu tugmalari bosilganda Gemini ga yuborilmasin."""
    text = (message.text or "").strip()
    await state.clear()
    if text == BUTTON_PHARMACIES:
        await present_pharmacy_catalog(message, db)
    elif text == BUTTON_COOPERATION:
        await present_cooperation(message, settings)
    elif text == BUTTON_DOCTOR_CONTACT:
        await doctor_referral_start(message, state, db)
    elif text == BUTTON_ADMIN_PANEL:
        await admin_login_start(message, state)


@router.message(AiChatState.active, F.text == BUTTON_END_AI_CHAT)
async def end_ai_chat(message: Message, state: FSMContext, settings: Settings) -> None:
    await state.clear()
    is_admin = message.from_user.id in settings.admin_ids
    await message.answer(AI_CHAT_ENDED_TEXT, reply_markup=get_main_menu(is_admin=is_admin))


@router.message(AiChatState.active, F.text)
async def ai_chat_answer(message: Message, gemini: GeminiService) -> None:
    answer = await gemini.ask((message.text or "").strip())
    await message.answer(answer, reply_markup=get_ai_chat_keyboard())

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.db import Database
from app.keyboards.main_menu import get_main_menu
from app.keyboards.registration import get_phone_request_keyboard, get_role_keyboard
from app.texts.uz import (
    INVALID_PHONE_TEXT,
    INVALID_ROLE_TEXT,
    REGISTRATION_DONE_TEXT,
    REGISTRATION_NAME_TEXT,
    REGISTRATION_PHONE_TEXT,
    REGISTRATION_ROLE_TEXT,
    WELCOME_TEXT,
)
from config import Settings


router = Router()


class RegistrationState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_role = State()


def _is_registered(user: tuple | None) -> bool:
    if not user:
        return False
    _, full_name, phone, role, *_ = user
    return bool(full_name and phone and role)


@router.message(CommandStart())
async def start_handler(message: Message, settings: Settings, db: Database, state: FSMContext) -> None:
    await db.touch_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        language_code=message.from_user.language_code,
    )
    user = await db.get_user(message.from_user.id)
    if not _is_registered(user):
        await state.set_state(RegistrationState.waiting_for_name)
        await message.answer(REGISTRATION_NAME_TEXT)
        return

    is_admin = message.from_user.id in settings.admin_ids
    await message.answer(WELCOME_TEXT, reply_markup=get_main_menu(is_admin=is_admin))


@router.message(RegistrationState.waiting_for_name, F.text)
async def registration_name_step(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Ism bo'sh bo'lmasin. Qayta kiriting.")
        return
    await state.update_data(full_name=name)
    await state.set_state(RegistrationState.waiting_for_phone)
    await message.answer(REGISTRATION_PHONE_TEXT, reply_markup=get_phone_request_keyboard())


@router.message(RegistrationState.waiting_for_phone)
async def registration_phone_step(message: Message, state: FSMContext) -> None:
    if not message.contact or not message.contact.phone_number:
        await message.answer(INVALID_PHONE_TEXT, reply_markup=get_phone_request_keyboard())
        return

    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(RegistrationState.waiting_for_role)
    await message.answer(REGISTRATION_ROLE_TEXT, reply_markup=get_role_keyboard())


@router.message(RegistrationState.waiting_for_role, F.text.in_({"Shifokor", "Oddiy foydalanuvchi"}))
async def registration_role_step(
    message: Message, state: FSMContext, db: Database, settings: Settings
) -> None:
    data = await state.get_data()
    full_name = data.get("full_name", "")
    phone = data.get("phone", "")
    role = "doctor" if message.text == "Shifokor" else "normal_user"

    await db.register_user(
        user_id=message.from_user.id,
        full_name=full_name,
        phone=phone,
        role=role,
    )
    await state.clear()

    is_admin = message.from_user.id in settings.admin_ids
    await message.answer(
        f"{REGISTRATION_DONE_TEXT}\n\n{WELCOME_TEXT}",
        reply_markup=get_main_menu(is_admin=is_admin),
    )


@router.message(RegistrationState.waiting_for_role)
async def registration_role_invalid(message: Message) -> None:
    await message.answer(INVALID_ROLE_TEXT, reply_markup=get_role_keyboard())


@router.message(F.text == "Back to start menu")
async def back_to_start_menu(message: Message, settings: Settings) -> None:
    is_admin = message.from_user.id in settings.admin_ids
    await message.answer("Bosh menyuga qaytdingiz.", reply_markup=get_main_menu(is_admin=is_admin))

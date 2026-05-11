import hashlib
import hmac
from collections import defaultdict

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.db import Database
from app.keyboards.admin_menu import (
    BUTTON_ADD_PHARMACY,
    BUTTON_BACK,
    BUTTON_REMOVE_PHARMACY,
    BUTTON_VIEW_DOCTORS,
    BUTTON_VIEW_PHARMACIES,
    BUTTON_VIEW_REFERRALS,
    BUTTON_VIEW_USERS,
    get_admin_menu,
)
from app.keyboards.main_menu import BUTTON_ADMIN_PANEL, get_main_menu
from app.texts.uz import (
    ADMIN_LOGIN_DENIED_TEXT,
    ADMIN_LOGIN_PROMPT_TEXT,
    ADMIN_PASSWORD_PROMPT_TEXT,
    ADMIN_VERIFYING_TEXT,
    NOT_ADMIN_TEXT,
)
from app.utils.admin_format import admin_empty_note, admin_section_title
from app.utils.pharmacy_display import send_pharmacy_list
from app.utils.text_tables import html_pre_table, html_pre_tables_batched
from config import Settings


router = Router()


class AdminLoginState(StatesGroup):
    waiting_login = State()
    waiting_password = State()


class AddPharmacyState(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
    waiting_image_url = State()
    waiting_admin_note = State()
    confirming = State()


class RemovePharmacyState(StatesGroup):
    waiting_for_id = State()


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


def _is_skip(text: str) -> bool:
    t = (text or "").strip().lower()
    return t in ("/skip", "-", "skip")


def _secret_str_eq(a: str, b: str) -> bool:
    """Constant-time comparison; avoids secrets.compare_digest length mismatch errors."""
    da = hashlib.sha256(a.encode("utf-8")).digest()
    db = hashlib.sha256(b.encode("utf-8")).digest()
    return hmac.compare_digest(da, db)


@router.message(F.text.in_({BUTTON_ADMIN_PANEL, "for admin"}))
async def admin_login_start(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminLoginState.waiting_login)
    await state.update_data(admin_login_candidate="")
    await message.answer(ADMIN_LOGIN_PROMPT_TEXT)


@router.message(AdminLoginState.waiting_login, F.text)
async def admin_login_receive_login(message: Message, state: FSMContext) -> None:
    await state.update_data(admin_login_candidate=message.text.strip())
    await state.set_state(AdminLoginState.waiting_password)
    await message.answer(ADMIN_PASSWORD_PROMPT_TEXT)


@router.message(AdminLoginState.waiting_password, F.text)
async def admin_login_receive_password(message: Message, state: FSMContext, settings: Settings) -> None:
    data = await state.get_data()
    login = (data.get("admin_login_candidate") or "").strip()
    password = message.text or ""

    await message.answer(ADMIN_VERIFYING_TEXT)

    id_ok = message.from_user.id in settings.admin_ids
    login_ok = _secret_str_eq(login, settings.admin_login)
    password_ok = _secret_str_eq(password, settings.admin_password)

    await state.clear()

    if not (id_ok and login_ok and password_ok):
        await message.answer(ADMIN_LOGIN_DENIED_TEXT)
        return

    await message.answer(
        "✅ <b>Admin paneli</b>\n<i>Quyidagi bo'limlardan birini tanlang.</i>",
        parse_mode="HTML",
        reply_markup=get_admin_menu(),
    )


@router.message(F.text == BUTTON_BACK)
async def admin_back_to_main(message: Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    await state.clear()
    await message.answer(
        "🏠 <b>Bosh menyu</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu(is_admin=True),
    )


@router.message(F.text == BUTTON_VIEW_USERS)
async def users_list(message: Message, settings: Settings, db: Database) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return

    users = await db.get_users()
    if not users:
        await message.answer(
            "👥 " + admin_empty_note("Hozircha ro'yxatdan o'tgan foydalanuvchilar yo'q."),
            parse_mode="HTML",
        )
        return

    rows: list[list[str]] = []
    for user_id, full_name, phone, role, username, _language_code, created_at in users[:100]:
        handle = f"@{username}" if username else "—"
        if role == "doctor":
            role_uz = "shifokor"
        elif role == "normal_user":
            role_uz = "foydalanuvchi"
        else:
            role_uz = role or "—"
        rows.append(
            [
                str(user_id),
                full_name or "—",
                phone or "—",
                role_uz,
                handle,
                str(created_at)[:16],
            ]
        )

    tables = html_pre_tables_batched(
        ["ID", "Ism", "Telefon", "Rol", "Username", "Ro'yxat sanasi"],
        [11, 18, 15, 12, 15, 18],
        rows,
        batch_size=25,
    )
    total_parts = len(tables)
    for i, table in enumerate(tables):
        header = admin_section_title(
            "👥",
            "Foydalanuvchilar",
            count=len(users),
            page=(i + 1, total_parts) if total_parts > 1 else None,
        )
        await message.answer(f"{header}\n\n{table}", parse_mode="HTML")


@router.message(F.text == BUTTON_VIEW_DOCTORS)
async def doctors_list_admin(message: Message, settings: Settings, db: Database) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return

    users = await db.get_users()
    doctors = [u for u in users if u[3] == "doctor"]
    if not doctors:
        await message.answer(
            "🩺 " + admin_empty_note("Hozircha ro'yxatdan o'tgan shifokorlar yo'q."),
            parse_mode="HTML",
        )
        return

    rows: list[list[str]] = []
    for user_id, full_name, phone, _role, username, _language_code, created_at in doctors[:100]:
        handle = f"@{username}" if username else "—"
        rows.append(
            [
                str(user_id),
                full_name or "—",
                phone or "—",
                handle,
                str(created_at)[:16],
            ]
        )

    tables = html_pre_tables_batched(
        ["ID", "Ism", "Telefon", "Username", "Ro'yxat sanasi"],
        [11, 18, 15, 15, 18],
        rows,
        batch_size=25,
    )
    total_parts = len(tables)
    for i, table in enumerate(tables):
        header = admin_section_title(
            "🩺",
            "Shifokorlar",
            count=len(doctors),
            page=(i + 1, total_parts) if total_parts > 1 else None,
        )
        await message.answer(f"{header}\n\n{table}", parse_mode="HTML")


@router.message(F.text == BUTTON_VIEW_REFERRALS)
async def referrals_list_admin(message: Message, settings: Settings, db: Database) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return

    users = await db.get_users()
    name_by_id = {u[0]: (u[1] or "—") for u in users}

    edges = await db.get_referral_sender_recipient_edges()
    by_sender: dict[int, set[int]] = defaultdict(set)
    for from_uid, doctor_id in edges:
        by_sender[from_uid].add(doctor_id)

    user_doctor_rows: list[list[str]] = []
    for uid in sorted(by_sender.keys(), key=lambda x: (-len(by_sender[x]), x)):
        doc_ids = sorted(by_sender[uid])
        labels = [name_by_id.get(d, str(d)) for d in doc_ids]
        summary = "; ".join(labels[:6])
        if len(labels) > 6:
            summary += "…"
        user_doctor_rows.append(
            [
                str(uid),
                name_by_id.get(uid, "—"),
                str(len(doc_ids)),
                summary,
            ]
        )

    if user_doctor_rows:
        ud_tables = html_pre_tables_batched(
            ["Foydalanuvchi", "Ism", "Shifokorlar soni", "Bog'langan shifokorlar"],
            [12, 16, 16, 36],
            user_doctor_rows,
            batch_size=20,
        )
        ud_total = len(ud_tables)
        for i, table in enumerate(ud_tables):
            header = admin_section_title(
                "🔗",
                "Foydalanuvchi → shifokorlar",
                count=len(user_doctor_rows),
                page=(i + 1, ud_total) if ud_total > 1 else None,
            )
            await message.answer(f"{header}\n\n{table}", parse_mode="HTML")
    else:
        await message.answer(
            admin_section_title("🔗", "Foydalanuvchi → shifokorlar")
            + "\n\n"
            + admin_empty_note("Hozircha murojaat xabarlari yo'q."),
            parse_mode="HTML",
        )

    ref_rows = await db.get_referrals_with_contacted_doctors(limit=100)
    per_ref_table_rows: list[list[str]] = []
    for (
        ref_id,
        from_uid,
        from_name,
        _from_phone,
        _ref_text,
        status,
        accepted_by,
        created_at,
        _accepted_at,
        docs_blob,
    ) in ref_rows:
        n_docs = 0
        if docs_blob:
            n_docs = len([p for p in docs_blob.split(",") if p.strip()])
        st = "kutilmoqda" if status == "pending" else ("qabul" if status == "accepted" else (status or "—"))
        ac = str(accepted_by) if accepted_by else "—"
        per_ref_table_rows.append(
            [
                str(ref_id),
                str(from_uid),
                from_name or "—",
                str(n_docs),
                st,
                ac,
                str(created_at)[:16],
            ]
        )

    if per_ref_table_rows:
        pr_tables = html_pre_tables_batched(
            ["№", "Kimdan (ID)", "Ism", "Shif.", "Holat", "Qabul qilgan", "Vaqt"],
            [5, 12, 14, 6, 11, 12, 18],
            per_ref_table_rows,
            batch_size=20,
        )
        pr_total = len(pr_tables)
        for i, table in enumerate(pr_tables):
            header = admin_section_title(
                "📋",
                "Murojaatlar ro'yxati",
                count=len(per_ref_table_rows),
                page=(i + 1, pr_total) if pr_total > 1 else None,
            )
            await message.answer(f"{header}\n\n{table}", parse_mode="HTML")
    else:
        await message.answer(
            admin_section_title("📋", "Murojaatlar ro'yxati")
            + "\n\n"
            + admin_empty_note("Hozircha murojaatlar yo'q."),
            parse_mode="HTML",
        )

    counts = await db.get_referral_counts_by_doctor()
    count_rows = [[str(did), name or "—", str(cnt)] for did, name, cnt in counts]
    if count_rows:
        tbl = html_pre_table(["Shifokor ID", "Ism", "Xabarlar"], [13, 22, 8], count_rows)
        header = admin_section_title("📊", "Shifokorlar bo'yicha xabarlar soni", count=len(count_rows))
        await message.answer(f"{header}\n\n{tbl}", parse_mode="HTML")
    else:
        await message.answer(
            admin_section_title("📊", "Shifokorlar bo'yicha xabarlar soni")
            + "\n\n"
            + admin_empty_note("Hozircha yo'q."),
            parse_mode="HTML",
        )


@router.message(F.text == BUTTON_VIEW_PHARMACIES)
async def pharmacies_list_admin(message: Message, settings: Settings, db: Database) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return

    pharmacies = await db.get_pharmacies()
    if not pharmacies:
        await message.answer(
            "🏪 " + admin_empty_note("Bazada dorixona yozuvlari yo'q."),
            parse_mode="HTML",
        )
        return

    intro = (
        admin_section_title("🏪", "Dorixonalar", count=len(pharmacies))
        + "\n\n<i>Har bir yozuv alohida xabar; rasm (havola yoki Telegram fayli) bo'lsa rasmli yuboriladi.</i>"
    )
    await message.answer(intro, parse_mode="HTML")
    await send_pharmacy_list(message, pharmacies, show_pharmacy_id=True)


@router.message(F.text == BUTTON_ADD_PHARMACY)
async def add_pharmacy_prompt(message: Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    await state.set_state(AddPharmacyState.waiting_name)
    await state.update_data(
        confirm_ready=False,
        pharmacy_name="",
        pharmacy_phone="",
        pharmacy_address="",
        pharmacy_image_url=None,
        pharmacy_admin_note=None,
    )
    await message.answer("Dorixona nomini kiriting.")


@router.message(AddPharmacyState.waiting_name, F.text)
async def add_pharmacy_name(message: Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("Nom bo'sh bo'lmasin. Qayta yuboring.")
        return
    await state.update_data(pharmacy_name=name)
    await state.set_state(AddPharmacyState.waiting_phone)
    await message.answer("Telefon raqamini kiriting.")


@router.message(AddPharmacyState.waiting_phone, F.text)
async def add_pharmacy_phone(message: Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    phone = (message.text or "").strip()
    if not phone or _is_skip(phone):
        await message.answer("Telefon majburiy. Qayta yuboring.")
        return
    await state.update_data(pharmacy_phone=phone)
    await state.set_state(AddPharmacyState.waiting_address)
    await message.answer("Manzilni kiriting.")


@router.message(AddPharmacyState.waiting_address, F.text)
async def add_pharmacy_address(message: Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    address = (message.text or "").strip()
    if not address or _is_skip(address):
        await message.answer("Manzil majburiy. Qayta yuboring.")
        return
    await state.update_data(pharmacy_address=address)
    await state.set_state(AddPharmacyState.waiting_image_url)
    await message.answer(
        "Dorixona rasmini <b>foto</b> sifatida yuboring.\n"
        "Yoki internetdan rasm bo'lsa, <code>https://...</code> havolasini yozing.\n"
        "Rasm kerak emas bo'lsa: <code>/skip</code>",
        parse_mode="HTML",
    )


async def _add_pharmacy_after_image_step(
    message: Message, state: FSMContext, settings: Settings, image_ref: str | None
) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    await state.update_data(pharmacy_image_url=image_ref)
    await state.set_state(AddPharmacyState.waiting_admin_note)
    await message.answer("Admin izohi (masalan, qo'shimcha yo'l-yo'riq) yoki /skip.")


@router.message(AddPharmacyState.waiting_image_url, F.photo)
async def add_pharmacy_image_photo(message: Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    photo = message.photo[-1]
    await _add_pharmacy_after_image_step(message, state, settings, photo.file_id)


@router.message(AddPharmacyState.waiting_image_url, F.text)
async def add_pharmacy_image_url(message: Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    raw = (message.text or "").strip()
    image_ref = None if _is_skip(raw) else raw
    await _add_pharmacy_after_image_step(message, state, settings, image_ref)


@router.message(AddPharmacyState.waiting_image_url)
async def add_pharmacy_image_unexpected(message: Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    await message.answer(
        "Iltimos, rasmni <b>foto</b> qilib yuboring, yoki havola matnini, yoki <code>/skip</code>.",
        parse_mode="HTML",
    )


@router.message(AddPharmacyState.waiting_admin_note, F.text)
async def add_pharmacy_admin_note(message: Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    raw = (message.text or "").strip()
    admin_note = None if _is_skip(raw) else raw

    data = await state.get_data()
    name = data.get("pharmacy_name") or ""
    phone = data.get("pharmacy_phone") or ""
    address = data.get("pharmacy_address") or ""
    image_url = data.get("pharmacy_image_url")

    await state.update_data(pharmacy_admin_note=admin_note, confirm_ready=True)
    await state.set_state(AddPharmacyState.confirming)

    if not image_url:
        img_line = "(rasm yo'q)"
    elif image_url.startswith("http://") or image_url.startswith("https://"):
        img_line = image_url
    else:
        img_line = "(Telegram orqali yuborilgan rasm)"
    note_line = admin_note or "(izoh yo'q)"
    summary = (
        "Quyidagi dorixona bazaga qo'shilsinmi?\n\n"
        f"Nomi: {name}\n"
        f"Telefon: {phone}\n"
        f"Manzil: {address}\n"
        f"Rasm URL: {img_line}\n"
        f"Izoh: {note_line}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Yes", callback_data="pharmacy_add:yes"),
                InlineKeyboardButton(text="No", callback_data="pharmacy_add:no"),
            ]
        ]
    )
    await message.answer(summary, reply_markup=kb)


@router.callback_query(F.data.in_({"pharmacy_add:yes", "pharmacy_add:no"}))
async def add_pharmacy_confirm(callback: CallbackQuery, state: FSMContext, settings: Settings, db: Database) -> None:
    if not callback.from_user or not _is_admin(callback.from_user.id, settings):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return

    data = await state.get_data()
    if not data.get("confirm_ready"):
        await callback.answer()
        return

    if callback.data == "pharmacy_add:yes":
        name = data.get("pharmacy_name") or ""
        phone = data.get("pharmacy_phone") or ""
        address = data.get("pharmacy_address") or ""
        if not (name and phone and address):
            await state.clear()
            await callback.answer()
            if callback.message:
                await callback.message.answer("Ma'lumotlar to'liq emas. Boshidan boshlang.")
            return

        image_url = data.get("pharmacy_image_url")
        admin_note = data.get("pharmacy_admin_note")
        await db.add_pharmacy(
            name=name,
            phone=phone,
            address=address,
            image_url=image_url,
            admin_note=admin_note,
        )
        await state.clear()
        await callback.answer()
        if callback.message:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass
            await callback.message.answer("Dorixona ma'lumotlar bazasiga qo'shildi.")
    else:
        await state.clear()
        await callback.answer()
        if callback.message:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass
            await callback.message.answer("Dorixona qo'shilmadi.")


@router.message(AddPharmacyState.confirming, F.text)
async def add_pharmacy_confirm_hint(message: Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    await message.answer("Iltimos, pastdagi Yes yoki No tugmasidan foydalaning.")


@router.message(F.text == BUTTON_REMOVE_PHARMACY)
async def remove_pharmacy_prompt(message: Message, state: FSMContext, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    await state.set_state(RemovePharmacyState.waiting_for_id)
    await message.answer("O'chirish uchun dorixona ID raqamini yuboring.")


@router.message(RemovePharmacyState.waiting_for_id, F.text.regexp(r"^\d+$"))
async def remove_pharmacy_save(
    message: Message, state: FSMContext, settings: Settings, db: Database
) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer(NOT_ADMIN_TEXT)
        return
    pharmacy_id = int(message.text)
    deleted = await db.remove_pharmacy(pharmacy_id)
    await state.clear()
    if deleted:
        await message.answer("Dorixona o'chirildi.")
    else:
        await message.answer("Bunday ID topilmadi.")

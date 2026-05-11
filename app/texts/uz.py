WELCOME_TEXT = (
    "Assalomu alaykum! VetZona botiga xush kelibsiz.\n\n"
    "Kerakli bo'limni tanlang:"
)
REGISTRATION_NAME_TEXT = "Ro'yxatdan o'tish uchun ismingizni kiriting."
REGISTRATION_PHONE_TEXT = "Endi telefon raqamingizni yuboring!"
REGISTRATION_ROLE_TEXT = "Rolingizni tanlang: "
REGISTRATION_DONE_TEXT = "Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!"
INVALID_PHONE_TEXT = "Iltimos, pastdagi tugma orqali telefon raqamingizni yuboring!"
INVALID_ROLE_TEXT = "Iltimos, ro'yxatdan bir rolni tanlang!"

AI_PROMPT_TEXT = (
    "AI chat bo'limidasiz!!!\n"
    "Savolingizni yozing, men Gemini AI orqali javob qaytaraman\n\n"
    "Suhbatni tugatish uchun pastdagi 'Ai chat tugatish ❌' tugmasini bosing!"
)
AI_CHAT_ENDED_TEXT = "AI chat tugadi!"
AI_SCOPE_LIMIT_TEXT = (
    "Kechirasiz, men faqat veterinariya va chorvachilik bo'yicha savollarga javob bera olaman!"
)

# Caption under cooperation image (HTML: phone plain, username in <a> if needed in handler)
COOPERATION_CAPTION_HTML_TEMPLATE = (
    "<b>Hamkorlik</b>\n\n"
    "Savol-javob va hamkorlik bo'yicha murojaatlar uchun administrator bilan bog'laning.\n\n"
    "Telefon: <code>{phone}</code>\n"
    "{tg_line}"
)

NO_PHARMACY_TEXT = "Hozircha dorixonalar ro'yxati bo'sh"

PHARMACY_LIST_INTRO_HTML = (
    "🧴 <b>Dorixonalar katalogi</b>\n"
    "<i>Hozir bazada <b>{n}</b> ta manzil mavjud. Har birida telefon, manzil va "
    "(mavjud bo'lsa) rasm ko'rsatiladi.</i>"
)
NOT_ADMIN_TEXT = "Ushbu bo'lim faqat admin uchun"
UNKNOWN_ADMIN_COMMAND = "Noma'lum admin buyrug'i"

ADMIN_LOGIN_PROMPT_TEXT = "Admin paneliga kirish uchun login yuboring"
ADMIN_PASSWORD_PROMPT_TEXT = "Parolni yuboring"
ADMIN_VERIFYING_TEXT = "Ma'lumotlaringiz tekshirilmoqda..."
ADMIN_LOGIN_DENIED_TEXT = "Tekshiruv muvaffaqiyatsiz!!! Kirish rad etildi"

# Doktorga murojaat (murojaat matni shifokorlarga yuboriladi)
DOCTOR_REFERRAL_PROMPT_TEXT = "Iltimos, shifokorga yubormoqchi bo'lgan murojaat matnini kiriting."
DOCTOR_REFERRAL_RECEIVED_TEXT = "Murojaatingiz shifokorlarga yuborildi."
DOCTOR_REFERRAL_TO_DOCTORS_TEMPLATE = (
    "Yangi yo'llanma:\n\n"
    "Matn: {referral_text}\n\n"
    "Bemor: {full_name}\n"
    "Telefon: {phone}\n\n"
    "Qabul qilish uchun 'Qabul qilish✅' ni bosing."
)
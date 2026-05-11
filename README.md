# Vetzona Telegram bot

Aiogram 3 asosidagi Telegram bot: boshlash, admin panel, AI suhbat (Google Gemini), dorixonalar, referallar va hamkorlik bo‘limlari.

## Talablar

- Python 3.10+
- [Telegram BotFather](https://t.me/BotFather) dan olingan bot tokeni
- (ixtiyoriy) [Google AI](https://aistudio.google.com/) Gemini API kaliti — AI funksiyasi uchun

## O‘rnatish

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`.env.example` faylini `.env` nomiga nusxalang va qiymatlarni to‘ldiring:

```bash
copy .env.example .env
```

## Ishga tushirish

```bash
python bot.py
```

## GitHubga yuklash (qisqa)

1. [GitHub](https://github.com) da yangi repository yarating (README qo‘shmasdan).
2. Loyiha papkasida:

```bash
git init
git add .
git commit -m "Initial commit: Vetzona bot"
git branch -M main
git remote add origin https://github.com/<USERNAME>/<REPO>.git
git push -u origin main
```

**Muhim:** `.env` faylini hech qachon commit qilmang — u `.gitignore` da. Token va parollar faqat serveringizdagi `.env` da saqlansin.

## Litsenziya

Loyiha egasi belgilaydi.

"""Telegram ochiq @username tekshiruvi (noto'g'ri .env dan buzilgan URL oldini olish)."""

from __future__ import annotations

import re

# Telegram: 5–32 belgi, harf bilan boshlanadi, a-z, raqam, _
_PUBLIC_USERNAME = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{4,31}$")


def public_telegram_username(raw: str | None) -> str | None:
    s = (raw or "").strip().lstrip("@")
    if _PUBLIC_USERNAME.fullmatch(s):
        return s
    return None

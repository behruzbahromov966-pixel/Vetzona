from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


# Prefer values from `.env` over pre-set process/env vars (avoids stale BOT_TOKEN masking the file).
load_dotenv(override=True)


def _clean_env_value(raw: str | None) -> str:
    """Strip whitespace and one pair of surrounding quotes (common in .env files)."""
    s = (raw or "").strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1].strip()
    return s


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: set[int]
    admin_username: str
    admin_login: str
    admin_password: str
    cooperation_phone: str
    cooperation_image_url: str
    gemini_api_key: str
    gemini_model: str
    database_path: str = "bot.db"


def _parse_admin_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    cleaned = _clean_env_value(raw)
    for item in cleaned.split(","):
        item = _clean_env_value(item)
        if not item:
            continue
        try:
            ids.add(int(item))
        except ValueError as exc:
            raise ValueError(
                f"ADMIN_IDS noto'g'ri: '{item}' butun son emas. Masalan: 123456789,987654321"
            ) from exc
    return ids


def get_settings() -> Settings:
    bot_token = _clean_env_value(os.getenv("BOT_TOKEN"))
    if not bot_token:
        raise ValueError("BOT_TOKEN is required in .env")

    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    if not admin_ids:
        raise ValueError("ADMIN_IDS is required in .env")

    admin_login = _clean_env_value(os.getenv("ADMIN_LOGIN"))
    admin_password = _clean_env_value(os.getenv("ADMIN_PASSWORD"))
    if not admin_login or not admin_password:
        raise ValueError("ADMIN_LOGIN and ADMIN_PASSWORD are required in .env")

    return Settings(
        bot_token=bot_token,
        admin_ids=admin_ids,
        admin_username=_clean_env_value(os.getenv("ADMIN_USERNAME", "admin")).lstrip("@"),
        admin_login=admin_login,
        admin_password=admin_password,
        cooperation_phone=_clean_env_value(os.getenv("COOPERATION_PHONE", "+998000000000")),
        cooperation_image_url=_clean_env_value(os.getenv("COOPERATION_IMAGE_URL", "")),
        gemini_api_key=_clean_env_value(os.getenv("GEMINI_API_KEY", "")),
        gemini_model=_clean_env_value(os.getenv("GEMINI_MODEL", "gemini-1.5-flash")),
    )

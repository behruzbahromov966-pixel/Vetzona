import asyncio
import atexit
import logging
import os
import warnings
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.db import Database
from app.handlers import setup_routers
from app.services.gemini_service import GeminiService
from config import get_settings

_LOCK_PATH = Path(__file__).resolve().parent / ".vetzona_bot.lock"


def _pid_is_running(pid: int) -> bool:
    """Windows / POSIX: jarayon hali yashaydimi (lock fayli eskirgan bo'lishi mumkin)."""
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return kernel32.GetLastError() != 87  # 87 = jarayon yo'q; boshqa xato = ehtimol ishlayapti
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _acquire_single_instance_lock() -> None:
    """Bitta polling instansiyasi: ikkinchisi TelegramConflictError bermasligi uchun."""
    if _LOCK_PATH.exists():
        try:
            old_pid = int(_LOCK_PATH.read_text(encoding="ascii").strip())
        except (OSError, ValueError):
            old_pid = -1
        if old_pid > 0 and not _pid_is_running(old_pid):
            try:
                _LOCK_PATH.unlink()
            except OSError:
                pass

    try:
        fd = os.open(_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit(
            "Bot allaqachon ishlamoqda (yoki boshqa kompyuterda shu token bilan polling yoqilgan).\n"
            "- Barcha terminallarda faqat bitta botni qoldiring (qolganlarini Ctrl+C).\n"
            "- @BotFather → /revoke yoki boshqa joyda webhook yoqilgan bo'lsa, o'chiring.\n"
            "- Agar bot o'chgan bo'lsa-yu .vetzona_bot.lock qolgan bo'lsa, uni o'chirib qayta urinib ko'ring."
        ) from None

    os.write(fd, str(os.getpid()).encode("ascii", errors="replace"))

    def _release() -> None:
        try:
            os.close(fd)
        finally:
            try:
                _LOCK_PATH.unlink(missing_ok=True)
            except OSError:
                pass

    atexit.register(_release)


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO)

    class _DemoteTelegramNoise(logging.Filter):
        """Conflict / vaqtincha tarmoq xatolari ERROR o'rniga WARNING — terminal chalkashmasin."""

        def filter(self, record: logging.LogRecord) -> bool:
            msg = record.getMessage()
            if record.levelno < logging.ERROR:
                return True
            if any(
                x in msg
                for x in (
                    "TelegramConflictError",
                    "TelegramNetworkError",
                    "ServerDisconnectedError",
                    "ClientConnectorError",
                )
            ):
                record.levelno = logging.WARNING
                record.levelname = "WARNING"
            return True

    class _UnhandledToDebug(logging.Filter):
        """'is not handled' faqat DEBUG da (INFO chiqmaydi)."""

        def filter(self, record: logging.LogRecord) -> bool:
            if "is not handled" in record.getMessage():
                record.levelno = logging.DEBUG
                record.levelname = "DEBUG"
            return True

    for name in ("aiogram.dispatcher", "aiogram.client.session.aiohttp"):
        logging.getLogger(name).addFilter(_DemoteTelegramNoise())
    logging.getLogger("aiogram.event").addFilter(_UnhandledToDebug())


async def main() -> None:
    settings = get_settings()
    db = Database(settings.database_path)
    await db.init()

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp["settings"] = settings
    dp["db"] = db
    dp["gemini"] = GeminiService(api_key=settings.gemini_api_key, model_name=settings.gemini_model)

    dp.include_router(setup_routers())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    warnings.filterwarnings(
        "ignore",
        category=FutureWarning,
        message=r".*google\.generativeai.*",
    )
    _acquire_single_instance_lock()
    _configure_logging()
    logging.getLogger("google.genai").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot to'xtatildi (Ctrl+C).")

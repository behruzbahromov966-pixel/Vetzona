from aiogram import Router

from app.handlers.admin import router as admin_router
from app.handlers.ai_chat import router as ai_chat_router
from app.handlers.cooperation import router as cooperation_router
from app.handlers.referrals import router as referrals_router
from app.handlers.pharmacies import router as pharmacies_router
from app.handlers.start import router as start_router


def setup_routers() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(admin_router)
    router.include_router(ai_chat_router)
    router.include_router(referrals_router)
    router.include_router(pharmacies_router)
    router.include_router(cooperation_router)
    return router

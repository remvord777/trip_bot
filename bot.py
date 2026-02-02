import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db.database import init_db

# handlers
from handlers import start, auth
from handlers.trip import trip, calendar


async def main():
    # ─────────────────────
    # ИНИЦИАЛИЗАЦИЯ БД
    # ─────────────────────
    init_db()

    # ─────────────────────
    # BOT / DISPATCHER
    # ─────────────────────
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # ─────────────────────
    # ROUTERS
    # порядок важен ТОЛЬКО для auth
    # ─────────────────────
    dp.include_router(auth.router)
    dp.include_router(start.router)
    dp.include_router(trip.router)
    dp.include_router(calendar.router)

    # ─────────────────────
    # START
    # ─────────────────────
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db.database import init_db

# handlers
from handlers import auth
from handlers import start as start_handler

from handlers.trip import trip, calendar, mail, advance
from handlers.advance_report import (
    start as ar_start,
    choose_trip,
    upload_files,
    amounts,
)


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
    # ─────────────────────

    # auth / главное меню
    dp.include_router(auth.router)
    dp.include_router(start_handler.router)

    # командировка
    dp.include_router(trip.router)
    dp.include_router(calendar.router)
    dp.include_router(advance.router)
    dp.include_router(mail.router)

    # авансовый отчёт
    dp.include_router(ar_start.router)
    dp.include_router(choose_trip.router)
    dp.include_router(upload_files.router)
    dp.include_router(amounts.router)

    # ─────────────────────
    # START
    # ─────────────────────
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

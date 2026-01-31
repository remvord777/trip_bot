import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import start, trip
from db.database import init_db


async def main():
    # 🔹 ВАЖНО: инициализация БД ДО запуска бота
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(trip.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

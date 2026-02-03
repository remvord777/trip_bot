import asyncio
import logging
import os
from pathlib import Path
from pathlib import Path   # ← ВОТ ЭТОГО НЕ ХВАТАЛО
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers.start import router as start_router
from handlers.trip.router import router as trip_router


# ================== ENV ==================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env.dev")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

# ================== LOGGING ==================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

# ================== BOT ==================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================== ROUTERS ==================

dp.include_router(start_router)
dp.include_router(trip_router)

# ================== MAIN ==================

async def main():
    logger.info("🚀 Starting polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

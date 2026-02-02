import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers import start, trip

from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
# ================== ENV ==================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ================== LOGGING ==================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ================== BOT ==================
bot = Bot(token=BOT_TOKEN)

# 🔥 ОБЯЗАТЕЛЬНО: FSM storage
dp = Dispatcher(storage=MemoryStorage())

# ================== ROUTERS ==================
dp.include_router(start.router)
dp.include_router(trip.router)

# ================== MAIN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

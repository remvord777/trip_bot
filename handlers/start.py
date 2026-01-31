from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.main import main_menu
from db.database import get_all_trips

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "Привет 👋\n"
        "Я помогу вести учёт командировок по России.\n\n"
        "Выберите действие:",
        reply_markup=main_menu
    )


@router.message(lambda message: message.text == "📋 Мои командировки")
async def my_trips(message: Message):
    trips = get_all_trips()

    if not trips:
        await message.answer("📋 Командировок пока нет.")
        return

    text = "📋 Ваши командировки:\n\n"

    for trip in trips:
        trip_id, city, place, date_from, date_to, purpose = trip

        text += (
            f"#{trip_id}\n"
            f"🏙 {city}\n"
            f"🏢 {place}\n"
            f"📅 {date_from} → {date_to}\n"
            f"🎯 {purpose}\n\n"
        )

    await message.answer(text)


@router.message(lambda message: message.text == "ℹ️ Помощь")
async def help_message(message: Message):
    await message.answer(
        "ℹ️ Помощь\n\n"
        "Этот бот помогает вести учёт командировок:\n"
        "— создание командировок\n"
        "— просмотр истории\n"
        "— хранение данных"
    )

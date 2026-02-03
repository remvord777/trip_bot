from data.trips_store import load_trips
import logging

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from data.trips_store import load_trips
from handlers.expense.states import ExpenseStates

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "💰 Авансовый отчёт")
async def expense_entry(message: Message, state: FSMContext):
    logger.info("EXPENSE ENTRY | telegram_id=%s", message.from_user.id)

    await state.clear()

    telegram_id = str(message.from_user.id)
    all_trips = load_trips()
    trips = all_trips.get(telegram_id, [])

    if not trips:
        await message.answer(
            "❗ У вас пока нет оформленных командировок.\n\n"
            "Сначала оформите командировку через пункт «🧳 Командировка»."
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{t['date_from']}–{t['date_to']} | {t['object_name']}",
                    callback_data=f"expense_trip:{t['trip_id']}",
                )
            ]
            for t in trips
        ]
    )

    await message.answer(
        "📊 Выберите командировку для авансового отчёта:",
        reply_markup=keyboard,
    )

    await state.set_state(ExpenseStates.select_trip)


# ======================================================
# SELECT TRIP
# ======================================================

@router.callback_query(
    ExpenseStates.select_trip,
    F.data.startswith("expense_trip:")
)
async def expense_trip_selected(call: CallbackQuery, state: FSMContext):
    trip_id = int(call.data.replace("expense_trip:", ""))
    telegram_id = str(call.from_user.id)

    all_trips = load_trips()
    trips = all_trips.get(telegram_id, [])
    trip = next((t for t in trips if t["trip_id"] == trip_id), None)

    if not trip:
        await call.answer("Командировка не найдена", show_alert=True)
        return

    await state.update_data(
        trip_id=trip_id,
        trip=trip,
        expense_files=[],
    )

    await call.message.answer(
        "📊 Авансовый отчёт\n\n"
        "Выбрана командировка:\n"
        f"📍 {trip['object_name']}\n"
        f"📅 {trip['date_from']} – {trip['date_to']}\n"
        f"🧮 {trip.get('total', '—')} дней\n\n"
        "📎 Пришлите чеки, фото или скриншоты.\n"
        "Можно отправлять несколько сообщений.\n\n"
        "Когда закончите — напишите «Готово»."
    )

    await state.set_state(ExpenseStates.upload_files)
    await call.answer()


# ======================================================
# UPLOAD FILES
# ======================================================

@router.message(
    ExpenseStates.upload_files,
    F.photo | F.document
)
async def expense_files_upload(message: Message, state: FSMContext):
    data = await state.get_data()
    files = data.get("expense_files", [])

    if message.photo:
        files.append({
            "type": "photo",
            "file_id": message.photo[-1].file_id,
        })

    if message.document:
        files.append({
            "type": "document",
            "file_id": message.document.file_id,
            "name": message.document.file_name,
        })

    await state.update_data(expense_files=files)

    await message.answer(
        f"📎 Файл принят (всего файлов: {len(files)})\n"
        "Можете отправить ещё или написать «Готово»."
    )


# ======================================================
# FINISH
# ======================================================

@router.message(
    ExpenseStates.upload_files,
    F.text.lower() == "готово"
)
async def expense_done(message: Message, state: FSMContext):
    data = await state.get_data()

    trip = data.get("trip")
    files = data.get("expense_files", [])

    await message.answer(
        "✅ Файлы приняты.\n\n"
        "Командировка:\n"
        f"📍 {trip['object_name']}\n"
        f"📅 {trip['date_from']} – {trip['date_to']}\n"
        f"📎 Файлов: {len(files)}\n\n"
        "Формирование авансового отчёта будет добавлено следующим шагом."
    )

    await state.clear()

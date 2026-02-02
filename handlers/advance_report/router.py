import os

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext

from keyboards.main import main_menu
from keyboards.trips import trips_select_keyboard
from states.advance_report import AdvanceReportStates
from db.database import get_connection

router = Router()

# ─────────────────────
# 📄 СТАРТ АВАНСОВОГО ОТЧЁТА
# ─────────────────────
@router.message(F.text == "📄 Авансовый отчёт")
async def start_advance_report(message: Message, state: FSMContext):
    await state.clear()

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, city, place, date_from, date_to
        FROM trips
        ORDER BY date_from DESC
        """
    ).fetchall()
    conn.close()

    if not rows:
        await message.answer(
            "Нет командировок для авансового отчёта.",
            reply_markup=main_menu,
        )
        return

    trips = [
        {
            "id": r[0],
            "city": r[1],
            "place": r[2],
            "date_from": r[3],
            "date_to": r[4],
        }
        for r in rows
    ]

    await message.answer(
        "📄 Выберите командировку:",
        reply_markup=trips_select_keyboard(trips),
    )
    await state.set_state(AdvanceReportStates.choose_trip)


# ─────────────────────
# ВЫБОР КОМАНДИРОВКИ
# ─────────────────────
@router.callback_query(
    AdvanceReportStates.choose_trip,
    F.data.startswith("trip:")
)
async def choose_trip(call: CallbackQuery, state: FSMContext):
    trip_id = int(call.data.split(":")[1])

    await state.update_data(
        trip_id=trip_id,
        files=[],
    )

    await call.message.answer(
        "📎 Загрузите чеки / билеты (фото или PDF).\n\n"
        "Когда закончите — нажмите «Готово».",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Готово")]],
            resize_keyboard=True,
        ),
    )

    await state.set_state(AdvanceReportStates.upload_files)
    await call.answer()


# ─────────────────────
# ЗАГРУЗКА ФАЙЛОВ
# ─────────────────────
@router.message(
    AdvanceReportStates.upload_files,
    F.photo | F.document
)
async def upload_files(message: Message, state: FSMContext):
    data = await state.get_data()
    trip_id = data.get("trip_id")

    if not trip_id:
        await message.answer("❌ Ошибка: не выбрана командировка.")
        return

    base_dir = f"storage/advance_reports/{trip_id}"
    os.makedirs(base_dir, exist_ok=True)

    if message.photo:
        file = message.photo[-1]
        filename = f"{file.file_id}.jpg"
    else:
        file = message.document
        filename = file.file_name

    path = os.path.join(base_dir, filename)
    await message.bot.download(file, destination=path)

    files = data.get("files", [])
    files.append(path)

    await state.update_data(files=files)

    await message.answer(
        f"📎 Добавлено файлов: {len(files)}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Готово")]],
            resize_keyboard=True,
        ),
    )


# ─────────────────────
# КНОПКА «ГОТОВО»
# ─────────────────────
@router.message(
    AdvanceReportStates.upload_files,
    F.text == "Готово"
)
async def finish_upload(message: Message, state: FSMContext):
    data = await state.get_data()

    if not data.get("files"):
        await message.answer(
            "Вы не загрузили ни одного файла.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Готово")]],
                resize_keyboard=True,
            ),
        )
        return

    await message.answer(
        "Введите общую сумму расходов:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(AdvanceReportStates.enter_amounts)


# ─────────────────────
# ВВОД СУММЫ (MVP ФИНИШ)
# ─────────────────────
@router.message(AdvanceReportStates.enter_amounts)
async def enter_amounts(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите сумму цифрами")
        return

    await state.update_data(total_amount=message.text)

    await message.answer(
        "✅ Авансовый отчёт принят (MVP).",
        reply_markup=main_menu,
    )
    await state.clear()

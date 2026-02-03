import logging
from datetime import date
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest

from keyboards.locations import locations_keyboard
from keyboards.trip_calendar import current_calendar, build_calendar
from keyboards.purpose import purpose_keyboard
from keyboards.confirm import confirm_keyboard

from utils.docx_render import render_docx

logger = logging.getLogger(__name__)
router = Router()


# ================== FSM ==================

class TripStates(StatesGroup):
    location = State()
    date_from = State()
    date_to = State()
    purpose = State()
    confirm = State()


# ================== START ==================

@router.message(F.text == "🧳 Командировка")
async def trip_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📍 Выберите место командировки:",
        reply_markup=locations_keyboard(),
    )
    await state.set_state(TripStates.location)


# ================== LOCATION ==================

@router.message(TripStates.location)
async def trip_location(message: Message, state: FSMContext):
    await state.update_data(city=message.text)

    today = date.today()
    await state.update_data(cal_year=today.year, cal_month=today.month)

    await message.answer(
        "🟢 Дата начала командировки:",
        reply_markup=current_calendar(),
    )
    await state.set_state(TripStates.date_from)


# ================== CALENDAR NAV ==================

@router.callback_query(F.data.in_(["prev_month", "next_month"]))
async def calendar_nav(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    year = data["cal_year"]
    month = data["cal_month"]

    if call.data == "prev_month":
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    else:
        month += 1
        if month == 13:
            month = 1
            year += 1

    await state.update_data(cal_year=year, cal_month=month)

    try:
        await call.message.edit_reply_markup(
            reply_markup=build_calendar(year, month)
        )
    except TelegramBadRequest:
        pass

    await call.answer()


# ================== DATE SELECT ==================

@router.callback_query(F.data.startswith("date:"))
async def calendar_date_selected(call: CallbackQuery, state: FSMContext):
    selected_date = call.data.split("date:")[1]
    current_state = await state.get_state()

    # ===== ДАТА НАЧАЛА =====
    if current_state == TripStates.date_from:
        await state.update_data(date_from=selected_date)

        await call.message.answer(
            f"🟢 Дата начала выбрана: <b>{selected_date}</b>\n\n"
            "🔴 Теперь выберите дату окончания:",
            reply_markup=current_calendar(),
            parse_mode="HTML",
        )

        await state.set_state(TripStates.date_to)

    # ===== ДАТА ОКОНЧАНИЯ =====
    elif current_state == TripStates.date_to:
        await state.update_data(date_to=selected_date)

        await call.message.answer(
            f"🔴 Дата окончания выбрана: <b>{selected_date}</b>\n\n"
            "🛠 Теперь выберите сервисную услугу:",
            reply_markup=purpose_keyboard(),
            parse_mode="HTML",
        )

        await state.set_state(TripStates.purpose)

    await call.answer()


# ================== PURPOSE → SUMMARY + DOCX ==================

@router.callback_query(TripStates.purpose)
async def trip_purpose(call: CallbackQuery, state: FSMContext):
    await state.update_data(purpose=call.data)
    data = await state.get_data()

    employee_name = data.get("name", "—")
    position = data.get("position", "—")

    # ===== формируем DOCX =====
    docx_path: Path = render_docx(
        template_name="service_task.docx",
        data={
            "employee_name": employee_name,
            "position": position,
            "city": data["city"],
            "date_from": data["date_from"],
            "date_to": data["date_to"],
            "purpose": data["purpose"],
        },
    )

    await state.update_data(docx_file=str(docx_path))

    # ===== итог =====
    text = (
        "🔎 Проверь данные командировки:\n\n"
        f"👤 Сотрудник: {employee_name}\n"
        f"💼 Должность: {position}\n"
        f"📍 Город: {data['city']}\n"
        f"🟢 Начало: {data['date_from']}\n"
        f"🔴 Окончание: {data['date_to']}\n"
        f"🛠 Услуга: {data['purpose']}\n\n"
        "📄 Служебное задание сформировано.\n"
        "Подтвердить?"
    )

    await call.message.answer(
        text,
        reply_markup=confirm_keyboard(),
    )

    await state.set_state(TripStates.confirm)
    await call.answer()


# ================== CONFIRM ==================

@router.callback_query(TripStates.confirm, F.data == "confirm")
async def trip_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await call.message.answer(
        "✅ Командировка подтверждена.\n"
        f"📄 Файл готов:\n<code>{data['docx_file']}</code>",
        parse_mode="HTML",
    )

    await state.clear()
    await call.answer()


@router.callback_query(TripStates.confirm, F.data == "edit")
async def trip_edit(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(
        "✏️ Начнём заново.\nВыберите место командировки:",
        reply_markup=locations_keyboard(),
    )
    await state.set_state(TripStates.location)
    await call.answer()

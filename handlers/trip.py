from datetime import date, datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from states.trip import TripStates
from keyboards.main import (
    main_menu,
    city_keyboard,
    object_keyboard,
    cancel_keyboard
)
from keyboards.calendar import build_calendar, current_calendar
from db.database import get_connection

router = Router()


# ───────────────
# ГЛОБАЛЬНАЯ ОТМЕНА
# ───────────────
@router.message(StateFilter("*"), F.text == "❌ Отмена")
async def cancel_anywhere(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Процесс отменён", reply_markup=main_menu)


# ───────────────
# СТАРТ
# ───────────────
@router.message(F.text == "🧳 Новая командировка")
async def start_trip(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "──────────────\n"
        "📍 МЕСТО КОМАНДИРОВКИ\n"
        "──────────────\n\n"
        "🏙 Город\n"
        "(начните вводить или выберите из популярных)",
        reply_markup=city_keyboard()
    )
    await state.set_state(TripStates.city)


# ───────────────
# ГОРОД
# ───────────────
@router.message(TripStates.city)
async def set_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer(
        "🏢 Объект\n"
        "(введите или выберите)",
        reply_markup=object_keyboard()
    )

    await state.set_state(TripStates.object)


# ───────────────
# ОБЪЕКТ
# ───────────────
@router.message(TripStates.object)
async def set_object(message: Message, state: FSMContext):
    await state.update_data(object=message.text)

    today = date.today()
    await state.update_data(cal=(today.year, today.month))

    await message.answer(
        "──────────────\n"
        "📅 ДАТЫ КОМАНДИРОВКИ\n"
        "──────────────\n\n"
        "🟢 Начало",
        reply_markup=current_calendar()
    )
    await state.set_state(TripStates.date_from)


# ───────────────
# КАЛЕНДАРЬ — ДАТА НАЧАЛА
# ───────────────
@router.callback_query(TripStates.date_from)
async def calendar_date_from(call: CallbackQuery, state: FSMContext):
    if call.data == "ignore":
        await call.answer()
        return

    data = await state.get_data()
    year, month = data.get("cal", (date.today().year, date.today().month))

    if call.data == "prev":
        month -= 1
        if month == 0:
            month = 12
            year -= 1

    elif call.data == "next":
        month += 1
        if month == 13:
            month = 1
            year += 1

    elif call.data.startswith("date:"):
        selected = call.data.split(":")[1]
        await state.update_data(date_from=selected)

        # 🔥 убираем календарь
        await call.message.edit_reply_markup(reply_markup=None)

        await call.message.answer(
            f"🟢 Начало: {selected}\n\n"
            "🔴 Окончание",
            reply_markup=current_calendar()
        )
        await state.set_state(TripStates.date_to)
        await call.answer()
        return

    await state.update_data(cal=(year, month))
    await call.message.edit_reply_markup(reply_markup=build_calendar(year, month))
    await call.answer()


# ───────────────
# КАЛЕНДАРЬ — ДАТА ОКОНЧАНИЯ
# ───────────────
@router.callback_query(TripStates.date_to)
async def calendar_date_to(call: CallbackQuery, state: FSMContext):
    if call.data == "ignore":
        await call.answer()
        return

    data = await state.get_data()
    year, month = data.get("cal", (date.today().year, date.today().month))

    if call.data == "prev":
        month -= 1
        if month == 0:
            month = 12
            year -= 1

    elif call.data == "next":
        month += 1
        if month == 13:
            month = 1
            year += 1

    elif call.data.startswith("date:"):
        selected = call.data.split(":")[1]

        start = datetime.strptime(data["date_from"], "%d.%m.%Y")
        end = datetime.strptime(selected, "%d.%m.%Y")

        if end < start:
            await call.answer(
                "Дата окончания не может быть раньше даты начала",
                show_alert=True
            )
            return

        await state.update_data(date_to=selected)

        # 🔥 убираем календарь
        await call.message.edit_reply_markup(reply_markup=None)

        await call.message.answer(
            f"🔴 Окончание: {selected}\n\n"
            "──────────────\n"
            "🎯 ЦЕЛЬ КОМАНДИРОВКИ\n"
            "──────────────",
            reply_markup=cancel_keyboard
        )
        await state.set_state(TripStates.purpose)
        await call.answer()
        return

    await state.update_data(cal=(year, month))
    await call.message.edit_reply_markup(reply_markup=build_calendar(year, month))
    await call.answer()


# ───────────────
# ЦЕЛЬ + СОХРАНЕНИЕ
# ───────────────
@router.message(TripStates.purpose)
async def finish_trip(message: Message, state: FSMContext):
    await state.update_data(purpose=message.text)
    data = await state.get_data()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO trips (city, place, date_from, date_to, purpose)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data["city"],
            data["object"],
            data["date_from"],
            data["date_to"],
            data["purpose"]
        )
    )
    conn.commit()
    conn.close()

    await message.answer(
        "✅ КОМАНДИРОВКА СОХРАНЕНА\n\n"
        f"🏙 Город: {data['city']}\n"
        f"🏢 Объект: {data['object']}\n\n"
        "📅 Даты:\n"
        f"🟢 {data['date_from']}\n"
        f"🔴 {data['date_to']}\n\n"
        "🎯 Цель:\n"
        f"{data['purpose']}",
        reply_markup=main_menu
    )

    await state.clear()

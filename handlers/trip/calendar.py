from datetime import datetime
from keyboards.main import purpose_keyboard
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from states.trip import TripStates
from keyboards.calendar import build_calendar, current_calendar

router = Router()


@router.callback_query(TripStates.date_from)
async def calendar_date_from(call: CallbackQuery, state: FSMContext):
    if call.data == "ignore":
        await call.answer()
        return

    data = await state.get_data()
    year, month = data["cal"]

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
        await call.message.edit_reply_markup(reply_markup=None)

        await call.message.answer(
            f"🟢 Начало: {selected}\n\n🔴 Окончание",
            reply_markup=current_calendar(),
        )
        await state.set_state(TripStates.date_to)
        await call.answer()
        return  # 🔴 важно — без мигания

    await state.update_data(cal=(year, month))
    await call.message.edit_reply_markup(build_calendar(year, month))
    await call.answer()


@router.callback_query(TripStates.date_to)
async def calendar_date_to(call: CallbackQuery, state: FSMContext):
    if call.data == "ignore":
        await call.answer()
        return

    data = await state.get_data()
    year, month = data["cal"]

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
                "Дата окончания раньше даты начала",
                show_alert=True,
            )
            return

        await state.update_data(date_to=selected)
        await call.message.edit_reply_markup(reply_markup=None)

        await call.message.answer(
            f"🔴 Окончание: {selected}\n\n🎯 Цель командировки",
            reply_markup=purpose_keyboard(),
        )

        await state.set_state(TripStates.purpose)
        await call.answer()
        return

    await state.update_data(cal=(year, month))
    await call.message.edit_reply_markup(build_calendar(year, month))
    await call.answer()

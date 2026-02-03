import logging
from datetime import date

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest

from keyboards.locations import locations_keyboard
from keyboards.trip_calendar import current_calendar, build_calendar
from keyboards.purpose import purpose_keyboard
from keyboards.email_targets import email_targets_keyboard
from keyboards.confirm import confirm_keyboard

from utils.docx_render import render_docx
from utils.mailer import send_email
from data.email_targets import EMAIL_TARGETS

logger = logging.getLogger(__name__)
router = Router()


# ================== FSM ==================

class TripStates(StatesGroup):
    location = State()
    date_from = State()
    date_to = State()
    purpose = State()
    recipients = State()
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

    if current_state == TripStates.date_from:
        await state.update_data(date_from=selected_date)

        await call.message.edit_text(
            "🔴 Дата окончания командировки:",
            reply_markup=current_calendar(),
        )
        await state.set_state(TripStates.date_to)

    elif current_state == TripStates.date_to:
        await state.update_data(date_to=selected_date)

        await call.message.edit_text(
            "🛠 Выберите сервисную услугу:",
            reply_markup=purpose_keyboard(),
        )
        await state.set_state(TripStates.purpose)

    await call.answer()


# ================== PURPOSE ==================

@router.callback_query(TripStates.purpose)
async def trip_purpose(call: CallbackQuery, state: FSMContext):
    await state.update_data(purpose=call.data)
    await state.update_data(emails=[])

    await call.message.answer(
        "📧 Выберите получателей:",
        reply_markup=email_targets_keyboard(selected=[]),
    )
    await state.set_state(TripStates.recipients)
    await call.answer()


# ================== RECIPIENTS ==================

@router.callback_query(TripStates.recipients)
async def trip_recipients(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("emails", [])
    value = call.data

    if value == "emails_done":
        if not selected:
            await call.answer("❗ Выберите получателя", show_alert=True)
            return

        preview = "\n".join(
            f"• {EMAIL_TARGETS[a]}"
            for a in selected
        )

        text = (
            "🔎 Проверь данные:\n\n"
            f"📍 Город: {data['city']}\n"
            f"🟢 Начало: {data['date_from']}\n"
            f"🔴 Окончание: {data['date_to']}\n"
            f"🛠 Услуга: {data['purpose']}\n"
            f"📧 Получатели:\n{preview}\n\n"
            "Подтвердить?"
        )

        await call.message.answer(text, reply_markup=confirm_keyboard())
        await state.set_state(TripStates.confirm)
        await call.answer()
        return

    if value in selected:
        selected.remove(value)
    else:
        selected.append(value)

    await state.update_data(emails=selected)

    try:
        await call.message.edit_reply_markup(
            reply_markup=email_targets_keyboard(selected=selected)
        )
    except TelegramBadRequest:
        pass

    await call.answer()


# ================== CONFIRM ==================

@router.callback_query(TripStates.confirm, F.data == "confirm")
async def trip_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    docx_file = render_docx(
        template_name="service_task.docx",
        data=data,
    )

    to_emails = [EMAIL_TARGETS[a] for a in data["emails"]]

    send_email(
        to_emails=to_emails,
        subject="Служебное задание",
        body="Служебное задание во вложении.",
        attachment=docx_file,
    )

    await call.message.answer("✅ Командировка оформлена")
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

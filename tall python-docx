from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards.locations import locations_keyboard
from keyboards.calendar import current_calendar
from keyboards.purpose import purpose_keyboard
from keyboards.confirm import confirm_keyboard

from utils.docx_render import render_docx
from utils.mailer import send_email

import logging

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
    await state.update_data(cal=current_calendar())
    await message.answer(
        "🟢 Дата начала командировки:",
        reply_markup=current_calendar(),
    )
    await state.set_state(TripStates.date_from)


# ================== PURPOSE ==================

@router.callback_query(TripStates.purpose)
async def trip_purpose_selected(call: CallbackQuery, state: FSMContext):
    await state.update_data(purpose=call.data)
    data = await state.get_data()

    text = (
        "🔎 Проверь данные:\n\n"
        f"Город: {data['city']}\n"
        f"Начало: {data['date_from']}\n"
        f"Окончание: {data['date_to']}\n"
        f"Цель: {data['purpose']}\n\n"
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

    # 👤 сотрудник (кладётся в FSM при /start)
    employee_name = data["employee_name"]
    position = data["position"]

    # 📄 формируем документ
    docx_file = render_docx(
        template_name="service_task.docx",
        data={
            **data,
            "employee_name": employee_name,
            "position": position,
        },
    )

    # 📧 получатели
    to_emails = [
        "vorobev@intermatic.energy",
        "",
    ]

    send_email(
        to_emails=to_emails,
        subject="Служебное задание",
        body="Служебное задание во вложении.",
        attachment=docx_file,
    )

    emails_text = "\n".join(f"• {email}" for email in to_emails)

    await call.message.answer(
        "✅ Командировка оформлена\n\n"
        "📧 Документы отправлены:\n"
        f"{emails_text}"
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

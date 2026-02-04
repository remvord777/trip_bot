# handlers/expense/router.py

import logging
from datetime import datetime
from pathlib import Path

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)
from aiogram.fsm.context import FSMContext

from handlers.expense.states import ExpenseStates
from keyboards.email_targets import email_targets_keyboard
from data.email_targets import EMAIL_TARGETS

from data.trips_store import load_trips
from data.advances_store import add_advance
from data.employees import EMPLOYEES
from utils.docx_render import render_docx
from utils.mailer import send_email

logger = logging.getLogger(__name__)
router = Router()

PER_DIEM_RATE = 1200


# ======================================================
# ENTRY
# ======================================================

@router.message(F.text == "💰 Авансовый отчёт")
async def expense_entry(message: Message, state: FSMContext):
    await state.clear()

    telegram_id = str(message.from_user.id)
    trips = load_trips().get(telegram_id, [])

    if not trips:
        await message.answer(
            "❗ У вас пока нет оформленных командировок.\n\n"
            "Сначала оформите командировку через «🧳 Командировка»."
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
    trip_id = int(call.data.split(":")[1])
    telegram_id = str(call.from_user.id)

    trips = load_trips().get(telegram_id, [])
    trip = next((t for t in trips if t["trip_id"] == trip_id), None)

    if not trip:
        await call.answer("Командировка не найдена", show_alert=True)
        return

    days = int(trip["total"])
    per_diem_total = days * PER_DIEM_RATE

    await state.update_data(
        trip=trip,
        days=days,
        per_diem_rate=PER_DIEM_RATE,
        per_diem_total=per_diem_total,
    )

    await call.message.answer(
        "📊 Авансовый расчёт\n\n"
        f"📍 {trip['object_name']}\n"
        f"📅 {trip['date_from']} – {trip['date_to']}\n"
        f"🧮 Дней: {days}\n\n"
        f"💰 Суточные: {days} × {PER_DIEM_RATE} ₽ = "
        f"<b>{per_diem_total:,} ₽</b>\n\n"
        "🏨 Выберите тип проживания:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏨 Гостиница", callback_data="acc:hotel")],
                [InlineKeyboardButton(text="🏠 Апартаменты", callback_data="acc:apart")],
                [InlineKeyboardButton(text="🚫 Не требуется", callback_data="acc:none")],
            ]
        ),
        parse_mode="HTML"
    )

    await state.set_state(ExpenseStates.select_accommodation)
    await call.answer()


# ======================================================
# ACCOMMODATION
# ======================================================

@router.callback_query(
    ExpenseStates.select_accommodation,
    F.data.startswith("acc:")
)
async def accommodation_selected(call: CallbackQuery, state: FSMContext):
    acc_type = call.data.split(":")[1]

    if acc_type == "none":
        await state.update_data(accommodation_amount=0)
        await call.message.answer("🚕 Введите сумму такси (₽):")
        await state.set_state(ExpenseStates.input_taxi_amount)
    else:
        await call.message.answer("🏨 Введите сумму проживания (₽):")
        await state.set_state(ExpenseStates.input_accommodation_amount)

    await call.answer()


@router.message(
    ExpenseStates.input_accommodation_amount,
    F.text.regexp(r"^\d+$")
)
async def accommodation_amount(message: Message, state: FSMContext):
    await state.update_data(accommodation_amount=int(message.text))
    await message.answer("🚕 Введите сумму такси (₽):")
    await state.set_state(ExpenseStates.input_taxi_amount)


# ======================================================
# TAXI
# ======================================================

@router.message(
    ExpenseStates.input_taxi_amount,
    F.text.regexp(r"^\d+$")
)
async def taxi_amount(message: Message, state: FSMContext):
    await state.update_data(taxi_amount=int(message.text))

    await message.answer(
        "✈️🚆 Выберите тип билетов:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✈️ Авиа", callback_data="ticket:avia")],
                [InlineKeyboardButton(text="🚆 ЖД", callback_data="ticket:rail")],
                [InlineKeyboardButton(text="🚫 Не требуется", callback_data="ticket:none")],
            ]
        )
    )
    await state.set_state(ExpenseStates.select_ticket_type)


# ======================================================
# TICKETS
# ======================================================

@router.callback_query(
    ExpenseStates.select_ticket_type,
    F.data.startswith("ticket:")
)
async def ticket_type_selected(call: CallbackQuery, state: FSMContext):
    ticket_type = call.data.split(":")[1]

    if ticket_type == "none":
        await state.update_data(ticket_amount=0)
        await show_confirm(call, state)
    else:
        await call.message.answer("Введите сумму билетов (₽):")
        await state.set_state(ExpenseStates.input_ticket_amount)

    await call.answer()


@router.message(
    ExpenseStates.input_ticket_amount,
    F.text.regexp(r"^\d+$")
)
async def ticket_amount(message: Message, state: FSMContext):
    await state.update_data(ticket_amount=int(message.text))
    await show_confirm(message, state)


# ======================================================
# CONFIRM
# ======================================================

async def show_confirm(target, state: FSMContext):
    data = await state.get_data()

    total = (
        data["per_diem_total"]
        + data.get("accommodation_amount", 0)
        + data.get("taxi_amount", 0)
        + data.get("ticket_amount", 0)
    )

    await state.update_data(total_amount=total)

    await target.answer(
        "📋 Авансовый расчёт\n\n"
        f"💰 Суточные: {data['per_diem_total']:,} ₽\n"
        f"🏨 Проживание: {data.get('accommodation_amount', 0):,} ₽\n"
        f"🚕 Такси: {data.get('taxi_amount', 0):,} ₽\n"
        f"✈️🚆 Билеты: {data.get('ticket_amount', 0):,} ₽\n\n"
        f"<b>💵 ИТОГО: {total:,} ₽</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Подтвердить", callback_data="advance_confirm")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="advance_cancel")],
            ]
        ),
        parse_mode="HTML"
    )

    await state.set_state(ExpenseStates.confirm)


# ======================================================
# SAVE + DOCX + EMAIL
# ======================================================

@router.callback_query(
    ExpenseStates.confirm,
    F.data == "advance_confirm"
)
async def advance_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    telegram_id = call.from_user.id

    trip = data["trip"]
    employee = EMPLOYEES.get(telegram_id, {})

    docx_data = {
        "employee_name": employee.get("employee_name", ""),
        "employee_short": employee.get("employee_short", ""),
        "position": employee.get("position", ""),
        "department": trip.get("department", ""),
        "object_name": trip.get("object_name", ""),
        "contract": trip.get("contract", ""),
        "organization": trip.get("organization", ""),
        "purpose": trip.get("service", ""),
        "date_from": trip.get("date_from", "")[:5],
        "date_to": trip.get("date_to", "")[:5],
        "report_date": datetime.now().strftime("%d.%m.%Y"),
        "accommodation_amount": str(data.get("accommodation_amount", 0)),
        "taxi_amount": str(data.get("taxi_amount", 0)),
        "ticket_amount": str(data.get("ticket_amount", 0)),
        "per_diem_total": str(data.get("per_diem_total", 0)),
        "total_amount": str(data.get("total_amount", 0)),
    }

    docx_path = Path(render_docx("advance_report.docx", docx_data))
    await state.update_data(advance_docx=docx_path, email_targets=[])

    await call.message.answer_document(
        FSInputFile(docx_path),
        caption="📄 Авансовый отчёт сформирован"
    )

    await state.set_state(ExpenseStates.email_select)
    await call.message.answer(
        "📤 Куда отправить авансовый отчёт?",
        reply_markup=email_targets_keyboard([])
    )

    await call.answer()


@router.callback_query(
    ExpenseStates.email_select,
    F.data.startswith("email:")
)
async def advance_email_select(call: CallbackQuery, state: FSMContext):
    action = call.data.replace("email:", "")
    data = await state.get_data()
    selected = data.get("email_targets", [])

    if action == "send":
        if not selected:
            await call.answer("Выберите получателя", show_alert=True)
            return

        recipients = []
        employee = EMPLOYEES.get(call.from_user.id, {})

        for key in selected:
            if key == "me":
                recipients.append(employee.get("email", ""))
            else:
                recipients.append(EMAIL_TARGETS.get(key, ""))

        recipients = [r for r in recipients if r]

        send_email(
            to_emails=recipients,
            subject="Авансовый отчёт",
            body="Во вложении авансовый отчёт.",
            attachments=[data["advance_docx"]],
        )

        await call.message.answer("✅ Авансовый отчёт отправлен")
        await state.clear()
        await call.answer()
        return

    if action in selected:
        selected.remove(action)
    else:
        selected.append(action)

    await state.update_data(email_targets=selected)
    await call.message.edit_reply_markup(
        reply_markup=email_targets_keyboard(selected)
    )
    await call.answer()


@router.callback_query(
    ExpenseStates.confirm,
    F.data == "advance_cancel"
)
async def advance_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ Аванс отменён.")
    await call.answer()

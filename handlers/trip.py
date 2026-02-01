from datetime import date, datetime

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from states.trip import TripStates
from keyboards.main import (
    main_menu,
    city_keyboard,
    object_keyboard,
    purpose_keyboard,
    confirm_keyboard,
    employee_keyboard,
)
from keyboards.calendar import build_calendar, current_calendar
from db.database import get_connection
from utils.docx_generator import generate_service_task
from utils.advance_docx_generator import generate_advance_request
from utils.mailer import send_email_with_attachments

router = Router()


# ─────────────────────
# ГЛОБАЛЬНАЯ ОТМЕНА
# ─────────────────────
@router.message(StateFilter("*"), F.text == "❌ Отмена")
async def cancel_anywhere(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Процесс оформления командировки отменён",
        reply_markup=main_menu
    )


# ─────────────────────
# СТАРТ
# ─────────────────────
@router.message(F.text == "🧳 Новая командировка")
async def start_trip(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "──────────────\n"
        "📍 МЕСТО КОМАНДИРОВКИ\n"
        "──────────────\n\n"
        "🏙 Населённый пункт",
        reply_markup=city_keyboard()
    )
    await state.set_state(TripStates.city)


# ─────────────────────
# НАСЕЛЁННЫЙ ПУНКТ
# ─────────────────────
@router.message(TripStates.city)
async def set_city(message: Message, state: FSMContext):
    await state.update_data(city_raw=message.text)
    await message.answer(
        "🏢 Объект",
        reply_markup=object_keyboard()
    )
    await state.set_state(TripStates.object)


# ─────────────────────
# ОБЪЕКТ
# ─────────────────────
@router.message(TripStates.object)
async def set_object(message: Message, state: FSMContext):
    await state.update_data(object=message.text)

    today = date.today()
    await state.update_data(cal=(today.year, today.month))

    await message.answer(
        "📅 Даты командировки\n\n🟢 Начало",
        reply_markup=current_calendar()
    )
    await state.set_state(TripStates.date_from)


# ─────────────────────
# КАЛЕНДАРЬ — НАЧАЛО
# ─────────────────────
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
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer(
            f"🟢 Начало: {selected}\n\n🔴 Окончание",
            reply_markup=current_calendar()
        )
        await state.set_state(TripStates.date_to)
        await call.answer()
        return

    await state.update_data(cal=(year, month))
    await call.message.edit_reply_markup(build_calendar(year, month))
    await call.answer()


# ─────────────────────
# КАЛЕНДАРЬ — ОКОНЧАНИЕ
# ─────────────────────
@router.callback_query(TripStates.date_to)
async def calendar_date_to(call: CallbackQuery, state: FSMContext):
    if call.data == "ignore":
        await call.answer()
        return

    data = await state.get_data()
    year, month = data.get("cal")

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
            await call.answer("Дата окончания раньше начала", show_alert=True)
            return

        await state.update_data(date_to=selected)
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer(
            "🎯 Цель командировки",
            reply_markup=purpose_keyboard()
        )
        await state.set_state(TripStates.purpose)
        await call.answer()
        return

    await state.update_data(cal=(year, month))
    await call.message.edit_reply_markup(build_calendar(year, month))
    await call.answer()


# ─────────────────────
# ЦЕЛЬ → СОТРУДНИК
# ─────────────────────
@router.message(TripStates.purpose)
async def ask_employee(message: Message, state: FSMContext):
    await state.update_data(purpose=message.text)
    await message.answer(
        "👤 Сотрудник",
        reply_markup=employee_keyboard()
    )
    await state.set_state(TripStates.employee)


# ─────────────────────
# СОТРУДНИК → ПОДТВЕРЖДЕНИЕ
# ─────────────────────
@router.message(TripStates.employee)
async def set_employee(message: Message, state: FSMContext):
    await state.update_data(employee_name=message.text)
    data = await state.get_data()

    await message.answer(
        f"📋 Проверь данные:\n\n"
        f"👤 {data['employee_name']}\n"
        f"🏙 {data['city_raw']}\n"
        f"🏢 {data['object']}\n"
        f"🟢 {data['date_from']} — 🔴 {data['date_to']}\n\n"
        f"🎯 {data['purpose']}",
        reply_markup=confirm_keyboard()
    )
    await state.set_state(TripStates.confirm)


# ─────────────────────
# ПОДТВЕРЖДЕНИЕ
# ─────────────────────
@router.message(TripStates.confirm)
async def confirm_trip(message: Message, state: FSMContext):
    if message.text != "✅ Сохранить":
        return

    data = await state.get_data()

    # нормализация населённого пункта
    raw = data["city_raw"].strip()
    prefix = "г."

    for p in ("г.", "п.", "пгт.", "с."):
        if raw.lower().startswith(p):
            prefix = p
            raw = raw[len(p):].strip()
            break

    city = f"{prefix} {raw}"

    date_from = datetime.strptime(data["date_from"], "%d.%m.%Y")
    date_to = datetime.strptime(data["date_to"], "%d.%m.%Y")
    total = (date_to - date_from).days + 1

    doc_data = {
        "employee_name": data["employee_name"],
        "city": city,
        "object": data["object"],
        "date_from": data["date_from"],
        "date_to": data["date_to"],
        "total": total,
        "purpose": data["purpose"],
        "position": "старший инженер",
        "contract": "ИМ-026/17",
    }

    conn = get_connection()
    conn.execute(
        "INSERT INTO trips (city, place, date_from, date_to, purpose) VALUES (?, ?, ?, ?, ?)",
        (city, data["object"], data["date_from"], data["date_to"], data["purpose"])
    )
    conn.commit()
    conn.close()

    service_task_path = generate_service_task(doc_data)
    await state.update_data(service_task_path=service_task_path)

    await message.answer_document(
        FSInputFile(service_task_path),
        caption="📄 Служебное задание сформировано"
    )

    await message.answer(
        "💰 Нужен запрос аванса?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]],
            resize_keyboard=True
        )
    )
    await state.set_state(TripStates.ask_advance)


# ─────────────────────
# НУЖЕН ЛИ АВАНС
# ─────────────────────
@router.message(TripStates.ask_advance)
async def ask_advance(message: Message, state: FSMContext):
    if message.text == "❌ Нет":
        await message.answer("Готово", reply_markup=main_menu)
        await state.clear()
        return

    await message.answer("Введите сумму аванса:")
    await state.set_state(TripStates.advance_amount)


# ─────────────────────
# АВАНС → DOCX → MAIL
# ─────────────────────
@router.message(TripStates.advance_amount)
async def advance_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите сумму цифрами")
        return

    await state.update_data(advance_amount=message.text)
    data = await state.get_data()

    city = data["city_raw"]

    advance_path = generate_advance_request({
        "employee_name": data["employee_name"],
        "city": city,
        "object": data["object"],
        "date_from": data["date_from"],
        "date_to": data["date_to"],
        "contract": "ИМ-026/17",
        "advance_amount": data["advance_amount"],
    })

    await message.answer_document(
        FSInputFile(advance_path),
        caption="💰 Запрос аванса сформирован"
    )

    send_email_with_attachments(
        to_email="vorobev@intermatic.energy",
        subject=f"Командировка — {city} ({data['date_from']}–{data['date_to']})",
        body=(
            "Добрый день.\n\n"
            "Направляю служебное задание и запрос аванса по командировке."
        ),
        file_paths=[
            data["service_task_path"],
            advance_path,
        ],
    )

    await state.clear()
    await message.answer(
        "✅ Процесс завершён.\n\nВыберите действие:",
        reply_markup=main_menu
    )

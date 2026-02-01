from datetime import date, datetime
import os

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
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
from keyboards.mail import email_select_keyboard

from db.database import get_connection
from utils.docx_generator import generate_service_task
from utils.advance_docx_generator import generate_advance_request
from utils.mailer import send_email_with_attachments

from data.locations import LOCATIONS
from data.employees import EMPLOYEES
from data.emails import EMAIL_RECIPIENTS

router = Router()

# ======================================================
# ГЛОБАЛЬНАЯ ОТМЕНА (работает в любом состоянии)
# ======================================================
@router.message(StateFilter("*"), F.text == "❌ Отмена")
async def cancel_anywhere(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Процесс оформления командировки отменён",
        reply_markup=main_menu,
    )


# ======================================================
# СТАРТ НОВОЙ КОМАНДИРОВКИ
# ======================================================
@router.message(F.text == "🧳 Новая командировка")
async def start_trip(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📍 МЕСТО КОМАНДИРОВКИ\n\nВыберите город или введите вручную:",
        reply_markup=city_keyboard(),
    )
    await state.set_state(TripStates.city)


# ======================================================
# ВЫБОР ГОРОДА
# ======================================================
@router.message(TripStates.city)
async def set_city(message: Message, state: FSMContext):
    city = message.text.strip()
    location = LOCATIONS.get(city)

    await state.update_data(
        city=city,
        settlement_prefix=location.get("settlement_prefix") if location else None,
        location_data=location,
    )

    # Если в справочнике ровно один объект — подставляем автоматически
    if location and len(location.get("objects", {})) == 1:
        object_name, obj = next(iter(location["objects"].items()))

        await state.update_data(
            object=object_name,
            organization=obj.get("organization"),
            contract=obj.get("contract"),
        )

        today = date.today()
        await state.update_data(cal=(today.year, today.month))

        await message.answer(
            f"🏢 Объект: {object_name}\n\n📅 Даты командировки\n\n🟢 Начало",
            reply_markup=current_calendar(),
        )
        await state.set_state(TripStates.date_from)
        return

    # Иначе — спрашиваем объект
    await message.answer(
        "🏢 Объект",
        reply_markup=object_keyboard(),
    )
    await state.set_state(TripStates.object)


# ======================================================
# ВЫБОР / ВВОД ОБЪЕКТА
# ======================================================
@router.message(TripStates.object)
async def set_object(message: Message, state: FSMContext):
    object_name = message.text.strip()
    data = await state.get_data()

    location = data.get("location_data")
    obj = location.get("objects", {}).get(object_name) if location else None

    await state.update_data(
        object=object_name,
        organization=obj.get("organization") if obj else "",
        contract=obj.get("contract") if obj else "",
    )

    today = date.today()
    await state.update_data(cal=(today.year, today.month))

    await message.answer(
        "📅 Даты командировки\n\n🟢 Начало",
        reply_markup=current_calendar(),
    )
    await state.set_state(TripStates.date_from)


# ======================================================
# КАЛЕНДАРЬ — ДАТА НАЧАЛА
# ======================================================
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
        return

    await state.update_data(cal=(year, month))
    await call.message.edit_reply_markup(build_calendar(year, month))
    await call.answer()


# ======================================================
# КАЛЕНДАРЬ — ДАТА ОКОНЧАНИЯ
# ======================================================
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


# ======================================================
# ЦЕЛЬ КОМАНДИРОВКИ
# ======================================================
@router.message(TripStates.purpose)
async def ask_employee(message: Message, state: FSMContext):
    await state.update_data(purpose=message.text)
    await message.answer(
        "👤 Сотрудник",
        reply_markup=employee_keyboard(),
    )
    await state.set_state(TripStates.employee)


# ======================================================
# СОТРУДНИК → ПОДТВЕРЖДЕНИЕ
# ======================================================
@router.message(TripStates.employee)
async def set_employee(message: Message, state: FSMContext):
    name = message.text.strip()
    emp = EMPLOYEES.get(name, {})

    await state.update_data(
        employee_name=name,
        position=emp.get("position", "Старший инженер"),
        employee_email=emp.get("email"),
        employee_signature=emp.get("signature"),
    )

    data = await state.get_data()

    await message.answer(
        "📋 Проверь данные:\n\n"
        f"👤 {data['employee_name']}\n"
        f"💼 {data['position']}\n"
        f"🏙 {data['city']}\n"
        f"🏢 {data['object']}\n"
        f"📄 Договор: {data.get('contract', '—')}\n"
        f"🟢 {data['date_from']} — 🔴 {data['date_to']}\n\n"
        f"🎯 {data['purpose']}",
        reply_markup=confirm_keyboard(),
    )
    await state.set_state(TripStates.confirm)


# ======================================================
# ИЗМЕНИТЬ ИЗ ПОДТВЕРЖДЕНИЯ
# ======================================================
@router.message(TripStates.confirm, F.text == "✏️ Изменить")
async def edit_from_confirm(message: Message, state: FSMContext):
    await message.answer(
        "👤 Выберите сотрудника заново:",
        reply_markup=employee_keyboard(),
    )
    await state.set_state(TripStates.employee)


# ======================================================
# СОХРАНИТЬ → СЛУЖЕБНОЕ ЗАДАНИЕ
# ======================================================
@router.message(TripStates.confirm, F.text == "✅ Сохранить")
async def confirm_trip(message: Message, state: FSMContext):
    data = await state.get_data()

    city = data["city"]
    prefix = data.get("settlement_prefix")

    if prefix:
        city = f"{prefix} {city}"
    elif not city.lower().startswith(("г.", "п.", "с.")):
        city = f"г. {city}"

    df = datetime.strptime(data["date_from"], "%d.%m.%Y")
    dt = datetime.strptime(data["date_to"], "%d.%m.%Y")
    total = (dt - df).days + 1

    doc_data = {
        "employee_name": data["employee_name"],
        "position": data["position"],
        "city": city,
        "object": data["object"],
        "date_from": data["date_from"],
        "date_to": data["date_to"],
        "total": total,
        "purpose": data["purpose"],
        "organization": data.get("organization", ""),
        "contract": data.get("contract", ""),
    }

    # --- БД
    conn = get_connection()
    conn.execute(
        "INSERT INTO trips (city, place, date_from, date_to, purpose) VALUES (?, ?, ?, ?, ?)",
        (city, data["object"], data["date_from"], data["date_to"], data["purpose"]),
    )
    conn.commit()
    conn.close()

    service_task_path = generate_service_task(doc_data)
    await state.update_data(service_task_path=service_task_path)

    await message.answer_document(
        FSInputFile(service_task_path),
        caption="📄 Служебное задание сформировано",
    )

    await message.answer(
        "💰 Нужен запрос аванса?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]],
            resize_keyboard=True,
        ),
    )
    await state.set_state(TripStates.ask_advance)


# ======================================================
# АВАНС: ДА / НЕТ
# ======================================================
@router.message(TripStates.ask_advance)
async def ask_advance(message: Message, state: FSMContext):
    if message.text == "❌ Нет":
        await state.update_data(advance_amount="0")
        await message.answer("💰 Аванс: 0 ₽", reply_markup=ReplyKeyboardRemove())
        await state.set_state(TripStates.advance_amount)
        return

    await message.answer("Введите сумму аванса:")
    await state.set_state(TripStates.advance_amount)


# ======================================================
# СУММА АВАНСА → ДОКУМЕНТ → ВЫБОР ПОЧТЫ
# ======================================================
@router.message(TripStates.advance_amount)
async def advance_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите сумму цифрами")
        return

    await state.update_data(advance_amount=message.text)
    data = await state.get_data()

    advance_path = generate_advance_request({
        "employee_name": data["employee_name"],
        "city": data["city"],
        "object": data["object"],
        "date_from": data["date_from"],
        "date_to": data["date_to"],
        "organization": data.get("organization", ""),
        "contract": data.get("contract", ""),
        "advance_amount": data["advance_amount"],
    })

    await state.update_data(advance_path=advance_path)

    await message.answer_document(
        FSInputFile(advance_path),
        caption=f"💰 Запрос аванса сформирован\nСумма: {data['advance_amount']} ₽",
    )

    await message.answer(
        "📨 Отправить документы:",
        reply_markup=email_select_keyboard(),
    )
    await state.set_state(TripStates.after_documents)


# ======================================================
# ОТПРАВКА ПОЧТЫ / ЗАВЕРШЕНИЕ
# ======================================================
@router.message(TripStates.after_documents, F.text == "✅ Завершить")
async def finish_after_documents(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Процесс завершён", reply_markup=main_menu)


@router.message(TripStates.after_documents)
async def send_mail(message: Message, state: FSMContext):
    recipients = EMAIL_RECIPIENTS.get(message.text)

    if not recipients:
        await message.answer(
            "Выберите вариант кнопкой",
            reply_markup=email_select_keyboard(),
        )
        return

    data = await state.get_data()

    signature = (
        data.get("employee_signature")
        or os.getenv("EMAIL_SIGNATURE", "")
    )

    body = (
        "Добрый день.\n\n"
        "Направляю служебное задание и запрос аванса по командировке.\n\n"
        f"{signature}"
    )

    send_email_with_attachments(
        to_email=", ".join(recipients),
        subject=f"Командировка — {data['city']} ({data['date_from']}–{data['date_to']})",
        body=body,
        file_paths=[
            data["service_task_path"],
            data["advance_path"],
        ],
    )

    await message.answer(
        f"📨 Отправлено: {message.text}\n\n"
        "Можно отправить ещё или завершить процесс.",
        reply_markup=email_select_keyboard(),
    )

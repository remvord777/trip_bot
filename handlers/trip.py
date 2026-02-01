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
from states.advance_report import AdvanceReportStates

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
from keyboards.trips import trips_select_keyboard

from db.database import get_connection
from utils.docx_generator import generate_service_task
from utils.advance_docx_generator import generate_advance_request
from utils.mailer import send_email_with_attachments

from data.locations import LOCATIONS
from data.employees import EMPLOYEES
from data.emails import EMAIL_RECIPIENTS


# ======================================================
# ROUTER (ОБЯЗАТЕЛЬНО ДО ДЕКОРАТОРОВ)
# ======================================================
router = Router()


# ======================================================
# ГЛОБАЛЬНАЯ ОТМЕНА
# ======================================================
@router.message(StateFilter("*"), F.text == "❌ Отмена")
async def cancel_anywhere(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Процесс отменён", reply_markup=main_menu)


# ======================================================
# 🧳 НОВАЯ КОМАНДИРОВКА
# ======================================================
@router.message(F.text == "🧳 Новая командировка")
async def start_trip(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📍 Место командировки\n\nВыберите город:",
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

    await message.answer("🏢 Объект", reply_markup=object_keyboard())
    await state.set_state(TripStates.object)


# ======================================================
# ВЫБОР ОБЪЕКТА
# ======================================================
@router.message(TripStates.object)
async def set_object(message: Message, state: FSMContext):
    data = await state.get_data()
    location = data.get("location_data")
    obj = location.get("objects", {}).get(message.text) if location else None

    await state.update_data(
        object=message.text,
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
# 📅 КАЛЕНДАРЬ — НАЧАЛО
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
# 📅 КАЛЕНДАРЬ — ОКОНЧАНИЕ
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
            await call.answer("Дата окончания раньше даты начала", show_alert=True)
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
# 🎯 ЦЕЛЬ → СОТРУДНИК
# ======================================================
@router.message(TripStates.purpose)
async def ask_employee(message: Message, state: FSMContext):
    await state.update_data(purpose=message.text)
    await message.answer("👤 Сотрудник", reply_markup=employee_keyboard())
    await state.set_state(TripStates.employee)


# ======================================================
# 👤 СОТРУДНИК → ПОДТВЕРЖДЕНИЕ
# ======================================================
@router.message(TripStates.employee)
async def set_employee(message: Message, state: FSMContext):
    emp = EMPLOYEES.get(message.text, {})
    await state.update_data(
        employee_name=message.text,
        position=emp.get("position", ""),
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
        f"🟢 {data['date_from']} — 🔴 {data['date_to']}\n\n"
        f"🎯 {data['purpose']}",
        reply_markup=confirm_keyboard(),
    )
    await state.set_state(TripStates.confirm)


# ======================================================
# ✅ ПОДТВЕРЖДЕНИЕ → ДОКУМЕНТЫ
# ======================================================
@router.message(TripStates.confirm, F.text == "✅ Сохранить")
async def confirm_trip(message: Message, state: FSMContext):
    data = await state.get_data()

    df = datetime.strptime(data["date_from"], "%d.%m.%Y")
    dt = datetime.strptime(data["date_to"], "%d.%m.%Y")
    total = (dt - df).days + 1

    doc_data = {
        "employee_name": data["employee_name"],
        "position": data["position"],
        "city": data["city"],
        "object": data["object"],
        "date_from": data["date_from"],
        "date_to": data["date_to"],
        "total": total,
        "purpose": data["purpose"],
        "organization": data.get("organization", ""),
        "contract": data.get("contract", ""),
    }

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
# 💰 АВАНС
# ======================================================
@router.message(TripStates.ask_advance)
async def ask_advance(message: Message, state: FSMContext):
    if message.text == "❌ Нет":
        await state.update_data(advance_amount="0")
        await message.answer("Аванс: 0 ₽", reply_markup=ReplyKeyboardRemove())
        await state.set_state(TripStates.advance_amount)
        return

    await message.answer("Введите сумму аванса:")
    await state.set_state(TripStates.advance_amount)


@router.message(TripStates.advance_amount)
async def advance_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите сумму цифрами")
        return

    await state.update_data(advance_amount=message.text)
    data = await state.get_data()

    advance_path = generate_advance_request(data)
    await state.update_data(advance_path=advance_path)

    await message.answer_document(
        FSInputFile(advance_path),
        caption=f"💰 Запрос аванса сформирован ({data['advance_amount']} ₽)",
    )

    await message.answer(
        "📨 Отправить документы:",
        reply_markup=email_select_keyboard(),
    )
    await state.set_state(TripStates.after_documents)


# ======================================================
# ✅ ЗАВЕРШИТЬ
# ======================================================
@router.message(TripStates.after_documents, F.text == "✅ Завершить")
async def finish_after_documents(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Процесс завершён", reply_markup=main_menu)


# ======================================================
# 📨 ОТПРАВКА ПОЧТЫ
# ======================================================
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

    body = (
        "Добрый день.\n\n"
        "Направляю служебное задание и запрос аванса по командировке.\n\n"
        f"{data.get('employee_signature', '')}"
    )

    send_email_with_attachments(
        to_email=", ".join(recipients),
        subject=f"Командировка — {data['city']} ({data['date_from']}–{data['date_to']})",
        body=body,
        file_paths=[
            data["service_task_path"],
            data.get("advance_path"),
        ],
    )

    await message.answer(
        f"📨 Отправлено: {message.text}\n\n"
        "Можно отправить ещё или завершить процесс.",
        reply_markup=email_select_keyboard(),
    )
# ======================================================
# 📄 АВАНСОВЫЙ ОТЧЁТ — СТАРТ
# ======================================================
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
        "📄 Авансовый отчёт\n\nВыберите командировку:",
        reply_markup=trips_select_keyboard(trips),
    )
    await state.set_state(AdvanceReportStates.choose_trip)
# ======================================================
# ВЫБОР КОМАНДИРОВКИ
# ======================================================
@router.callback_query(
    AdvanceReportStates.choose_trip,
    F.data.startswith("trip:")
)
async def advance_choose_trip(call: CallbackQuery, state: FSMContext):
    trip_id = int(call.data.split(":")[1])
    await state.update_data(trip_id=trip_id, files=[])

    await call.message.answer(
        "📎 Загрузите чеки / билеты (фото или PDF).\n"
        "Можно несколько файлов.\n\n"
        "Когда закончите — нажмите «Готово».",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Готово")]],
            resize_keyboard=True,
        ),
    )
    await state.set_state(AdvanceReportStates.upload_files)
    await call.answer()
# ======================================================
# ЗАГРУЗКА ФАЙЛОВ
# ======================================================
@router.message(AdvanceReportStates.upload_files, F.text == "Готово")
async def advance_finish_upload(message: Message, state: FSMContext):
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


@router.message(AdvanceReportStates.upload_files, F.photo | F.document)
async def advance_upload_files(message: Message, state: FSMContext):
    data = await state.get_data()
    trip_id = data["trip_id"]

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
        f"📎 Файл добавлен ({len(files)})",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Готово")]],
            resize_keyboard=True,
        ),
    )
# ======================================================
# СУММА РАСХОДОВ
# ======================================================
@router.message(AdvanceReportStates.enter_amounts)
async def advance_enter_amounts(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите сумму цифрами")
        return

    await state.update_data(total_amount=message.text)

    await message.answer(
        "Авансовый отчёт принят.\n"
        "Дальше: формирование DOCX.",
        reply_markup=main_menu,
    )
    await state.clear()

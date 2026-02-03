from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards.locations import locations_keyboard
from keyboards.calendar import current_calendar
from keyboards.services import services_keyboard
from keyboards.confirm import confirm_keyboard

from data.locations import LOCATIONS
from data.services import SERVICES

from utils.docx_render import render_docx

router = Router()


# ================= FSM =================

class TripStates(StatesGroup):
    location = State()
    date_from = State()
    date_to = State()
    service = State()
    confirm = State()


# ================= START =================

@router.message(F.text == "🧳 Командировка")
async def trip_start(message: Message, state: FSMContext):
    data = await state.get_data()

    # ⚠️ ВАЖНО: сохраняем данные сотрудника, которые положил /start
    await state.set_data({
        "employee_name": data.get("employee_name"),
        "position": data.get("position"),
        "email": data.get("email"),
        "signature": data.get("signature"),
    })

    await message.answer(
        "📍 Выберите город командировки:",
        reply_markup=locations_keyboard(),
    )
    await state.set_state(TripStates.location)


# ================= LOCATION =================

@router.message(TripStates.location)
async def trip_location(message: Message, state: FSMContext):
    city = message.text
    location = LOCATIONS[city]

    # берём первый объект из справочника
    object_key = next(iter(location["objects"]))
    obj = location["objects"][object_key]

    await state.update_data(
        city=f"г. {city}",        # ← ВОТ ЗДЕСЬ
        object_name=object_key,
        organization=obj["organization"],
        contract=obj["contract"],
    )

    await message.answer(
        "🟢 Дата начала командировки:",
        reply_markup=current_calendar(),
    )
    await state.set_state(TripStates.date_from)


# ================= DATE FROM =================

@router.callback_query(TripStates.date_from, F.data.startswith("date:"))
async def date_from(call: CallbackQuery, state: FSMContext):
    date_str = call.data.replace("date:", "")
    await state.update_data(date_from=date_str)

    await call.message.answer(
        "🔴 Дата окончания командировки:",
        reply_markup=current_calendar(),
    )
    await state.set_state(TripStates.date_to)
    await call.answer()


# ================= DATE TO =================

@router.callback_query(TripStates.date_to, F.data.startswith("date:"))
async def date_to(call: CallbackQuery, state: FSMContext):
    date_str = call.data.replace("date:", "")
    await state.update_data(date_to=date_str)

    await call.message.answer(
        "🛠 Выберите вид сервисных работ:",
        reply_markup=services_keyboard(),
    )
    await state.set_state(TripStates.service)
    await call.answer()


# ================= SERVICE =================

@router.callback_query(TripStates.service, F.data.startswith("service:"))
async def service_selected(call: CallbackQuery, state: FSMContext):
    service_key = call.data.replace("service:", "")
    service_title = SERVICES.get(service_key)

    if not service_title:
        await call.answer("Неизвестный вид работ", show_alert=True)
        return

    await state.update_data(service=service_title)

    data = await state.get_data()

    # ===== считаем общее количество дней =====
    date_from = datetime.strptime(data["date_from"], "%d.%m.%Y")
    date_to = datetime.strptime(data["date_to"], "%d.%m.%Y")
    total_days = (date_to - date_from).days + 1

    await state.update_data(total=total_days)

    text = (
        "🔎 Проверь данные командировки:\n\n"
        f"👤 {data.get('employee_name', '')}\n"
        f"💼 {data.get('position', '')}\n\n"
        f"📍 {data.get('city', '')}\n"
        f"🏭 {data.get('object_name', '')}\n"
        f"🏢 {data.get('organization', '')}\n"
        f"📄 Договор №{data.get('contract', '')}\n\n"
        f"🟢 С {data.get('date_from', '')}\n"
        f"🔴 По {data.get('date_to', '')}\n"
        f"📆 Дней: {total_days}\n\n"
        f"🛠 {service_title}"
    )

    await call.message.answer(text, reply_markup=confirm_keyboard())
    await state.set_state(TripStates.confirm)
    await call.answer()


# ================= CONFIRM =================

@router.callback_query(TripStates.confirm, F.data == "confirm")
async def confirm_trip(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # ===== формируем DOCX =====
    file_path = render_docx(
        template_name="service_task.docx",
        data={
            "employee_name": data.get("employee_name", ""),
            "position": data.get("position", ""),
            "city": data.get("city", ""),
            "object": data.get("object_name", ""),  # ← ВАЖНО
            "contract": data.get("contract", ""),
            "date_from": data.get("date_from", ""),
            "date_to": data.get("date_to", ""),
            "total": data.get("total", ""),
            "purpose": data.get("service", ""),  # ← ВАЖНО
            "signature": data.get("signature", ""),
        },
    )

    # ===== отправляем файл пользователю =====
    document = FSInputFile(file_path)

    await call.message.answer_document(
        document=document,
        caption="📄 Служебное задание сформировано",
    )

    await state.clear()
    await call.answer()

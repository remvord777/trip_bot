from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

from keyboards.locations import locations_keyboard
from keyboards.calendar import current_calendar
from keyboards.services import services_keyboard
from keyboards.confirm import confirm_keyboard, advance_keyboard

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
    advance_sum = State()


# ================= START =================

@router.message(F.text == "🧳 Командировка")
async def trip_start(message: Message, state: FSMContext):
    # В state УЖЕ лежат employee_name / position / email (из /start)
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

    object_key = next(iter(location["objects"]))
    obj = location["objects"][object_key]

    await state.update_data(
        city=city,
        settlement_prefix=location.get("settlement_prefix", ""),
        object_name=obj.get("name", object_key),
        organization=obj.get("organization", ""),
        contract=obj.get("contract", ""),
    )

    await message.answer(
        "🟢 Дата начала командировки:",
        reply_markup=current_calendar(),
    )
    await state.set_state(TripStates.date_from)


# ================= DATE FROM =================

@router.callback_query(TripStates.date_from, F.data.startswith("date:"))
async def date_from(call: CallbackQuery, state: FSMContext):
    date = call.data.replace("date:", "")
    await state.update_data(date_from=date)

    await call.message.answer(
        "🔴 Дата окончания командировки:",
        reply_markup=current_calendar(),
    )
    await state.set_state(TripStates.date_to)
    await call.answer()


# ================= DATE TO =================

@router.callback_query(TripStates.date_to, F.data.startswith("date:"))
async def date_to(call: CallbackQuery, state: FSMContext):
    date = call.data.replace("date:", "")
    await state.update_data(date_to=date)

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
    service_title = SERVICES[service_key]

    await state.update_data(service=service_title)
    data = await state.get_data()

    text = (
        "🔎 Проверь данные командировки:\n\n"
        f"👤 {data['employee_name']}\n"
        f"💼 {data['position']}\n\n"
        f"📍 {data['settlement_prefix']} {data['city']}\n"
        f"🏭 {data['object_name']}\n"
        f"🏢 {data['organization']}\n"
        f"📄 Договор №{data['contract']}\n\n"
        f"🟢 С {data['date_from']}\n"
        f"🔴 По {data['date_to']}\n\n"
        f"🛠 {data['service']}"
    )

    await call.message.answer(text, reply_markup=confirm_keyboard())
    await state.set_state(TripStates.confirm)
    await call.answer()


# ================= CONFIRM =================

@router.callback_query(TripStates.confirm, F.data == "confirm")
async def confirm_trip(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    file_path = render_docx(
        template_name="service_task.docx",
        data={
            **data,
            "apply_date": datetime.now().strftime("%d.%m.%Y"),
        },
    )

    await call.message.answer_document(
        FSInputFile(file_path),
        caption="📄 Служебное задание сформировано",
        reply_markup=advance_keyboard(),
    )
    await call.answer()


# ================= ADVANCE =================

# ================= ADVANCE =================

@router.callback_query(F.data == "advance_yes")
async def advance_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("💰 Введите сумму аванса:")
    await state.set_state(TripStates.advance_sum)
    await call.answer()


@router.callback_query(F.data == "advance_no")
async def advance_cancel(call: CallbackQuery, state: FSMContext):
    await call.message.answer("✅ Командировка оформлена без аванса")
    await state.clear()
    await call.answer()


@router.message(TripStates.advance_sum)
async def advance_sum_entered(message: Message, state: FSMContext):
    amount = message.text.strip()

    if not amount.isdigit():
        await message.answer("❗ Введите сумму цифрами")
        return

    await state.update_data(advance_amount=amount)
    data = await state.get_data()

    file_path = render_docx(
        template_name="money_avans.docx",
        data={
            **data,
            "apply_date": datetime.now().strftime("%d.%m.%Y"),
        },
    )

    await message.answer_document(
        FSInputFile(file_path),
        caption="💰 Авансовый запрос сформирован",
    )

    await state.clear()

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards.locations import locations_keyboard
from keyboards.calendar import current_calendar
from keyboards.services import services_keyboard
from keyboards.confirm import confirm_keyboard
from keyboards.advance import advance_offer_keyboard

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
    advance_offer = State()
    advance_amount = State()  # 👈 НОВОЕ

@router.callback_query(TripStates.advance_offer, F.data == "advance:yes")
async def advance_yes(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "💰 Введите сумму аванса (в рублях):\n"
        "Например: 45000"
    )
    await state.set_state(TripStates.advance_amount)
    await call.answer()
@router.message(TripStates.advance_amount)
async def advance_amount(message: Message, state: FSMContext):
    text = message.text.replace(" ", "")

    if not text.isdigit():
        await message.answer("❌ Введите сумму **числом**, без букв.")
        return

    amount = int(text)

    await state.update_data(advance_amount=amount)

    data = await state.get_data()

    await message.answer(
        "✅ Авансовый запрос принят:\n\n"
        f"👤 {data['employee_name']}\n"
        f"💼 {data['position']}\n"
        f"📍 {data['city']}\n"
        f"🏭 {data['object_name']}\n"
        f"💰 Сумма аванса: {amount:,} ₽".replace(",", " ")
    )

    # дальше можно:
    # 1) сформировать DOCX
    # 2) спросить комментарий
    # 3) отправить письмо

    await state.clear()


# ================= START =================

@router.message(F.text == "🧳 Командировка")
async def trip_start(message: Message, state: FSMContext):
    data = await state.get_data()

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

    object_key = next(iter(location["objects"]))
    obj = location["objects"][object_key]

    await state.update_data(
        city=f"г. {city}",
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
        "Выберите вид работ:",
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
        f"📍 {data['city']}\n"
        f"🏭 {data['object_name']}\n"
        f"🏢 {data['organization']}\n"
        f"📄 Договор №{data['contract']}\n\n"
        f"🟢 С {data['date_from']}\n"
        f"🔴 По {data['date_to']}\n\n"
        f"{data['service']}"
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
            "employee_name": data["employee_name"],
            "position": data["position"],
            "city": data["city"],
            "object": data["object_name"],
            "organization": data["organization"],
            "contract": data["contract"],
            "date_from": data["date_from"],
            "date_to": data["date_to"],
            "service": data["service"],
            "purpose": data["service"],
            "signature": data.get("signature", ""),
        },
    )

    await call.message.answer_document(
        document=FSInputFile(file_path),
        caption="📄 Служебное задание сформировано",
    )

    await call.message.answer(
        "Сформировать авансовый запрос?",
        reply_markup=advance_offer_keyboard(),
    )

    await state.set_state(TripStates.advance_offer)
    await call.answer()


# ================= ADVANCE OFFER =================

@router.callback_query(TripStates.advance_offer, F.data == "advance:no")
async def advance_no(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Хорошо, можно сформировать позже 👍")
    await state.clear()
    await call.answer()


@router.callback_query(TripStates.advance_offer, F.data == "advance:yes")
async def advance_yes(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "Ок 👍\n"
        "Следующим шагом сформируем авансовый запрос."
    )
    await state.clear()
    await call.answer()

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
from pathlib import Path
from utils.email_templates import build_subject, build_body

from data.trips_store import load_trips, save_trips

from keyboards.main import main_menu

from keyboards.locations import locations_keyboard
from keyboards.calendar import current_calendar
from keyboards.services import services_keyboard
from keyboards.confirm import confirm_keyboard, advance_keyboard
from keyboards.email_targets import email_targets_keyboard

from data.locations import LOCATIONS
from data.services import SERVICES
from data.email_targets import EMAIL_TARGETS

from utils.docx_render import render_docx
from utils.mailer import send_email
from data.employees import EMPLOYEES


router = Router()


# ================= FSM =================

class TripStates(StatesGroup):
    location = State()
    date_from = State()
    date_to = State()
    service = State()
    confirm = State()
    advance_sum = State()
    email_select = State()


# ================= START =================

# @router.message(F.text == "🧳 Командировка")
# async def trip_start(message: Message, state: FSMContext):
#     await message.answer(
#         "📍 Выберите город командировки:",
#         reply_markup=locations_keyboard(),
#     )
#     await state.set_state(TripStates.location)
#
@router.message(F.text == "🧳 Командировка")
async def trip_start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    employee = EMPLOYEES.get(telegram_id)

    if not employee:
        await message.answer("❗ Сотрудник не найден. Выполните /start")
        return

    # 🔥 ГАРАНТИЯ ДАННЫХ
    await state.update_data(
        employee_name=employee["employee_name"],
        position=employee["position"],
        email=employee["email"],
        signature=employee["signature"],
    )

    await message.answer(
        "📍 Выберите город командировки:",
        reply_markup=locations_keyboard(),
    )
    await state.set_state(TripStates.location)
# ================= LOCATION =================

@router.message(TripStates.location)
async def trip_location(message: Message, state: FSMContext):
    city = message.text
    location = LOCATIONS.get(city)

    if not location:
        await message.answer("❗ Выберите город кнопкой")
        return

    objects = location.get("objects", {})
    if not objects:
        await message.answer("❗ Для этого города нет объектов")
        return

    object_key, obj = next(iter(objects.items()))

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
    await state.update_data(date_from=call.data.replace("date:", ""))

    await call.message.answer(
        "🔴 Дата окончания командировки:",
        reply_markup=current_calendar(),
    )
    await state.set_state(TripStates.date_to)
    await call.answer()


# ================= DATE TO =================
@router.callback_query(TripStates.date_to, F.data.startswith("date:"))
async def date_to(call: CallbackQuery, state: FSMContext):
    date_to_str = call.data.replace("date:", "")
    data = await state.get_data()

    date_from = datetime.strptime(data["date_from"], "%d.%m.%Y")
    date_to = datetime.strptime(date_to_str, "%d.%m.%Y")

    total_days = (date_to - date_from).days + 1

    await state.update_data(
        date_to=date_to_str,
        total=str(total_days),
    )

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
        await call.answer("Ошибка выбора сервиса", show_alert=True)
        return

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

    file_path = Path(render_docx(
        template_name="service_task.docx",
        data={
            **data,
            "apply_date": datetime.now().strftime("%d.%m.%Y"),
        },
    ))

    await state.update_data(files=[file_path])

    await call.message.answer_document(
        FSInputFile(file_path),
        caption="📄 Служебное задание сформировано",
        reply_markup=advance_keyboard(),
    )
    await call.answer()


# ================= ADVANCE =================

@router.callback_query(F.data == "advance_yes")
async def advance_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("💰 Введите сумму аванса:")
    await state.set_state(TripStates.advance_sum)
    await call.answer()


@router.callback_query(F.data == "advance_no")
async def advance_cancel(call: CallbackQuery, state: FSMContext):
    await state.update_data(email_targets=[])

    await call.message.answer(
        "📧 Кому отправить документы?",
        reply_markup=email_targets_keyboard([]),
    )
    await state.set_state(TripStates.email_select)
    await call.answer()


@router.message(TripStates.advance_sum)
async def advance_sum_entered(message: Message, state: FSMContext):
    amount = message.text.strip()

    if not amount.isdigit():
        await message.answer("❗ Введите сумму цифрами")
        return

    await state.update_data(advance_amount=amount)
    data = await state.get_data()

    file_path = Path(render_docx(
        template_name="money_avans.docx",
        data={
            **data,
            "apply_date": datetime.now().strftime("%d.%m.%Y"),
        },
    ))

    files = data.get("files", [])
    files.append(file_path)

    await state.update_data(files=files, email_targets=[])

    await message.answer_document(
        FSInputFile(file_path),
        caption="💰 Авансовый запрос сформирован",
    )

    await message.answer(
        "📧 Кому отправить документы?",
        reply_markup=email_targets_keyboard([]),
    )
    await state.set_state(TripStates.email_select)


# ================= EMAIL =================

from keyboards.main import main_menu
from data.trips_store import load_trips, save_trips

@router.callback_query(TripStates.email_select, F.data.startswith("email:"))
async def email_select(call: CallbackQuery, state: FSMContext):
    action = call.data.replace("email:", "")
    data = await state.get_data()
    selected = data.get("email_targets", [])

    # ================= SEND =================
    if action == "send":
        if not selected:
            await call.answer("Выберите получателя", show_alert=True)
            return

        # --- формируем список получателей ---
        recipients: list[str] = []
        for key in selected:
            if key == "me":
                recipients.append(data.get("email", ""))
            else:
                recipients.append(EMAIL_TARGETS.get(key, ""))

        recipients = [r for r in recipients if r]  # защита от пустых

        # --- отправка письма ---
        send_email(
            to_emails=recipients,
            subject=build_subject(data),
            body=build_body(data),
            attachments=data.get("files", []),
        )

        # --- уведомление пользователю ---
        await call.message.answer(
            "✅ Документы отправлены\n\n"
            "Кому:\n"
            + "\n".join(f"• {email}" for email in recipients)
        )

        # ================= SAVE TRIP =================

        trips = load_trips()
        uid = str(call.from_user.id)

        trips.setdefault(uid, [])

        trips[uid].append({
            "trip_id": len(trips[uid]) + 1,
            "city": data.get("city"),
            "object_name": data.get("object_name"),
            "date_from": data.get("date_from"),
            "date_to": data.get("date_to"),
            "total": data.get("total"),
            "files": [str(p) for p in data.get("files", [])],
        })

        save_trips(trips)

        # ================= BACK TO MENU =================

        await state.clear()

        await call.message.answer(
            "Выберите действие:",
            reply_markup=main_menu,
        )

        await call.answer()
        return

    # ================= TOGGLE EMAIL =================

    if action in selected:
        selected.remove(action)
    else:
        selected.append(action)

    await state.update_data(email_targets=selected)

    await call.message.edit_reply_markup(
        reply_markup=email_targets_keyboard(selected)
    )
    await call.answer()

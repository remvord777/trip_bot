from aiogram import Router
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from states.trip import TripStates
from keyboards.mail import email_select_keyboard
from utils.advance_docx_generator import generate_advance_request

router = Router()


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


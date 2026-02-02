import os

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.trip import TripStates
from keyboards.mail import email_select_keyboard
from data.emails import EMAIL_RECIPIENTS
from utils.mailer import send_email_with_attachments

router = Router()

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
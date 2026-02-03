import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from data.employees import EMPLOYEES
from keyboards.main import main_menu

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    logger.info("START | telegram_id=%s", telegram_id)

    await state.clear()

    employee = EMPLOYEES.get(telegram_id)

    if not employee:
        await message.answer(
            "❗ Вы не зарегистрированы.\n\n"
            f"Ваш telegram_id:\n<code>{telegram_id}</code>",
            parse_mode="HTML",
        )
        return

    # сохраняем сотрудника в FSM
    await state.update_data(
        employee_name=employee["employee_name"],
        position=employee["position"],
        email=employee["email"],
        signature=employee["signature"],
    )

    await message.answer(
        "✅ Вход выполнен\n\n"
        f"👤 <b>{employee['employee_name']}</b>\n"
        f"💼 {employee['position']}\n"
        f"🆔 <code>{telegram_id}</code>\n\n"
        "Выберите действие:",
        reply_markup=main_menu,   # ❗ БЕЗ ()
        parse_mode="HTML",
    )

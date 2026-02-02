from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from data.employees import EMPLOYEES
from keyboards.main import main_menu

router = Router()


@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    employee = EMPLOYEES.get(user_id)

    if not employee:
        await message.answer(f"Твой telegram_id: {user_id}")
        return

    await state.clear()  # ✅ ТОЛЬКО ЗДЕСЬ

    await state.update_data(
        employee_name=employee["employee_name"],
        position=employee["position"],
    )

    await message.answer(
        f"Вы вошли как:\n"
        f"{employee['employee_name']}\n"
        f"{employee['position']}",
        reply_markup=main_menu,
    )

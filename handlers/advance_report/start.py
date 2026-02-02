from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.main import main_menu
from states.advance_report import AdvanceReportStates

router = Router()


@router.message(F.text == "📄 Авансовый отчёт")
async def start_advance_report(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📄 Авансовый отчёт\n\nВыберите командировку:",
        reply_markup=main_menu,  # временно
    )

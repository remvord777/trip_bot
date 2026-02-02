from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.advance_report import AdvanceReportStates

router = Router()


@router.message(AdvanceReportStates.enter_amounts)
async def enter_amounts(message: Message, state: FSMContext):
    await message.answer("Ввод суммы (заглушка)")

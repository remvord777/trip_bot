from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import F

from states.advance_report import AdvanceReportStates

router = Router()


@router.callback_query(
    AdvanceReportStates.choose_trip,
    F.data.startswith("trip:")
)
async def choose_trip(call: CallbackQuery, state: FSMContext):
    await call.answer("Командировка выбрана (заглушка)")

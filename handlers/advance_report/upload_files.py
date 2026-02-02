from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.advance_report import AdvanceReportStates

router = Router()


@router.message(AdvanceReportStates.upload_files)
async def upload_files(message: Message, state: FSMContext):
    await message.answer("Загрузка файлов (заглушка)")

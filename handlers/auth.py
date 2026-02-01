from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards.main import main_menu

router = Router()

PIN_CODE = "3479"
AUTHORIZED_USERS: set[int] = set()


class AuthStates(StatesGroup):
    waiting_pin = State()


# ─────────────────────
# /start
# ─────────────────────
@router.message(F.text == "/start")
async def start_auth(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id in AUTHORIZED_USERS:
        await message.answer(
            "🧳 Выберите действие:",
            reply_markup=main_menu
        )
        return

    await message.answer("🔐 Введите PIN-код:")
    await state.set_state(AuthStates.waiting_pin)


# ─────────────────────
# ВВОД PIN
# ─────────────────────
@router.message(AuthStates.waiting_pin)
async def process_pin(message: Message, state: FSMContext):
    if message.text.strip() != PIN_CODE:
        await message.answer("❌ Неверный PIN. Попробуйте ещё раз:")
        return

    AUTHORIZED_USERS.add(message.from_user.id)
    await state.clear()

    await message.answer(
        "🧳 Выберите действие:",
        reply_markup=main_menu
    )

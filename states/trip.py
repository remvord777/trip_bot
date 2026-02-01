from aiogram.fsm.state import StatesGroup, State


class TripStates(StatesGroup):
    city = State()
    object = State()
    date_from = State()
    date_to = State()
    purpose = State()
    employee = State()
    confirm = State()

    # ───── ДОБАВЛЕНО ─────
    ask_advance = State()        # ❓ нужен ли аванс
    advance_amount = State()    # 💰 сумма аванса
    # ⬇️ ВОТ ЭТОГО НЕ ХВАТАЛО
    select_email = State()
    after_documents = State()

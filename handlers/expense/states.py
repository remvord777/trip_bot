from aiogram.fsm.state import StatesGroup, State


class ExpenseStates(StatesGroup):
    select_trip = State()
    upload_files = State()

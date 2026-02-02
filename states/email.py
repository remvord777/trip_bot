from aiogram.fsm.state import StatesGroup, State


class EmailStates(StatesGroup):
    select_recipients = State()

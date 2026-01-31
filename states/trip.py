from aiogram.fsm.state import StatesGroup, State

class TripStates(StatesGroup):
    city = State()
    object = State()
    date_from = State()
    date_to = State()
    purpose = State()
    confirm = State()

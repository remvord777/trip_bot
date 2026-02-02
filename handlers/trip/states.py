from aiogram.fsm.state import StatesGroup, State

class TripStates(StatesGroup):
    location = State()
    object = State()
    date_from = State()
    date_to = State()
    purpose = State()

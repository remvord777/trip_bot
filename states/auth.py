from aiogram.fsm.state import StatesGroup, State

class AuthStates(StatesGroup):
    waiting_pin = State()

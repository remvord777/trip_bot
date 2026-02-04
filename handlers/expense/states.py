from aiogram.fsm.state import StatesGroup, State


class ExpenseStates(StatesGroup):
    select_trip = State()

    select_accommodation = State()
    input_accommodation_amount = State()

    input_taxi_amount = State()

    select_ticket_type = State()
    input_ticket_amount = State()

    confirm = State()

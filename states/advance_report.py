from aiogram.fsm.state import StatesGroup, State


class AdvanceReportStates(StatesGroup):
    choose_trip = State()
    upload_files = State()
    confirm_files = State()
    enter_amounts = State()
    preview = State()
    send_email = State()

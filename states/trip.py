from aiogram.fsm.state import StatesGroup, State


class TripStates(StatesGroup):
    city = State()        # город
    object = State()      # объект (ГРЭС / ТЭЦ / ТЭС / вручную)
    date_from = State()   # дата начала
    date_to = State()     # дата окончания
    purpose = State()     # цель командировки

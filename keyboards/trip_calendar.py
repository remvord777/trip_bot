from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date, timedelta


def current_calendar():
    today = date.today()
    keyboard = []

    for i in range(14):
        d = today + timedelta(days=i)
        keyboard.append([
            InlineKeyboardButton(
                text=d.strftime("%d.%m.%Y"),
                callback_data=d.strftime("%d.%m.%Y"),
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

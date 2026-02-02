from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from data.locations import LOCATIONS


def locations_keyboard(columns: int = 2):
    cities = list(LOCATIONS.keys())
    keyboard = []

    for i in range(0, len(cities), columns):
        row = [
            KeyboardButton(text=city)
            for city in cities[i:i + columns]
        ]
        keyboard.append(row)

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )

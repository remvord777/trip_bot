from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def purpose_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Служебная")],
            [KeyboardButton(text="Учебная")],
        ],
        resize_keyboard=True,
    )

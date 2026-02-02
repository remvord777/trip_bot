from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅ Подтвердить"),
                KeyboardButton(text="✏️ Исправить"),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


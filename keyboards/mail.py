from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from data.emails import EMAIL_RECIPIENTS

def email_select_keyboard():
    keyboard = [[KeyboardButton(text=name)] for name in EMAIL_RECIPIENTS.keys()]
    keyboard.append([KeyboardButton(text="✅ Завершить")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

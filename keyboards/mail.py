from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from data.emails import EMAIL_RECIPIENTS


def email_select_keyboard():
    keyboard = []

    # кнопки получателей
    for title in EMAIL_RECIPIENTS.keys():
        keyboard.append([KeyboardButton(text=title)])

    # кнопка завершения
    keyboard.append([KeyboardButton(text="✅ Завершить")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

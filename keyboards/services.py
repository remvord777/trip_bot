from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.services import SERVICES


def services_keyboard() -> InlineKeyboardMarkup:
    keyboard = []

    for key, title in SERVICES.items():
        keyboard.append([
            InlineKeyboardButton(
                text=title,
                callback_data=key,
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.services import SERVICES


def services_keyboard() -> InlineKeyboardMarkup:
    keyboard = []

    for key, title in SERVICES.items():
        keyboard.append([
            InlineKeyboardButton(
                text=f"{title}",
                callback_data=f"service:{key}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


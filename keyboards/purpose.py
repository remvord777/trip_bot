from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def purpose_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ПНР", callback_data="ПНР")],
            [InlineKeyboardButton(text="ТО", callback_data="ТО")],
            [InlineKeyboardButton(text="Диагностика", callback_data="Диагностика")],
        ]
    )

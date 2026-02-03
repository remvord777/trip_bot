from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def advance_offer_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Сформировать авансовый запрос",
                    callback_data="advance:yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Нет, позже",
                    callback_data="advance:no",
                )
            ],
        ]
    )

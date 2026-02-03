from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data="confirm",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить",
                    callback_data="edit",
                )
            ],
        ]
    )

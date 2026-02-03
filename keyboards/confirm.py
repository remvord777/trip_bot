from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить",
                    callback_data="edit",
                ),
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data="confirm",
                ),

            ]
        ]
    )


def advance_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Нет",
                    callback_data="advance_no",
                ),
                InlineKeyboardButton(
                    text="💰 Аванс запрос",
                    callback_data="advance_yes",
                ),

            ]
        ]
    )

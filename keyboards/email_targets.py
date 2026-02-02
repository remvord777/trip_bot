from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.email_targets import EMAIL_TARGETS


def email_targets_keyboard(selected: set[str]):
    buttons = []

    for key, item in EMAIL_TARGETS.items():
        prefix = "✅ " if key in selected else ""
        buttons.append([
            InlineKeyboardButton(
                text=prefix + item["label"],
                callback_data=f"email:{key}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="📤 Отправить",
            callback_data="email:send",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

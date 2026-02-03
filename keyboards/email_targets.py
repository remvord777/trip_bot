from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.email_targets import EMAIL_TARGETS


def email_targets_keyboard(selected: list[str]):
    keyboard = []

    for alias in EMAIL_TARGETS.keys():
        prefix = "✅ " if alias in selected else ""
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prefix}{alias}",
                callback_data=alias,
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="➡️ Далее",
            callback_data="emails_done",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

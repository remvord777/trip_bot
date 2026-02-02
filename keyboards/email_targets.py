from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.email_targets import EMAIL_TARGETS


def email_targets_keyboard(selected: list[str]):
    keyboard = []

    for email in EMAIL_TARGETS:
        prefix = "✅ " if email in selected else ""
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prefix}{email}",
                callback_data=email,
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="➡️ Далее",
            callback_data="emails_done",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# keyboards/email_targets.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.email_targets import EMAIL_TARGETS


def email_targets_keyboard(selected: list[str]):
    keyboard = []

    for alias in EMAIL_TARGETS:
        prefix = "✅ " if alias in selected else ""
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prefix}{alias}",
                callback_data=f"email:{alias}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="📨 Отправить",
            callback_data="email:send",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

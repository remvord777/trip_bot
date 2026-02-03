from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.services import SERVICES


SERVICE_ICONS = {
    "pnr": "🛠",
    "service_asu": "🔧",
    "service_asu_pgu": "🔧",
}


def services_keyboard() -> InlineKeyboardMarkup:
    keyboard = []

    for key, title in SERVICES.items():
        icon = SERVICE_ICONS.get(key, "")
        text = f"{icon} {title}" if icon else title

        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"service:{key}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

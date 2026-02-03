from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.email_targets import EMAIL_TARGETS


# красивые названия кнопок
EMAIL_TITLES = {
    "me": "👤 Мне",
    "office_im": "🏢 Офис ИМ",
    "office_ik": "🏢 Офис ИК",
}


def email_targets_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    keyboard = []

    for key in EMAIL_TITLES:
        checked = "✅ " if key in selected else ""
        keyboard.append([
            InlineKeyboardButton(
                text=f"{checked}{EMAIL_TITLES[key]}",
                callback_data=f"email:{key}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="📨 Отправить",
            callback_data="email:send",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

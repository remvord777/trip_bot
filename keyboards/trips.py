from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def trips_select_keyboard(trips: list[dict]) -> InlineKeyboardMarkup:
    keyboard = []

    for trip in trips:
        text = (
            f"📍 {trip['city']} — {trip['place']}\n"
            f"📅 {trip['date_from']} – {trip['date_to']}"
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"trip:{trip['id']}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

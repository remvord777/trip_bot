from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    keyboard = []

    # заголовок
    keyboard.append([
        InlineKeyboardButton(text="◀", callback_data="prev"),
        InlineKeyboardButton(text=f"{month:02d}.{year}", callback_data="ignore"),
        InlineKeyboardButton(text="▶", callback_data="next"),
    ])

    # дни недели
    keyboard.append([
        InlineKeyboardButton(text=d, callback_data="ignore")
        for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    ])

    import calendar
    month_calendar = calendar.monthcalendar(year, month)

    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                date_str = f"{day:02d}.{month:02d}.{year}"
                row.append(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"date:{date_str}",
                    )
                )
        keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def current_calendar() -> InlineKeyboardMarkup:
    now = datetime.now()
    return build_calendar(now.year, now.month)

from datetime import date
from calendar import monthrange
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    kb = []

    # Заголовок (месяц + год)
    kb.append([
        InlineKeyboardButton(
            text=f"{month:02d}.{year}",
            callback_data="ignore"
        )
    ])

    # Дни недели
    kb.append([
        InlineKeyboardButton(text=d, callback_data="ignore")
        for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    ])

    first_weekday, days_in_month = monthrange(year, month)
    week = []

    # Пустые ячейки в начале
    for _ in range(first_weekday):
        week.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    for day in range(1, days_in_month + 1):
        week.append(
            InlineKeyboardButton(
                text=str(day),
                callback_data=f"date:{day:02d}.{month:02d}.{year}"
            )
        )

        if len(week) == 7:
            kb.append(week)
            week = []

    if week:
        while len(week) < 7:
            week.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        kb.append(week)

    # Навигация
    kb.append([
        InlineKeyboardButton(text="⬅️", callback_data="prev"),
        InlineKeyboardButton(text="➡️", callback_data="next"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def current_calendar():
    today = date.today()
    return build_calendar(today.year, today.month)

from datetime import date, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import calendar


def build_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    kb = []

    # ===== HEADER =====
    kb.append([
        InlineKeyboardButton(
            text=f"{calendar.month_name[month]} {year}",
            callback_data="ignore"
        )
    ])

    # ===== WEEK DAYS =====
    kb.append([
        InlineKeyboardButton(text=day, callback_data="ignore")
        for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    ])

    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdates(year, month))

    # всегда 6 недель
    month_days = month_days[:42]

    week = []
    for d in month_days:
        if d.month == month:
            text = f"{d.day}"
            callback = f"date:{d.strftime('%d.%m.%Y')}"
        else:
            text = " "
            callback = "ignore"

        week.append(
            InlineKeyboardButton(text=text, callback_data=callback)
        )

        if len(week) == 7:
            kb.append(week)
            week = []

    # ===== NAVIGATION =====
    prev_month = month - 1 or 12
    prev_year = year - 1 if month == 1 else year

    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    kb.append([
        InlineKeyboardButton(
            text="⬅️",
            callback_data=f"nav:{prev_year}:{prev_month}"
        ),
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"nav:{next_year}:{next_month}"
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def current_calendar() -> InlineKeyboardMarkup:
    today = date.today()
    return build_calendar(today.year, today.month)

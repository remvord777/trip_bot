from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from datetime import date, timedelta
from db.database import get_last_cities


# ───────────────
# ГЛАВНОЕ МЕНЮ
# ───────────────
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧳 Новая командировка")],
        [KeyboardButton(text="📋 Мои командировки")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)


# ───────────────
# ГОРОДА
# ───────────────
def city_keyboard() -> ReplyKeyboardMarkup:
    cities = get_last_cities()

    keyboard = []

    # формируем кнопки 2×2
    row = []
    for city in cities:
        row.append(KeyboardButton(text=city))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton(text="❌ Отмена")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Начните вводить город"
    )


# ───────────────
# ОБЪЕКТЫ
# ───────────────
def object_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ГРЭС"), KeyboardButton(text="ТЭЦ"), KeyboardButton(text="ТЭС")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Введите объект"
    )


def purpose_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Сервисное обслуживание ПТК АСУТП ПГУ и ДКС")],
            [KeyboardButton(text="Сервис ПТК АСУТП")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Сохранить")],
            [KeyboardButton(text="✏️ Изменить")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

# ───────────────
# КНОПКА ОТМЕНЫ
# ───────────────
cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True
)


# ───────────────
# КАЛЕНДАРЬ (7 дней)
# ───────────────
def calendar_keyboard() -> InlineKeyboardMarkup:
    today = date.today()
    buttons = []

    for i in range(7):
        d = today + timedelta(days=i)
        text = d.strftime("%d.%m.%Y")
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"date:{text}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

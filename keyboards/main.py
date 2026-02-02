from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from datetime import date, timedelta
from data.locations import LOCATIONS


# ─────────────────────
# ГЛАВНОЕ МЕНЮ
# ─────────────────────
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧳 Новая командировка")],
        [KeyboardButton(text="📄 Авансовый отчёт")], #->handlers/advance_report/router.py
        [KeyboardButton(text="📋 Мои командировки")],
        [KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True,
)



# ─────────────────────
# ТИП НАСЕЛЁННОГО ПУНКТА (на будущее)
# ─────────────────────
def settlement_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏙 Город")],
            [KeyboardButton(text="🏘 Посёлок")],
            [KeyboardButton(text="🏡 Село")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


# ─────────────────────
# ГОРОДА / НАС. ПУНКТЫ
# ─────────────────────
def city_keyboard() -> ReplyKeyboardMarkup:
    cities = list(LOCATIONS.keys())

    # fallback, если справочник пуст
    if not cities:
        cities = [
            "Кириши",
            "Адлер",
            "Крымск",
            "Рефтинский",
        ]

    keyboard: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []

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
        input_field_placeholder="Введите город или населённый пункт",
    )


# ─────────────────────
# ОБЪЕКТ
# ─────────────────────
def object_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="ГРЭС"),
                KeyboardButton(text="ТЭЦ"),
                KeyboardButton(text="ТЭС"),
            ],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Введите объект",
    )


# ─────────────────────
# ЦЕЛЬ КОМАНДИРОВКИ
# ─────────────────────
def purpose_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Сервисное обслуживание ПТК АСУТП ПГУ и ДКС")],
            [KeyboardButton(text="Сервис ПТК АСУТП")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


# ─────────────────────
# ПОДТВЕРЖДЕНИЕ
# ─────────────────────
def confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Сохранить")],
            [KeyboardButton(text="✏️ Изменить")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


# ─────────────────────
# СОТРУДНИК
# ─────────────────────
def employee_keyboard() -> ReplyKeyboardMarkup:
    from data.employees import EMPLOYEES

    keyboard = [[KeyboardButton(text=name)] for name in EMPLOYEES.keys()]
    keyboard.append([KeyboardButton(text="➕ Ввести вручную")])
    keyboard.append([KeyboardButton(text="❌ Отмена")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


# ─────────────────────
# ПОСЛЕ КОМАНДИРОВКИ (на будущее)
# ─────────────────────
def after_trip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Запрос аванса")],
            [KeyboardButton(text="🏠 В главное меню")],
        ],
        resize_keyboard=True,
    )


# ─────────────────────
# КНОПКА ОТМЕНЫ
# ─────────────────────
cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True,
)


# ─────────────────────
# INLINE-КАЛЕНДАРЬ (7 дней)
# ─────────────────────
def calendar_keyboard() -> InlineKeyboardMarkup:
    today = date.today()
    buttons = []

    for i in range(7):
        d = today + timedelta(days=i)
        text = d.strftime("%d.%m.%Y")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"date:{text}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)

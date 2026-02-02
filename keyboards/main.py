from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# ================== ГЛАВНОЕ МЕНЮ ==================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧳 Командировка")],
        [KeyboardButton(text="💰 Авансовый отчёт")],
    ],
    resize_keyboard=True,
)


# ================== ЦЕЛЬ КОМАНДИРОВКИ ==================
def purpose_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пусконаладочные работы")],
            [KeyboardButton(text="Сервисное обслуживание ПТК АСУТП ПГУ")],
            [KeyboardButton(text="Сервис ПТК АСУТП")],
            [KeyboardButton(text="Комплексная наладка ПТК до проведения комплексных испытаний")],
            [KeyboardButton(text="Другое")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

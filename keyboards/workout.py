from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram_calendar import build_calendar

# Клавиатура для меню тренировок
workout_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить тренировку")],
        [KeyboardButton(text="Список тренировок")],
        [KeyboardButton(text="Назад в главное меню")],
    ],
    resize_keyboard=True
)

# Клавиатура для подтверждения/отмены создания тренировки
workout_confirm_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сохранить тренировку")],
        [KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True
)

# Инлайн-календарь на текущий месяц
def generate_calendar_kb(base_date: date = None):
    if base_date is None:
        base_date = date.today()
    return build_calendar(base_date.year, base_date.month)

# Клавиатура для этапа добавления упражнений
add_exercise_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить упражнение", callback_data="add_exercise")],
        [InlineKeyboardButton(text="📅 Календарь", callback_data="calendar")],
        [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
    ]
)

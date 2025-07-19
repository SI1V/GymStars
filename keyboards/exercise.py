from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_exercise_keyboard(exercises, page: int, total: int, page_size: int, for_workout: bool = False) -> InlineKeyboardMarkup:
    keyboard = []

    # Список упражнений
    for exercise in exercises:
        callback_prefix = "workout_add_exercise_" if for_workout else "exercise_"
        keyboard.append([
            InlineKeyboardButton(
                text=exercise.name,
                callback_data=f"{callback_prefix}{exercise.id}"
            )
        ])

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"exercises_page_{page - 1}"
            )
        )
    if (page + 1) * page_size < total:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"exercises_page_{page + 1}"
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Добавляем кнопку "Назад" в зависимости от контекста
    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Назад к типам",
            callback_data="back_to_types"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_exercise_type_keyboard(for_workout: bool = False) -> InlineKeyboardMarkup:
    prefix = "workout_type_" if for_workout else "exercise_type_"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️‍♂️ Силовые", callback_data=f"{prefix}STRENGTH")],
        [InlineKeyboardButton(text="🏃‍♂️ Кардио", callback_data=f"{prefix}CARDIO")],
        [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
    ])


def build_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️‍♂️ Силовые", callback_data="new_type_strength")],
        [InlineKeyboardButton(text="🏃‍♂️ Кардио", callback_data="new_type_cardio")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create_exercise")],
    ])


def build_exercise_action_keyboard(exercise_id: int, exercise_type: str = None, is_default: bool = False) -> InlineKeyboardMarkup:
    keyboard = []

    # Только если упражнение НЕ дефолтное, показываем редактирование и удаление
    if not is_default:
        keyboard.append([
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_exercise_{exercise_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_exercise_{exercise_id}")
        ])

    # Кнопка "Назад" — либо к упражнениям определённого типа, либо ко всем типам
    if exercise_type:
        keyboard.append([InlineKeyboardButton(
            text="⬅️ Назад к упражнениям",
            callback_data=f"back_to_exercises_{exercise_type}"
        )])
    else:
        keyboard.append([InlineKeyboardButton(
            text="⬅️ Назад к упражнениям",
            callback_data="back_to_types"
        )])

    # Кнопка главного меню
    keyboard.append([InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_delete_confirmation_keyboard(exercise_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_delete"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад к упражнениям",
                callback_data=f"back_to_exercises_{exercise_type}"
            )
        ]
    ])

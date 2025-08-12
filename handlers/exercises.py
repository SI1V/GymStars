from loguru import logger
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.connection import connection
from keyboards.main_menu import MAIN_MENU_TEXT
from models import ExerciseType
from states.exercise_states import ExerciseStates, CreateExerciseState, ExerciseEditState, DeleteExercise
from keyboards.exercise import build_exercise_keyboard, build_exercise_type_keyboard, build_type_keyboard, \
    build_exercise_action_keyboard, build_delete_confirmation_keyboard
from crud.exercise import get_exercises_by_type, create_exercise
from crud.exercise import get_exercise_by_id, update_exercise_by_name, delete_exercise

router = Router()

PAGE_SIZE = 5


async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup):
    """
    Безопасное обновление сообщения: обновляет только если текст или клавиатура изменились.
    """
    current_text = callback.message.text
    current_markup = callback.message.reply_markup

    if current_text == text and current_markup == reply_markup:
        logger.info("Сообщение не изменено, пропускаем обновление.")
        await callback.answer()
        return

    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()


@router.message(F.text == "/exercises")
async def start_exercise_flow(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} начал просмотр упражнений.")
    await message.answer("Выбери тип упражнения:", reply_markup=build_exercise_type_keyboard())
    await state.set_state(ExerciseStates.choosing_type)


@router.callback_query(F.data.startswith("exercise_type_"))
@connection
async def chosen_type(callback: CallbackQuery, state: FSMContext, session):
    try:
        # Надёжно вытаскиваем тип
        _, _, type_raw = callback.data.split("_", maxsplit=2)
        enum_type = ExerciseType[type_raw.upper()]
    except (ValueError, KeyError) as e:
        logger.error(f"Неверный формат типа упражнения: {callback.data} | {e}")
        await callback.answer("❌ Ошибка выбора типа упражнения.", show_alert=True)
        return

    logger.info(f"Пользователь {callback.from_user.id} выбрал тип упражнения: {enum_type.value}")
    await state.update_data(exercise_type=enum_type.value)

    page = 0        # Начинаем с первой страницы
    page_size = 5   # Количество упражнений на странице

    # Загружаем упражнения с указанием page и page_size
    exercises, total = await get_exercises_by_type(
        session,
        exercise_type=enum_type.value,
        user_id=callback.from_user.id,
        page=page,
        page_size=page_size,
    )

    keyboard = build_exercise_keyboard(
        exercises=exercises,
        page=page,
        total=total,
        page_size=page_size,
        for_workout=False
    )

    await callback.message.edit_text(
        text=f"📋 Упражнения типа: {enum_type.value}",
        reply_markup=keyboard
    )
    await callback.answer()



@router.callback_query(F.data.startswith("exercises_page_"))
@connection
async def paginate(callback: CallbackQuery, state: FSMContext, session):
    logger.info(f"Пользователь {callback.from_user.id} перешел на страницу {callback.data.split('_')[-1]}.")
    data = await state.get_data()
    type_raw = data.get("exercise_type")
    page = int(callback.data.split("_")[-1])
    await state.update_data(page=page)

    exercises, total = await get_exercises_by_type(
        session=session,
        exercise_type=type_raw,
        user_id=callback.from_user.id,
        page=page,
        page_size=PAGE_SIZE
    )

    markup = build_exercise_keyboard(exercises, page=page, total=total, page_size=PAGE_SIZE)

    await safe_edit_message(callback, f"Тип: {type_raw.upper()}\nВыбери упражнение:", markup)


@router.message(F.text == "/new_exercise")
async def start_create_exercise(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} начал создание нового упражнения.")
    await message.answer("Выбери тип упражнения:", reply_markup=build_type_keyboard())
    await state.set_state(CreateExerciseState.choosing_type)


@router.callback_query(F.data.startswith("new_type_"))
async def choose_type(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Пользователь {callback.from_user.id} выбрал тип нового упражнения: {callback.data}.")
    type_str = callback.data.split("_")[-1]
    await state.update_data(type=type_str)
    await callback.message.edit_text(f"Тип упражнения: {type_str.upper()}\nТеперь введи название упражнения:")
    await state.set_state(CreateExerciseState.entering_name)
    await callback.answer()


@router.message(CreateExerciseState.entering_name)
@connection
async def enter_name(message: Message, state: FSMContext, session):
    data = await state.get_data()
    type_str = data.get("type")
    logger.info(f"Пользователь {message.from_user.id} создает упражнение типа {type_str} с названием: {message.text}.")
    try:
        ex = await create_exercise(
            session=session,
            name=message.text,
            description="",
            ex_type=type_str,
            user_id=message.from_user.id
        )
        logger.info(f"Упражнение {ex.name} успешно создано для пользователя {message.from_user.id}.")
        await message.answer(f"✅ Упражнение «{ex.name}» типа {type_str.upper()} создано!")
        # Показываем список упражнений этого типа
        page = 0
        exercises, total = await get_exercises_by_type(
            session=session,
            exercise_type=type_str,
            user_id=message.from_user.id,
            page=page,
            page_size=PAGE_SIZE
        )
        markup = build_exercise_keyboard(exercises, page=page, total=total, page_size=PAGE_SIZE)
        await message.answer(f"Тип: {type_str.upper()}\nВыбери упражнение:", reply_markup=markup)
        await state.update_data(exercise_type=type_str, page=0)
        await state.set_state(ExerciseStates.showing_exercises)
    except ValueError as e:
        logger.error(f"Ошибка при создании упражнения для пользователя {message.from_user.id}: {e}")
        await message.answer("🚫 Неверный тип упражнения. Попробуй снова команду /new_exercise.")
        await state.clear()


@router.callback_query(F.data.regexp(r"^exercise_\d+$"))
@connection
async def show_exercise_actions(callback: CallbackQuery, state: FSMContext, session):
    try:
        parts = callback.data.split("_")
        if len(parts) < 2 or not parts[1].isdigit():
            raise ValueError("Некорректный формат callback_data")

        exercise_id = int(parts[1])
    except ValueError as e:
        logger.error(f"Ошибка парсинга ID упражнения из callback_data: {callback.data} | {e}")
        await callback.answer("❌ Неверные данные кнопки.", show_alert=True)
        return

    exercise = await get_exercise_by_id(session=session, ex_id=exercise_id)

    if exercise is None:
        logger.warning(f"Пользователь {callback.from_user.id} попытался получить доступ к недоступному упражнению.")
        await callback.answer("🚫 Упражнение не найдено.", show_alert=True)
        return

    # Получаем тип упражнения из состояния, чтобы сделать кнопку "Назад"
    data = await state.get_data()
    exercise_type = data.get("exercise_type")

    if exercise.is_default:
        logger.info(f"Пользователь {callback.from_user.id} выбрал упражнение по умолчанию {exercise.name}.")
        await callback.message.edit_text(
            f"🏋️ Упражнение: {exercise.name}",
            reply_markup=build_exercise_action_keyboard(
                exercise_id=exercise.id,
                exercise_type=exercise_type,
                is_default=exercise.is_default
            )
        )
        await callback.answer()
        return

    # Для редактируемых упражнений тоже передаём клавиатуру с кнопкой "Назад"
    await callback.message.edit_text(
        f"🏋️ Упражнение: {exercise.name}\n\n"
        f"Тип: {exercise.type.value}",
        reply_markup=build_exercise_action_keyboard(
            exercise_id=exercise.id,
            exercise_type=exercise_type
        )
    )
    await callback.answer()



@router.callback_query(F.data.startswith("edit_exercise_"))
async def edit_exercise(callback: CallbackQuery, state: FSMContext):
    exercise_id = int(callback.data.split("_")[2])
    logger.info(f"Пользователь {callback.from_user.id} начал редактирование упражнения {exercise_id}.")
    await state.update_data(exercise_id=exercise_id)
    await callback.message.edit_text("Введите новое название упражнения:")
    await state.set_state(ExerciseEditState.entering_name)
    await callback.answer()


@router.message(ExerciseEditState.entering_name)
@connection
async def update_exercise_name_handler(message: Message, state: FSMContext, session):
    data = await state.get_data()
    exercise_id = data.get("exercise_id")
    new_name = message.text

    try:
        updated_exercise = await update_exercise_by_name(session=session, exercise_id=exercise_id, new_name=new_name)
        logger.info(f"Упражнение {updated_exercise.id} успешно обновлено пользователем {message.from_user.id}.")
        # После редактирования показываем список упражнений этого типа
        type_str = updated_exercise.type.value.lower()
        page = 0
        exercises, total = await get_exercises_by_type(
            session=session,
            exercise_type=type_str,
            user_id=message.from_user.id,
            page=page,
            page_size=PAGE_SIZE
        )
        markup = build_exercise_keyboard(exercises, page=page, total=total, page_size=PAGE_SIZE)
        await message.answer(f"✅ Упражнение обновлено: {updated_exercise.name}")
        await message.answer(f"Тип: {type_str.upper()}\nВыбери упражнение:", reply_markup=markup)
        await state.update_data(exercise_type=type_str, page=0)
        await state.set_state(ExerciseStates.showing_exercises)
    except ValueError as e:
        logger.error(f"Ошибка при обновлении упражнения: {e}")
        await message.answer("🚫 Ошибка при обновлении упражнения. Попробуйте снова.")
        await state.clear()


@router.callback_query(F.data.startswith("delete_exercise_"))
async def confirm_delete_exercise(callback: CallbackQuery, state: FSMContext):
    try:
        exercise_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Неверный формат ID упражнения.", show_alert=True)
        return

    logger.info(f"Пользователь {callback.from_user.id} запросил удаление упражнения {exercise_id}.")

    # Сохраняем данные в состояние
    data = await state.get_data()
    await state.update_data(exercise_id=exercise_id, exercise_type=data.get("exercise_type"))

    await callback.message.edit_text(
        "❗ Вы уверены, что хотите удалить это упражнение?",
        reply_markup=build_delete_confirmation_keyboard(data.get("exercise_type"))
    )
    await state.set_state(DeleteExercise.confirm)
    await callback.answer()



@router.callback_query(F.data == "confirm_delete")
@connection
async def confirm_delete(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    exercise_id = data.get("exercise_id")
    exercise_type = data.get("exercise_type")
    user_id = callback.from_user.id

    if not exercise_id:
        logger.error("ID упражнения не найден в состоянии.")
        await callback.answer("🚫 Ошибка: ID упражнения не найден.", show_alert=True)
        return

    logger.info(f"Пользователь {user_id} подтвердил удаление упражнения {exercise_id}.")

    deleted_count = await delete_exercise(session=session, ex_id=exercise_id, user_id=user_id)

    if deleted_count == 0:
        logger.warning(f"Удаление упражнения {exercise_id} не удалось — не найдено или нет доступа.")
        await callback.answer("🚫 Невозможно удалить это упражнение.", show_alert=True)
        return

    await callback.answer("✅ Упражнение удалено.")

    # Загружаем обновлённый список
    page = 0
    page_size = 5
    exercises, total = await get_exercises_by_type(
        session=session,
        exercise_type=exercise_type,
        user_id=user_id,
        page=page,
        page_size=page_size
    )

    await callback.message.edit_text(
        text="Список упражнений",
        reply_markup=build_exercise_keyboard(
            exercises=exercises,
            page=page,
            total=total,
            page_size=page_size,
            for_workout=False
        )
    )

    await state.clear()



@router.callback_query(F.data == "confirm_delete")
@connection
async def confirm_delete(callback: CallbackQuery, state: FSMContext, session):
    data = await state.get_data()
    exercise_id = data.get("exercise_id")
    exercise_type = data.get("exercise_type")
    user_id = callback.from_user.id

    if not exercise_id:
        logger.error("ID упражнения не найден в состоянии.")
        await callback.answer("🚫 Ошибка: ID упражнения не найден.", show_alert=True)
        return

    logger.info(f"Пользователь {user_id} подтвердил удаление упражнения {exercise_id}.")

    deleted_count = await delete_exercise(session=session, ex_id=exercise_id, user_id=user_id)

    if deleted_count == 0:
        logger.warning(f"Удаление упражнения {exercise_id} не удалось — не найдено или нет доступа.")
        await callback.answer("🚫 Невозможно удалить это упражнение.", show_alert=True)
        return

    await callback.answer("✅ Упражнение удалено.")

    # Загружаем обновлённый список
    page = 0
    page_size = 5
    exercises, total = await get_exercises_by_type(
        session=session,
        exercise_type=exercise_type,
        user_id=user_id,
        page=page,
        page_size=page_size
    )

    await callback.message.edit_text(
        text="📋 Упражнение удалено. Вот обновлённый список:",
        reply_markup=build_exercise_keyboard(
            exercises=exercises,
            page=page,
            total=total,
            page_size=page_size,
            for_workout=False
        )
    )

    await state.clear()



@router.callback_query(F.data.startswith("back_to_exercises_"))
@connection
async def back_to_exercises(callback: CallbackQuery, state: FSMContext, session):
    exercise_type = callback.data.split("_")[-1]
    logger.info(f"Пользователь {callback.from_user.id} вернулся к списку упражнений типа {exercise_type}.")

    # Сбросить выбранное упражнение, но оставить тип и страницу
    data = await state.get_data()
    page = data.get("page", 0)
    await state.update_data(exercise_id=None)

    exercises, total = await get_exercises_by_type(
        session=session,
        exercise_type=exercise_type,
        user_id=callback.from_user.id,
        page=page,
        page_size=PAGE_SIZE
    )

    markup = build_exercise_keyboard(exercises, page=page, total=total, page_size=PAGE_SIZE)

    await safe_edit_message(callback, f"Тип: {exercise_type.upper()}\nВыбери упражнение:", markup)
    await state.set_state(ExerciseStates.showing_exercises)


@router.callback_query(F.data == "back_to_types")
async def back_to_types(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Пользователь {callback.from_user.id} вернулся к выбору типа упражнений.")
    await callback.message.edit_text(
        "Выбери тип упражнения:",
        reply_markup=build_exercise_type_keyboard()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню.")
    await callback.message.answer(MAIN_MENU_TEXT)
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_create_exercise")
async def cancel_create_exercise(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Пользователь {callback.from_user.id} отменил создание упражнения.")
    await callback.message.edit_text(
        "Создание упражнения отменено.",
        reply_markup=build_exercise_type_keyboard()
    )
    await state.set_state(ExerciseStates.choosing_type)
    await callback.answer()

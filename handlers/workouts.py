from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

from database.connection import connection
from keyboards.main_menu import MAIN_MENU_TEXT
from states.workout_states import WorkoutStates
from keyboards.workout import workout_menu_kb, workout_confirm_kb, generate_calendar_kb, add_exercise_kb
from crud.workout import create_workout, get_user_workouts, get_workout_by_id, get_workout_by_user_and_date, get_workout_details
from crud.exercise import get_exercises_by_type, get_exercise_by_id
from loguru import logger
from aiogram.types import CallbackQuery
from telegram_calendar import build_calendar, CalendarCallback
from typing import Dict
from datetime import datetime
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from schemas.workout import WorkoutCreateSchema
from keyboards.exercise import build_exercise_keyboard, build_exercise_type_keyboard

router = Router()


@router.message(Command("workouts"))
@connection
async def workouts_calendar(message: Message, state: FSMContext, session):
    logger.info(f"Пользователь {message.from_user.id} открыл календарь тренировок")
    now = datetime.now()
    workouts = await get_user_workouts(session, user_id=message.from_user.id)
    icon_dates: Dict[str, str] = {}
    for w in workouts:
        # Заменяем дату на иконку кубка
        icon_dates[str(w.date)] = "🏆"
    calendar = build_calendar(now.year, now.month, icon_dates=icon_dates)
    await message.answer("Выберите дату для создания тренировки:", reply_markup=calendar)
    await state.clear()

@router.callback_query(CalendarCallback.filter())
@connection
async def process_calendar_selection(call: CallbackQuery, callback_data: CalendarCallback, state: FSMContext, session):
    logger.info(f"Пользователь {call.from_user.id} выбрал дату через календарь: {callback_data}")
    action = callback_data.action
    year = callback_data.year
    month = callback_data.month
    day = getattr(callback_data, "day", 0)
    workouts = await get_user_workouts(session, user_id=call.from_user.id)
    icon_dates: Dict[str, str] = {}
    for w in workouts:
        # Используем такую же иконку при обновлении календаря
        icon_dates[str(w.date)] = "🏆"
    if action == "select_day" and day > 0:
        date = datetime(year, month, day).date()
        workout = await get_workout_by_user_and_date(session, user_id=call.from_user.id, date=date)
        if workout:
            try:
                workout_details = await get_workout_details(session=session, workout=workout)

                # Формируем текст с информацией о тренировке
                text = f"Тренировка на {date.strftime('%d.%m.%Y')}\nЗаметка: {workout.comment or '-'}\n\nУпражнения:"

                # Упражнения уже отсортированы в порядке добавления (старые вверху, новые внизу)
                for exercise in workout_details["exercises"]:
                    text += f"\n\n🔹 {exercise['name']} ({exercise['type']})"
                    if exercise['reps']:
                        if exercise['type'] == 'CARDIO':
                            text += "\nВремя:"
                        else:
                            text += "\nПодходы:"
                        # Подходы отсортированы в порядке добавления
                        for i, rep in enumerate(exercise['reps'], 1):
                            if exercise['type'] == 'CARDIO':
                                text += f"\n⏱ {rep.get('duration', 0)} мин"
                            else:
                                text += f"\n💪 {rep['weight']}кг x {rep['count']}"
                    else:
                        if exercise['type'] == 'CARDIO':
                            text += "\nВремя не указано"
                        else:
                            text += "\nНет записанных подходов"

                await call.message.answer(text, reply_markup=add_exercise_kb)
                logger.info(f"Пользователь {call.from_user.id} просмотрел тренировку на дату {date}")
            except Exception as e:
                logger.error(f"Ошибка при получении деталей тренировки: {e}")
                await call.message.answer("Произошла ошибка при получении деталей тренировки.")
        else:
            await state.set_state(WorkoutStates.adding_exercises)
            await state.update_data(date=date)

            await call.message.answer(
                f"Дата тренировки: {date.strftime('%d.%m.%Y')}\nТеперь вы можете добавить упражнения.",
                reply_markup=add_exercise_kb
            )
            logger.info(f"Пользователь {call.from_user.id} начал добавление тренировки на дату {date}")
        await call.answer()
    elif action in ("select_month", "show_months"):
        calendar = build_calendar(year, month, icon_dates=icon_dates)
        await call.message.edit_reply_markup(reply_markup=calendar)
        await call.answer()
    elif action == "show_years":
        from telegram_calendar import build_year_selector
        calendar = build_year_selector(year)
        await call.message.edit_reply_markup(reply_markup=calendar)
        await call.answer()
    elif action == "select_year":
        from telegram_calendar import build_month_selector
        calendar = build_month_selector(year)
        await call.message.edit_reply_markup(reply_markup=calendar)
        await call.answer()
    elif action == "change_year_range":
        from telegram_calendar import build_year_selector
        calendar = build_year_selector(year)
        await call.message.edit_reply_markup(reply_markup=calendar)
        await call.answer()
    else:
        await call.answer()

@router.message(WorkoutStates.adding_exercises, F.text == "Добавить упражнение")
async def add_exercise(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} выбрал добавить упражнение")
    await state.set_state(WorkoutStates.choosing_exercise_type)
    await message.answer("Выберите тип упражнения:", reply_markup=build_exercise_type_keyboard())

@router.callback_query(F.data == "add_exercise")
async def add_exercise_inline(call: CallbackQuery, state: FSMContext):
    # Сохраняем дату из текущей тренировки
    data = await state.get_data()

    if not data.get("date"):
        # Пытаемся извлечь дату из текста сообщения
        message_text = call.message.text
        if "Тренировка на" in message_text:
            try:
                date_str = message_text.split("Тренировка на")[1].split("\n")[0].strip()
                date = datetime.strptime(date_str, "%d.%m.%Y").date()
                await state.update_data(date=date)
            except Exception as e:
                logger.error(f"Ошибка при извлечении даты: {e}")
                await call.answer("Не удалось определить дату тренировки", show_alert=True)
                return

    # Переходим к выбору типа упражнения для тренировки
    await state.set_state(WorkoutStates.choosing_exercise_type)
    await call.message.edit_text(
        "Выберите тип упражнения для добавления в тренировку:",
        reply_markup=build_exercise_type_keyboard(for_workout=True)
    )
    await call.answer()

@router.callback_query(F.data.startswith("workout_type_"))
@connection
async def choose_exercise_type(call: CallbackQuery, state: FSMContext, session):
    """Обработчик выбора типа упражнения при добавлении в тренировку"""
    current_state = await state.get_state()
    if current_state != WorkoutStates.choosing_exercise_type:
        logger.info(f"Игнорируем workout_type_ callback в неправильном состоянии: {current_state}")
        return False

    # workout_type_STRENGTH -> STRENGTH (уже в верхнем регистре)
    exercise_type = call.data.split("_")[-1]
    logger.info(f"Пользователь {call.from_user.id} выбрал тип упражнения для тренировки: {exercise_type}")
    await state.update_data(exercise_type=exercise_type)
    await state.set_state(WorkoutStates.choosing_exercise)

    page = 0
    page_size = 5
    exercises, total = await get_exercises_by_type(session, exercise_type, call.from_user.id, page, page_size)

    await call.message.edit_text(
        "Выберите упражнение для добавления в тренировку:",
        reply_markup=build_exercise_keyboard(exercises, page, total, page_size, for_workout=True)
    )
    await call.answer()


@router.callback_query(F.data.startswith("workout_exercise_"))
@connection
async def choose_workout_exercise(call: CallbackQuery, state: FSMContext, session):
    exercise_id = int(call.data.split("_")[-1])
    logger.info(f"Пользователь {call.from_user.id} выбрал упражнение для тренировки: {exercise_id}")

    current_state = await state.get_state()
    if current_state != WorkoutStates.choosing_exercise:
        logger.warning(f"Неверное состояние для добавления упражнения: {current_state}")
        return

    data = await state.get_data()
    if "date" not in data:
        await call.answer("Сначала выберите дату тренировки", show_alert=True)
        return

    exercise = await get_exercise_by_id(session, exercise_id)
    if not exercise:
        await call.answer("Упражнение не найдено", show_alert=True)
        return

    await state.update_data(exercise_id=exercise_id)
    await state.set_state(WorkoutStates.entering_sets)

    # Формируем сообщение в зависимости от типа упражнения
    if exercise.type.value.upper() == "CARDIO":
        message_text = "Введите длительность упражнения в минутах (например: 30)"
    else:
        message_text = (
            "Введите подходы в формате:\n"
            "20 10\n"
            "40 10\n"
            "60 10\n"
            "(вес пробел количество повторов, перевод строки — новый подход)"
        )

    await call.message.edit_text(message_text)
    await call.answer()

@router.message(WorkoutStates.entering_sets)
@connection
async def enter_sets(message: Message, state: FSMContext, session):
    logger.info(f"Пользователь {message.from_user.id} ввёл подходы: {message.text}")
    data = await state.get_data()

    if "date" not in data or "exercise_id" not in data:
        logger.error(f"Нет даты или упражнения в state для пользователя {message.from_user.id}: {data}")
        await message.answer("Ошибка: не выбрана дата или упражнение. Пожалуйста, начните с выбора даты через календарь.")
        await state.clear()
        return

    workout = await get_workout_by_user_and_date(session, user_id=message.from_user.id, date=data["date"])
    if not workout:
        workout = await create_workout(
            session=session,
            user_id=message.from_user.id,
            data=WorkoutCreateSchema(date=data["date"], note=data.get("comment"))
        )

    # Получаем тип упражнения
    exercise = await get_exercise_by_id(session, data["exercise_id"])
    is_cardio = exercise.type.value == "CARDIO"

    # Сохраняем упражнение в workout_exercises
    from crud.rep import create_reps
    from models.workout_exercise import WorkoutExercise
    from sqlalchemy import select

    result = await session.execute(
        select(WorkoutExercise).where(
            WorkoutExercise.workout_id == workout.id,
            WorkoutExercise.exercise_id == data["exercise_id"]
        )
    )
    workout_exercise = result.scalar_one_or_none()
    if not workout_exercise:
        workout_exercise = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=data["exercise_id"]
        )
        session.add(workout_exercise)
        await session.commit()
        await session.refresh(workout_exercise)

    # Парсим подходы
    reps = []
    if is_cardio:
        try:
            duration = int(message.text.strip())
            reps.append({"duration": duration})
        except ValueError:
            await message.answer("Ошибка: введите только число минут")
            return
    else:
        for line in message.text.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) == 2:
                try:
                    weight = float(parts[0])
                    count = int(parts[1])
                    reps.append({"weight": weight, "count": count})
                except Exception as e:
                    logger.warning(f"Ошибка парсинга подхода: {line} ({e})")

    if reps:
        await create_reps(session, workout_exercise.id, reps)

    # Получаем обновленные данные тренировки и показываем их
    workout_details = await get_workout_details(session=session, workout=workout)
    text = f"Тренировка на {workout.date.strftime('%d.%m.%Y')}\nЗаметка: {workout.comment or '-'}\n\nУпражнения:"

    for ex in workout_details["exercises"]:
        text += f"\n\n🔹 {ex['name']} ({ex['type']})"
        if ex['reps']:
            if ex['type'] == 'CARDIO':
                text += "\nВремя:"
                for rep in ex['reps']:
                    text += f"\n{rep.get('duration', 0)} мин"
            else:
                text += "\nПодходы:"
                for rep in ex['reps']:
                    text += f"\n{rep['weight']}кг x {rep['count']}"
        else:
            text += "\nПодходы не указаны"


    # Используем reply_markup для отображения клавиатуры
    await message.answer(text, reply_markup=add_exercise_kb)
    await state.set_state(WorkoutStates.adding_exercises)


# Календарь и главное меню
@router.message(WorkoutStates.adding_exercises, F.text.in_(["Календарь", "Главная"]))
async def workout_nav_keyboard(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} выбрал: {message.text}")
    await state.clear()
    if message.text == "Календарь":
        await message.answer("Выберите дату для создания тренировки:", reply_markup=generate_calendar_kb())
    else:
        await message.answer("Главное меню", reply_markup=MAIN_MENU_TEXT)

# Начало добавления тренировки
@router.message(F.text == "Добавить тренировку")
async def add_workout_start(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} начал добавление тренировки")
    await state.set_state(WorkoutStates.choosing_date)
    await message.answer("Введите дату тренировки в формате ГГГГ-ММ-ДД:", reply_markup=types.ReplyKeyboardRemove())

# Ввод даты
@router.message(WorkoutStates.choosing_date)
async def add_workout_date(message: Message, state: FSMContext):
    try:
        date = datetime.strptime(message.text, "%Y-%m-%d").date()
        await state.update_data(date=date)
        await state.set_state(WorkoutStates.entering_note)
        await message.answer("Добавьте заметку к тренировке (или напишите - для пропуска):")
    except ValueError:
        logger.warning(f"Некорректная дата: {message.text}")
        await message.answer("Неверный формат. Введите в формате ГГГГ-ММ-ДД:")

# Ввод заметки
@router.message(WorkoutStates.entering_note)
async def add_workout_note(message: Message, state: FSMContext):
    note = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(note=note)
    await state.set_state(WorkoutStates.confirming)
    await message.answer("Сохранить тренировку?", reply_markup=workout_confirm_kb)

# Подтверждение сохранения
@router.message(WorkoutStates.confirming, F.text == "Сохранить тренировку")
@connection
async def add_workout_save(message: Message, state: FSMContext, session):
    data = await state.get_data()
    await create_workout(session, user_id=message.from_user.id, data=WorkoutCreateSchema(date=data["date"], note=data["note"]))
    await state.clear()
    await message.answer("Тренировка добавлена!", reply_markup=workout_menu_kb)
    logger.info(f"Тренировка сохранена для пользователя {message.from_user.id}")

# Отмена
@router.message(WorkoutStates.confirming, F.text == "Отмена")
async def add_workout_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Создание тренировки отменено.", reply_markup=workout_menu_kb)

# Список тренировок
@router.message(F.text == "Список тренировок")
@connection
async def list_workouts(message: Message, state: FSMContext, session):
    workouts = await get_user_workouts(user_id=message.from_user.id)
    if not workouts:
        await message.answer("У вас нет тренировок.", reply_markup=workout_menu_kb)
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"{w.id}: {w.date} {w.comment or ''}")] for w in workouts] +
                 [[KeyboardButton(text="Назад в главное меню")]],
        resize_keyboard=True
    )
    text = "Ваши тренировки:\n" + "\n".join([f"{w.id}: {w.date} {w.comment or ''}" for w in workouts])
    await message.answer(text, reply_markup=kb)

# Назад в главное меню
@router.message(F.text == "Назад в главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=MAIN_MENU_TEXT)

# Просмотр тренировки
@connection
@router.message(F.text.regexp(r"^\d+:"))
async def view_workout(message: Message, state: FSMContext, session):
    try:
        workout_id = int(message.text.split(":")[0])
        workout = await get_workout_by_id(session, workout_id)
    except Exception:
        await message.answer("Некорректный формат. Выберите тренировку из списка.")
        return

    if not workout or workout.user_id != message.from_user.id:
        await message.answer("Тренировка не найдена.")
        return

    await state.update_data(viewing_workout_id=workout.id)
    text = f"Тренировка №{workout.id}\nДата: {workout.date}\nЗаметка: {workout.comment or '-'}"
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Редактировать"), KeyboardButton("Удалить")],
            [KeyboardButton("Назад к списку тренировок")]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=kb)

# Назад к списку тренировок
@router.message(F.text == "Назад к списку тренировок")
@connection
async def back_to_workout_list(message: Message, state: FSMContext, session):
    workouts = await get_user_workouts(user_id=message.from_user.id)
    if not workouts:
        await message.answer("У вас нет тренировок.", reply_markup=workout_menu_kb)
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"{w.id}: {w.date} {w.comment or ''}")] for w in workouts] +
                 [[KeyboardButton(text="Назад в главное меню")]],
        resize_keyboard=True
    )
    text = "Ваши тренировки:\n" + "\n".join([f"{w.id}: {w.date} {w.comment or ''}" for w in workouts])
    await message.answer(text, reply_markup=kb)

# Инлайн: показать действия
@router.message(WorkoutStates.adding_exercises)
async def show_add_exercise_inline(message: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Добавить упражнение", callback_data="add_exercise")],
            [InlineKeyboardButton("Календарь", callback_data="calendar")],
            [InlineKeyboardButton("Главная", callback_data="main_menu")],
        ]
    )
    await message.answer("Выберите действие:", reply_markup=kb)

# Инлайн: добавить упражнение
@router.callback_query(F.data == "add_exercise")
async def add_exercise_inline(call: CallbackQuery, state: FSMContext):
    # Сохраняем дату из текущей тренировки
    data = await state.get_data()

    if not data.get("date"):
        # Пытаемся извлечь дату из текста сообщения
        message_text = call.message.text
        if "Тренировка на" in message_text:
            try:
                date_str = message_text.split("Тренировка на")[1].split("\n")[0].strip()
                date = datetime.strptime(date_str, "%d.%m.%Y").date()
                await state.update_data(date=date)
            except Exception as e:
                logger.error(f"Ошибка при извлечении даты: {e}")
                await call.answer("Не удалось определить дату тренировки", show_alert=True)
                return

    # Переходим к выбору типа упражнения для тренировки
    await state.set_state(WorkoutStates.choosing_exercise_type)
    await call.message.edit_text(
        "Выберите тип упражнения для добавления в тренировку:",
        reply_markup=build_exercise_type_keyboard(for_workout=True)
    )
    await call.answer()

# Инлайн: вернуться к календарю
@router.callback_query(F.data == "calendar")
@connection
async def back_to_calendar_inline(call: CallbackQuery, state: FSMContext, session):
    now = datetime.now()
    workouts = await get_user_workouts(session=session, user_id=call.from_user.id)
    icon_dates: Dict[str, str] = {}
    for w in workouts:
        icon_dates[str(w.date)] = "🏆"
    calendar = build_calendar(now.year, now.month, icon_dates=icon_dates)
    await state.clear()
    await call.message.edit_text("Выберите дату для создания тренировки:", reply_markup=calendar)
    await call.answer()

# Инлайн: вернуться в главное меню
@router.callback_query(F.data == "main_menu")
async def back_to_main_inline(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(MAIN_MENU_TEXT)
    await call.answer()

@router.callback_query(F.data.startswith("workout_add_exercise_"))
@connection
async def add_exercise_to_workout(call: CallbackQuery, state: FSMContext, session):
    exercise_id = int(call.data.split("_")[-1])
    logger.info(f"Пользователь {call.from_user.id} выбрал упражнение для тренировки: {exercise_id}")

    current_state = await state.get_state()
    if current_state != WorkoutStates.choosing_exercise:
        logger.warning(f"Неверное состояние для добавления упражнения: {current_state}")
        return

    data = await state.get_data()
    if "date" not in data:
        await call.answer("Сначала выберите дату тренировки", show_alert=True)
        return

    exercise = await get_exercise_by_id(session, exercise_id)
    if not exercise:
        await call.answer("Упражнение не найдено", show_alert=True)
        return

    await state.update_data(exercise_id=exercise_id)
    await state.set_state(WorkoutStates.entering_sets)

    # Формируем сообщение в зависимости от типа упражнения
    if exercise.type.value == "CARDIO":
        message_text = "Введите длительность упражнения в минутах (например: 30)"
    else:
        message_text = (
            "Введите подходы в формате:\n"
            "20 10\n"
            "40 10\n"
            "60 10\n"
            "(вес пробел количество повторов, каждый подход с новой строки)"
        )

    await call.message.edit_text(message_text)
    await call.answer()

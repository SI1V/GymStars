from aiogram.fsm.state import State, StatesGroup

class ExerciseStates(StatesGroup):
    choosing_type = State()
    showing_exercises = State()


class CreateExerciseState(StatesGroup):
    choosing_type = State()
    entering_name = State()


class ExerciseEditState(StatesGroup):
    waiting_for_new_name = State()
    entering_name = State()


class DeleteExercise(StatesGroup):
    confirm = State()

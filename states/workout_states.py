from aiogram.fsm.state import StatesGroup, State

class WorkoutStates(StatesGroup):
    choosing_date = State()
    entering_note = State()
    confirming = State()
    editing = State()
    deleting = State()
    adding_exercises = State()
    choosing_exercise_type = State()
    choosing_exercise = State()
    entering_sets = State()

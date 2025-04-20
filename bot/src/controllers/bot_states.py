from aiogram.fsm.state import StatesGroup, State

class UserStates(StatesGroup):
    automatic_mode = State()
    manual_mode = State()

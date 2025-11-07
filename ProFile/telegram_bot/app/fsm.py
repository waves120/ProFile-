
from aiogram.fsm.state import StatesGroup, State

class AddFlow(StatesGroup):
    waiting_title = State()
    waiting_board_choice = State()
    waiting_new_board_name = State()

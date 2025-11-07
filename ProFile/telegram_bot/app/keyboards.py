
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def title_choice_kb(basic_title: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Оставить: «{basic_title[:24]}»", callback_data=f"title_keep")],
        [InlineKeyboardButton(text="Изменить название", callback_data="title_change")]
    ])

def boards_kb(board_names: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=name, callback_data=f"board:{name}") ] for name in board_names[:60]]
    rows.append([InlineKeyboardButton(text="Создать новую…", callback_data="board_create")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

def get_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Задать вопрос техподдержке", callback_data="manual_mode")]
        ]
    )

def get_pagination_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    if current_page > 0:
        buttons.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"page_{current_page - 1}"))
    if current_page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="Вперед ➡", callback_data=f"page_{current_page + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

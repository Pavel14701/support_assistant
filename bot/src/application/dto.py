from typing import Union
from dataclasses import dataclass

from aiogram.types import Message
from aiogram.fsm.context import FSMContext

@dataclass(slots=True)
class PaginateAnswerDto:
    answer: str
    user_id: Union[str,int]


@dataclass(slots=True, frozen=True)
class StartDto:
    message: Message
    state: FSMContext


@dataclass(slots=True)
class QuestionHandlerDto:
    user_id: str|int
    question: str
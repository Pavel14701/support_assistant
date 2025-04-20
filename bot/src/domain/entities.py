from dataclasses import dataclass, asdict, field
from typing import Optional, TypedDict

from aiogram import Bot
from aiogram.types import User, CallbackQuery, Message
from aiogram.fsm.context import FSMContext

class AsDict:
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True, frozen=True)
class ApiRequest(AsDict):
    role: str
    content: str


@dataclass(slots=True, frozen=True)
class MessagePaginatorDm:
    user: User 
    callback: CallbackQuery
    pages: Optional[list[str]]


@dataclass(slots=True, frozen=True)
class SendMessageGroupDm:
    message: Message 
    state: FSMContext


@dataclass(slots=True, frozen=True)
class StartDm:
    message: Message
    state: FSMContext
    current_state: str


@dataclass(slots=True, frozen=True)
class SendAnswerDm:
    message: Message
    state: FSMContext


class ResponseMessage(TypedDict):
    user_id: int
    answer_uuid: str


@dataclass(slots=True)
class QuestionHandlerDm:
    user_id: str|int
    question: str
    correlation_id: str
    timeout: int = field(default=60)
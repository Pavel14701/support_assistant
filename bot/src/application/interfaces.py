from typing import Optional, Protocol
from abc import abstractmethod
from uuid import UUID

from bot.src.domain.entities import (
    MessagePaginatorDm, 
    QuestionHandlerDm, 
    ResponseMessage, 
    StartDm
)


class Start(Protocol):
    @abstractmethod
    async def start(self, params: StartDm) -> None: ...


class AnswersGetter(Protocol):
    @abstractmethod
    async def get_saved_answers(self, uuid: str) -> Optional[list[str]]: ...


class ApiProvider(Protocol):
    @abstractmethod
    async def main(message: dict[str:str]) -> str: ...


class MessagePaginator(Protocol):
    @abstractmethod
    async def paginate_message(self, params: MessagePaginatorDm) -> None: ...


class AnswersGetter(Protocol):
    @abstractmethod
    async def get_saved_answers(self, uuid: str) -> Optional[list[str]]: ...


class AnswersHandler(Protocol):
    @abstractmethod
    async def send_and_receive(self, params: QuestionHandlerDm) -> ResponseMessage: ...


class UUIDGenerator(Protocol):
    def __call__(self) -> UUID: ...
from typing import Optional, Protocol
from abc import abstractmethod
from uuid import UUID

from torch import Tensor

from sentence_bert.src.domain.entities import (
    AnswerBaseDataDm,
    AnswersChunksDm,
    AnswersDataDm,
    EncodedAnswersDm,
    ProcessQueryDm
)


class KnowledgeBaseService(Protocol):
    @abstractmethod
    async def process_query(self, params: ProcessQueryDm) -> str: ...


class EmbendingNormalization(Protocol):
    @abstractmethod
    def l2_normalization(self, embeddings: Tensor) -> Tensor: ...


class EmbendingEncoder(Protocol):
    @abstractmethod
    def encode_knowledge_base(self, knowledge_base: AnswersDataDm) -> EncodedAnswersDm: ...


class CacheEmbendingsGetter(Protocol):
    @abstractmethod
    async def get_all_embeddings_scan(self) -> Optional[EncodedAnswersDm]: ...


class ResultSender(Protocol):
    @abstractmethod
    async def send_answer(self, params) -> None: ...


class AnswerPaginator(Protocol):
    @abstractmethod
    async def paginate_answer(self, text: str) -> AnswersChunksDm: ...


class LoadKnowledgeBase(Protocol):
    @abstractmethod
    def from_csv(self, delimiter: str = "~") -> AnswerBaseDataDm: ...


class SaveAnswersCache(Protocol):
    @abstractmethod
    async def save_answers(self, params: AnswersDataDm) -> AnswersDataDm: ...


class CreateAnswersDict(Protocol):
    @abstractmethod
    def create_answers_data(self, answers: list[AnswersChunksDm]) -> AnswersDataDm: ...


class UUIDGenerator(Protocol):
    def __call__(self) -> UUID: ...
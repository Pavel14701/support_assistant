from dataclasses import dataclass
from typing import Callable, Optional

from torch import Tensor


@dataclass(frozen=True, slots=True)
class AnswerBaseDataDm:
    answers: list[str]


@dataclass(frozen=True, slots=True)
class AnswersChunksDm:
    chunks: list[str]


@dataclass(frozen=True, slots=True)
class AnswersGetUuidDm:
    chunks: list[list[str]]
    embendings: list[Tensor]


@dataclass(frozen=True, slots=True)
class AnswersDataDm:
    answers: dict[str, list[str]]
    answers_embendings: dict[str, Tensor]

@dataclass(frozen=True, slots=True)
class AnswerDm:
    user_id: str|int
    answer: Optional[str]
    correlation_id: str


@dataclass(frozen=True, slots=True)
class EncodedAnswersDm:
    answers: dict[str, Tensor]


@dataclass(frozen=True, slots=True)
class ProcessQueryDm:
    query: str
    knowledge_base_embeddings: dict[str, Tensor]
    normalization: Callable[[Tensor], Tensor]
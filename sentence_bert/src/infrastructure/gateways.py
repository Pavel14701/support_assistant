import csv
import json
from io import BytesIO
from typing import Optional

from redis.asyncio import Redis
from faststream.rabbit import RabbitBroker
from faststream.rabbit.message import RabbitMessage

from transformers import T5Tokenizer, T5EncoderModel
from transformers.modeling_outputs import BaseModelOutput
from torch.nn.functional import cosine_similarity
import torch

from sentence_bert.src.application.interfaces import (
    AnswerPaginator,
    CreateAnswersDict,
    KnowledgeBaseService,
    EmbendingNormalization,
    EmbendingEncoder,
    LoadKnowledgeBase,
    ResultSender,
    SaveAnswersCache,
    UUIDGenerator
)
from sentence_bert.src.config import BertConfig
from sentence_bert.src.domain.entities import (
    AnswerBaseDataDm, 
    AnswerDm,
    AnswersChunksDm, 
    AnswersDataDm,
    AnswersGetUuidDm, 
    EncodedAnswersDm, 
    ProcessQueryDm
)


class KnowledgeBaseGateway(
    KnowledgeBaseService,
    EmbendingNormalization,
    EmbendingEncoder,
    ResultSender
):
    def __init__(
        self, 
        model: T5EncoderModel,
        tokenizer: T5Tokenizer,
        config: BertConfig, 
        rabbitmq_broker: RabbitBroker,
        redis: Redis,
    ) -> None:
        self._model = model
        self._tokenizer = tokenizer
        self._query_instruction = config.query_instruction
        self._document_instruction = config.document_instruction
        self._broker = rabbitmq_broker
        self._redis = redis

    def l2_normalization(self, embeddings: torch.Tensor) -> torch.Tensor:
        return embeddings / embeddings.norm(dim=1, keepdim=True)

    def encode_knowledge_base(self, knowledge_base: AnswersDataDm) -> EncodedAnswersDm:
        encoded_knowledge_base = {}
        for key, doc in knowledge_base.answers.items():
            inputs = self._tokenizer(
                f"{self._document_instruction} {doc}",
                return_tensors="pt",
                padding=True,
                truncation=True
            )
            output: BaseModelOutput = self._model(**inputs)
            embedding = output.last_hidden_state.mean(dim=1)
            normalized_embedding = self.l2_normalization(embedding)
            encoded_knowledge_base[key] = normalized_embedding
        return EncodedAnswersDm(answers=encoded_knowledge_base)

    async def get_all_embeddings_scan(self) -> Optional[EncodedAnswersDm]:
        async with self._redis as redis:
            cursor = "0"
            embeddings = {}
            while cursor != "0":
                cursor, keys = await redis.scan(cursor=cursor, match="embedding:*", count=100)
                for key in keys:
                    key: str
                    data = await redis.get(key)
                    if data:
                        buffer = BytesIO(data)
                        embeddings[key.split(":")[1]] = torch.load(buffer)
            return EncodedAnswersDm(answers=embeddings) if embeddings else None

    async def process_query(self, params: ProcessQueryDm) -> str:
        inputs = self._tokenizer(
            f"{self._query_instruction} {params.query}",
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        output: BaseModelOutput = self._model(**inputs)
        query_embedding = output.last_hidden_state.mean(dim=1)
        query_embedding = params.normalization(query_embedding)
        similarities = {
            key: cosine_similarity(query_embedding, embedding).item()
            for key, embedding in params.knowledge_base_embeddings.items()
        }
        return max(similarities, key=similarities.get)

    async def send_answer(self, params: AnswerDm) -> None:
        async with self._broker as broker:
            await broker.publish(
                RabbitMessage(
                    body={
                        "user_id": params.user_id,
                        "answer": params.answer,
                    }
                ),
                exchange="custom_model",
                routing_key="send_answer",
                correlation_id=params.correlation_id
            )


class KnowledgeBasePrepareGateway(
    LoadKnowledgeBase,
    CreateAnswersDict,
    AnswerPaginator,
    SaveAnswersCache
):
    def __init__(
        self, 
        redis: Redis,
        config: BertConfig,
        uuid_generator: UUIDGenerator,
    ) -> None:
        self._redis = redis
        self._config = config 
        self._uuid_generator = uuid_generator

    def from_csv(self, delimiter: str = "~") -> AnswerBaseDataDm:
        answers_list = []
        with open(
            file=self._config.base_path, 
            mode="r", 
            encoding="utf-8"
        ) as file:
            reader = csv.reader(file, delimiter=delimiter)
            for row in reader:
                if len(row) == 2:
                    _, answer = row
                    answers_list.append(answer.strip())
        return AnswerBaseDataDm(answers=answers_list)

    async def paginate_answer(self, text: str) -> AnswersChunksDm:
        min_length = 2048
        max_length = 4096
        chunks = []
        i = 0
        while i < len(text):
            chunk_size = max_length if (len(text) - i) > max_length \
                else min(max_length, len(text) - i)
            chunks.append(text[i:i + chunk_size])
            i += chunk_size
        if len(chunks[-1]) < min_length:
            last_chunk = chunks.pop()
            total_length = sum(len(chunk) for chunk in chunks) + len(last_chunk)
            avg_length = total_length // len(chunks)
            redistributed_chunks = []
            start = 0
            for _ in range(len(chunks)):
                redistributed_chunks.append(text[start:start + avg_length])
                start += avg_length
            redistributed_chunks.append(text[start:])
            return AnswersChunksDm(chunks=redistributed_chunks)
        return AnswersChunksDm(chunks=chunks)

    def create_answers_data(self, answers: AnswersGetUuidDm) -> AnswersDataDm:
        answers_dict = {}
        answers_embending_dict = {}
        for answer, answer_embending in zip(answers.chunks, answers.embendings):
            uuid = self._uuid_generator()
            answers_dict[uuid] = answer
            answers_embending_dict[uuid] = answer_embending
        return AnswersDataDm(
            answers=answers_dict,
            answers_embendings=answers_embending_dict
        )

    async def save_answers(self, params: AnswersDataDm) -> None:
        async with self._redis as redis:
            for uuid, answer_list in params.answers.items():
                serialized_data = json.dumps(answer_list)
                await redis.set(f"answer:{uuid}", serialized_data)
            for uuid, embedding in params.answers_embendings.items():
                buffer = BytesIO()
                torch.save(embedding, buffer)
                serialized_embedding = buffer.getvalue()
                await redis.set(f"embedding:{uuid}", serialized_embedding)
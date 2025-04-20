from typing import Optional
from sentence_bert.src.application.dto import QuestionHandlerDto
from sentence_bert.src.application.interfaces import (
    AnswerPaginator,
    CacheEmbendingsGetter,
    KnowledgeBaseService,
    LoadKnowledgeBase, 
    EmbendingNormalization,
    EmbendingEncoder,
    SaveAnswersCache,
    CreateAnswersDict,
    ResultSender,
)
from sentence_bert.src.domain.entities import (
    AnswerDm,
    AnswersDataDm, 
    AnswersGetUuidDm, 
    EncodedAnswersDm,
    ProcessQueryDm
)

class PrepareKnowledgeBaseInteractor:
    def __init__(
        self,
        base_loader: LoadKnowledgeBase,
        paginator: AnswerPaginator,
        encoder_gateway: EmbendingEncoder,
        enum_gateway: CreateAnswersDict,
        cache: SaveAnswersCache,
    ) -> None:
        self._paginator = paginator
        self._base_loader = base_loader
        self._encoder_gateway = encoder_gateway
        self._enum_gateway = enum_gateway
        self._cache = cache

    async def __call__(self) -> None:
        knowledge_base = self._base_loader.from_csv()
        answers_chunks = []
        for answer in knowledge_base:
            answers_chunks.append(await self._paginator.paginate_answer(answer))
        encoded_knowledge_base = self._encoder_gateway.encode_knowledge_base(knowledge_base)
        enum_dm_base = self._enum_gateway.create_answers_data(
            AnswersGetUuidDm(
                chunks=answers_chunks,
                embendings=encoded_knowledge_base
            )
        )
        await self._cache.save_answers(enum_dm_base)

class QuestionsHandlerInteractor:
    def __init__(
        self,
        emb_getter_gateway: CacheEmbendingsGetter,
        answer_gateway: KnowledgeBaseService,
        normalization_gateway: EmbendingNormalization,
        sender_gateway: ResultSender,
        knowledge_base_embendings: EncodedAnswersDm
    ) -> None:
        self._emb_getter_gateway = emb_getter_gateway
        self._answer_gateway = answer_gateway
        self._normalization_gateway = normalization_gateway
        self._sender_gateway = sender_gateway
        self._base = knowledge_base_embendings

    async def __call__(self, dto: QuestionHandlerDto) -> Optional[bool]:
        embendigs = await self._emb_getter_gateway.get_all_embeddings_scan()
        if not embendigs:
            return None
        answer = await self._answer_gateway.process_query(
            params=ProcessQueryDm(
                query=dto.question, 
                knowledge_base_embeddings=self._base, 
                normalization=self._normalization_gateway.l2_normalization
            )
        )
        await self._sender_gateway.send_answer(
            AnswerDm(
                user_id=dto.user_id,
                answer=answer,
                correlation_id=dto.correlation_id
            )
        )
        return True
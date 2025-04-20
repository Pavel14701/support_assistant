from typing import AsyncIterable
from uuid import uuid4

from dishka import Provider, Scope, provide, AnyOf, from_context
from redis.asyncio import Redis
from faststream.rabbit import RabbitBroker

from sentence_bert.src.application import interfaces
from sentence_bert.src.application.interactors import (
    QuestionsHandlerInteractor,
    PrepareKnowledgeBaseInteractor
)
from sentence_bert.src.config import Config
from sentence_bert.src.infrastructure.gateways import (
    KnowledgeBaseGateway,
    KnowledgeBasePrepareGateway
)
from sentence_bert.src.infrastructure.broker import new_broker
from sentence_bert.src.infrastructure.cache import init_redis


class AppProvider(Provider):
    config = from_context(provides=Config, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_uuid_generator(self) -> interfaces.UUIDGenerator:
        return uuid4

    @provide(scope=Scope.APP)
    async def get_redis(self, config: Config) -> AsyncIterable[Redis]:
        redis = init_redis(config.redis)
        try:
            yield redis
        finally:
            await redis.aclose()

    @provide(scope=Scope.APP)
    def get_broker(self, config: Config) -> RabbitBroker:
        return new_broker(config.rabbitmq)

    prepare_gateway = provide(
        KnowledgeBasePrepareGateway,
        scope=Scope.REQUEST,
        provides=AnyOf[
            interfaces.LoadKnowledgeBase,
            interfaces.CreateAnswersDict,
            interfaces.AnswerPaginator,
            interfaces.SaveAnswersCache
        ]
    )

    question_handler_gateway = provide(
        KnowledgeBaseGateway,
        scope=Scope.REQUEST,
        provides=AnyOf[
            interfaces.KnowledgeBaseService,
            interfaces.EmbendingNormalization,
            interfaces.EmbendingEncoder,
            interfaces.ResultSender,
            interfaces.CacheEmbendingsGetter
        ]
    )

    base_prepare_interactor = provide(PrepareKnowledgeBaseInteractor, scope=Scope.REQUEST)
    question_handler_interactor = provide(QuestionsHandlerInteractor, scope=Scope.REQUEST)
from redis.asyncio import Redis

from bot.src.application.interfaces import AnswersGetter, AnswersHandler, Start, UUIDGenerator
from bot.src.controllers.bot_states import UserStates
from bot.src.domain.entities import QuestionHandlerDm, StartDm
from src.application.dto import PaginateAnswerDto, QuestionHandlerDto, StartDto
from  src.infrastructure.message_paginator import PaginatorGateway

class PaginationInteractor:
    def __init__(
        self, 
        redis: Redis,
        pagination_gateway: PaginatorGateway
    ) -> None:
        self._redis = redis
        self._pagination_gateway = pagination_gateway

    async def __call__(self, params: PaginateAnswerDto) -> str:
        pages = await self._pagination_gateway.paginate_text(params.answer)
        await self._redis.set(f"user:{params.user_id}:pages", "|".join(pages))
        await self._redis.set(f"user:{params.user_id}:current_page", 0)
        return pages[0]


class StartInteractor:
    def __init__(
        self,
        states: UserStates,
        start_gateway: Start
    ) -> None:
        self._states = states
        self._start_gateway = start_gateway

    async def __call__(self, params: StartDto) -> None:
        start_dm = StartDm(params.message, params.state, self._states.automatic_mode)
        await self._start_gateway.start(start_dm)


class CustomModelQueryHandler:
    def __init__(
        self, 
        uuid_gateway: UUIDGenerator,
        answers_handler_gateway: AnswersHandler,
        answers_getter_gateway: AnswersGetter,
    ) -> None:
        self._uuid_gateway = uuid_gateway
        self._answers_handler_gateway = answers_handler_gateway
        self._answers_getter_gateway = answers_getter_gateway

    async def __call__(self, params: QuestionHandlerDto) -> dict[str, str]:
        dm = QuestionHandlerDm(
            user_id=params.user_id,
            question=params.question,
            correlation_id=self._uuid_gateway()
        )
        try:
            response = await self._answers_handler_gateway.send_and_receive(dm)
            await self._answers_getter_gateway.get_saved_answers(response.answer_uuid)
        except Exception as e:
            return {"status": "error", "message": str(e)}

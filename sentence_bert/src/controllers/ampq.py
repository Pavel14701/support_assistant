import json

from dishka.integrations.base import FromDishka as Depends
from faststream.rabbit import RabbitRouter, RabbitMessage

from sentence_bert.src.application.dto import QuestionHandlerDto
from sentence_bert.src.application.interactors import (
    QuestionsHandlerInteractor,
    PrepareKnowledgeBaseInteractor
)


TasksController=RabbitRouter()


@TasksController.subscri1ber("question_handler")
async def question_handler(
    message: RabbitMessage,
    prepare_interactor: Depends[PrepareKnowledgeBaseInteractor],
    handler_interactor: Depends[QuestionsHandlerInteractor]
) -> None:
    data: dict[str|int, str] = json.loads(message.body.decode()) 
    dto=QuestionHandlerDto(
        user_id=data.get("user_id"),
        question=data.get("question"),
        correlation_id=message.correlation_id
    )
    status = await handler_interactor(dto)
    if not status:
        await prepare_interactor()
        await handler_interactor(dto)
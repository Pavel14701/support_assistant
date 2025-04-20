import asyncio
from typing import Optional

from aiogram import Router, Bot
from aiogram.types import (
    Message, 
    CallbackQuery,
    User,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from redis.asyncio import Redis
from dishka.integrations.aiogram import FromDishka as Depends, inject
from faststream.rabbit import RabbitRouter

from bot.src.application.dto import QuestionHandlerDto, StartDto
from bot.src.application.interactors import CustomModelQueryHandler, StartInteractor
from bot.src.controllers.filters import CustomFilter
from bot.src.controllers.bot_states import UserStates
from bot.src.controllers.keyboards import get_keyboard, get_pagination_keyboard

AnswersController = RabbitRouter()
router = Router()

class BotRouters:
    def __init__(
        self, 
        future: asyncio.Future
    ) -> None:
        self._future = future

    @router.message(Command("start"))
    @inject
    async def start_handler(
        self,
        message: Message,
        state: FSMContext,
        interactor: Depends[StartInteractor]
    ) -> None:
        params = StartDto(message, state)
        await interactor(params)

    @router.message(UserStates.automatic_mode)
    @inject
    async def handle_automatic_mode(
        self,
        message: Message,
        user: Depends[User],
        custom_model_interactor: Depends[CustomModelQueryHandler],
        api_interactor: Depends[],
    ) -> None:
        dto = QuestionHandlerDto(
            user_id=user.id,
            question=message.text 
        )
        answer = await custom_model_interactor()
        if not answer:
            answer = await api_interactor(dto)

    @router.callback_query(CustomFilter(pattern="manual_mode"))
    @inject
    async def manual_mode_callback(callback: CallbackQuery, state: FSMContext):
        await state.set_state(UserStates.manual_mode)
        await callback.message.edit_text(
            "Теперь вы в режиме обращения к технической поддержке. "
            "Пожалуйста, напишите ваш вопрос, и техническая поддержка ответит вам."
        )
        await callback.answer()


    @router.callback_query(CustomFilter(pattern="automatic_mode"))
    @inject
    async def automatic_mode_callback(callback: CallbackQuery, state: FSMContext):
        await state.set_state(UserStates.automatic_mode)
        await callback.message.edit_text(
            "Отлично, рады что смогли помочь. У вас остались ещё вопросы?"
            "Пожалуйста, напишите ваш вопрос, и бот вам ответит"
        )
        await callback.answer()


    @router.callback_query(CustomFilter(startwith="page_"))
    @inject
    async def pagination_handler(
        callback: CallbackQuery, 
        user: Depends[User],
        redis: Depends[Redis]
    ) -> None:
        user_id = user.id
        current_page = int(callback.data.split("_")[1])
        pages_data: Optional[bytes] = await redis.get(f"user:{user_id}:pages")
        if not pages_data:
            await callback.answer("Ошибка: страницы не найдены.", show_alert=True)
            return
        pages = pages_data.decode("utf-8").split("|")
        if current_page < 0 or current_page >= len(pages):
            await callback.answer("Ошибка: неверный номер страницы.", show_alert=True)
            return
        await redis.set(f"user:{user_id}:current_page", current_page)
        await callback.message.edit_text(
            text=pages[current_page],
            reply_markup=get_pagination_keyboard(current_page=current_page, total_pages=len(pages))
        )
        await callback.answer()

    @router.message()
    @inject
    async def forward_message_to_group(
        message: Message, 
        state: FSMContext, 
        bot: Bot,
        interactor: Depends[]
    ) -> None:
        current_state = await state.get_state()
        if current_state == "UserStates:manual_mode":
            try:
                forwarded_message = await bot.forward_message(chat_id=GROUP_CHAT_ID, from_chat_id=message.chat.id, message_id=message.message_id)
                
                # Сохраняем связь между сообщением в группе и пользователем в Redis
                redis_client.set(f"group_message:{forwarded_message.message_id}", message.from_user.id)
            except Exception as e:
                await message.reply(f"Ошибка при пересылке сообщения: {e}")


    @router.message()
    @inject
    async def reply_to_user(
        self, 
        message: Message, 
        bot: Bot,
        interactor: Depends[]
    ) -> None:
        pass







from faststream.rabbit import RabbitBroker, RabbitMessage, RabbitRouter
from faststream import FastAPI
import asyncio
from redis.asyncio import Redis
from typing import TypedDict

class ResponseMessage(TypedDict):
    user_id: int
    answer: str


# Инициализация RabbitMQ и Redis
broker = RabbitBroker()
controller = RabbitRouter()
redis = Redis.from_url("redis://localhost")

# Включаем маршрутизатор в брокер
broker.include_router(controller)

# FastAPI приложение
app = FastAPI(lifespan=broker.lifespan)

# Future для ожидания ответа с нужным correlation_id
response_futures: dict[str|int, asyncio.Future] = {}

# Подписчик на очередь для ответов
@controller.subscriber("send_answer")
async def handle_response(message: RabbitMessage):
    correlation_id = message.correlation_id
    if correlation_id and correlation_id in response_futures:
        # Устанавливаем результат для Future
        response_futures[correlation_id].set_result(message.body)
        del response_futures[correlation_id]  # Удаляем Future после обработки

# Функция отправки запроса, сохранения в кэш, и ожидания ссылки
async def send_and_receive(user_id: int, question: str, timeout: int = 10) -> ResponseMessage:
    correlation_id = str(user_id)

    # Сохраняем вопрос в кэш Redis
    cache_key = f"user_question:{user_id}"
    await redis.set(cache_key, question)

    # Создаём Future для ожидания ответа
    future = asyncio.Future()
    response_futures[correlation_id] = future

    # Публикуем сообщение в очередь
    await broker.publish(
        {
            "user_id": user_id,
            "question": cache_key  # Отправляем ключ кэша вместо полного текста вопроса
        },
        routing_key="question_handler",
        correlation_id=correlation_id
    )

    # Ожидаем результат с таймаутом
    try:
        response = await asyncio.wait_for(future, timeout=timeout)
        return response
    except asyncio.TimeoutError:
        raise Exception("Ответ из очереди не получен в течение указанного времени")

# Обработчик API для приёма запросов от пользователя
@app.post("/automatic_mode")
async def handle_automatic_mode(user_id: int, question: str):
    try:
        response = await send_and_receive(user_id, question)
        return {"status": "success", "cache_key": response.get("answer", "Ссылка на кэш отсутствует")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


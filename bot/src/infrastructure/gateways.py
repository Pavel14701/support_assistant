import asyncio
from typing import Optional
import json
import uuid


from aiogram import Bot
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message
)
from g4f.client import AsyncClient
from g4f.Provider import BaseProvider
from redis.asyncio import Redis
from faststream.rabbit import (
    RabbitMessage, 
    RabbitRouter, 
    RabbitBroker
)

from bot.src.application.interfaces import AnswersGetter, ApiProvider, MessagePaginator
from bot.src.config import BotConfig
from bot.src.domain.entities import ApiRequest, MessagePaginatorDm, QuestionHandlerDm, ResponseMessage, SendAnswerDm, SendMessageGroupDm, StartDm

controller = RabbitRouter()

class ApiProviderGateway(ApiProvider):
    response_futures: dict[str|int, asyncio.Future] = {}

    def __init__(
        self, 
        provider: BaseProvider,
        broker: RabbitBroker,
        redis: Redis
    ) -> None:
        self._provider = provider
        self._broker = broker
        self._redis = redis

    async def main(self, message: ApiRequest) -> str:
        try:
            response = await AsyncClient().chat.completions.create(
                provider = self._provider,
                messages=[message.to_dict()]
            )
            message = response.choices[0].message or None
            if message is not None:
                print(message.content)
                return message.content
            return "Error, response not created, please try again"
        except Exception as e:
            print(f"Error {e}")
            return "Error, response not created, please try again"

    @controller.subscriber("send_answer")
    async def handle_response(self, message: RabbitMessage) -> None:
        correlation_id = message.correlation_id
        if correlation_id and correlation_id in self.response_futures:
            self.response_futures[correlation_id].set_result(message.body)
            del self.response_futures[correlation_id]


    async def send_and_receive(self, params: QuestionHandlerDm) -> ResponseMessage:
        future = asyncio.Future()
        self.response_futures[params.correlation_id] = future
        await self._broker.publish(
            {"user_id": params.user_id, "question": params.question},
            routing_key="question_handler",
            correlation_id=params.correlation_id
        )
        try:
            response = await asyncio.wait_for(future, timeout=params.timeout)
            data: ResponseMessage = json.loads(response)
            await self._redis.set(f"user_answer:{params.user_id}:", data.answer_uuid)
            return response
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка десериализации: {e}")
        except asyncio.TimeoutError:
            raise Exception("Ответ из очереди не получен в течение указанного времени")


class BotGateways(
    MessagePaginator,
    AnswersGetter,
):
    def __init__(
        self,
        bot: Bot,
        redis: Redis,
        config: BotConfig
    ) -> None:
        self._bot = bot
        self._redis = redis
        self._config = config

    async def start(self, params: StartDm) -> None:
        await params.state.set_state(params.current_state)
        await params.message.reply(
            text="Добро пожаловать! Используйте кнопку ниже, чтобы задать вопрос техподдержке:",
            reply_markup=self.get_manual_keyboard()
        )

    async def get_saved_answers(self, uuid: str) -> Optional[list[str]]:
        async with self._redis as redis:
            serialized_data = await redis.get(f"answer:{uuid}")
            if not serialized_data:
                return None
            return json.loads(serialized_data)

    async def send_answer(self, params: SendAnswerDm) -> None:
        await params.message.reply(
                text=
                    f"{params.message}"
                    "Используйте кнопку ниже, чтобы задать вопрос техподдержке:",
                reply_markup=self.get_manual_keyboard()
            )

    async def get_current_answer(self, user_id: int|str) -> str:
        response = await self._redis.get(f"user_answer:{user_id}:")
        return json.loads(response)

    async def paginate_message(self, params: MessagePaginatorDm) -> None:
        current_page = int(params.callback.data.split("_")[1])
        if not params.pages:
            await params.callback.answer("Ошибка: данные не найдены.", show_alert=True)
            return
        if len(params.pages) == 1:
            await params.callback.message.edit_text(text=params.pages[0])
            await params.callback.answer()
            return
        if current_page < 0 or current_page >= len(params.pages):
            await params.callback.answer("Ошибка: неверный номер страницы.", show_alert=True)
            return
        await self._redis.set(f"user:{params.user.id}:current_page", current_page)
        await params.callback.message.edit_text(
            text=params.pages[current_page],
            reply_markup=self.get_pagination_keyboard(
                current_page=current_page,
                total_pages=len(params.pages)
            )
        )
        await params.callback.answer()

    def get_pagination_keyboard(self, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
        buttons = []
        if current_page > 0:
            buttons.append(
                InlineKeyboardButton(
                    text="⬅ Назад",
                    callback_data=f"page_{current_page - 1}"
                )
            )
        if current_page < total_pages - 1:
            buttons.append(
                InlineKeyboardButton(
                    text="Вперед ➡", 
                    callback_data=f"page_{current_page + 1}"
                )
            )
        buttons.append(
            InlineKeyboardButton(
                text="Задать вопрос техподдержке", 
                callback_data="manual_mode")
            )
        return InlineKeyboardMarkup(inline_keyboard=[buttons])

    async def paginate_text(self, text: str) -> list[str]:
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
            return redistributed_chunks
        return chunks

    def get_manual_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Задать вопрос техподдержке", 
                        callback_data="manual_mode")
                ]
            ]
        )

    async def forward_message_to_group(self, params: SendMessageGroupDm) -> None:
        current_state = await params.state.get_state()
        if current_state == "UserStates:manual_mode":
            try:
                forwarded_message = await self._bot.forward_message(
                    chat_id=self._config.group_id, 
                    from_chat_id=params.message.chat.id, 
                    message_id=params.message.message_id
                )
                self._redis.set(f"group_message:{forwarded_message.message_id}", params.message.from_user.id)
            except Exception as e:
                await params.message.reply(f"Ошибка при пересылке сообщения: {e}")

    async def reply_to_user(self, message: Message) -> None:
        if message.reply_to_message:
            user_id = self._redis.get(f"group_message:{message.reply_to_message.message_id}")
            if user_id:
                user_id = int(user_id)
                sender = message.from_user
                try:
                    chat_member = await self._bot.get_chat_member(chat_id=message.chat.id, user_id=sender.id)
                    is_admin = chat_member.status in ["administrator", "creator"]
                    if sender.id in self._config.allowed_users or is_admin:
                        await self._bot.send_message(chat_id=user_id, text=message.text)
                    else:
                        await message.reply("У вас недостаточно прав для ответа пользователю.")
                except Exception as e:
                    await message.reply(f"Произошла ошибка: {e}")
            else:
                await message.reply("Ошибка: пользователь не найден.")

    def get_auto_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Спасибо, всё понятно", 
                        callback_data="manual_mode")
                ]
            ]
        )
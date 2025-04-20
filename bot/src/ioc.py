from collections.abc import AsyncIterator

from aiogram import Bot
from aiogram.types import Chat, TelegramObject, User
from dishka import Provider, Scope, provide, from_context
from dishka.integrations.aiogram import AiogramMiddlewareData

from bot.src.config import Config

class MyProvider(Provider):
    config = from_context(provides=Config, scope=Scope.APP)
    bot = from_context(provides=Bot, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    async def get_user(self, obj: TelegramObject) -> User:
        return obj.from_user

    @provide(scope=Scope.REQUEST)
    async def get_chat(self, middleware_data: AiogramMiddlewareData) -> Chat | None:
        return middleware_data.get("event_chat")

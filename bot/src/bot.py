import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.storage.redis import RedisStorage

from src.infrastructure.redis_storage import init_redis_storage
from controllers.bot_states import UserStates
from src.config import Config, BotConfig



config = Config()
storage = init_redis_storage(config)


async def main(config: BotConfig, storage: RedisStorage):
    storage = await init_redis_storage()
    bot = Bot(token=config.token, parse_mode=config.parse_mode)
    dp = Dispatcher(storage=storage)

    # Команда /start
    @dp.message(Command("start"))
    async def start_handler(message: types.Message, state: FSMContext):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Автоматический режим", "Ручной режим")
        await message.reply("Выберите режим работы:", reply_markup=keyboard)

    # Переход в автоматический режим
    @dp.message(lambda message: message.text == "Автоматический режим")
    async def automatic_mode_handler(message: types.Message, state: FSMContext):
        await message.reply("Бот в автоматическом режиме. Введите текст для обработки.")
        await state.set_state(UserStates.automatic_mode)

    # Переход в ручной режим
    @dp.message(lambda message: message.text == "Ручной режим")
    async def manual_mode_handler(message: types.Message, state: FSMContext):
        await message.reply("Бот в ручном режиме. Напишите ваш вопрос.")
        await state.set_state(UserStates.manual_mode)

    # Обработка сообщений в автоматическом режиме
    @dp.message(UserStates.automatic_mode)
    async def handle_automatic_mode(message: types.Message, state: FSMContext):
        # Обработка автоматического запроса
        response = f"Автоматически обработан ваш запрос: {message.text}"
        await message.reply(response)

    # Обработка сообщений в ручном режиме
    @dp.message(UserStates.manual_mode)
    async def handle_manual_mode(message: types.Message, state: FSMContext):
        # Обработка ручного запроса
        response = f"Вы ввели запрос вручную: {message.text}"
        await message.reply(response)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

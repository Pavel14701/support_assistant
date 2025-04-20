from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage

from bot.src.config import RedisConfig

async def init_redis(config: RedisConfig) -> Redis:
    return Redis(
        host=config.host, 
        port=config.port, 
        db=config.db,
        password=config.password
    )

async def init_redis_storage(config: RedisConfig) -> RedisStorage:
    return RedisStorage(redis=init_redis(config))
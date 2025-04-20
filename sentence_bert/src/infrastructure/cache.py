from redis.asyncio import Redis

from sentence_bert.src.config import RedisConfig

def init_redis(config: RedisConfig) -> Redis:
    return Redis(
        host=config.host, 
        port=config.port, 
        db=config.db,
        password=config.password
    )
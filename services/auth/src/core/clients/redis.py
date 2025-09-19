from redis.asyncio import Redis as AsyncRedis

from core.configs.redis import redis_settings

redis = AsyncRedis(
    host=redis_settings.HOST,
    port=redis_settings.PORT,
    db=redis_settings.DB,
    username=redis_settings.USERNAME,
    password=redis_settings.PASSWORD,
    ssl=redis_settings.SSL,
    decode_responses=True,
)

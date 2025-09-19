from shared.core.health import healthcheck
from sqlalchemy import text

from core.clients.redis import redis
from db.session import async_session_factory


@healthcheck("postgres")
async def check_postgres() -> None:
    """Check postgres connection."""
    async with async_session_factory() as session:
        await session.execute(text("SELECT 1"))


@healthcheck("redis")
async def check_redis() -> None:
    """Check redis connection."""
    await redis.ping()

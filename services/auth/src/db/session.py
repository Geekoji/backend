from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.configs.postgres import pg_settings

__all__ = [
    "async_session_factory",
    "Session",
]

async_engine = create_async_engine(
    url=pg_settings.ASYNC_DATABASE_URL,
    echo=pg_settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=pg_settings.POOL_SIZE,
    max_overflow=pg_settings.MAX_OVERFLOW,
    pool_timeout=pg_settings.POOL_TIMEOUT,
    pool_recycle=pg_settings.POOL_RECYCLE,
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)


async def _db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session with auto-commit and auto-rollback."""
    async with async_session_factory() as async_session:
        async with async_session.begin():
            yield async_session


Session = Annotated[AsyncSession, Depends(_db_session)]

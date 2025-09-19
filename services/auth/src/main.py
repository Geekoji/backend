from logging.config import dictConfig

from asyncpg import PostgresError
from authlib.integrations.base_client import OAuthError
from authlib.jose import JoseError
from fastapi import FastAPI
from shared.core.exceptions import db_exception_handler
from shared.middlewares import InternalOnlyMiddleware, PrometheusMiddleware, RateLimiterMiddleware
from shared.security import setup_docs
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware

from api.routers import router
from core.clients.redis import redis
from core.configs.base import settings
from core.exceptions import auth_exception_handler
from core.logs.config import logging_settings

dictConfig(dict(logging_settings))

app = FastAPI(
    title=settings.SERVICE_TITLE,
    version=settings.API_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    root_path="/auth",
)
setup_docs(app)

# Routers
app.include_router(router)

# Middleware
app.add_middleware(RateLimiterMiddleware, redis_client=redis)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(InternalOnlyMiddleware)
app.add_middleware(PrometheusMiddleware)

# Exception handlers
app.add_exception_handler(JoseError, auth_exception_handler)
app.add_exception_handler(OAuthError, auth_exception_handler)

app.add_exception_handler(PostgresError, db_exception_handler)
app.add_exception_handler(SQLAlchemyError, db_exception_handler)
app.add_exception_handler(TimeoutError, db_exception_handler)

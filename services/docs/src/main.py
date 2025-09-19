from fastapi import FastAPI
from httpx import HTTPError

from api.docs import router
from core.exceptions import http_error_handler

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(router)
app.add_exception_handler(HTTPError, http_error_handler)

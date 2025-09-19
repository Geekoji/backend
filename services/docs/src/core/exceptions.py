from fastapi import Request, status
from fastapi.responses import JSONResponse

__all__ = [
    "http_error_handler",
]


def http_error_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )

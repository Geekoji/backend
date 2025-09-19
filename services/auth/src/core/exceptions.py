from logging import getLogger

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from enums import OAuth2ProviderEnum, TokenTypeEnum

__all__ = [
    "auth_exception_handler",
    "InvalidCredentials",
    "InvalidProviderForPlatform",
    "InvalidState",
    "MissingCodeVerifier",
    "MissingNonce",
    "AccountAlreadyExists",
    "OAuth2AccountExists",
    "InvalidToken",
    "TokenRevoked",
    "TokenRequired",
]

logger = getLogger("uvicorn.error")


def auth_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handle Auth exceptions and return JSONResponse."""
    status_code, detail = status.HTTP_401_UNAUTHORIZED, exc.description  # type: ignore[attr-defined]
    return JSONResponse(content={"detail": detail or "Unauthorized"}, status_code=status_code)


class InvalidCredentials(HTTPException):

    def __init__(self, detail: str = "Invalid credentials.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class InvalidProviderForPlatform(HTTPException):

    def __init__(self, detail: str = "Invalid provider for current platform.") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class InvalidState(HTTPException):

    def __init__(self, detail: str = "Invalid state.") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class MissingCodeVerifier(HTTPException):

    def __init__(self, detail: str = "Missing code verifier.") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class MissingNonce(HTTPException):

    def __init__(self, detail: str = "Missing nonce.") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class AccountAlreadyExists(HTTPException):

    def __init__(self, detail: str = "Client with this account already exists.") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class OAuth2AccountExists(HTTPException):

    def __init__(self, provider: OAuth2ProviderEnum) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid credentials. Please try logging with {provider.title()} account.",
        )


class InvalidToken(HTTPException):

    def __init__(self, detail: str = "Invalid token.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class TokenRevoked(HTTPException):

    def __init__(self, detail: str = "Refresh token revoked.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class TokenRequired(HTTPException):

    def __init__(self, token_type: TokenTypeEnum) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{token_type.title()} token required.",
        )

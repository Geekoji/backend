from datetime import datetime, timedelta, timezone
from functools import lru_cache
from time import time
from typing import Annotated
from uuid import uuid4

from authlib.jose import JsonWebKey, JsonWebToken, JWTClaims
from fastapi import Depends, Request

from core.clients.redis import redis
from core.configs.jwt import jwt_settings
from core.exceptions import InvalidToken, TokenRequired, TokenRevoked
from enums import TokenTypeEnum
from models import Account
from schemas import JWKS, AccessToken, TokenPair

__all__ = [
    "RefreshRequire",
    "TokenFactory",
]


class _TokenFactory:
    """Token factory for creating and validating tokens."""

    JWT = JsonWebToken(jwt_settings.ALGORITHM)
    ISSUER = jwt_settings.ISSUER

    PRIVATE_KEYS = jwt_settings.PRIVATE_KEYS
    PUBLIC_KEYS = jwt_settings.PUBLIC_KEYS
    SIGNING_KID = jwt_settings.SIGNING_KID

    ALGORITHM = jwt_settings.ALGORITHM
    ACCESS_EXPIRES = jwt_settings.access_token_expires
    REFRESH_EXPIRES = jwt_settings.refresh_token_expires

    BLACKLIST_ENABLED = jwt_settings.BLACKLIST_ENABLED
    BLACKLIST_PREFIX = jwt_settings.BLACKLIST_PREFIX

    __slots__ = (
        "_now",
        "_request",
        "_payload",
    )

    def __init__(self, request: Request) -> None:
        """Initialize token factory."""
        self._now = datetime.now(timezone.utc)
        self._payload = JWTClaims(payload={}, header={})
        self._request = request

    @property
    def payload(self) -> JWTClaims:
        """Get payload of token."""
        return self._payload

    @property
    def jwks(self) -> JWKS:
        return self.get_jwks()

    @classmethod
    def signing_kid(cls, value: int | None = None) -> str:
        return f"auth-key-{cls.SIGNING_KID if value is None else value}"

    @classmethod
    @lru_cache(maxsize=1)
    def get_jwks(cls) -> JWKS:
        """Get JSON web key set."""
        options = {"alg": cls.ALGORITHM, "use": "sig"}

        keys = [
            JsonWebKey.import_key(public_key, options).tokens  # type: ignore[arg-type]
            for idx, public_key in enumerate(cls.PUBLIC_KEYS)
            if options.update({"kid": cls.signing_kid(idx)}) is None
        ]
        return JWKS(keys=keys)

    def create_token(self, subject: str, token_type: TokenTypeEnum) -> str:
        """Create a token from a subject and token type."""
        expires_delta = getattr(self, f"{token_type.name}_EXPIRES")

        header = {
            "alg": self.ALGORITHM,
            "kid": self.signing_kid(),
            "typ": "JWT",
        }
        payload = {
            "exp": self._now + expires_delta,
            "iat": self._now,
            "iss": self.ISSUER,
            "jti": str(uuid4()),
            "nbf": self._now,
            "sub": subject,
            "type": token_type,
        }
        token: str = self.JWT.encode(
            header=header,
            payload=payload,
            key=self.PRIVATE_KEYS[self.SIGNING_KID],
        )
        return token

    def access_token(self, subject: str) -> str:
        """Create an access token from a subject."""
        return self.create_token(subject, TokenTypeEnum.ACCESS)

    def refresh_token(self, subject: str) -> str:
        """Create a refresh token from a subject."""
        return self.create_token(subject, TokenTypeEnum.REFRESH)

    async def create_access_token_from_refresh(self) -> AccessToken | TokenPair:
        """
        Create an access token from refresh token.
        If the refresh token closes to be expired, create a new pair.
        """
        if not self.payload:
            await self.token_required(TokenTypeEnum.REFRESH)

        subject, exp = self.payload["sub"], self.payload["exp"]
        signin_changed = self.payload.header["kid"] != self.signing_kid()

        if timedelta(seconds=int(exp) - int(time())) < timedelta(days=3) or signin_changed:
            await self.blacklist_token()
            return self.create_pair(subject)

        return AccessToken(access_token=self.access_token(subject))

    def create_pair(self, account: Account | str) -> TokenPair:
        """Create a token pair from a client account."""
        subject = str(account.id) if isinstance(account, Account) else account

        return TokenPair(
            access_token=self.access_token(subject),
            refresh_token=self.refresh_token(subject),
        )

    async def blacklist_token(self) -> None:
        """Blacklist refresh token."""
        if not self.payload:
            await self.token_required(TokenTypeEnum.REFRESH)

        jti = self.payload["jti"]
        ttl = int(self.payload["exp"]) - int(time())

        await redis.setex(f"{self.BLACKLIST_PREFIX}:{jti}", ttl, 1)

    def get_token_from_header(self) -> str | None:
        """Get token from header."""
        header = self._request.headers.get("Authorization")

        if not header or "Bearer" not in header:
            return None

        return header.split("Bearer ")[1]

    def get_token_from_cookie(self, token_type: TokenTypeEnum) -> str | None:
        """Get token from cookie."""
        return self._request.cookies.get(f"{token_type}_token")

    def get_token(self, token_type: TokenTypeEnum) -> str | None:
        """Get token from cookie or header."""
        cookie_token = self.get_token_from_cookie(token_type)
        header_token = self.get_token_from_header()
        return cookie_token or header_token

    def decode_token(self, token: str) -> JWTClaims:
        """Decode the token and check if it is valid."""
        try:
            key = self.jwks.model_dump()["keys"]
            claims = self.JWT.decode(token, key)
        except ValueError as exc:
            raise InvalidToken(exc.args[0])

        claims.validate()
        return claims

    async def token_required(self, token_type: TokenTypeEnum) -> None:
        """Check if the token is valid."""
        if not (token := self.get_token(token_type)):
            raise TokenRequired(token_type)

        self._payload = self.decode_token(token)

        if self.payload.get("type") != token_type:
            raise TokenRequired(token_type)

        if token_type is TokenTypeEnum.REFRESH and await self.is_token_revoked():
            raise TokenRevoked()

    async def is_token_revoked(self) -> bool:
        """Check if the token is revoked."""
        if not self.BLACKLIST_ENABLED:
            return False

        jti = self.payload["jti"]
        key = f"{self.BLACKLIST_PREFIX}:{jti}"

        return bool(await redis.exists(key))


async def _require_refresh(factory: "TokenFactory") -> "TokenFactory":
    """Check if the token is valid."""
    await factory.token_required(TokenTypeEnum.REFRESH)
    return factory


TokenFactory = Annotated[_TokenFactory, Depends(_TokenFactory)]
RefreshRequire = Annotated[TokenFactory, Depends(_require_refresh)]

from pydantic import BaseModel

__all__ = [
    "AccessToken",
    "TokenPair",
    "JWK",
    "JWKS",
]


class _Token(BaseModel):
    type: str = "bearer"  # noqa: VNE003


class AccessToken(_Token):
    access_token: str


class TokenPair(AccessToken):
    refresh_token: str


class JWK(BaseModel):
    alg: str
    e: str  # noqa: VNE001
    kid: str
    kty: str
    n: str  # noqa: VNE001
    use: str


class JWKS(BaseModel):
    keys: list[JWK]

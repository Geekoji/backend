from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from fastapi import Request
from redis.asyncio import Redis

from services.token import _TokenFactory  # noqa


@pytest.fixture(scope="session")
def mock_redis() -> AsyncMock:
    redis_mock = AsyncMock(spec=Redis)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.setex = AsyncMock()
    return redis_mock


@pytest.fixture(scope="session")
def mock_request() -> MagicMock:
    request = MagicMock(spec=Request)
    return request


@pytest.fixture(scope="session")
def rsa_key_pair() -> tuple[str, str]:
    """Generates a new RSA key pair for testing."""
    private_key = generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )

    return private_pem, public_pem


@pytest.fixture
def token_factory(mock_request: MagicMock, rsa_key_pair: tuple[str, str]) -> Generator[_TokenFactory, Any, None]:
    private_pem, public_pem = rsa_key_pair

    with (
        patch.object(_TokenFactory, "PRIVATE_KEYS", [private_pem]),
        patch.object(_TokenFactory, "PUBLIC_KEYS", [public_pem]),
        patch.object(_TokenFactory, "SIGNING_KID", 0),
    ):
        yield _TokenFactory(request=mock_request)
        _TokenFactory.get_jwks.cache_clear()

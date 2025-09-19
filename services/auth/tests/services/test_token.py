from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from time import time
from typing import Any
from unittest.mock import AsyncMock

import pytest
from authlib.jose import JWTClaims
from pytest_mock import MockerFixture

from core.exceptions import InvalidToken, TokenRequired, TokenRevoked
from enums import TokenTypeEnum
from models import Account
from schemas import AccessToken, TokenPair
from services.token import _require_refresh, _TokenFactory  # noqa


@pytest.mark.unit
class TestTokenFactory:
    @pytest.fixture(autouse=True)
    def setup(self, token_factory: Any, mock_redis: AsyncMock) -> None:
        self.factory = token_factory
        self.redis = mock_redis

        self.subject = "test_user_id"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "token_type, old_token_with_expired_kid",
        [
            (TokenTypeEnum.ACCESS, False),
            (TokenTypeEnum.REFRESH, False),
            (TokenTypeEnum.ACCESS, True),
            (TokenTypeEnum.REFRESH, True),
        ],
    )
    async def test_create_and_decode_token(
        self,
        mocker: MockerFixture,
        token_type: TokenTypeEnum,
        old_token_with_expired_kid: bool,
    ) -> None:
        # Create token
        token = self.factory.create_token(self.subject, token_type)

        if old_token_with_expired_kid:
            # Imitate action for old token with not actual key id in system
            # It will raise exception in this case if we try to decode token
            mocker.patch.object(_TokenFactory, "signing_kid", return_value="auth-key-1")

        # Decode token
        with pytest.raises(InvalidToken) if old_token_with_expired_kid else nullcontext():
            self.factory.decode_token(token)

    @pytest.mark.parametrize("token_type", [TokenTypeEnum.ACCESS, TokenTypeEnum.REFRESH])
    def test_access_and_refresh_token_create(self, mocker: MockerFixture, token_type: TokenTypeEnum) -> None:
        create_token_mock = mocker.patch.object(_TokenFactory, "create_token", return_value="test_token")
        result = getattr(self.factory, f"{token_type}_token")(self.subject)
        create_token_mock.assert_called_once_with(self.subject, token_type)

        assert result == "test_token"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "payload_exists, refresh_will_expire",
        [
            (True, False),
            (False, True),
            (True, True),
            (False, False),
        ],
    )
    async def test_create_access_token_from_refresh(
        self,
        mocker: MockerFixture,
        payload_exists: bool,
        refresh_will_expire: bool,
    ) -> None:
        now = datetime.now(timezone.utc)
        expires_delta = timedelta(days=3) if refresh_will_expire else timedelta(days=4)
        payload = JWTClaims(
            payload={
                "sub": self.subject,
                "exp": (now + expires_delta).timestamp() - 1,
                "type": TokenTypeEnum.REFRESH,
            },
            header={
                "kid": "auth-key-0",
            },
        )

        access_token_mock = mocker.patch.object(
            _TokenFactory,
            "access_token",
            return_value="test_access_token",
        )
        blacklist_token_mock = mocker.patch.object(_TokenFactory, "blacklist_token")
        create_pair_mock = mocker.patch.object(_TokenFactory, "create_pair")

        async def fake_token_required(_: Any) -> None:
            self.factory._payload = payload
            return None

        token_required_mock = mocker.patch.object(
            _TokenFactory,
            "token_required",
            side_effect=fake_token_required,
        )

        if payload_exists:
            self.factory._payload = payload

        result = await self.factory.create_access_token_from_refresh()

        if payload_exists:
            token_required_mock.assert_not_called()
        else:
            token_required_mock.assert_called_once_with(TokenTypeEnum.REFRESH)

        if refresh_will_expire:
            blacklist_token_mock.assert_called_once_with()
            create_pair_mock.assert_called_once_with(self.subject)
            access_token_mock.assert_not_called()
        else:
            blacklist_token_mock.assert_not_called()
            create_pair_mock.assert_not_called()
            access_token_mock.assert_called_once_with(self.subject)
            assert isinstance(result, AccessToken)

    @pytest.mark.parametrize("account_type", [Account, "some account"])
    def test_create_pair_with_account_and_str(
        self,
        mocker: MockerFixture,
        account_type: Account | str,
    ) -> None:
        mocker.patch.object(_TokenFactory, "access_token", return_value="test_access_token")
        mocker.patch.object(_TokenFactory, "refresh_token", return_value="test_refresh_token")
        result = self.factory.create_pair(account_type)
        assert isinstance(result, TokenPair)

    @pytest.mark.parametrize(
        "auth_header, expected",
        [
            (None, None),
            ("", None),
            ("Token test_token", None),
            ("Bearer test_token", "test_token"),
        ],
    )
    def test_get_token_from_header(
        self,
        mocker: MockerFixture,
        auth_header: str | None,
        expected: str | None,
    ) -> None:
        headers_mock = mocker.MagicMock()
        headers_mock.get.return_value = auth_header
        mocker.patch.object(self.factory._request, "headers", headers_mock, create=True)

        result = self.factory.get_token_from_header()
        assert result == expected

    @pytest.mark.parametrize(
        "token_type, has_cookie",
        [
            (TokenTypeEnum.ACCESS, False),
            (TokenTypeEnum.REFRESH, False),
            (TokenTypeEnum.ACCESS, True),
            (TokenTypeEnum.REFRESH, True),
        ],
    )
    def test_get_token_from_cookie(
        self,
        mocker: MockerFixture,
        token_type: TokenTypeEnum,
        has_cookie: bool,
    ) -> None:
        cookie_key = f"{token_type}_token"
        mocker.patch.object(self.factory._request, "cookies", {}, create=True)

        if has_cookie:
            self.factory._request.cookies[cookie_key] = "test_token"

        result = self.factory.get_token_from_cookie(token_type)
        assert result == ("test_token" if has_cookie else None)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload_exists", [True, False])
    async def test_blacklist_token(self, payload_exists: bool, mocker: MockerFixture) -> None:
        mocker.patch("services.token.redis", self.redis)

        jti = "test-jti"
        exp = int(time()) + 3600
        payload = {
            "jti": jti,
            "exp": str(exp),
        }

        async def fake_token_required(_: Any) -> None:
            self.factory._payload = payload
            return None

        token_required_mock = mocker.patch.object(
            _TokenFactory,
            "token_required",
            side_effect=fake_token_required,
        )

        if payload_exists:
            self.factory._payload = payload

        self.redis.setex.reset_mock()

        await self.factory.blacklist_token()

        if payload_exists:
            token_required_mock.assert_not_awaited()
        else:
            token_required_mock.assert_awaited_once_with(TokenTypeEnum.REFRESH)

        self.redis.setex.assert_awaited_once()
        args, kwargs = self.redis.setex.await_args
        key, ttl, value = args[:3]

        assert key.endswith(f":{jti}")
        assert isinstance(ttl, int) and 1 <= ttl <= 3600
        assert value == 1

    @pytest.mark.parametrize(
        "token_type, token_from",
        [
            (TokenTypeEnum.ACCESS, "header"),
            (TokenTypeEnum.REFRESH, "header"),
            (TokenTypeEnum.ACCESS, "cookie"),
            (TokenTypeEnum.REFRESH, "cookie"),
        ],
    )
    def test_get_token(self, mocker: MockerFixture, token_type: TokenTypeEnum, token_from: str) -> None:
        if token_from == "header":
            mocker.patch.object(_TokenFactory, "get_token_from_cookie", return_value=None)
            mocker.patch.object(_TokenFactory, "get_token_from_header", return_value="test_header_token")
        else:
            mocker.patch.object(_TokenFactory, "get_token_from_cookie", return_value="test_cookie_token")
            mocker.patch.object(_TokenFactory, "get_token_from_header", return_value=None)

        result = self.factory.get_token(token_type)

        assert result == f"test_{token_from}_token"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "expected_token_type, token, expected_exception",
        [
            (TokenTypeEnum.ACCESS, {"type": TokenTypeEnum.ACCESS}, None),
            (TokenTypeEnum.REFRESH, {"type": TokenTypeEnum.REFRESH}, None),
            #
            (TokenTypeEnum.ACCESS, {}, TokenRequired),
            (TokenTypeEnum.REFRESH, {}, TokenRequired),
            #
            (TokenTypeEnum.ACCESS, {"type": TokenTypeEnum.REFRESH}, TokenRequired),
            (TokenTypeEnum.REFRESH, {"type": TokenTypeEnum.ACCESS}, TokenRequired),
            #
            (TokenTypeEnum.ACCESS, {"type": TokenTypeEnum.ACCESS}, TokenRevoked),
            (TokenTypeEnum.REFRESH, {"type": TokenTypeEnum.REFRESH}, TokenRevoked),
        ],
    )
    async def test_token_required(
        self,
        mocker: MockerFixture,
        expected_token_type: TokenTypeEnum,
        token: dict[str, TokenTypeEnum | str],
        expected_exception: type[Exception] | None,
    ) -> None:
        mocker.patch.object(_TokenFactory, "get_token", return_value=token)
        mocker.patch.object(_TokenFactory, "decode_token", return_value=token)
        mocker.patch.object(_TokenFactory, "is_token_revoked", return_value=False)

        if expected_token_type is TokenTypeEnum.REFRESH and expected_exception is TokenRevoked:
            mocker.patch.object(_TokenFactory, "is_token_revoked", return_value=True)

        if expected_token_type is TokenTypeEnum.ACCESS and expected_exception is TokenRevoked:
            expected_exception = None

        with pytest.raises(expected_exception) if expected_exception else nullcontext():
            await self.factory.token_required(expected_token_type)

    @pytest.mark.asyncio
    async def test_is_token_revoked_enabled(self, mocker: MockerFixture) -> None:
        mocker.patch("services.token.redis", self.redis)
        mocker.patch.object(_TokenFactory, "BLACKLIST_ENABLED", True)
        self.factory._payload = {"jti": "test-jti"}

        self.redis.exists.return_value = True
        assert await self.factory.is_token_revoked()

    @pytest.mark.asyncio
    async def test_is_token_revoked_disabled(self, mocker: MockerFixture) -> None:
        mocker.patch.object(_TokenFactory, "BLACKLIST_ENABLED", False)
        assert not await self.factory.is_token_revoked()

    @pytest.mark.asyncio
    async def test__require_refresh(self, mocker: MockerFixture) -> None:
        mocker.patch.object(_TokenFactory, "token_required", return_value=None)
        result = await _require_refresh(self.factory)

        assert result is self.factory

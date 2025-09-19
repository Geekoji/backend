from secrets import token_urlsafe

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.configs.oauth2 import OAuth2Settings
from core.exceptions import (
    InvalidProviderForPlatform,
    InvalidState,
    MissingCodeVerifier,
    MissingNonce,
    OAuth2AccountExists,
)
from core.security import hash_password
from enums import MobilePlatformEnum, OAuth2ProviderEnum, PlatformEnum
from models import Account, OAuth2Account
from schemas import OAuth2AccountSchema, OAuth2Callback, TokenPair
from services.token import TokenFactory

__all__ = [
    "get_oauth2_client",
    "oauth2_finalize_mobile",
    "oauth2_finalize_web",
]

oauth2 = OAuth()  # type: ignore

# --- Google -----------------------------------------------------------------------------------------------------------

for google_platform in PlatformEnum:
    google = OAuth2ProviderEnum.GOOGLE

    google_oauth2 = OAuth2Settings.get_settings(
        provider=google,
        platform=google_platform,
    )

    oauth2.register(
        name=f"{google}_{google_platform}",
        client_id=google_oauth2.CLIENT_ID,
        client_secret=google_oauth2.CLIENT_SECRET,
        client_kwargs={"scope": "openid email profile"},
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    )

# --- Facebook ---------------------------------------------------------------------------------------------------------

for facebook_platform in PlatformEnum:
    facebook = OAuth2ProviderEnum.FACEBOOK

    facebook_oauth2 = OAuth2Settings.get_settings(
        provider=facebook,
        platform=facebook_platform,
    )

    oauth2.register(
        name=f"{facebook}_{facebook_platform}",
        client_id=facebook_oauth2.CLIENT_ID,
        client_secret=facebook_oauth2.CLIENT_SECRET,
        access_token_url="https://graph.facebook.com/v19.0/oauth/access_token",
        authorize_url="https://www.facebook.com/v19.0/dialog/oauth",
        api_base_url="https://graph.facebook.com/v19.0/",
        client_kwargs={"scope": "email public_profile"},
    )

# --- Apple ------------------------------------------------------------------------------------------------------------

for apple_platform in [PlatformEnum.IOS, PlatformEnum.WEB]:
    apple = OAuth2ProviderEnum.APPLE

    apple_oauth2 = OAuth2Settings.get_settings(
        provider=apple,
        platform=apple_platform,
    )

    oauth2.register(
        name=f"{apple}_{apple_platform}",
        client_id=apple_oauth2.CLIENT_ID,  # usually the Services ID
        client_secret=apple_oauth2.CLIENT_SECRET,  # JWT signed with an Apple private key
        server_metadata_url="https://appleid.apple.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email name"},
    )

# ----------------------------------------------------------------------------------------------------------------------


async def oauth2_authenticate(session: AsyncSession, account_info: OAuth2AccountSchema) -> Account:
    """Authenticate client with OAuth2 provider."""
    # 1. Check for existing a client account by email
    account: Account | None = await session.scalar(
        select(Account).where(Account.email == account_info.email),
    )

    # 2. Raise error if a client account exists but the provider mismatches
    if account and isinstance(account.oauth2, OAuth2Account):
        if (provider := account.oauth2.provider) != account_info.provider:
            raise OAuth2AccountExists(OAuth2ProviderEnum(provider))

    # 3. Create a new account
    if account is None:
        new_account = Account(
            email=account_info.email,
            password_hash=hash_password(token_urlsafe(32)),
            is_verified=True,
            oauth2=OAuth2Account(
                provider=account_info.provider,
                provider_id=account_info.provider_id,
            ),
        )
        session.add(new_account)
        return new_account

    # 4. Create a new OAuth account
    if account.oauth2 is None:
        account.is_verified = True
        account.oauth2 = OAuth2Account(
            account_id=account.id,
            provider=account_info.provider,
            provider_id=account_info.provider_id,
        )

    return account


def get_oauth2_client(provider: OAuth2ProviderEnum, platform: PlatformEnum | MobilePlatformEnum) -> OAuth:
    """Get OAuth client for a given provider and platform."""
    try:
        return getattr(oauth2, f"{provider}_{platform}")  # type: ignore
    except AttributeError:
        raise InvalidProviderForPlatform()


async def oauth2_finalize(
    provider: OAuth2ProviderEnum,
    token: str,
    nonce: str,
    platform: PlatformEnum | MobilePlatformEnum,
    session: AsyncSession,
    factory: TokenFactory,
) -> TokenPair:
    """Finalize authentication."""
    oauth2_client = get_oauth2_client(provider, platform)
    account_info = await oauth2_client.parse_id_token(token, nonce)

    account_info = OAuth2AccountSchema(
        email=account_info["email"],
        provider="google",
        provider_id=account_info["sub"],
    )

    account = await oauth2_authenticate(session, account_info)
    return factory.create_pair(account)


async def oauth2_finalize_mobile(
    provider: OAuth2ProviderEnum,
    platform: MobilePlatformEnum,
    data: OAuth2Callback,
    session: AsyncSession,
    factory: TokenFactory,
) -> TokenPair:
    """Finalize mobile authentication."""
    provider_settings = OAuth2Settings.get_settings(provider, platform)
    async_client = AsyncOAuth2Client(
        client_id=provider_settings.CLIENT_ID,
        token_endpoint=provider_settings.TOKEN_ENDPOINT,
    )

    async with async_client as client:
        token = await client.fetch_token(
            code=data.code,
            code_verifier=data.code_verifier,
            grant_type="authorization_code",
            redirect_uri=provider_settings.REDIRECT_URI,
        )

    return await oauth2_finalize(
        provider=provider,
        token=token,
        nonce=data.nonce,
        platform=platform,
        session=session,
        factory=factory,
    )


async def oauth2_finalize_web(
    request: Request,
    provider: OAuth2ProviderEnum,
    state: str,
    session: AsyncSession,
    factory: TokenFactory,
) -> TokenPair:
    """Finalize web authentication."""
    if state != request.session.pop("state", ""):
        raise InvalidState()

    if not (nonce := request.session.pop("nonce", "")):
        raise MissingNonce()

    if not (code_verifier := request.session.pop("code_verifier", "")):
        raise MissingCodeVerifier()

    oauth2_client = get_oauth2_client(provider, PlatformEnum.WEB)
    token = await oauth2_client.authorize_access_token(
        request=request,
        code_verifier=code_verifier,
    )

    return await oauth2_finalize(
        provider=provider,
        token=token,
        nonce=nonce,
        platform=PlatformEnum.WEB,
        session=session,
        factory=factory,
    )

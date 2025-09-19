from uuid import uuid4

from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

from api.deps import Session, TokenFactory
from api.limits import LimitOAuth2Callback, LimitOAuth2Login
from core.configs.oauth2 import OAuth2Settings
from core.security import generate_code_challenge, generate_code_verifier
from enums import MobilePlatformEnum, OAuth2ProviderEnum, PlatformEnum
from schemas import OAuth2Callback, TokenPair
from services.oauth2 import get_oauth2_client, oauth2_finalize_mobile, oauth2_finalize_web

router = APIRouter(prefix="/oauth2", tags=["OAuth2"])


@router.get("/{provider}/login", dependencies=[LimitOAuth2Login])
async def oauth2_login(
    provider: OAuth2ProviderEnum,
    request: Request,
    platform: PlatformEnum,
) -> RedirectResponse:
    """Login with OAuth provider."""
    nonce = str(uuid4())
    state = str(uuid4())

    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    request.session["nonce"] = nonce
    request.session["state"] = state
    request.session["platform"] = platform
    request.session["code_verifier"] = code_verifier

    oauth2_client = get_oauth2_client(provider, platform)
    settings = OAuth2Settings.get_settings(provider, platform)

    return await oauth2_client.authorize_redirect(  # type: ignore
        redirect_uri=settings.REDIRECT_URI,
        request=request,
        nonce=nonce,
        state=state,
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )


@router.get("/{provider}/callback", include_in_schema=False, dependencies=[LimitOAuth2Callback])
async def oauth2_web_callback(
    request: Request,
    provider: OAuth2ProviderEnum,
    state: str,
    session: Session,
    factory: TokenFactory,
) -> TokenPair:
    """Callback for web authentication."""
    return await oauth2_finalize_web(
        request=request,
        provider=provider,
        state=state,
        session=session,
        factory=factory,
    )


@router.post("/{provider}/mobile/callback", dependencies=[LimitOAuth2Callback])
async def oauth2_mobile_callback(
    provider: OAuth2ProviderEnum,
    platform: MobilePlatformEnum,
    data: OAuth2Callback,
    session: Session,
    factory: TokenFactory,
) -> TokenPair:
    """Callback for mobile authentication."""
    return await oauth2_finalize_mobile(
        provider=provider,
        platform=platform,
        data=data,
        session=session,
        factory=factory,
    )

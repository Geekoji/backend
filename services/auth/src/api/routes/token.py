from fastapi import APIRouter

from api.deps import RefreshRequire, TokenFactory
from api.limits import LimitTokenRefresh
from schemas import JWKS, AccessToken, TokenPair

router = APIRouter(tags=["Token"])


@router.post("/token/refresh", dependencies=[LimitTokenRefresh])
async def refresh_jwt_token(factory: RefreshRequire) -> AccessToken | TokenPair:
    """Create a jwt access token from refresh token."""
    return await factory.create_access_token_from_refresh()


@router.get("/.well-known/jwks.json", include_in_schema=False)
async def get_jwks(factory: TokenFactory) -> JWKS:
    """Get JSON web key set."""
    return factory.jwks

from fastapi import APIRouter, status

from api.deps import RefreshRequire, Session, TokenFactory
from api.limits import LimitLogin, LimitLogout, LimitRegister
from schemas import Credentials, LogoutStatus, TokenPair
from services.auth import authenticate, register_account

router = APIRouter(tags=["Default Auth"])


@router.post("/register", dependencies=[LimitRegister], status_code=status.HTTP_201_CREATED)
async def register(creds: Credentials, session: Session, factory: TokenFactory) -> TokenPair:
    """Register a new client account with provided credentials."""
    account = await register_account(session, creds)
    return factory.create_pair(account)


@router.post("/login", dependencies=[LimitLogin])
async def login(creds: Credentials, session: Session, factory: TokenFactory) -> TokenPair:
    """Authenticate a client with provided credentials."""
    account = await authenticate(session, creds)
    return factory.create_pair(account)


@router.post("/logout", dependencies=[LimitLogout])
async def logout(factory: RefreshRequire) -> LogoutStatus:
    """Revoke client authentication."""
    await factory.blacklist_token()
    return LogoutStatus()

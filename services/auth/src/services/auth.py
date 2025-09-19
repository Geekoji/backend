from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import AccountAlreadyExists, InvalidCredentials, OAuth2AccountExists
from core.security import hash_password, verify_password
from enums import OAuth2ProviderEnum
from models import OAuth2Account
from models.account import Account
from schemas import Credentials

__all__ = [
    "authenticate",
    "register_account",
]


async def get_account(session: AsyncSession, email: EmailStr) -> Account | None:
    """Get a client account by email address from a database."""
    stmt = select(Account).where(Account.email == email)
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def register_account(session: AsyncSession, creds: Credentials) -> Account:
    """Register a new client account with provided credentials."""
    if await get_account(session, creds.email):
        raise AccountAlreadyExists()

    account = Account(
        email=creds.email,
        password_hash=hash_password(creds.password),
    )

    session.add(account)
    await session.flush()

    return account


async def authenticate(session: AsyncSession, creds: Credentials) -> Account:
    """Authenticate a client with provided credentials."""
    if account := await get_account(session, creds.email):

        # Check password and return a client account if the password is valid
        if verify_password(creds.password, str(account.password_hash)):
            return account

        # Notify a client that he can get in through his provider.
        if isinstance(account.oauth2, OAuth2Account):
            raise OAuth2AccountExists(OAuth2ProviderEnum(account.oauth2.provider))

    raise InvalidCredentials()

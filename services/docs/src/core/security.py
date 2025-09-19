from os import environ
from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

__all__ = [
    "basic_auth",
]

security = HTTPBasic()


def _get_basic_auth_credentials() -> tuple[str, str]:
    """Get basic auth credentials from secrets."""

    # TODO: Add Vault support for credentials
    # secret = client.secrets.kv.v2.read_secret_version(path="secret/openapi")
    # data = secret["data"]["data"]
    # return data["BASIC_AUTH_USER"], data["BASIC_AUTH_PASS"]

    return environ.get("BASIC_AUTH_USER", "admin"), environ.get("BASIC_AUTH_PASS", "admin")


async def basic_auth(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> None:
    auth_user, auth_pass = _get_basic_auth_credentials()

    is_correct_username = compare_digest(credentials.username, auth_user)
    is_correct_password = compare_digest(credentials.password, auth_pass)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

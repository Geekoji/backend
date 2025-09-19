from base64 import urlsafe_b64encode
from hashlib import sha256
from logging import ERROR, getLogger
from os import urandom

from passlib.context import CryptContext

getLogger("passlib").setLevel(ERROR)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password with bcrypt algorithm."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with the bcrypt algorithm and return status valid or not."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_code_verifier() -> str:
    """Generate code verifier for PKCE."""
    return urlsafe_b64encode(urandom(40)).rstrip(b"=").decode("ascii")


def generate_code_challenge(code_verifier: str) -> str:
    """Generate code challenge for PKCE."""
    digest = sha256(code_verifier.encode("ascii")).digest()
    return urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

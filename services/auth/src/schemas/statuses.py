from pydantic import BaseModel

__all__ = [
    "LogoutStatus",
]


class LogoutStatus(BaseModel):
    detail: str = "Logged out"

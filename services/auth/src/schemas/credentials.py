from pydantic import BaseModel, EmailStr

__all__ = [
    "Credentials",
]


class Credentials(BaseModel):
    email: EmailStr
    password: str

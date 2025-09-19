from pydantic import BaseModel, EmailStr

__all__ = [
    "OAuth2Callback",
    "OAuth2AccountSchema",
]


class OAuth2Callback(BaseModel):
    code: str
    code_verifier: str
    nonce: str
    state: str


class OAuth2AccountSchema(BaseModel):
    email: EmailStr
    provider: str
    provider_id: str

from enum import StrEnum, auto

__all__ = [
    "OAuth2ProviderEnum",
]


class OAuth2ProviderEnum(StrEnum):
    APPLE = auto()
    GOOGLE = auto()
    FACEBOOK = auto()

from enum import StrEnum, auto

__all__ = [
    "TokenTypeEnum",
]


class TokenTypeEnum(StrEnum):
    ACCESS = auto()
    REFRESH = auto()

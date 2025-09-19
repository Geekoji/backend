from enum import StrEnum, auto

__all__ = [
    "PlatformEnum",
    "MobilePlatformEnum",
]


class PlatformEnum(StrEnum):
    # DESKTOP = auto()
    ANDROID = auto()
    IOS = auto()
    WEB = auto()


class MobilePlatformEnum(StrEnum):
    ANDROID = PlatformEnum.ANDROID
    IOS = PlatformEnum.IOS

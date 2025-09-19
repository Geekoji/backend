from shared.core.logs.settings import LoggingSettings as SharedLoggingSettings

from core.configs.base import settings

__all__ = [
    "logging_settings",
]


class LoggingSettings(SharedLoggingSettings):
    SERVICE_NAME: str = settings.service_name


logging_settings = LoggingSettings()

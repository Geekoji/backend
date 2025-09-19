from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_VERSION: str = "1.0.0"

    BASIC_AUTH_USER: str = "admin"
    BASIC_AUTH_PASS: str = "admin"

    NAMESPACE: str = "development"

    SERVICE_TITLE: str = "MiM Network API"
    SERVICES: list[str] = []

    # noinspection PyMethodParameters
    @field_validator("SERVICES")
    def validate_services(cls, values: list[str]) -> list[str]:
        return sorted(list({service.lower() for service in values}))


settings = Settings()

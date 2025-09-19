from datetime import timedelta
from logging import getLogger

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "jwt_settings",
    "JWTSettings",
]

logger = getLogger("uvicorn.error")


class JWTSettings(BaseSettings):
    PRIVATE_KEY_0: str = "private"
    PUBLIC_KEY_0: str = "public"

    PRIVATE_KEY_1: str | None = None
    PUBLIC_KEY_1: str | None = None

    SIGNING_KID: int = 0

    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    BLACKLIST_ENABLED: bool = True
    BLACKLIST_PREFIX: str = "jwt-denylist"

    ISSUER: str = "https://example.com"

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        case_sensitive=True,
    )

    @property
    def access_token_expires(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def refresh_token_expires(self) -> timedelta:
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

    @property
    def PRIVATE_KEYS(self) -> list[str]:  # noqa
        return self.get_values(field_prefix="PRIVATE_KEY_")

    @property
    def PUBLIC_KEYS(self) -> list[str]:  # noqa
        return self.get_values(field_prefix="PUBLIC_KEY_")

    # noinspection PyMethodParameters
    @field_validator("PRIVATE_KEY_0", "PUBLIC_KEY_0", "PRIVATE_KEY_1", "PUBLIC_KEY_1", mode="before")
    def replace_newlines(cls, value: str | None) -> str | None:
        """Replace newlines in strings."""
        if isinstance(value, str) and value.lower() not in ["none", "", "<nil>"]:
            return value.replace(r"\n", "\n")

        return None

    # noinspection PyMethodParameters
    @field_validator("SIGNING_KID", mode="after")
    def validate_signing_kid(cls, value: int, info: ValidationInfo) -> int:
        """Validate signing key index value."""
        private_keys = [v for k, v in info.data.items() if v and k.startswith("PRIVATE_KEY_")]

        if value > (max_index := len(private_keys) - 1):
            logger.warning(
                f"SIGNING_KID value '{value}' is out of range. "
                f"Automatically setting to max available index '{max_index}'.",
            )
            return max_index
        return max(value, 0)

    def get_values(self, field_prefix: str) -> list[str]:
        """Get list of values by field prefix."""
        fields = [f for f in self.__class__.model_fields.keys() if f.startswith(field_prefix)]
        return [v for v in [getattr(self, f) for f in fields] if v is not None and v != ""]


jwt_settings = JWTSettings()

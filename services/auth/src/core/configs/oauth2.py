from functools import lru_cache
from os import getenv

from pydantic_settings import BaseSettings, SettingsConfigDict

from enums import MobilePlatformEnum, OAuth2ProviderEnum, PlatformEnum

__all__ = [
    "OAuth2Settings",
]


class OAuth2Settings(BaseSettings):

    CLIENT_ID: str = "id"
    CLIENT_SECRET: str | None = None

    @property
    def TOKEN_ENDPOINT(self) -> str:  # noqa
        raise NotImplementedError()

    @property
    def REDIRECT_URI(self) -> str:  # noqa
        raise NotImplementedError()

    @property
    def BASE_REDIRECT_URI(self) -> str:  # noqa
        return getenv("OAUTH_BASE_REDIRECT_URI", "http://localhost:8000")

    @classmethod
    @lru_cache(maxsize=len(OAuth2ProviderEnum) * len(PlatformEnum))
    def get_settings(  # noqa: CFQ004
        cls,
        provider: OAuth2ProviderEnum,
        platform: PlatformEnum | MobilePlatformEnum,
    ) -> "OAuth2Settings":
        """Get OAuth2 settings for provider and platform."""
        prefix = f"{provider.name}_{platform.name}_"

        class DynamicSettings(OAuth2Settings):
            model_config = SettingsConfigDict(
                env_prefix=prefix,
                case_sensitive=True,
            )

            @property
            def REDIRECT_URI(self) -> str:  # noqa
                """OAuth redirect URI."""
                if provider == OAuth2ProviderEnum.GOOGLE:

                    google_url = "com.googleusercontent.apps"
                    client_id_prefix = self.CLIENT_ID.split(".", 1)[0]

                    if platform == PlatformEnum.IOS:
                        return f"{google_url}.{client_id_prefix}:/oauthredirect"
                    elif platform == PlatformEnum.ANDROID:
                        return f"{google_url}.{client_id_prefix}:/oauth2redirect"

                return f"{self.BASE_REDIRECT_URI}/oauth2/{provider}/callback"

            @property
            def TOKEN_ENDPOINT(self) -> str:  # noqa
                token_endpoint_map = {
                    OAuth2ProviderEnum.APPLE: "https://appleid.apple.com/auth/token",
                    OAuth2ProviderEnum.GOOGLE: "https://oauth2.googleapis.com/token",
                    OAuth2ProviderEnum.FACEBOOK: "https://graph.facebook.com/v19.0/oauth/access_token",
                }
                return token_endpoint_map[provider]

        return DynamicSettings()

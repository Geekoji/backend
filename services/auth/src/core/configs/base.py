from shared.configs import SharedSettings


class Settings(SharedSettings):
    SERVICE_TITLE: str = "Auth Service"
    SECRET_KEY: str = "secret"


settings = Settings()

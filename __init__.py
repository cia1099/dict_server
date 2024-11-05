from pydantic_settings import BaseSettings, SettingsConfigDict


class APIConfig(BaseSettings):
    DB_URL: str | None = None
    SPEECH_REGION: str | None = None
    SPEECH_KEY: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = APIConfig()

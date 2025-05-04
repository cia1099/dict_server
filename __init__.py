from pydantic_settings import BaseSettings, SettingsConfigDict


class APIConfig(BaseSettings):
    DB_URL: str = ""
    REMOTE_DB: str = ""
    SPEECH_REGION: str | None = None
    SPEECH_KEY: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    GCLOUD_SERVICE_FILE: str | None = None
    FIREBASE_ADMIN: str | None = None
    JWT_SECRETE_KEY: str = "jwt_key"
    CHAT_BOT_UUID: str = "-".join(["0" * 8, "0" * 4, "0" * 4, "0" * 4, "0" * 12])
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = APIConfig()

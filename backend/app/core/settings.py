from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="billing-platform-api", alias="APP_NAME")
    app_port: int = Field(default=8000, alias="APP_PORT")
    database_url: str = Field(
        default="mysql+pymysql://billing_user:billing_password@localhost:3306/billing_platform",
        alias="DATABASE_URL",
    )
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    billing_ai_enabled: bool = Field(default=False, alias="BILLING_AI_ENABLED")
    billing_ai_model: str = Field(default="gpt-4.1-mini", alias="BILLING_AI_MODEL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

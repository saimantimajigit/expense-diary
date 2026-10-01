from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://expense_diary:expense_diary@localhost:5432/expense_diary"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def ignore_non_boolean_debug_values(cls, value: object) -> object:
        # Generic DEBUG variables are sometimes set by the host environment to
        # labels such as "release". Treat those as disabled instead of failing
        # application startup.
        if isinstance(value, str) and value.strip().lower() not in {
            "true", "false", "1", "0", "yes", "no", "on", "off",
        }:
            return False
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

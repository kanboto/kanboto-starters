"""All configuration comes from the environment, with no hard-coded value; see `.env.example`."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    port: int = 8080
    database_url: str
    log_level: str = "INFO"
    shutdown_timeout_s: int = 20
    idempotency_ttl_s: int = 86_400


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Configuration shared by every component, from the environment with no hard-coded value; see
`.env.example`. Each component adds its own settings in `<package>/config.py`."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    database_read_url: str | None = None  # read replica; the primary when unset
    log_level: str = "INFO"

    # Database: every call is bounded, and the pool is sized per instance.
    db_connect_timeout_s: float = 3
    db_statement_timeout_s: float = 10
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_pool_timeout_s: float = 5
    db_pool_recycle_s: int = 1800


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Settings of the scheduled tasks, from the environment with no hard-coded value; see `.env.example`. The
shared ones (database, logs) are in `common.config`."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # A run longer than this is stopped and fails: a stuck run never blocks the next ones.
    task_timeout_s: float = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Configuration shared by every component, from the environment with no hard-coded value; see
`.env.example`. Each component adds its own settings in `<package>/config.py`."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # No database when unset: the probes skip it, the commands that need it refuse to run.
    database_url: str | None = None
    database_read_url: str | None = None  # read replica; the primary when unset
    log_level: str = "INFO"

    # Database: every call is bounded, and the pool is sized per instance.
    db_connect_timeout_s: float = 3
    db_statement_timeout_s: float = 10
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_pool_timeout_s: float = 5
    db_pool_recycle_s: int = 1800
    ready_timeout_s: float = 2  # readiness: database and buckets check

    # Object storage (S3): a bucket is configured when its name is set; see `common/storage.py`.
    s3_endpoint: str = "http://localhost:3900"
    s3_region: str = "garage"
    s3_private_bucket: str | None = None
    s3_private_access_key_id: str | None = None
    s3_private_secret_access_key: str | None = None
    s3_public_bucket: str | None = None
    s3_public_access_key_id: str | None = None
    s3_public_secret_access_key: str | None = None
    s3_public_url: str | None = None  # where the public bucket is served, without a trailing slash
    s3_connect_timeout_s: float = 3
    s3_timeout_s: float = 30

    @field_validator(
        "database_url",
        "database_read_url",
        "s3_private_bucket",
        "s3_public_bucket",
        "s3_public_url",
    )
    @classmethod
    def _empty_is_unset(cls, value: str | None) -> str | None:
        return value or None


@lru_cache
def get_settings() -> Settings:
    return Settings()

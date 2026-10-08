"""All configuration comes from the environment, with no hard-coded value; see `.env.example`."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    port: int = 8080
    database_url: str
    log_level: str = "INFO"

    # Database: every call is bounded, and the pool is sized per instance.
    db_connect_timeout_s: float = 3
    db_statement_timeout_s: float = 10
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_pool_timeout_s: float = 5
    db_pool_recycle_s: int = 1800
    ready_timeout_s: float = 2

    # Shutdown: on SIGTERM, /readyz fails for DRAIN_DELAY_S while traffic is still served, then in-flight
    # requests get SHUTDOWN_TIMEOUT_S to complete.
    drain_delay_s: float = 5
    shutdown_timeout_s: int = 20

    # Proxies trusted for X-Forwarded-* headers (comma-separated IPs or CIDRs).
    forwarded_allow_ips: str = "127.0.0.1"
    max_body_bytes: int = 1_048_576
    idempotency_ttl_s: int = 86_400


@lru_cache
def get_settings() -> Settings:
    return Settings()

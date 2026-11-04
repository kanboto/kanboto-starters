"""Settings of the API, from the environment with no hard-coded value; see `.env.example`. The shared ones
(database, logs) are in `common.config`."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    port: int = 8080

    # Shutdown: on SIGTERM, /readyz fails for DRAIN_DELAY_S while traffic is still served, then in-flight
    # requests get SHUTDOWN_TIMEOUT_S to complete.
    drain_delay_s: float = 5
    shutdown_timeout_s: int = 20

    # Outbound HTTP: one shared client, every call bounded.
    http_connect_timeout_s: float = 3
    http_timeout_s: float = 10
    http_max_connections: int = 100

    # Browser origins allowed to call the API (comma-separated); none when empty.
    cors_origins: str = ""

    # Proxies trusted for X-Forwarded-* headers (comma-separated IPs or CIDRs).
    forwarded_allow_ips: str = "127.0.0.1"
    max_body_bytes: int = 1_048_576
    max_upload_bytes: int = 10_485_760  # routes that receive files (`middleware.UPLOAD_PATHS`)
    idempotency_ttl_s: int = 86_400


@lru_cache
def get_settings() -> Settings:
    return Settings()

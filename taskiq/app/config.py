"""All configuration comes from the environment, with no hard-coded value; see `.env.example`."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    port: int = 8080
    log_level: str = "INFO"

    # NATS JetStream: one stream holds the tasks and, under their own subject, the dead letters.
    nats_url: str  # several servers of a cluster: comma-separated
    nats_connect_timeout_s: float = 3
    nats_stream: str = "tasks"
    nats_subject: str = "tasks"
    nats_dead_letter_subject: str = "tasks.dead"
    nats_consumer: str = "worker"  # durable consumer shared by every instance

    # Execution: tasks run concurrently up to WORKER_CONCURRENCY per instance, each bounded by TASK_TIMEOUT_S.
    worker_concurrency: int = 10
    task_timeout_s: float = 60
    max_retries: int = 3

    # Shutdown: on SIGTERM, no new task is fetched and in-flight ones get SHUTDOWN_TIMEOUT_S to complete.
    shutdown_timeout_s: float = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()

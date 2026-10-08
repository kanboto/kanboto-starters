# Starter FastAPI

API FastAPI prête pour Kubernetes, aux standards de Kanboto : configuration par l'environnement, sans état,
sondes et métriques Prometheus, arrêt propre, logs JSON, image non-root, API versionnée et idempotente.

## Lancer

```sh
cp .env.example .env            # puis ajuster DATABASE_URL
uv sync
uv run python -m app migrate    # applique les migrations
uv run python -m app            # http://localhost:8080/api/v1/items
```

## Tester

```sh
uv run ruff check . && uv run ruff format --check . && uv run mypy .
uv run pytest
```

## Image

```sh
docker build -t starter-fastapi .
docker run --read-only --tmpfs /tmp --env-file .env.example -p 8080:8080 starter-fastapi
```

`python -m app migrate` dans la même image applique les migrations (un Job Kubernetes en production).

| Variable | Défaut | Rôle |
|---|---|---|
| `PORT` | 8080 | port de l'API, des sondes et des métriques |
| `DATABASE_URL` | — | base PostgreSQL (`postgresql+asyncpg://…`) |
| `LOG_LEVEL` | `INFO` | niveau des logs |
| `SHUTDOWN_TIMEOUT_S` | 20 | délai d'arrêt propre après `SIGTERM` |
| `IDEMPOTENCY_TTL_S` | 86400 | durée de garde des clés d'idempotence |

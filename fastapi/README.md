# FastAPI starter

A minimal, Kubernetes-ready HTTP API built with FastAPI, SQLAlchemy (async) and PostgreSQL. It ships with
everything a production service needs and nothing it does not: probes, Prometheus metrics, graceful
shutdown, JSON logs, a hardened image, and a versioned, idempotent API.

## Requirements

- Python 3.13 and [uv](https://docs.astral.sh/uv/)
- PostgreSQL 15 or later
- Docker, to build the image

## Getting started

```sh
cp .env.example .env               # then set DATABASE_URL
uv sync
uv run python -m app migrate       # apply database migrations
uv run python -m app               # serve on http://localhost:8080
```

Try it:

```sh
curl -X POST localhost:8080/api/v1/items \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"name": "first item"}'
curl localhost:8080/api/v1/items
```

## Development

| Task | Command |
|---|---|
| Lint | `uv run ruff check .` |
| Format check | `uv run ruff format --check .` |
| Type check | `uv run mypy .` |
| Tests | `uv run pytest` |
| Regenerate the OpenAPI spec | `uv run python -m app openapi > openapi/public.yaml` |

Tests run against SQLite, created by the migrations for every test, so migrations are exercised on every
run. Production uses PostgreSQL through `asyncpg`.

## Configuration

All configuration comes from environment variables.

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | Port for the API, the probes and the metrics |
| `DATABASE_URL` | required | PostgreSQL URL, e.g. `postgresql+asyncpg://user:pass@host:5432/db` |
| `LOG_LEVEL` | `INFO` | Log level |
| `SHUTDOWN_TIMEOUT_S` | `20` | Grace period for in-flight requests after `SIGTERM` |
| `IDEMPOTENCY_TTL_S` | `86400` | How long idempotency keys are kept |

## Container image

```sh
docker build -t starter-fastapi .
docker run --read-only --tmpfs /tmp --env-file .env.example -p 8080:8080 starter-fastapi
```

The same image runs the migrations with `python -m app migrate`, typically from a Kubernetes Job before a
rollout. The service itself never migrates at startup.

## Endpoints

| Path | Purpose | Exposed publicly |
|---|---|---|
| `/api/v1/...` | Public API, documented in [`openapi/public.yaml`](openapi/public.yaml) | Yes |
| `/healthz` | Liveness: the server responds | No |
| `/readyz` | Readiness: the database is reachable; `503` during shutdown | No |
| `/metrics` | Prometheus metrics | No |

## Project layout

```
app/
├── __main__.py      Entrypoint: serve, migrate, openapi
├── main.py          Application factory
├── config.py        Settings, from the environment
├── api/v1/          Version 1 of the public API (items is an example resource)
├── health.py        Liveness and readiness probes
├── metrics.py       Prometheus metrics
├── logs.py          JSON logging
├── errors.py        RFC 9457 problem details
├── idempotency.py   Idempotency-Key handling
├── pagination.py    Cursor pagination
└── db.py            Database models and session
migrations/          Alembic migrations
openapi/             Generated OpenAPI specification
tests/
```

Replace the `items` resource with your own, keeping its conventions. The other modules implement the
runtime and API contracts and are meant to stay.

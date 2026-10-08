# FastAPI starter

A minimal, production-ready HTTP API built with FastAPI, SQLAlchemy (async) and PostgreSQL. It ships with
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
| Tests (SQLite) | `uv run pytest` |
| Tests (PostgreSQL) | `TEST_DATABASE_URL=postgresql+asyncpg://… uv run pytest` |
| Regenerate the OpenAPI spec | `uv run python -m app openapi > openapi/public.yaml` |

Every test gets a fresh database built by the migrations, so migrations are exercised on every run. Run the
suite against PostgreSQL before merging: it is what production uses.

## Configuration

All configuration comes from environment variables.

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | Port for the API, the probes and the metrics |
| `DATABASE_URL` | required | PostgreSQL URL, e.g. `postgresql+asyncpg://user:pass@host:5432/db` |
| `LOG_LEVEL` | `INFO` | Log level |
| `DB_CONNECT_TIMEOUT_S` | `3` | Timeout to open a database connection |
| `DB_STATEMENT_TIMEOUT_S` | `10` | Timeout for a single SQL statement |
| `DB_POOL_SIZE` | `5` | Connections kept open per instance |
| `DB_MAX_OVERFLOW` | `5` | Extra connections allowed under load, per instance |
| `DB_POOL_TIMEOUT_S` | `5` | Wait for a free connection before failing the request |
| `READY_TIMEOUT_S` | `2` | Timeout of the readiness database check |
| `DRAIN_DELAY_S` | `5` | After `SIGTERM`, time readiness fails while traffic is still served |
| `SHUTDOWN_TIMEOUT_S` | `20` | Then, grace period for in-flight requests |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1` | Proxies trusted for `X-Forwarded-*` headers (IPs or CIDRs) |
| `MAX_BODY_BYTES` | `1048576` | Largest request body accepted (`413` beyond) |
| `IDEMPOTENCY_TTL_S` | `86400` | How long idempotency keys are kept |

Size the pool so that `instances × (DB_POOL_SIZE + DB_MAX_OVERFLOW)` stays under the database's
connection limit. After `SIGTERM`, the process exits within `DRAIN_DELAY_S + SHUTDOWN_TIMEOUT_S`.

## Container image

```sh
docker build -t starter-fastapi .
docker run --read-only --tmpfs /tmp --env-file .env.example -p 8080:8080 starter-fastapi
```

The same image runs the other commands:

| Command | When | Purpose |
|---|---|---|
| `python -m app migrate` | before starting a new version | Apply pending migrations; the service never migrates at startup |
| `python -m app cleanup` | periodically, e.g. hourly | Delete expired idempotency keys |

## Endpoints

| Path | Purpose |
|---|---|
| `/api/v1/...` | Public API, documented in [`openapi/public.yaml`](openapi/public.yaml) |
| `/healthz` | Liveness: the server responds |
| `/readyz` | Readiness: the database is reachable; `503` as soon as shutdown starts |
| `/metrics` | Prometheus metrics |

Every response carries an `X-Request-ID` (the caller's, or a generated one), also present on every log line
written while handling the request.

## Project layout

```
app/
├── __main__.py      Entrypoint: serve, migrate, openapi
├── main.py          Application factory
├── config.py        Settings, from the environment
├── api/v1/          Version 1 of the public API (items is an example resource)
├── health.py        Liveness and readiness probes
├── middleware.py    Request id, access log, body limit, security headers
├── metrics.py       Prometheus metrics
├── deprecation.py   Deprecation and Sunset headers for an old API version
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

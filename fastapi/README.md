# FastAPI module

A minimal, production-ready HTTP API built with FastAPI, over the [Python base](../python/) (SQLAlchemy async,
PostgreSQL). It ships with everything a production service needs and nothing it does not: probes, Prometheus
metrics, graceful shutdown, JSON logs, a hardened image, and a versioned, idempotent API.

The module is the package `api/` and its tests `tests/api/`; [`module.toml`](module.toml) says how
[`scripts/compose.py`](../scripts/compose.py) adds it to a project, under its own name or another one:

```sh
python3 scripts/compose.py ../shop fastapi            # api/
python3 scripts/compose.py ../shop fastapi fastapi:hooks  # two APIs: api/ and hooks/
```

## Getting started

In the composed project:

```sh
cp .env.example .env               # then set DATABASE_URL: the example resource needs a database
uv sync --extra api
uv run python -m api migrate       # apply database migrations
uv run python -m api               # serve on http://localhost:8080
```

Try it:

```sh
curl -X POST localhost:8080/api/v1/items \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"name": "first item"}'
curl localhost:8080/api/v1/items
```

Files (needs a bucket, see the base's README): `POST /api/v1/files?access=private|public` with the file as
the body stores it under a random key; a private file is read back with `GET /api/v1/files/{key}`, a public
one at the returned `url`.

```sh
curl -X POST 'localhost:8080/api/v1/files?access=public' -H 'Content-Type: image/png' --data-binary @logo.png
```

Regenerate the OpenAPI spec after a change to the API: `uv run python -m api openapi > openapi/api.yaml`
(a test fails when it is out of date). Development commands are in the base's README.

## Configuration

Variables of the API, added to `.env.example` by the composition; the shared ones (database, logs) are in
the base's README.

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | Port for the API, the probes and the metrics |
| `DRAIN_DELAY_S` | `5` | After `SIGTERM`, time readiness fails while traffic is still served |
| `SHUTDOWN_TIMEOUT_S` | `20` | Then, grace period for in-flight requests |
| `HTTP_CONNECT_TIMEOUT_S` | `3` | Outbound HTTP: timeout to connect |
| `HTTP_TIMEOUT_S` | `10` | Outbound HTTP: timeout for a call |
| `HTTP_MAX_CONNECTIONS` | `100` | Outbound HTTP: connections kept per instance |
| `CORS_ORIGINS` | empty | Browser origins allowed to call the API, comma-separated; CORS is off when empty |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1` | Proxies trusted for `X-Forwarded-*` headers (IPs or CIDRs) |
| `MAX_BODY_BYTES` | `1048576` | Largest request body accepted (`413` beyond) |
| `MAX_UPLOAD_BYTES` | `10485760` | Largest file accepted by the routes that receive files (`UPLOAD_PATHS`) |
| `IDEMPOTENCY_TTL_S` | `86400` | How long idempotency keys are kept |

Reads go through `deps.ReadSession`, whose transactions are read-only, and writes through `deps.WriteSession`.
Without `DATABASE_READ_URL`, both share the primary's pool; with a replica, the replica gets its own pool,
with the same settings. Size the pool so that `instances × (DB_POOL_SIZE + DB_MAX_OVERFLOW)` stays under
each database's connection limit. After `SIGTERM`, the process exits within `DRAIN_DELAY_S + SHUTDOWN_TIMEOUT_S`.

## Container image

The project's image runs the API by default when the module comes first, and the other commands:

| Command | When | Purpose |
|---|---|---|
| `python -m api` | always | Serve the API (`serve`) |
| `python -m api migrate` | before starting a new version | Apply pending migrations, one run at a time; the service never migrates at startup |
| `python -m api cleanup` | periodically, e.g. hourly | Delete expired idempotency keys |

## Endpoints

| Path | Purpose |
|---|---|
| `/api/v1/...` | Public API, documented in [`openapi/api.yaml`](openapi/api.yaml) (`openapi/<package>.yaml`) |
| `/healthz` | Liveness: the server responds |
| `/readyz` | Readiness: the database is reachable, when one is configured; `503` as soon as shutdown starts |
| `/metrics` | Prometheus metrics |

Every response carries an `X-Request-ID` (the caller's, or a generated one), also present on every log line
written while handling the request.

## Module layout

```
api/
├── __main__.py      Entrypoint: serve, migrate, cleanup, openapi
├── main.py          Application factory
├── config.py        Settings of the API, from the environment
├── deps.py          Read and write sessions, as dependencies
├── v1/              Version 1 of the public API (items is an example resource)
├── health.py        Liveness and readiness probes
├── middleware.py    Request id, access log, body limit, security headers
├── outbound.py      Shared HTTP client for calls to other services
├── metrics.py       Prometheus metrics of HTTP requests
├── deprecation.py   Deprecation and Sunset headers for an old API version
├── errors.py        RFC 9457 problem details
├── idempotency.py   Idempotency-Key handling
└── pagination.py    Cursor pagination
openapi/api.yaml     Generated OpenAPI specification (openapi/<package>.yaml)
tests/api/
module.toml          How compose.py adds the module (not copied)
```

Replace the `items` resource with your own, keeping its conventions. The other modules implement the
runtime and API contracts and are meant to stay.

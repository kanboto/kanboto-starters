# AGENTS.md

<!-- kanboto:start -->
## Kanboto rules (FastAPI stack)

This section is maintained by Kanboto: do not edit it by hand, Kanboto updates it through pull requests.
The CI (`kanboto-ci-*`) enforces these rules; a pull request that breaks them does not pass.

### Runtime (Kubernetes)

- Configuration through environment variables only, each one listed in `.env.example`; no hard-coded
  value, no configuration file in the image. Addresses of other services come from explicit variables
  (`BILLING_API_URL`), never from Kubernetes service discovery variables.
- Stateless: nothing is written outside `/tmp` (the image runs on a read-only filesystem); sessions, files
  and caches live in an external service. Several replicas run side by side.
- Non-blocking: async drivers (database, HTTP), no blocking call inside an `async` function, a timeout on
  every outbound call; long CPU-bound work goes to a worker through a queue.
- `GET /healthz` (alive), `GET /readyz` (dependencies reachable, `503` during shutdown) and `GET /metrics`
  (Prometheus) stay at the root path on `PORT`; they are never exposed publicly.
- Graceful shutdown on `SIGTERM` within `SHUTDOWN_TIMEOUT_S`: in-flight work completes.
- JSON logs on stdout, one line per event.
- Multi-stage image, non-root user, base images pinned by digest; migrations run through
  `python -m app migrate`, never at service startup.

### API

- Public routes under `/api/v<N>/`, internal routes under `/internal/v<N>/`; only the major version
  appears in the path.
- A backward-compatible change (new field, optional parameter or endpoint) stays in the current version.
  A breaking change opens `/api/v<N+1>/`; the previous version keeps being served, marked `deprecated`
  with a removal date (`Deprecation` and `Sunset` headers). Nothing breaks in a published version.
- `openapi/public.yaml` follows the code: `python -m app openapi > openapi/public.yaml`.
- Errors use RFC 9457 (`application/problem+json`); dates are ISO 8601 in UTC; pagination is
  cursor-based (`limit`, `cursor`, response `items` and `next_cursor`); resource names are plural.
- A `POST` that creates a resource or triggers a side effect requires `Idempotency-Key` (see
  `app/idempotency.py`).

### Commands

- Install: `uv sync`
- Lint, format, types: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`
- Tests: `uv run pytest`
<!-- kanboto:end -->

## This starter

- `app/main.py` assembles the application; `app/api/v1/` holds version 1 of the API. `items` is an example
  resource: replace it with your domain's, keeping its conventions.
- `app/health.py`, `app/metrics.py`, `app/logs.py`, `app/errors.py`, `app/idempotency.py` and
  `app/pagination.py` implement the contracts; keep them.
- Tests run against SQLite, built by the migrations for each test; production uses PostgreSQL.

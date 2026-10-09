# AGENTS.md

<!-- kanboto:start -->
## Kanboto rules (FastAPI stack)

This section is maintained by Kanboto: do not edit it by hand, Kanboto updates it through pull requests. The
CI (`kanboto-ci-*`) enforces these rules; a pull request that breaks them does not pass.

### Runtime

- Configuration through environment variables only, each one listed in `.env.example`; no hard-coded value, no
  configuration file in the image. Each service the application calls has its own variable
  (`BILLING_API_URL`).
- Stateless: nothing is written outside `/tmp` (the image runs on a read-only filesystem); sessions, files and
  caches live in an external service. Several instances run side by side.
- Non-blocking: async drivers (database, HTTP), no blocking call inside an `async` function, a timeout on
  every outbound call; long CPU-bound work goes to a worker through a queue. Other services are called through
  the shared client of `app/outbound.py`, never a client created per request.
- Database connections come from the pools of `app/db.py`, never opened per request. Keep transactions short,
  and never hold one open while calling another service.
- A handler that only reads uses `db.ReadSession` (read replica when `DATABASE_READ_URL` is set, read-only in
  any case). A handler that writes uses `db.WriteSession` for all its work, including the reads it needs to
  decide; it never mixes both. A write returns the updated resource, so clients need not read it back.
- `GET /healthz` (alive), `GET /readyz` (dependencies reachable, `503` during shutdown) and `GET /metrics`
  (Prometheus) stay at the root path, on `PORT`, outside `/api` and `/internal`.
- Graceful shutdown on `SIGTERM` within `SHUTDOWN_TIMEOUT_S`: in-flight work completes.
- JSON logs on stdout, one line per event.
- Multi-stage image, non-root user, base images pinned by digest; migrations run through
  `python -m app migrate`, never at service startup.

### Code

Rules in priority order: when two conflict, the first one wins.

1. **Correct first.** The code does what the ticket asks, and its tests prove it.
2. **Simplest that works (KISS, YAGNI).** No abstraction, option, layer or setting for a need that does not
   exist yet. Three plain lines beat a clever helper.
3. **Search before you write (DRY).** Reuse the repository's existing functions, models and helpers. Extract a
   shared function when the same rule appears a third time, not before: duplication is cheaper than the wrong
   abstraction. A business rule is written once.
4. **One reason to change (single responsibility).** A function does one thing and is named after it; a module
   holds one concern. Split a function when it needs a comment to separate its steps.
5. **Abstractions earn their place (SOLID, pragmatically).** An interface, base class or factory only when two
   implementations exist, or a test must substitute one. Prefer plain functions and composition to
   inheritance. Pass dependencies in (arguments, framework dependency injection) rather than reaching for
   globals from business code.
6. **The repository's conventions first.** Structure, naming, error handling and test style follow what is
   already there. A new convention is a decision: say so in the pull request description.
7. **Nothing dead.** No commented-out code, no unused function or parameter, no TODO without a ticket.
   Comments explain why, never what the code already says.

### API

- Public routes under `/api/v<N>/`, internal routes under `/internal/v<N>/`; only the major version appears in
  the path.
- A backward-compatible change (new field, optional parameter or endpoint) stays in the current version. A
  breaking change opens `/api/v<N+1>/`; the previous version keeps being served, marked `deprecated` with a
  removal date (`Deprecation` and `Sunset` headers, see `app/deprecation.py`). Nothing breaks in a published
  version.
- `openapi/public.yaml` follows the code: `python -m app openapi > openapi/public.yaml`.
- Errors use RFC 9457 (`application/problem+json`); dates are ISO 8601 in UTC; pagination is cursor-based
  (`limit`, `cursor`, response `items` and `next_cursor`); resource names are plural.
- A `POST` that creates a resource or triggers a side effect requires `Idempotency-Key` (see
  `app/idempotency.py`).

### Commands

- Install: `uv sync --locked`
- Lint, format, types: `uv run ruff check . --extend-select C901,PLR0911,PLR0912,PLR0913,PLR0915`,
  `uv run ruff format --check .`, `uv run mypy .`
- Tests: `uv run pytest` (SQLite), `TEST_DATABASE_URL=postgresql://… uv run pytest` (PostgreSQL)
<!-- kanboto:end -->

## This starter

- `app/main.py` assembles the application; `app/api/v1/` holds version 1 of the API. `items` is an example
  resource: replace it with your domain's, keeping its conventions.
- `app/health.py`, `app/middleware.py`, `app/metrics.py`, `app/logs.py`, `app/errors.py`,
  `app/idempotency.py`, `app/pagination.py`, `app/deprecation.py` and `app/outbound.py` implement the
  contracts; keep them.
- Every database call goes through `app/db.py`, whose engine bounds connections and statements by timeouts.

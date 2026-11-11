# AGENTS.md

<!-- kanboto:start -->
## Kanboto rules (Python stack)

This section is maintained by Kanboto: do not edit it by hand, Kanboto updates it through pull requests. The
CI (`kanboto-ci-*`) enforces these rules; a pull request that breaks them does not pass.

### Structure

- One project, one image: one manifest, one lock, one `Dockerfile` at the root. Each component is a package
  named after it, run by `python -m <package>`; a component added later is one more package.
- `common/` holds the domain, shared by the components: entities, rules and invariants, use cases,
  transactions, data access. It never imports a component package.
- A component package holds the exposure only (HTTP routes and schemas, authentication, consumers,
  serialization, retries, `__main__`) and calls `common/`: no business rule, no direct data access, no import
  of another component package. Inside it, imports are relative (`from .health import …`).
- `migrations/` holds the database schema, driven by `common/`. Tests mirror the packages: `tests/common/`,
  `tests/<package>/`.

### Runtime

- Configuration through environment variables only, each one listed in `.env.example`; no hard-coded value, no
  configuration file in the image. Each service the application calls has its own variable
  (`BILLING_API_URL`).
- Values in `.env.example` are development values. A variable that has no valid default outside development
  gets a comment line just above it: `# secret` for a credential, whose example value is never reused,
  `# required` for any other value set per environment (an external service's URL, an account identifier).
- Stateless: nothing is written outside `/tmp` (the image runs on a read-only filesystem); sessions, files and
  caches live in an external service. Several instances run side by side.
- Non-blocking: async drivers (database, HTTP), no blocking call inside an `async` function, a timeout on
  every outbound call; long CPU-bound work goes to a worker through a queue. Other services are called through
  the shared client of the API package's `outbound.py`, never a client created per request.
- Database connections come from the pools of `common/db.py`, never opened per request. Keep transactions
  short, and never hold one open while calling another service.
- Files go to the S3 buckets through `common/storage.py`, never to disk: `private` for what only the
  application serves, `public` for what anyone loads at `S3_PUBLIC_URL/<key>`. Keys are random, a frontend
  only reads public files, and uploads go through an API.
- A handler that only reads uses `deps.ReadSession` (read replica when `DATABASE_READ_URL` is set, read-only
  in any case). A handler that writes uses `deps.WriteSession` for all its work, including the reads it needs
  to decide; it never mixes both. A write returns the updated resource, so clients need not read it back.
- `GET /healthz` (alive), `GET /readyz` (dependencies reachable, `503` during shutdown) and `GET /metrics`
  (Prometheus) stay at the root path, on `PORT`, outside `/api` and `/internal`.
- Graceful shutdown on `SIGTERM` within `SHUTDOWN_TIMEOUT_S`: in-flight work completes.
- JSON logs on stdout, one line per event.
- Multi-stage image, non-root user, base images pinned by digest; migrations run through
  `python -m <package> migrate`, never at service startup.

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

### Tasks

- Tasks live in the worker package's `tasks.py`, each with an explicit task name. A task is delivered at least
  once: it is idempotent, and finishes within `TASK_TIMEOUT_S`.
- A failed task is retried up to `MAX_RETRIES` times, then kept as a dead letter, never lost.
- At most `WORKER_CONCURRENCY` tasks run at once in an instance.

### Scheduled tasks

- A scheduled task is the `run()` coroutine of `tasks/jobs/<name>.py`, run by `python -m tasks <name>` on its
  schedule: it starts, does its work through `common/`, and exits. The runner gives it one run at a time, a
  bound of `TASK_TIMEOUT_S` and its exit code; the task itself stays idempotent, as it may run again after a
  failure.
- A scheduled task never serves requests nor runs in a loop: work that waits for an event belongs to a worker.

### API

- Public routes under `/api/v<N>/`, internal routes under `/internal/v<N>/`; only the major version appears in
  the path.
- A backward-compatible change (new field, optional parameter or endpoint) stays in the current version. A
  breaking change opens `/api/v<N+1>/`; the previous version keeps being served, marked `deprecated` with a
  removal date (`Deprecation` and `Sunset` headers, see the API package's `deprecation.py`). Nothing breaks in
  a published version.
- Each API's OpenAPI spec follows the code: `python -m <package> openapi > openapi/<package>.yaml`.
- Errors use RFC 9457 (`application/problem+json`); dates are ISO 8601 in UTC; pagination is cursor-based
  (`limit`, `cursor`, response `items` and `next_cursor`); resource names are plural.
- A `POST` that creates a resource or triggers a side effect requires `Idempotency-Key` (see the API package's
  `idempotency.py`).

### Database

- Every schema change is backward compatible with the code currently in production: old and new versions run
  side by side during a deploy, and a rollback keeps the migrated schema.
- Breaking changes go through expand/contract, in separate pull requests.
- Expand: add only (new column nullable or with a default, new table, index built without locking the table).
- Migrate: the code writes both shapes and reads the new one; large backfills run in batches, outside the
  migration.
- Contract: drop or rename the old shape only once the expand version is released to production.
- Never in a single migration: drop or rename a column or table the production code still reads, add a NOT
  NULL column without a default, change a column type in place.
- The expand pull request says what the contract step will remove, and when.

### Commands

- Install: `uv sync --locked --all-extras`
- Lint, format, types: `uv run ruff check . --extend-select C901,PLR0911,PLR0912,PLR0913,PLR0915`,
  `uv run ruff format --check .`, `uv run mypy .`
- Tests: `uv run pytest` (SQLite), `TEST_DATABASE_URL=postgresql://… uv run pytest` (PostgreSQL)
<!-- kanboto:end -->

## This project

One Python project, one image, several components: each component is a package run as
`python -m <package>`, and every component shares `common/`.

- `common/` holds what every component shares: the business code (`common/models/`, `common/services/`) and
  the plumbing (`common/config.py`, `common/db.py`, `common/logs.py`, `common/metrics.py`,
  `common/schema.py`). It never imports a component, nor FastAPI or TaskIQ. A business rule is written once,
  in `common/services/`, and called from a handler, a task or a command.
- Every database call goes through `common/db.py`, whose engines bound connections and statements by
  timeouts. Every table is declared in `common/models/`, whichever component uses it, so that the migrations
  (`migrations/`) see the whole schema. `items` (model, service, API resource) is an example: replace it with
  your domain's, keeping its conventions.
- A component's own settings live in its `config.py`; the shared ones (database, logs) in `common/config.py`.
- Within a component's package, imports are relative (`from . import health`) and `common` is imported by
  name; the package never spells its own name (`__package__` for loggers and module paths). Its tests, in
  `tests/<package>/`, import it by name.

### API component (`api/` by default, FastAPI)

- `api/main.py` assembles the application; `api/v1/` holds version 1 of the API.
- `api/health.py`, `api/middleware.py`, `api/metrics.py`, `api/errors.py`, `api/idempotency.py`,
  `api/pagination.py`, `api/deprecation.py` and `api/outbound.py` implement the contracts; keep them. Sessions
  come from `api/deps.py` (`ReadSession`, `WriteSession`), over the pools of `common/db.py`.
- `openapi/<package>.yaml` follows the code: `python -m api openapi > openapi/api.yaml`; migrations run through
  `python -m api migrate`.

### Worker component (`worker/` by default, TaskIQ and NATS JetStream)

- `worker/tasks.py` holds the tasks. `process_item` is an example task: replace it with your domain's, keeping
  its conventions (explicit `task_name`, idempotent, one log line per execution).
- `worker/worker.py` runs the worker (`python -m worker`): the consumer loop, the HTTP server for the probes
  and metrics, and the graceful shutdown, in one asyncio process.
- `worker/broker.py` (JetStream stream, durable consumer, dead letters), `worker/middleware.py` (task id on
  logs, timeout, execution log and metrics, retries), `worker/health.py`, `worker/metrics.py` and
  `worker/logs.py` implement the contracts; keep them.
- Tasks are delivered at least once: a retry or a redelivery can run a task again, so a task must be idempotent
  and finish within `TASK_TIMEOUT_S`.

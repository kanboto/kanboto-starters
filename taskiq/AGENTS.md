# AGENTS.md

<!-- kanboto:start -->
## Kanboto rules (TaskIQ stack)

This section is maintained by Kanboto: do not edit it by hand, Kanboto updates it through pull requests. The
CI (`kanboto-ci-*`) enforces these rules; a pull request that breaks them does not pass.

### Runtime

- Configuration through environment variables only, each one listed in `.env.example`; no hard-coded value, no
  configuration file in the image. Each service the application calls has its own variable
  (`BILLING_API_URL`).
- Stateless: nothing is written outside `/tmp` (the image runs on a read-only filesystem); sessions, files and
  caches live in an external service. Several instances run side by side.
- Non-blocking: async drivers (database, HTTP), no blocking call inside an `async` function, a timeout on
  every outbound call; long CPU-bound work goes to a worker through a queue.
- `GET /healthz` (alive), `GET /readyz` (dependencies reachable, `503` during shutdown) and `GET /metrics`
  (Prometheus) stay at the root path, on `PORT`, outside `/api` and `/internal`.
- Graceful shutdown on `SIGTERM` within `SHUTDOWN_TIMEOUT_S`: in-flight work completes.
- JSON logs on stdout, one line per event.
- Multi-stage image, non-root user, base images pinned by digest.

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

- Tasks live in `app/tasks.py`, each with an explicit task name. A task is delivered at least once: it is
  idempotent, and finishes within `TASK_TIMEOUT_S`.
- A failed task is retried up to `MAX_RETRIES` times, then kept as a dead letter, never lost.
- At most `WORKER_CONCURRENCY` tasks run at once in an instance.

### Commands

- Install: `uv sync --locked`
- Lint, format, types: `uv run ruff check . --extend-select C901,PLR0911,PLR0912,PLR0913,PLR0915`,
  `uv run ruff format --check .`, `uv run mypy .`
- Tests: `uv run pytest`
<!-- kanboto:end -->

## This starter

- `app/tasks.py` holds the tasks. `process_item` is an example task: replace it with your domain's, keeping its
  conventions (explicit `task_name`, idempotent, one log line per execution).
- `app/worker.py` runs the worker (`python -m app worker`): the consumer loop, the HTTP server for the probes
  and metrics, and the graceful shutdown, in one asyncio process.
- `app/broker.py` (JetStream stream, durable consumer, dead letters), `app/middleware.py` (task id on logs,
  timeout, execution log and metrics, retries), `app/health.py`, `app/metrics.py` and `app/logs.py` implement
  the contracts; keep them.
- Tasks are delivered at least once: a retry or a redelivery can run a task again, so a task must be idempotent
  and finish within `TASK_TIMEOUT_S`.

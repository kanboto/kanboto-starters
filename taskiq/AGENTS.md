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

### Tasks

- Tasks live in `app/tasks.py`, each with an explicit task name. A task is delivered at least once: it is
  idempotent, and finishes within `TASK_TIMEOUT_S`.
- A failed task is retried up to `MAX_RETRIES` times, then kept as a dead letter, never lost.
- At most `WORKER_CONCURRENCY` tasks run at once in an instance.

### Commands

- Install: `uv sync --locked`
- Lint, format, types: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`
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

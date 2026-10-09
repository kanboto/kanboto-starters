# TaskIQ starter

A minimal, production-ready background worker built with TaskIQ and NATS JetStream. It ships with everything a
production worker needs and nothing it does not: tasks that are never lost, bounded retries with dead letters,
bounded concurrency, probes, Prometheus metrics, graceful shutdown, JSON logs and a hardened image.

## Requirements

- Python 3.13 and [uv](https://docs.astral.sh/uv/)
- A NATS server with JetStream enabled, 2.10 or later
- Docker, to build the image

## Getting started

```sh
docker run -d --name nats -p 4222:4222 nats -js   # a local NATS server with JetStream
cp .env.example .env
uv sync
uv run python -m app                              # run the worker; probes on http://localhost:8080
```

Try it, from another terminal:

```sh
uv run python -m app enqueue process_item '{"item": {"id": "42", "name": "Widget", "quantity": 2}}'
```

The worker writes one log line for the task (`item processed`) and one for its execution (`task`).

## Development

| Task | Command |
|---|---|
| Lint | `uv run ruff check .` |
| Format check | `uv run ruff format --check .` |
| Type check | `uv run mypy .` |
| Tests | `uv run pytest` |

Tests need no NATS server: tasks run on TaskIQ's in-memory broker, and the worker loop on an in-process broker
with acknowledgements.

## Configuration

All configuration comes from environment variables.

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | Port for the probes and the metrics |
| `LOG_LEVEL` | `INFO` | Log level |
| `NATS_URL` | required | NATS URL, e.g. `nats://user:pass@host:4222`; several servers comma-separated |
| `NATS_CONNECT_TIMEOUT_S` | `3` | Timeout of one connection attempt |
| `NATS_STREAM` | `tasks` | JetStream stream holding the tasks and the dead letters, created if missing |
| `NATS_SUBJECT` | `tasks` | Subject tasks are published on |
| `NATS_DEAD_LETTER_SUBJECT` | `tasks.dead` | Subject of the messages kept aside: failed every attempt, invalid or unreadable |
| `NATS_CONSUMER` | `worker` | Durable consumer shared by every instance, created if missing |
| `WORKER_CONCURRENCY` | `10` | Tasks run at the same time, per instance |
| `TASK_TIMEOUT_S` | `60` | Longest run of a task before it fails; a task may set its own with the `timeout` label |
| `MAX_RETRIES` | `3` | Retries after a failed first attempt, before the task is dead-lettered |
| `SHUTDOWN_TIMEOUT_S` | `20` | After `SIGTERM`, grace period for in-flight tasks |

The worker connects to NATS at startup and after an outage, waiting as long as it takes: `/readyz` answers
`503` meanwhile. After `SIGTERM`, the process exits within `SHUTDOWN_TIMEOUT_S`.

## How tasks are delivered

- **Never lost.** A task is a message in a JetStream stream, read by a durable pull consumer that every instance
  shares: each task goes to one instance. The message is acknowledged only after the task has run (or been
  retried, or dead-lettered). If an instance stops mid-task, JetStream delivers the task again after
  `TASK_TIMEOUT_S` plus 30 seconds. A task can therefore run more than once: make tasks idempotent.
- **Retries.** A task that raises (or exceeds its timeout) is published again at once, with its `attempt` label
  incremented, up to `MAX_RETRIES` times. A task that may fail for a while (a service being down) should wait
  inside, within its timeout, rather than rely on retries.
- **Dead letters.** After its last attempt, the task is published on `NATS_DEAD_LETTER_SUBJECT`, in the same
  stream, with the error in an `error` header. So are, at once, a message with invalid arguments (`invalid
  fields: …`), a message that is not a task message and one that names an unknown task: nothing is dropped,
  and no message content reaches the logs. No consumer reads that subject, so dead letters stay until
  someone looks at them. Inspect them with the [NATS CLI](https://github.com/nats-io/natscli):
  `nats stream view tasks --subject tasks.dead`. To run one again, publish its payload on `NATS_SUBJECT` (it gets a
  single attempt); delete it with `nats stream rmm`.
- **Concurrency.** An instance fetches a new task only when one of its `WORKER_CONCURRENCY` slots is free;
  scale out with more instances.

## Sending tasks

A task takes typed arguments, here a Pydantic model. It travels as JSON and the worker gets the model back,
validated: an invalid message is dead-lettered at once, without retries (the logs name the fields in error,
never their values).

From Python code that shares this project's tasks:

```python
from app.broker import broker
from app.tasks import Item, process_item

await broker.startup()  # once per process
await process_item.kiq(Item(id="42", name="Widget", quantity=2))
```

On the wire, the message's arguments are plain JSON:

```json
{"args": [{"id": "42", "name": "Widget", "quantity": 2, "tags": []}], "kwargs": {}}
```

From the command line, or from the image:

```sh
python -m app enqueue process_item '{"item": {"id": "42", "name": "Widget", "quantity": 2}}'
```

## Container image

```sh
docker build -t starter-taskiq .
docker run --read-only --tmpfs /tmp --env-file .env.example -p 8080:8080 starter-taskiq
```

The image is distroless (`gcr.io/distroless/python3-debian13`): Python 3.13 and its libraries, no shell and no
package manager, running as the non-root `nonroot` user (uid 65532). The image runs on a read-only filesystem.

The same image runs the other command:

| Command | Purpose |
|---|---|
| `python -m app enqueue <task> '<json kwargs>'` | Send one task, e.g. for a manual run |

## Endpoints

| Path | Purpose |
|---|---|
| `/healthz` | Liveness: the process responds |
| `/readyz` | Readiness: connected to NATS and consuming; `503` as soon as shutdown starts |
| `/metrics` | Prometheus metrics: runtime, `tasks_total`, `task_duration_seconds`, `tasks_dead_lettered_total` |

Every log line written while a task runs carries its `task_id`, kept across retries.

## Project layout

```
app/
├── __main__.py      Entrypoint: worker, enqueue
├── worker.py        Consumer loop, HTTP server and graceful shutdown, in one process
├── broker.py        NATS JetStream broker: stream, consumer, dead letters
├── tasks.py         Tasks (process_item is an example)
├── middleware.py    Task id on logs, timeout, execution log and metrics, retries
├── health.py        Liveness and readiness probes, metrics endpoint
├── metrics.py       Prometheus metrics
├── config.py        Settings, from the environment
└── logs.py          JSON logging
tests/
```

Replace the `process_item` task with your own, keeping its conventions. The other modules implement the runtime
contracts and are meant to stay.

# Scheduled tasks module

Short commands run on a schedule, over the [Python base](../python/): each one starts, does its work through
the project's business code (`common/`) and exits. The platform schedules them (a Kubernetes CronJob per
task); the module gives every task the same contract, with no framework.

The module is the package `tasks/` and its tests `tests/tasks/`; [`module.toml`](module.toml) says how
[`scripts/compose.py`](../scripts/compose.py) adds it to a project:

```sh
python3 scripts/compose.py ../shop fastapi tasks     # api/ and tasks/
```

## A task

A task is a module of `tasks/jobs/`, named after it, with an async `run()` that takes no argument and raises
on failure:

```python
# tasks/jobs/purge_sessions.py
from common import db
from common.services import sessions


async def run() -> None:
    async with db.sessionmaker()() as session, session.begin():
        await sessions.purge_expired(session)
```

`run()` may run again after a failure, or twice in a row: a second run does no harm (idempotent).

## Running one

```sh
cp .env.example .env
uv sync --extra tasks
uv run python -m tasks example     # runs tasks/jobs/example.py
uv run python -m tasks migrate     # applies the database migrations
uv run python -m tasks             # loads every task and lists them (the image's default command)
```

The runner gives every run:

- one run at a time: a PostgreSQL advisory lock on the task's name, when the database is configured (the
  platform never starts two runs at once; the lock also covers manual runs);
- a bounded duration: `TASK_TIMEOUT_S`, after which the run stops and fails;
- one JSON log line with its outcome and duration, every line of the run carrying its `task_id`;
- an exit code: `0` done, `1` failed or timed out, `2` unknown task, `3` another run holds the lock.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `TASK_TIMEOUT_S` | `300` | Longest run, in seconds |

The shared variables (database, buckets, logs) are in the base's README.

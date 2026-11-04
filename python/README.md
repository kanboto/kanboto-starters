# Python starter

The base of a Python project with one or more components (an HTTP API, a background worker...), in a single
project, a single lock and a single image. Python 3.13, uv, SQLAlchemy (async) and PostgreSQL.

This folder alone holds what every component shares. Components come from modules
([`fastapi/`](../fastapi/), [`taskiq/`](../taskiq/)), added with
[`scripts/compose.py`](../scripts/compose.py):

```sh
python3 scripts/compose.py ../shop fastapi taskiq     # api/ and worker/, from the root of kanboto-starters
```

## Requirements

- Python 3.13 and [uv](https://docs.astral.sh/uv/)
- PostgreSQL 15 or later
- Docker, to build the image

## Getting started

In a composed project:

```sh
cp .env.example .env               # then set DATABASE_URL, if the project uses a database
uv sync --all-extras
uv run python -m api migrate       # apply database migrations (any component has the command)
uv run python -m api               # one component: serve the API on http://localhost:8080
```

## Development

| Task | Command |
|---|---|
| Lint | `uv run ruff check .` |
| Format check | `uv run ruff format --check .` |
| Type check | `uv run mypy .` |
| Tests (SQLite) | `uv run pytest` |
| Tests (PostgreSQL) | `TEST_DATABASE_URL=postgresql+asyncpg://… uv run pytest` |

The `database` fixture (`tests/conftest.py`) builds a fresh database with the migrations, so migrations are
exercised on every run. Run the suite against PostgreSQL before merging: it is what production uses.

## Dependencies

`pyproject.toml` lists the dependencies of `common/` and, as optional dependencies, one extra per kind of
component (`api`, `worker`); `uv.lock` resolves them all. The image installs only the extras of its
components (`uv sync --locked --no-dev --no-install-project --extra api ...` in the `Dockerfile`).

## Configuration

All configuration comes from environment variables, each one in `.env.example`. Shared by every component:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | unset | PostgreSQL URL, e.g. `postgresql+asyncpg://user:pass@host:5432/db`; no database when unset |
| `DATABASE_READ_URL` | unset | Read replica URL; reads go to the primary when unset |
| `LOG_LEVEL` | `INFO` | Log level |
| `DB_CONNECT_TIMEOUT_S` | `3` | Timeout to open a database connection |
| `DB_STATEMENT_TIMEOUT_S` | `10` | Timeout for a single SQL statement, cancelled by the server |
| `DB_POOL_SIZE` | `5` | Connections kept open per instance |
| `DB_MAX_OVERFLOW` | `5` | Extra connections allowed under load, per instance |
| `DB_POOL_TIMEOUT_S` | `5` | Wait for a free connection before failing the request |
| `DB_POOL_RECYCLE_S` | `1800` | Replace connections older than this |
| `READY_TIMEOUT_S` | `2` | Timeout of the readiness check (database and buckets) |
| `S3_ENDPOINT` | `http://localhost:3900` | S3 server |
| `S3_REGION` | `garage` | S3 region |
| `S3_PRIVATE_BUCKET` | unset | Private bucket, read through the API only; none when unset |
| `S3_PRIVATE_ACCESS_KEY_ID`, `S3_PRIVATE_SECRET_ACCESS_KEY` | unset | Its key |
| `S3_PUBLIC_BUCKET` | unset | Public bucket, served as-is at `S3_PUBLIC_URL`; none when unset |
| `S3_PUBLIC_ACCESS_KEY_ID`, `S3_PUBLIC_SECRET_ACCESS_KEY` | unset | Its key |
| `S3_PUBLIC_URL` | unset | Where the public bucket is served (`https://…`, no trailing slash) |
| `S3_CONNECT_TIMEOUT_S` | `3` | Timeout to open a connection to S3 |
| `S3_TIMEOUT_S` | `30` | Timeout of a single S3 request |

Each component adds its own (see its module's README). The database is optional: without `DATABASE_URL`, the
readiness probes skip it and the commands that need it (`migrate`, `cleanup`) stop with exit code 1. Pools
are opened on first use, so a component that never touches the database opens none. Size them so that `instances × (DB_POOL_SIZE + DB_MAX_OVERFLOW)`
stays under each database's connection limit, every component included.

Files go to object storage (`common/storage.py`), never to the read-only filesystem: a `private` bucket for
what only the API serves, a `public` one for what anyone may load at `S3_PUBLIC_URL/<key>`, with random keys
(`storage.new_key()`). Both are optional like the database: an unset bucket name means no bucket, and the
readiness probes skip it.

## Container image

```sh
docker build -t shop .
docker run --read-only --tmpfs /tmp --env-file .env.example -p 8080:8080 shop            # the first component
docker run --read-only --tmpfs /tmp --env-file .env.example -p 8080:8080 shop worker     # another one
```

The image is distroless (`gcr.io/distroless/python3-debian13`): Python 3.13 and its libraries, no shell and no
package manager, running as the non-root `nonroot` user (uid 65532), on a read-only filesystem. Its entrypoint
is `python -m`: each component runs as `python -m <package>`, which Kubernetes sets per component.

## Project layout

```
common/              Shared by every component
├── config.py        Shared settings, from the environment
├── db.py            Engines, pools, sessions, Base, UTC dates
├── models/          Every table of the project (items is an example)
├── services/        Business rules (items is an example)
├── schema.py        Migrations, for each component's `migrate` command
├── logs.py          JSON logging, request id and task id on every line
└── metrics.py       Prometheus exposition: runtime metrics and a component's registry
migrations/          Alembic migrations, over common/models
tests/
├── conftest.py      Fresh database per test
├── common/          Tests of common/
└── <package>/       Tests of each component
<package>/           One package per component (api/, worker/...)
```

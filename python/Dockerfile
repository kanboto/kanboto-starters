# Production image: multi-stage, runtime dependencies only, non-root user, base images pinned by digest.
# Distroless runtime: Python 3.13 and its libraries, no shell, no package manager.
# One image for every component of the project: `scripts/compose.py` adds each module's extra to `uv sync`
# and its package after the last COPY of the build stage.
FROM ghcr.io/astral-sh/uv:0.12.24@sha256:3af4716e991d6956a41e573eab705d0ee08500cd829ed30293eb8472f372c65a AS uv

# The runtime image, as root: the virtual environment is built with the very interpreter it runs on. No shell
# in distroless, hence the exec form of RUN.
FROM gcr.io/distroless/python3-debian13:latest@sha256:5bac3c3ab33426c460db63504cd1a267b3326b9f804d21c63359492858d1beda AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PYTHON=/usr/bin/python3.13
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN ["uv", "sync", "--locked", "--no-dev", "--no-install-project"]
COPY common ./common
COPY migrations ./migrations
COPY alembic.ini ./

FROM gcr.io/distroless/python3-debian13:nonroot@sha256:c3ed2b61f3c4e410685565ceb3c818197b552832521b39d53eca5d2d9d0dc1e1
WORKDIR /app
COPY --from=build --chown=root:root /app /app
ENV PATH=/app/.venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# The `nonroot` user of distroless images.
USER 65532
EXPOSE 8080
# Each component runs as `python -m <package>`: Kubernetes sets the command per component, and the default is
# the first module's.
ENTRYPOINT ["/app/.venv/bin/python", "-m"]
CMD ["api", "serve"]

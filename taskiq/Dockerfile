# Production image: multi-stage, runtime dependencies only, non-root user, base images pinned by digest.
# Distroless runtime: Python 3.13 and its libraries, no shell, no package manager.
FROM ghcr.io/astral-sh/uv:0.12.24@sha256:3af4716e991d6956a41e573eab705d0ee08500cd829ed30293eb8472f372c65a AS uv

# The runtime image, as root: the virtual environment is built with the very interpreter it runs on. No shell
# in distroless, hence the exec form of RUN.
FROM gcr.io/distroless/python3-debian13:latest@sha256:931a490beb37db6a1d137ad11ed47ae4c0d4741ca5c2285818b49e9a8ee11c56 AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PYTHON=/usr/bin/python3.13
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN ["uv", "sync", "--locked", "--no-dev", "--no-install-project"]
COPY app ./app

FROM gcr.io/distroless/python3-debian13:nonroot@sha256:83aa8d4f74a4d7f7cf2d472054139bef71a927b76c680c0f2e1021d6b1d6d732
WORKDIR /app
COPY --from=build --chown=root:root /app /app
ENV PATH=/app/.venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# The `nonroot` user of distroless images.
USER 65532
EXPOSE 8080
ENTRYPOINT ["/app/.venv/bin/python", "-m", "app"]
CMD ["worker"]

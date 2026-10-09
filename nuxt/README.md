# Nuxt starter

A minimal, production-ready web frontend built with Nuxt, rendered on the server (SSR). It ships with everything
a production frontend needs and nothing it does not: runtime configuration, probes, Prometheus metrics,
graceful shutdown, JSON logs and a hardened image. Its one page shows the application's name and "Hello world".

## Requirements

- Node.js 24 (`.nvmrc`), 24.15 or later, and npm
- Docker, to build the image

## Getting started

```sh
cp .env.example .env               # read by the development server only
npm ci
npm run dev                        # serve on http://localhost:8080, with hot reload
```

Or the production build, as the image runs it (it reads the environment, not `.env`):

```sh
npm run build
PORT=8080 npm start                # serve on http://localhost:8080
```

## Development

| Task | Command |
|---|---|
| Lint | `npm run lint` |
| Type check | `npm run typecheck` |
| Tests | `npm test` |
| Build | `npm run build` |

Tests build the application and run the production server on `127.0.0.1`, as the image does: they check the
server-side rendered page, the probes, the metrics, the logs and the graceful shutdown. They need no network.

## Configuration

All configuration comes from environment variables, read when the server starts: one build serves every
environment.

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | Port for the application, the probes and the metrics; set by the image (Nitro's own default is `3000`) |
| `LOG_LEVEL` | `info` | Log level: `debug`, `info`, `warn` or `error` |
| `DRAIN_DELAY_S` | `5` | After `SIGTERM`, time readiness fails while traffic is still served |
| `SHUTDOWN_TIMEOUT_S` | `20` | Then, grace period for in-flight requests |
| `NUXT_PUBLIC_APP_NAME` | `My app` | Application name, shown on the page and in its title |
| `NUXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Address of the backend API, used by `useApi()` on the server and in the browser |
| `NUXT_PUBLIC_API_TIMEOUT_S` | `10` | Timeout of a call to the backend API |

The application's settings are Nuxt's [runtime config](https://nuxt.com/docs/guide/going-further/runtime-config):
each key of `runtimeConfig` in `nuxt.config.ts` holds a default, overridden at runtime by its `NUXT_*` variable
(`public.apiBaseUrl` by `NUXT_PUBLIC_API_BASE_URL`). Keys under `public` reach the browser, through the page:
never put a secret there; a server-only key goes at the top level of `runtimeConfig`. The process settings
(`PORT`, `LOG_LEVEL`, `DRAIN_DELAY_S`, `SHUTDOWN_TIMEOUT_S`) are read from the environment by the server.

After `SIGTERM`, the process exits within `DRAIN_DELAY_S + SHUTDOWN_TIMEOUT_S`.

## Graceful shutdown

The server is Nitro's `node-server`. On its shutdown signal, Nitro stops accepting connections, closes idle
ones, waits for in-flight requests, runs its `close` hooks and exits with code 0. This starter adds the drain
phase Nitro lacks: on `SIGTERM`, `/readyz` answers `503` at once while traffic is still served for
`DRAIN_DELAY_S`, so that load balancers stop sending new requests before the server stops accepting them. Nitro's
shutdown then runs, with `SHUTDOWN_TIMEOUT_S` as its grace period. A second `SIGTERM`, or `SIGINT` (Ctrl-C),
skips the drain. Nitro's `NITRO_SHUTDOWN_*` variables are set by the application from these two; do not set them.

## Container image

```sh
docker build -t starter-nuxt .
docker run --read-only --tmpfs /tmp --env-file .env.example -p 8080:8080 starter-nuxt
```

The image is distroless (`gcr.io/distroless/nodejs24-debian13`): Node.js 24, no shell and no package manager,
running as the non-root `nonroot` user (uid 65532). It holds only the server built by `nuxt build` (`.output/`),
which bundles the few dependencies it uses. The image runs on a read-only filesystem.

## Endpoints

| Path | Purpose |
|---|---|
| `/` | Home page, rendered on the server |
| `/healthz` | Liveness: the server responds |
| `/readyz` | Readiness: `503` as soon as shutdown starts |
| `/metrics` | Prometheus metrics: Node.js runtime, `http_requests_total`, `http_request_duration_seconds` |

Every response carries an `X-Request-ID` (the caller's, or a generated one), also present on every log line
written while handling the request. Each request gets one log line and is counted in the metrics, labelled by
its route pattern (`/`, `/items/:id()`), never by its raw path: `/_nuxt/**` for what the build produces, `static` for a file of `public/`,
`unmatched` for a page that does not exist. Probes and metrics are neither logged nor counted. Logs never hold
a query string or a request body.

## Project layout

```
app/
├── app.vue                     Root component: title, base styles
├── pages/index.vue             Home page (an example: replace it with your own)
├── composables/useApi.ts       Client for the backend API, configured at runtime
└── plugins/route-pattern.server.ts   Hands the matched page's pattern to the server, for logs and metrics
server/
├── routes/                     healthz, readyz and metrics endpoints
├── plugins/observability.ts    Request id, request log and metrics, error log, JSON console
├── plugins/shutdown.ts         Drain phase and Nitro's graceful shutdown
└── lib/                        Settings, JSON logging, Prometheus metrics, process state
shared/types/                   Types shared by the app and the server
nuxt.config.ts                  Nuxt configuration and runtime config defaults
tests/
```

Replace the home page with your own, keeping its conventions. The `server/` modules and the route-pattern
plugin implement the runtime contracts and are meant to stay.

`package.json` overrides `simple-git`, a dependency of Nuxt DevTools (turned off here), with a release that fixes
a known vulnerability; drop the override once Nuxt depends on a fixed release.

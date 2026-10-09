# AGENTS.md

<!-- kanboto:start -->
## Kanboto rules (Nuxt stack)

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
  `useApi()` of `app/composables/useApi.ts`, never a client created per request.
- `GET /healthz` (alive), `GET /readyz` (dependencies reachable, `503` during shutdown) and `GET /metrics`
  (Prometheus) stay at the root path, on `PORT`, outside `/api` and `/internal`.
- Graceful shutdown on `SIGTERM` within `SHUTDOWN_TIMEOUT_S`: in-flight work completes.
- JSON logs on stdout, one line per event.
- Multi-stage image, non-root user, base images pinned by digest.

### Commands

- Install: `npm ci`
- Lint, format, types: `npm run lint`, `npm run typecheck`
- Tests: `npm test`
<!-- kanboto:end -->

## This starter

- `app/` is the Vue application, rendered on the server: `app/pages/` holds the pages (file-based routing),
  `app/app.vue` the root component, `app/composables/` the composables. `pages/index.vue` is an example page:
  replace it with your domain's, keeping its conventions (sober plain CSS, no secret in the page).
- The application's name comes from `NUXT_PUBLIC_APP_NAME` (`runtimeConfig.public.appName`), shown on the home
  page and as the page title. When scaffolding a project from this starter, set its default in
  `nuxt.config.ts` and its value in `.env.example` to the project's name.
- Configuration lives in `runtimeConfig` (`nuxt.config.ts`): each key holds a default, overridden at runtime by
  its `NUXT_*` variable, listed in `.env.example` and in the README. Read it with `useRuntimeConfig()`, never
  `process.env` and never a value baked in at build time: one image serves every environment. Keys under
  `public` reach the browser; a secret goes at the top level of `runtimeConfig`, read on the server only.
- The backend API is called through `useApi()` (`app/composables/useApi.ts`): its address and timeout come
  from the runtime config. Each other service gets its own `NUXT_*` variable.
- `server/` is the Nitro server. `server/routes/` holds the probes and the metrics endpoint;
  `server/plugins/observability.ts` (request id, request log and metrics, error log, JSON console),
  `server/plugins/shutdown.ts` (drain, then Nitro's graceful shutdown), `server/lib/` and
  `app/plugins/route-pattern.server.ts` implement the runtime contracts; keep them.
- Server code logs through `log()` (`server/lib/log.ts`), one JSON line per event, with neither personal data,
  query string nor body. Metrics are labelled by route pattern, never by raw path.
- Nothing is written to disk outside `/tmp`: the image runs on a read-only filesystem.
- Commands: `npm ci`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.

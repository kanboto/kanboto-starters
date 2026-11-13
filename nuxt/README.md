# Nuxt starter

A minimal, production-ready web frontend built with Nuxt, rendered on the server (SSR). It ships with everything
a production frontend needs and nothing it does not: runtime configuration, probes, Prometheus metrics,
graceful shutdown, JSON logs, a hardened image, what search engines need (robots.txt, sitemap,
structured data, canonical addresses), design tokens and a share image for every page. Its one page shows the
application's name and "Hello world".

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
server-side rendered page, the probes, the metrics, the logs and the graceful shutdown. Only the build uses the
network, to fetch the design's fonts. `tests/seo.test.ts` runs it as in production and checks every page of
the sitemap: title, description, canonical address, one heading, structured data, share image.

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
| `NUXT_PUBLIC_S3_PUBLIC_URL` | empty | Where the public bucket is served; `useFileUrl(key)` builds a file's address from it. The frontend only reads it: files are sent through the API |
| `NUXT_PUBLIC_SITE_URL` | `http://localhost:8080` | Public address of the site: canonical addresses, sitemap, structured data |
| `NUXT_PUBLIC_SITE_INDEXABLE` | `false` | `true` lets search engines index the site; set in production only |
| `NUXT_PUBLIC_SITE_DEFAULT_LOCALE` | `en` | Language of the pages (`<html lang>`, `og:locale`) |
| `NUXT_APP_SECRET` | a development value | Signs the share image addresses: at least 32 characters, stable, one per environment. Without it, share images answer `500` |

The application's settings are Nuxt's [runtime config](https://nuxt.com/docs/guide/going-further/runtime-config):
each key of `runtimeConfig` in `nuxt.config.ts` holds a default, overridden at runtime by its `NUXT_*` variable
(`public.apiBaseUrl` by `NUXT_PUBLIC_API_BASE_URL`). Keys under `public` reach the browser, through the page:
never put a secret there; a server-only key goes at the top level of `runtimeConfig`. The process settings
(`PORT`, `LOG_LEVEL`, `DRAIN_DELAY_S`, `SHUTDOWN_TIMEOUT_S`) are read from the environment by the server.

After `SIGTERM`, the process exits within `DRAIN_DELAY_S + SHUTDOWN_TIMEOUT_S`.

## Search engines

`@nuxtjs/robots`, `@nuxtjs/sitemap` and `nuxt-schema-org` read the `site` keys of the runtime config, so the
same image is indexable in production and hidden everywhere else. While `NUXT_PUBLIC_SITE_INDEXABLE` is not
`true`, `robots.txt` disallows everything and every page carries `X-Robots-Tag: noindex, nofollow`.

- Each page sets its own title and description with `useSeoMeta()`; `app/app.vue` adds the site name, the
  canonical address (the page's path on `NUXT_PUBLIC_SITE_URL`, without its query string), the language and the
  Open Graph defaults.
- `/sitemap.xml` lists the pages found in `app/pages/`. Pages built from data are added through a
  sitemap source (see the `@nuxtjs/sitemap` documentation).
- Pages under `/app/` are the signed-in area: rendered in the browser and never indexed (`routeRules`).
- Every page carries the structured data of the site and of the page (`WebSite`, `WebPage`); add others with
  `useSchemaOrg()`.

## Design

Every style value (colours, fonts, sizes, spacing, radii, shadows, durations) is a CSS variable of
`app/assets/design/tokens.css`, loaded on every page and used through `var(--…)`; `tokens.json` holds the same
values in the [Design Tokens](https://www.designtokens.org/) format. The names are fixed; the values start
neutral and are replaced by the project's visual direction.

- Fonts: the first family of `font.display` and `font.body` that is not a system font is fetched from Google
  Fonts at build time by `@nuxt/fonts`, with the weights of `fontWeight`, and served by the site itself: no
  request to Google at runtime.
- Share image: `nuxt-og-image` draws each page's `og:image` (1200×630) from
  `app/components/OgImage/Page.takumi.vue`: the top of the site in a window, with the page's title and
  description, in the colours and fonts of `tokens.json`. Takumi renders it on the server, without a browser.
  Its addresses are signed with `NUXT_APP_SECRET`; an unsigned address is refused. A page changes the image's
  text with `defineOgImage('Page', { title, description })`.
- The tab icon (`/favicon.svg`) is the name's initial in the action colours.

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
| `/robots.txt`, `/sitemap.xml` | For search engines, built at runtime from the site's address |
| `/_og/…` | Share images, drawn on demand from signed addresses |
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
├── app.vue                     Root component: title, canonical address, language, share image, base styles
├── assets/design/              Design tokens: tokens.css (used by every style), tokens.json (fonts, share image)
├── components/OgImage/         Template of the share image
├── pages/index.vue             Home page (an example: replace it with your own)
├── composables/useApi.ts       Client for the backend API, configured at runtime
└── plugins/route-pattern.server.ts   Hands the matched page's pattern to the server, for logs and metrics
server/
├── routes/                     healthz, readyz and metrics endpoints
├── plugins/observability.ts    Request id, request log and metrics, error log, JSON console
├── plugins/shutdown.ts         Drain phase and Nitro's graceful shutdown
├── plugins/site.ts             The application's name as the site's name, for search engines
└── lib/                        Settings, JSON logging, Prometheus metrics, process state
shared/types/                   Types shared by the app and the server
nuxt.config.ts                  Nuxt configuration and runtime config defaults
tests/
```

Replace the home page with your own, keeping its conventions. The `server/` modules and the route-pattern
plugin implement the runtime contracts and are meant to stay.

`package.json` overrides `simple-git`, a dependency of Nuxt DevTools (turned off here), with a release that fixes
a known vulnerability; drop the override once Nuxt depends on a fixed release.

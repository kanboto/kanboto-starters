# AGENTS.md

<!-- kanboto:start -->
## Kanboto rules (Nuxt stack)

This section is maintained by Kanboto: do not edit it by hand, Kanboto updates it through pull requests. The
CI (`kanboto-ci-*`) enforces these rules; a pull request that breaks them does not pass.

### Runtime

- Configuration through environment variables only, each one listed in `.env.example`; no hard-coded value, no
  configuration file in the image. Each service the application calls has its own variable
  (`BILLING_API_URL`).
- Values in `.env.example` are development values. A variable that has no valid default outside development
  gets a comment line just above it: `# secret` for a credential, whose example value is never reused,
  `# required` for any other value set per environment (an external service's URL, an account identifier).
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

### Search engines

- Every public page is rendered on the server and sets its own `title`, `description`, `ogTitle` and
  `ogDescription` through `useSeoMeta()`, with exactly one `h1`; `app/app.vue` adds what every page shares
  (site name, canonical address, language).
- The signed-in area lives under `/app/`: rendered in the browser, never indexed, left out of the sitemap. A
  public page renders without a session.
- Only production is indexable, decided by `NUXT_PUBLIC_SITE_INDEXABLE`; never force indexing in code. Public
  pages built from data (one per record) are added to the sitemap through a sitemap source.
- Links between pages are `<NuxtLink>` with descriptive text; every image has an `alt`, a `width` and a
  `height`.
- `tests/seo.test.ts` checks every page of the sitemap: extend it, never skip a page to make it pass.

### Design

- Every style value (colour, font, size, spacing, radius, shadow, duration) comes from
  `app/assets/design/tokens.css` through `var(--…)`; never a literal value outside that file. The variable
  names are fixed by Kanboto: a value that is missing is added to `tokens.css` and `tokens.json` together.
- `tokens.css` and `tokens.json` hold the same values: `tokens.json` feeds the fonts (fetched at build time
  from Google Fonts, never at runtime) and the share image. When `.kanboto/design/` holds the project's visual
  direction, its `tokens.css`, `tokens.json` and charter prevail over them.
- Every public page has a share image (`og:image`, 1200×630) drawn by `app/components/OgImage/` from its title
  and description; a page changes them with `defineOgImage()`. The template uses token values only.

### Commands

- Install: `npm ci`
- Lint, format, types: `npm run lint`, `npm run typecheck`
- Tests: `npm test`
<!-- kanboto:end -->

## This starter

- `app/` is the Vue application, rendered on the server: `app/pages/` holds the pages (file-based routing),
  `app/app.vue` the root component, `app/composables/` the composables. `pages/index.vue` is an example page:
  replace it with your domain's, keeping its conventions (plain CSS on the design tokens, no secret in the
  page).
- The application's name comes from `NUXT_PUBLIC_APP_NAME` (`runtimeConfig.public.appName`), shown on the home
  page and as the page title. When scaffolding a project from this starter, set its default in
  `nuxt.config.ts` and its value in `.env.example` to the project's name.
- Configuration lives in `runtimeConfig` (`nuxt.config.ts`): each key holds a default, overridden at runtime by
  its `NUXT_*` variable, listed in `.env.example` and in the README. Read it with `useRuntimeConfig()`, never
  `process.env` and never a value baked in at build time: one image serves every environment. Keys under
  `public` reach the browser; a secret goes at the top level of `runtimeConfig`, read on the server only.
- Search engines: `@nuxtjs/robots`, `@nuxtjs/sitemap` and `nuxt-schema-org` read `runtimeConfig.public.site`
  (`NUXT_PUBLIC_SITE_*`). Each page sets its title and description with `useSeoMeta()`; `app/app.vue` adds the
  canonical address, the language and the Open Graph defaults, `server/plugins/site.ts` the site's name. When
  scaffolding, set `NUXT_PUBLIC_SITE_DEFAULT_LOCALE` to the language of the pages.
- Design: `app/assets/design/tokens.css` (every style reads it) and `tokens.json` (read by `nuxt.config.ts` for
  the fonts, by the share image template and by the tab icon). The share image is
  `app/components/OgImage/Page.takumi.vue`, declared once in `app/app.vue` (`defineOgImage('Page')`); Takumi
  lays it out like flexbox, with inline styles. Its addresses are signed with `NUXT_APP_SECRET`
  (`runtimeConfig.appSecret`).
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

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

### Pages

- A page is a document, `app/content/pages/<slug>.json`, rendered by `<KbPage :page>`; its route file only
  loads it with `usePageContent()` and sets `useSeoMeta()` from its `title` and `description`.
- A block shown on several pages (navigation, footer, a shared call to action) is written once in
  `app/content/shared.json`; a page holds only `{"ref": "<id>"}` at its place and `usePageContent()` resolves
  it. Change the shared file, never copy a shared block into a page.
- When `.kanboto/pages/` holds a page validated in Kanboto, its document is copied as is: block order,
  variants, settings, texts and images come from it. Change the document, never rebuild a section by hand in a
  page.
- Every section of `app/components/blocks/` keeps `data-kb-block` and `data-kb-type` on its root,
  `data-kb-field` on each element showing a field and `data-kb-item` on each list entry, in the
  server-rendered HTML: Kanboto reads them back on the deployed page.
- An image of a page is committed as received, at its original definition, under `public/`; the image block
  serves it as WebP at the width of each screen (`NuxtImg`). Never convert, resize or compress an image by
  hand, and never replace the image block with a plain `img`.
- The site's logo is `app/assets/brand/logo.svg`, copied as received from `.kanboto/design/`; the navigation
  shows it by itself (`kb:logo`, provided in `app.vue`). Never redraw it, inline it in a component or replace
  it with an image.
- Every field is optional: a missing field renders no element. Exactly one `h1` per page, designated by
  `KbPage`.
- `app/components/blocks/` imports only its own files (relative imports, explicit `vue` imports, no Nuxt
  composable); its only tie to Nuxt is `NuxtLink` inside `KbLink`.
- Block styles use the semantic colour classes mapped to the design tokens, `rounded-(--radius-*)`,
  `shadow-(--shadow-*)` and container variants (`@3xl:`); never a viewport variant, `dark:`, or a literal
  colour or size.
- A block the library lacks is a `custom` block: implement it as a new section wrapped in `KbSection` and
  registered in `KbPage`, never as markup in the page.
- Application blocks (`list`, `table`, `detail`, `form`) get their real data by building the block's `props`
  from `useApi()`, with loading, empty and error states; the document's items are examples.

### Commands

- Install: `npm ci`
- Lint, format, types: `npm run lint`, `npm run typecheck`
- Tests: `npm test`
<!-- kanboto:end -->

## This starter

- `app/` is the Vue application, rendered on the server: `app/pages/` holds the pages (file-based routing),
  `app/app.vue` the root component, `app/composables/` the composables.
- Pages are data. A page is a document of `app/content/pages/<slug>.json` (`slug`, `path`, `title`,
  `description`, `blocks`), rendered block by block by `<KbPage :page>`; its route file only loads it
  (`usePageContent('<slug>')`) and sets `useSeoMeta()` from its title and description. `pages/index.vue`
  (`home.json`) and `pages/app/items.vue` (`app-items.json`) are the examples: replace their content, keep the
  pattern. `all-blocks.json` holds every block for the tests and is never routed.
- A block several pages show lives once in `app/content/shared.json` (`blocks`, by id); a page holds
  `{ "ref": "<id>" }` at its place and `usePageContent()` resolves it. Never copy a shared block into a page.
- To add a page: write `app/content/pages/<slug>.json`, add `app/pages/<path>.vue` on the model of
  `pages/index.vue`, and wire the data of its application blocks (list, table, detail) by building the block's
  `props` from `useApi()` instead of the document's examples. Layout, order and variants come from the
  document: do not rebuild a section by hand in the page.
- The block library is `app/components/blocks/`: one section per block type (`sections/Kb*.vue`), the shadcn-vue
  primitives they use (`ui/`), `KbPage`, `KbLink`, `KbImage` and `blocks.css`, which sets shadcn's variables from
  the design tokens under `.kb-root`. Kanboto copies this folder as is into its page workshop: inside it, only
  relative imports between its files, explicit `vue` imports, no Nuxt composable (`KbLink` resolves `NuxtLink`),
  no value outside the tokens. Sections use shadcn's colour classes (`bg-background`, `text-muted-foreground`,
  `bg-primary`…), `rounded-(--radius-*)`, `shadow-(--shadow-*)` and container variants (`@3xl:`), never
  viewport ones (`md:`), never `dark:`.
- A section keeps what the workshop reads: `data-kb-block` and `data-kb-type` on its root (through
  `KbSection`), `data-kb-field` on each element that shows a field, `data-kb-item` on each entry of a list.
  A missing field renders nothing; the title is `h1` only in the block `KbPage` designates (`useHeading()`).
- A block the block library does not have is a `custom` block, shown by `KbCustom` with its description. To build it:
  write its component in `app/components/blocks/sections/` on the model of the others (wrapped in `KbSection`,
  same markers), then register it under its type in the `SECTIONS` map of `KbPage.vue` and give the block that
  type in the page document.
- More shadcn-vue primitives: `npx shadcn-vue@latest add <name>` (`components.json` points to the library's `ui/`),
  then rewrite the generated imports as relative ones and drop `dark:` classes. Icons named in a page document
  come from the allowlist of `blocks/lib/icons.ts`.
- Kanboto's page workshop frames the running site to point at blocks: `app/plugins/kanboto-inspect.client.ts`
  and `server/plugins/frame.ts`, both off unless `NUXT_PUBLIC_KANBOTO_INSPECT_ORIGIN` is set (outside
  production only); keep them.
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
- Design: `app/assets/design/tokens.css` (every style reads it; `app/assets/css/tailwind.css` maps Tailwind's
  theme onto shadcn's variables and holds no value) and `tokens.json` (read by `nuxt.config.ts` for
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

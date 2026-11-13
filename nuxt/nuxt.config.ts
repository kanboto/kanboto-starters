// Application configuration. Values under `runtimeConfig` are defaults: each one is overridden at runtime by
// its `NUXT_*` environment variable (`public.appName` by `NUXT_PUBLIC_APP_NAME`), so one build serves every
// environment. Nothing here is read from the environment at build time.
import tokens from './app/assets/design/tokens.json'

// System and generic families are never downloaded: only the first other family of the display and body stacks.
const SYSTEM = /^(serif|sans-serif|monospace|cursive|fantasy|system-ui|ui-\w+|-apple-system|BlinkMacSystemFont)$/

/** The design's fonts, served from the site itself: fetched once at build time, never at runtime. */
function fontFamilies() {
  const weights = Object.values(tokens.fontWeight).map(w => Number(w.$value))
  const names = [tokens.font.display, tokens.font.body]
    .map(font => font.$value.find(name => !SYSTEM.test(name)))
    .filter(name => name !== undefined)
  // `global`: the share image (`app/components/OgImage/`) renders with them too.
  return [...new Set(names)].map(name => ({ name, weights, global: true }))
}

export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/fonts',
    '@nuxtjs/robots',
    '@nuxtjs/sitemap',
    'nuxt-schema-org',
    'nuxt-og-image',
  ],
  devtools: { enabled: false },

  // The design's values (colours, fonts, sizes, spacing…), set once and used everywhere through `var(--…)`.
  css: ['~/assets/design/tokens.css'],

  runtimeConfig: {
    // Signs the share image addresses (`/_og/…`): at least 32 characters, stable, one per environment.
    appSecret: '',
    // `public` values reach the browser: never put a secret there.
    public: {
      appName: 'My app',
      apiBaseUrl: 'http://localhost:8000',
      apiTimeoutS: 10,
      // Where the public bucket is served (`useFileUrl()`); empty when the project has none.
      s3PublicUrl: '',
      // Read by the search engine modules (robots.txt, sitemap, structured data) and by `app.vue`: the public
      // address, the language, and whether search engines may index the site. Only production is indexable.
      site: { url: '', indexable: false, defaultLocale: 'en' },
    },
  },

  routeRules: {
    // The signed-in area: rendered in the browser, never indexed, left out of the sitemap.
    '/app/**': { ssr: false, robots: false },
    '/**': {
      headers: {
        'x-content-type-options': 'nosniff',
        'x-frame-options': 'DENY',
        'referrer-policy': 'no-referrer',
      },
    },
  },

  compatibilityDate: '2026-10-01',

  nitro: {
    preset: 'node-server',
    // `useEvent()` anywhere on the server: log lines written while a request is handled carry its request id.
    experimental: { asyncContext: true },
  },

  eslint: {
    config: { stylistic: true },
  },

  fonts: {
    families: fontFamilies(),
    // The design's fonts come from Google Fonts: no other provider is asked.
    provider: 'google',
    defaults: { subsets: ['latin', 'latin-ext'] },
  },

  // The share image of every page (`app/components/OgImage/`), drawn by Takumi without a browser.
  ogImage: {
    defaults: { width: 1200, height: 630 },
  },
})

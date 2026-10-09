// Application configuration. Values under `runtimeConfig` are defaults: each one is overridden at runtime by
// its `NUXT_*` environment variable (`public.appName` by `NUXT_PUBLIC_APP_NAME`), so one build serves every
// environment. Nothing here is read from the environment at build time.
export default defineNuxtConfig({
  modules: ['@nuxt/eslint'],
  devtools: { enabled: false },

  runtimeConfig: {
    // `public` values reach the browser: never put a secret there.
    public: {
      appName: 'My app',
      apiBaseUrl: 'http://localhost:8000',
      apiTimeoutS: 10,
    },
  },

  routeRules: {
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
})

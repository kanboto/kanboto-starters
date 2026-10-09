/**
 * Client for the backend API, on the server (SSR) and in the browser alike. Its address and timeout come from
 * the runtime config (`NUXT_PUBLIC_API_BASE_URL`, `NUXT_PUBLIC_API_TIMEOUT_S`), read when the app starts, never
 * baked in at build time: the same image serves every environment.
 *
 *   const { data } = await useAsyncData('items', () => useApi()('/api/v1/items'))
 */
export function useApi() {
  const { apiBaseUrl, apiTimeoutS } = useRuntimeConfig().public
  return $fetch.create({ baseURL: apiBaseUrl, timeout: apiTimeoutS * 1000 })
}

/**
 * Who may show the site in a frame. Nobody by default. When `NUXT_PUBLIC_KANBOTO_INSPECT_ORIGIN` is set
 * (Kanboto's page workshop, outside production only), that origin and no other.
 */
function inspectOrigin(value: unknown): string | undefined {
  try {
    return typeof value === 'string' && value ? new URL(value).origin : undefined
  }
  catch {
    return undefined // not an address: nobody may frame the site
  }
}

export default defineNitroPlugin((nitroApp) => {
  nitroApp.hooks.hook('request', (event) => {
    const origin = inspectOrigin(useRuntimeConfig(event).public.kanbotoInspectOrigin)
    if (origin) {
      setResponseHeader(event, 'content-security-policy', `frame-ancestors ${origin}`)
    }
    else {
      setResponseHeader(event, 'x-frame-options', 'DENY')
    }
  })
})

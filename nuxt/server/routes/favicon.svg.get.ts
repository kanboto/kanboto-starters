/** The tab icon: the application name's initial, read from the runtime config like the name itself. */
const XML = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', '\'': '&apos;' } as const

export default defineEventHandler((event) => {
  const { appName } = useRuntimeConfig(event).public
  const initial = ([...String(appName).trim()][0] ?? '?').toUpperCase()
  const letter = initial.replace(/[&<>"']/g, c => XML[c as keyof typeof XML])
  setResponseHeaders(event, { 'content-type': 'image/svg+xml', 'cache-control': 'public, max-age=3600' })
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1f2328"/><text x="32" y="44" text-anchor="middle" font-family="system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif" font-size="36" font-weight="600" fill="#fff">${letter}</text></svg>`
})

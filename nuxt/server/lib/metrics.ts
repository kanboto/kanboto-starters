/**
 * Prometheus metrics: Node.js runtime (CPU, memory, event loop, garbage collector) and HTTP requests.
 *
 * One process per container: scale out with more instances. Counters stay accurate without aggregation.
 */
import type { H3Event } from 'h3'
import { Counter, Histogram, Registry, collectDefaultMetrics } from 'prom-client'

export const registry = new Registry()
collectDefaultMetrics({ register: registry })
// Gauges named like counters, which Prometheus's linter rejects; their per-type gauges
// (`nodejs_active_handles{type}`...) carry the same information.
for (const name of ['nodejs_active_handles_total', 'nodejs_active_requests_total', 'nodejs_active_resources_total']) {
  registry.removeSingleMetric(name)
}

const requests = new Counter({
  name: 'http_requests_total',
  help: 'HTTP requests handled',
  labelNames: ['method', 'route', 'status'] as const,
  registers: [registry],
})
const duration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'route'] as const,
  registers: [registry],
})

/** Probes and metrics are neither logged nor counted: they would drown the application's own traffic. */
export const UNTRACKED = new Set(['/healthz', '/readyz', '/metrics'])

/**
 * The route pattern, never the raw path, so metric cardinality stays bounded: the page's pattern (`/`,
 * `/items/:id()`), a server route's (`/api/items/:id`), `/_nuxt/**` for what the build produced (file names
 * change with every build), `static` for a file of `public/`, `unmatched` otherwise.
 */
export function route(event: H3Event, status: number): string {
  if (event.context.routePattern) return event.context.routePattern
  const assets = useRuntimeConfig(event).app.buildAssetsDir
  if (event.path.startsWith(assets)) return `${assets}**`
  const matched = event.context.matchedRoute?.path
  // `/**` is Nuxt's page renderer: a page was asked for, but none matched.
  if (matched && matched !== '/**') return matched
  return !matched && status < 400 ? 'static' : 'unmatched'
}

export function observe(method: string, route: string, status: number, seconds: number): void {
  duration.labels(method, route).observe(seconds)
  requests.labels(method, route, String(status)).inc()
}

/**
 * Per-request plumbing, as Nitro hooks: request id, one JSON log line and metrics per request, errors logged
 * with their stack. Also turns every `console.*` call (Nitro's, Vue's, the libraries') into a JSON log line, so
 * that nothing else reaches the output.
 */
import { format } from 'node:util'
import type { H3Event } from 'h3'
import { useEvent } from 'nitropack/runtime'
import { context, logger } from '../lib/log'
import type { Level } from '../lib/settings'
import { UNTRACKED, observe, route } from '../lib/metrics'

const REQUEST_ID = /^[\w.-]{1,128}$/
/** Lines dropped: they repeat the raw URL, query string included, and add nothing to the request line and the
 * error line written below. Nitro's on an unhandled error, Vue Router's on a page that does not exist. */
const SKIPPED = ['[request error]', '[h3] [unhandled]', '[VUE_ROUTER_R0004]']

function currentRequestId(): string | undefined {
  try {
    return useEvent().context.requestId
  }
  catch {
    return undefined // outside a request
  }
}

/** A sub-request made by the server itself (`$fetch('/…')` during rendering, Nuxt's error page) is part of
 * the request that made it: it is neither logged nor counted on its own. */
function internal(event: H3Event): boolean {
  return '__unenv__' in event.node.req
}

const appLog = logger('app')
const accessLog = logger('access')
const consoleLog = logger('console')

function redirectConsole(): void {
  const levels: Record<'debug' | 'log' | 'info' | 'warn' | 'error', Level> = {
    debug: 'debug',
    log: 'info',
    info: 'info',
    warn: 'warn',
    error: 'error',
  }
  for (const [method, level] of Object.entries(levels) as [keyof typeof levels, Level][]) {
    console[method] = (...args: unknown[]) => {
      const error = args.find(arg => arg instanceof Error)
      const message = format(...args.filter(arg => arg !== error)).trim() || String(error?.message ?? '')
      if (SKIPPED.some(prefix => message.startsWith(prefix))) return
      consoleLog[level](message, { error })
    }
  }
}

export default defineNitroPlugin((nitroApp) => {
  context.requestId = currentRequestId
  redirectConsole()

  nitroApp.hooks.hook('request', (event) => {
    if (internal(event)) return
    const incoming = getRequestHeader(event, 'x-request-id') ?? ''
    const requestId = REQUEST_ID.test(incoming) ? incoming : crypto.randomUUID().replaceAll('-', '')
    event.context.requestId = requestId
    setResponseHeader(event, 'x-request-id', requestId)
    if (UNTRACKED.has(event.path.split('?')[0]!)) return

    // Once the response is sent, whatever produced it: Nitro's `afterResponse` hook is skipped on errors.
    const started = performance.now()
    const response = event.node.res
    response.once('close', () => {
      const seconds = (performance.now() - started) / 1000
      // 499: the client went away before the response was complete.
      const status = response.writableFinished ? response.statusCode : 499
      const label = route(event, status)
      observe({ method: event.method, route: label, status }, seconds)
      accessLog.info('request', {
        request_id: requestId,
        method: event.method,
        route: label,
        status,
        duration_ms: Math.round(seconds * 10000) / 10,
      })
    })
  })

  nitroApp.hooks.hook('error', (error, { event }) => {
    const status = (error as { statusCode?: number }).statusCode ?? 500
    if (status < 500) return // a 404 is an answer, not a failure: the request line records it
    // h3 wraps what a handler throws: log the original error, its stack points at the faulty code.
    const cause = (error as { cause?: unknown }).cause
    appLog.error('request failed', {
      request_id: event?.context.requestId,
      method: event?.method,
      route: event ? route(event, status) : undefined,
      error: cause instanceof Error ? cause : error,
    })
  })
})

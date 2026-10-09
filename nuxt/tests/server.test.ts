/**
 * Runtime contract, against the production build served by Node.js as in the image: server-side rendering,
 * probes, metrics, JSON logs and graceful shutdown. No network: the server listens on 127.0.0.1.
 */
import { fileURLToPath } from 'node:url'
import { $fetch, fetch, getServerLogs, setup, useTestContext } from '@nuxt/test-utils/e2e'
import { describe, expect, it } from 'vitest'

await setup({
  rootDir: fileURLToPath(new URL('..', import.meta.url)),
  env: {
    NUXT_PUBLIC_APP_NAME: 'Acme Console',
    LOG_LEVEL: 'info',
    DRAIN_DELAY_S: '1',
    SHUTDOWN_TIMEOUT_S: '5',
  },
})

function logs(): Record<string, unknown>[] {
  return getServerLogs()
    .flatMap(chunk => String(chunk).split('\n'))
    .filter(line => line.trim())
    .map(line => JSON.parse(line))
}

describe('home page', () => {
  it('is rendered on the server, with the configured name', async () => {
    const html = await $fetch<string>('/')
    expect(html).toMatch(/<h1[^>]*>Acme Console<\/h1>/)
    expect(html).toContain('Hello world')
    expect(html).toContain('<title>Acme Console</title>')
    expect(html).toContain('<link rel="icon" type="image/svg+xml" href="/favicon.svg">')
  })

  it('has an icon drawn from the name, served as a route of its own', async () => {
    const icon = await fetch('/favicon.svg')
    expect(icon.headers.get('content-type')).toBe('image/svg+xml')
    expect(await icon.text()).toMatch(/>A<\/text><\/svg>$/)
    const legacy = await fetch('/favicon.ico', { redirect: 'manual' })
    expect([legacy.status, legacy.headers.get('location')]).toEqual([301, '/favicon.svg'])
    await expect.poll(() => logs().filter(l => l.logger === 'access').map(l => l.route)).toContain('/favicon.svg')
    expect(logs().some(l => l.route === 'unmatched')).toBe(false)
  })
})

describe('probes', () => {
  it('answers liveness and readiness', async () => {
    expect(await $fetch('/healthz')).toEqual({ status: 'ok' })
    expect(await $fetch('/readyz')).toEqual({ status: 'ok' })
  })
})

describe('metrics', () => {
  it('exposes runtime and request metrics, labelled by route pattern', async () => {
    const html = await (await fetch('/')).text()
    await fetch(html.match(/\/_nuxt\/[\w.-]+\.js/)![0]) // a file of the build
    await fetch('/_nuxt/gone-since-last-build.js') // a client still on a previous build
    await fetch('/no/such/page/42?token=abc')
    await fetch('/healthz')
    const response = await fetch('/metrics')
    expect(response.headers.get('content-type')).toMatch(/^text\/plain/)
    const text = await response.text()
    expect(text).toMatch(/^http_requests_total\{method="GET",route="\/",status="200"\} \d+$/m)
    expect(text).toMatch(/^http_requests_total\{method="GET",route="unmatched",status="404"\} \d+$/m)
    expect(text).toMatch(/^http_requests_total\{method="GET",route="\/_nuxt\/\*\*",status="200"\} \d+$/m)
    expect(text).toMatch(/^http_requests_total\{method="GET",route="\/_nuxt\/\*\*",status="404"\} \d+$/m)
    expect(text).not.toContain('route="static"')
    expect(text).toContain('# TYPE http_request_duration_seconds histogram')
    expect(text).toContain('# TYPE nodejs_eventloop_lag_seconds gauge')
    expect(text).not.toMatch(/^# TYPE \w+_total gauge$/m) // Prometheus's linter rejects it
    expect(text).not.toContain('/no/such/page')
    expect(text).not.toContain('route="/healthz"')
  })
})

describe('logs', () => {
  it('are JSON, one line per request, with a request id and no query string', async () => {
    const response = await fetch('/?email=someone@example.com', { headers: { 'x-request-id': 'req-123' } })
    expect(response.headers.get('x-request-id')).toBe('req-123')
    await expect.poll(() => logs().some(line => line.request_id === 'req-123')).toBe(true)

    const lines = logs()
    expect(lines.find(line => line.request_id === 'req-123')).toMatchObject({
      level: 'info',
      message: 'request',
      method: 'GET',
      route: '/',
      status: 200,
    })
    expect(lines.some(line => String(line.message).startsWith('Listening on'))).toBe(true)
    expect(JSON.stringify(lines)).not.toContain('someone@example.com')
  })

  it('generate a request id when the caller sends none or an invalid one', async () => {
    const response = await fetch('/', { headers: { 'x-request-id': 'not valid!' } })
    expect(response.headers.get('x-request-id')).toMatch(/^[0-9a-f]{32}$/)
  })
})

describe('shutdown', () => {
  it('fails readiness first, keeps serving while draining, then exits with code 0', async () => {
    const server = useTestContext().serverProcess!
    const exited = new Promise<number | null>(resolve => server.process!.once('exit', code => resolve(code)))
    server.process!.kill('SIGTERM')
    await expect.poll(async () => (await fetch('/readyz')).status).toBe(503)
    expect(await $fetch('/readyz', { ignoreResponseError: true })).toEqual({ status: 'stopping' })
    expect((await fetch('/')).status).toBe(200)

    expect(await exited).toBe(0)
    const messages = logs().map(line => line.message)
    expect(messages).toEqual(expect.arrayContaining(['draining', 'stopping', 'stopped']))
  })
})

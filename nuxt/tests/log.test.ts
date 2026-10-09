/** Log lines and settings, without a server. */
import { describe, expect, it } from 'vitest'
import { context, entry } from '../server/lib/log'
import { readSettings } from '../server/lib/settings'

describe('log entry', () => {
  it('carries the request id and fields, and an error with its stack', () => {
    context.requestId = () => 'r1'
    try {
      const line = entry({ level: 'error', logger: 'app', message: 'request failed' }, { route: '/', error: new TypeError('boom') })
      expect(JSON.parse(JSON.stringify(line))).toMatchObject({
        level: 'error',
        logger: 'app',
        message: 'request failed',
        request_id: 'r1',
        route: '/',
        error: 'TypeError: boom',
      })
      expect(line.exception).toMatch(/^TypeError: boom\n\s+at /)
    }
    finally {
      context.requestId = () => undefined
    }
  })
})

describe('settings', () => {
  it('have defaults and reject invalid values', () => {
    expect(readSettings({})).toEqual({ logLevel: 'info', drainDelayS: 5, shutdownTimeoutS: 20 })
    expect(readSettings({ LOG_LEVEL: 'WARN', SHUTDOWN_TIMEOUT_S: '3' })).toMatchObject({
      logLevel: 'warn',
      shutdownTimeoutS: 3,
    })
    expect(() => readSettings({ LOG_LEVEL: 'verbose' })).toThrow(/LOG_LEVEL/)
    expect(() => readSettings({ DRAIN_DELAY_S: 'soon' })).toThrow(/DRAIN_DELAY_S/)
  })
})

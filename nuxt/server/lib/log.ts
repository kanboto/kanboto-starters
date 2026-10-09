/**
 * JSON logs on stdout, one line per event. Every line written while a request is handled carries its
 * `request_id` (see server/plugins/observability.ts). Never log a body, a query string or personal data.
 */
import { LEVELS, settings, type Level } from './settings'

export type Fields = Record<string, unknown>

/** Where the request id of the current request comes from; set once the server is up. */
export const context: { requestId: () => string | undefined } = { requestId: () => undefined }

/** What a line is about; the fields come on top. */
export interface Event { level: Level, logger: string, message: string }

export function entry(event: Event, fields: Fields = {}): Fields {
  const line: Fields = { time: new Date().toISOString(), ...event }
  const requestId = context.requestId()
  if (requestId) line.request_id = requestId
  for (const [key, value] of Object.entries(fields)) {
    if (value instanceof Error) {
      line.error = `${value.name}: ${value.message}`
      line.exception = value.stack
    }
    else if (value !== undefined) {
      line[key] = value
    }
  }
  return line
}

export type Logger = Record<Level, (message: string, fields?: Fields) => void>

/** A named logger, one method per level: `logger('app').info('stopping', { signal })`. */
export function logger(name: string): Logger {
  const write = (level: Level) => (message: string, fields?: Fields) => {
    if (LEVELS.indexOf(level) < LEVELS.indexOf(settings.logLevel)) return
    process.stdout.write(`${JSON.stringify(entry({ level, logger: name, message }, fields))}\n`)
  }
  return Object.fromEntries(LEVELS.map(level => [level, write(level)])) as Logger
}

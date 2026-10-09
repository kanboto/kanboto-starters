/**
 * JSON logs on stdout, one line per event. Every line written while a request is handled carries its
 * `request_id` (see server/plugins/observability.ts). Never log a body, a query string or personal data.
 */
import { LEVELS, settings, type Level } from './settings'

export type Fields = Record<string, unknown>

/** Where the request id of the current request comes from; set once the server is up. */
export const context: { requestId: () => string | undefined } = { requestId: () => undefined }

export function entry(level: Level, logger: string, message: string, fields: Fields = {}): Fields {
  const line: Fields = { time: new Date().toISOString(), level, logger, message }
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

export function log(level: Level, logger: string, message: string, fields?: Fields): void {
  if (LEVELS.indexOf(level) < LEVELS.indexOf(settings.logLevel)) return
  process.stdout.write(`${JSON.stringify(entry(level, logger, message, fields))}\n`)
}

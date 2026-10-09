/**
 * Settings of the server process, from the environment; see `.env.example`. The application's own settings
 * live in `runtimeConfig` (nuxt.config.ts), overridden by `NUXT_*` variables. `PORT` is read by Nitro itself.
 */
export const LEVELS = ['debug', 'info', 'warn', 'error'] as const
export type Level = (typeof LEVELS)[number]

export interface Settings {
  logLevel: Level
  /** After SIGTERM, time `/readyz` fails while traffic is still served. */
  drainDelayS: number
  /** Then, grace period for in-flight requests. */
  shutdownTimeoutS: number
}

function seconds(env: NodeJS.ProcessEnv, name: string, fallback: number): number {
  const raw = env[name]
  if (raw === undefined || raw === '') return fallback
  const value = Number(raw)
  if (!Number.isFinite(value) || value < 0) throw new Error(`${name} must be a number of seconds, got ${raw}`)
  return value
}

export function readSettings(env: NodeJS.ProcessEnv = process.env): Settings {
  const level = (env.LOG_LEVEL || 'info').toLowerCase()
  if (!(LEVELS as readonly string[]).includes(level)) {
    throw new Error(`LOG_LEVEL must be one of ${LEVELS.join(', ')}, got ${env.LOG_LEVEL}`)
  }
  return {
    logLevel: level as Level,
    drainDelayS: seconds(env, 'DRAIN_DELAY_S', 5),
    shutdownTimeoutS: seconds(env, 'SHUTDOWN_TIMEOUT_S', 20),
  }
}

export const settings = readSettings()

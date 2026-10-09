/**
 * Graceful shutdown, built on Nitro's own (node-server preset).
 *
 * Nitro, on its shutdown signal, stops accepting connections, closes idle ones, waits for in-flight requests
 * (up to `NITRO_SHUTDOWN_TIMEOUT` ms), runs the `close` hooks and exits with code 0. What it lacks is a drain
 * phase: it stops accepting at once, before load balancers have seen the instance go unready.
 *
 * So, on SIGTERM: `/readyz` fails at once while traffic is still served for `DRAIN_DELAY_S`, then Nitro's
 * shutdown runs with `SHUTDOWN_TIMEOUT_S` as its grace period. The process exits within
 * `DRAIN_DELAY_S + SHUTDOWN_TIMEOUT_S`. A second signal, or SIGINT (Ctrl-C), skips the drain.
 *
 * Nitro reads its `NITRO_SHUTDOWN_*` variables when the server starts, after the plugins have run: they are
 * set here, from this application's variables, and are not meant to be set by hand.
 */
import { lifecycle } from '../lib/lifecycle'
import { log } from '../lib/log'
import { settings } from '../lib/settings'

/** A process event, not a signal: Nitro's shutdown is bound to it, and it is emitted once the drain is over. */
const DRAINED = 'drained'

export default defineNitroPlugin((nitroApp) => {
  if (import.meta.dev) return

  process.env.NITRO_SHUTDOWN_SIGNALS = `SIGINT ${DRAINED}`
  process.env.NITRO_SHUTDOWN_TIMEOUT = String(Math.round(settings.shutdownTimeoutS * 1000))
  delete process.env.NITRO_SHUTDOWN_DISABLED

  let timer: NodeJS.Timeout | undefined
  let stopped = false
  // Logs the stop; Nitro's shutdown runs on SIGINT by itself, on SIGTERM once `drained` is emitted.
  const stop = (signal: NodeJS.Signals) => {
    clearTimeout(timer)
    lifecycle.stopping = true
    if (stopped) return
    stopped = true
    log('info', 'app', 'stopping', { signal, timeout_s: settings.shutdownTimeoutS })
    if (signal === 'SIGTERM') process.emit(DRAINED, signal)
  }

  process.on('SIGTERM', () => {
    if (lifecycle.stopping) return stop('SIGTERM')
    lifecycle.stopping = true
    log('info', 'app', 'draining', { delay_s: settings.drainDelayS })
    timer = setTimeout(stop, settings.drainDelayS * 1000, 'SIGTERM')
  })
  process.on('SIGINT', () => stop('SIGINT'))

  nitroApp.hooks.hook('close', () => log('info', 'app', 'stopped'))
})

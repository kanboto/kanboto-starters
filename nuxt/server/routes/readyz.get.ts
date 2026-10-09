/**
 * Readiness: 200 while the instance takes traffic, 503 as soon as shutdown starts, so traffic is routed
 * elsewhere before the process exits. Check here the dependencies the server side cannot work without.
 */
import { lifecycle } from '../lib/lifecycle'

export default defineEventHandler((event) => {
  if (lifecycle.stopping) {
    setResponseStatus(event, 503)
    return { status: 'stopping' }
  }
  return { status: 'ok' }
})

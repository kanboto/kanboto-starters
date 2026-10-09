/** Prometheus metrics, in the text exposition format. */
import { registry } from '../lib/metrics'

export default defineEventHandler(async (event) => {
  setResponseHeader(event, 'content-type', registry.contentType)
  return registry.metrics()
})

/** Process state shared by the shutdown plugin and the readiness probe. */
export const lifecycle = {
  /** Set as soon as SIGTERM is received: `/readyz` answers 503 from then on. */
  stopping: false,
}

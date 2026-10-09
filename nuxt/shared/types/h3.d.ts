declare module 'h3' {
  interface H3EventContext {
    /** Pattern of the page that rendered the request (`/items/:id()`), set during server-side rendering. */
    routePattern?: string
    /** The caller's `X-Request-ID`, or a generated one. */
    requestId?: string
  }
}

export {}

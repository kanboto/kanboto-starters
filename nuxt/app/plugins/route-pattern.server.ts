/**
 * Hands the matched page's pattern (`/items/:id()`, never `/items/42`) to the server, which labels the
 * request's log line and metrics with it: metric cardinality stays bounded and no id reaches the logs.
 */
export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.hook('app:rendered', ({ ssrContext }) => {
    const page = nuxtApp.$router.currentRoute.value.matched.at(-1)
    if (page && ssrContext?.event) {
      ssrContext.event.context.routePattern = page.path
    }
  })
})

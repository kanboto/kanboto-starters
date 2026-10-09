/** Browsers ask for `/favicon.ico` on a page without an icon link (a probe opened in a tab): send them to the
 * SVG icon, rather than letting the page renderer answer. */
export default defineEventHandler(event => sendRedirect(event, '/favicon.svg', 301))

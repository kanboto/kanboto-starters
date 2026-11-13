/** The site's name, used by the structured data and the sitemap, is the application's: one variable for both. */
export default defineNitroPlugin((nitroApp) => {
  nitroApp.hooks.hook('site-config:init', ({ siteConfig }) => {
    siteConfig.push({ _context: 'app', name: useRuntimeConfig().public.appName })
  })
})

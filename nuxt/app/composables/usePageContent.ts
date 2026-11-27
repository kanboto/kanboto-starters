import type { KbPageDocument } from '~/components/kit/lib/types'

// The pages of the site as data: one document per file of `app/content/pages/`, rendered by `KbPage`.
// `kit-all.json` holds every block of the kit for the tests: it is left out of the build.
const documents = import.meta.glob<KbPageDocument>(
  ['../content/pages/*.json', '!../content/pages/kit-all.json'],
  { eager: true, import: 'default' },
)

const pages = new Map(Object.values(documents).map(page => [page.slug, page]))

/** The page document of that slug (`home` for `app/content/pages/home.json`). */
export function usePageContent(slug: string): KbPageDocument {
  const page = pages.get(slug)
  if (!page) {
    throw createError({ statusCode: 404, statusMessage: 'Page not found', fatal: true })
  }
  return page
}

import { resolvePage } from '~/components/blocks/lib/shared'
import type { KbPageDocument, KbSharedBlocks, KbStoredPage } from '~/components/blocks/lib/types'
import shared from '../content/shared.json'

// The pages of the site as data: one document per file of `app/content/pages/`, rendered by `KbPage`.
// The blocks several pages show (navigation, footer…) are written once in `app/content/shared.json`; a page
// holds `{ "ref": "<id>" }` at their place. `all-blocks.json` holds every block of the block library for the tests: it is
// left out of the build.
const documents = import.meta.glob<KbStoredPage>(
  ['../content/pages/*.json', '!../content/pages/all-blocks.json'],
  { eager: true, import: 'default' },
)

const pages = new Map(Object.values(documents).map(page => [page.slug, page]))

/** The page document of that slug (`home` for `app/content/pages/home.json`), shared blocks in place. */
export function usePageContent(slug: string): KbPageDocument {
  const page = pages.get(slug)
  if (!page) {
    throw createError({ statusCode: 404, statusMessage: 'Page not found', fatal: true })
  }
  return resolvePage(page, shared as KbSharedBlocks)
}

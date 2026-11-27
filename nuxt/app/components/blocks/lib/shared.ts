import type { KbBlock, KbBlockRef, KbPageDocument, KbSharedBlocks, KbStoredPage } from './types'

const isRef = (block: KbBlock | KbBlockRef): block is KbBlockRef => 'ref' in block

/** The page with each `{ "ref": "<id>" }` replaced by the shared block of that id. A shared block is written
 * once and every page showing it follows; a reference to a block that no longer exists renders nothing. */
export function resolvePage(page: KbStoredPage, shared: KbSharedBlocks): KbPageDocument {
  const blocks = page.blocks.flatMap((block) => {
    if (!isRef(block)) return [block]
    const found = shared.blocks[block.ref]
    return found ? [found] : []
  })
  return { ...page, blocks }
}

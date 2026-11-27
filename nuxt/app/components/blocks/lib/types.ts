/** The page document Kanboto's page workshop produces: a page is a list of typed blocks, each rendered by one
 * section of the block library. Every field is optional at render time. */

export interface KbLinkField {
  label?: string
  href?: string
  /** An icon of the allowlist (`lib/icons.ts`), shown before the label of a button. */
  icon?: string
}

export interface KbImageField {
  src?: string
  alt?: string
  /** `1:1`, `4:3`, `3:2`, `16:9`, `3:4` or `21:9`. */
  ratio?: string
  width?: number
  height?: number
  /** What the image should show, when it is still to be made. */
  prompt?: string
}

export type KbFieldValue = string | number | boolean | null | KbLinkField | KbImageField | KbItem[]

/** One entry of an `items` field: its sub-fields by key. */
export interface KbItem {
  [key: string]: KbFieldValue | undefined
}

export interface KbSettings {
  /** `default`, `surface`, `accent` or `inverse`. */
  tone?: string
  /** A decoration behind the content: `none`, `glow`, `grid` or `dots`. */
  backdrop?: string
  /** `auto` (the section decides), `start` or `center`. */
  align?: string
  /** `compact`, `normal` or `spacious`. */
  density?: string
  /** `narrow`, `contained` or `full`. */
  width?: string
}

export interface KbBlock {
  id: string
  /** A block type of the catalog (`hero`, `features`…); an unknown one renders `KbCustom`. */
  type: string
  /** A missing or unknown variant falls back to the first one of the section. */
  variant?: string
  settings?: KbSettings
  options?: Record<string, string | undefined>
  props?: KbItem
}

/** A shared block at its place in a stored page: its content lives once, in `app/content/shared.json`. */
export interface KbBlockRef {
  ref: string
}

/** The shared blocks of the site, by id: navigation, footer and any block several pages show. */
export interface KbSharedBlocks {
  blocks: Record<string, KbBlock>
}

/** A page as its file stores it: its own blocks, and references to the shared ones. */
export interface KbStoredPage extends Omit<KbPageDocument, 'blocks'> {
  blocks: (KbBlock | KbBlockRef)[]
}

/** A page ready to render: every reference replaced by its shared block. */
export interface KbPageDocument {
  slug: string
  path: string
  title?: string
  description?: string
  blocks: KbBlock[]
}

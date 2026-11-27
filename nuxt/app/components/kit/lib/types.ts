/** The page document Kanboto's page workshop produces: a page is a list of typed blocks, each rendered by one
 * section of the kit. Every field is optional at render time. */

export interface KbLinkField {
  label?: string
  href?: string
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
  /** `default`, `surface` or `inverse`. */
  tone?: string
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

export interface KbPageDocument {
  slug: string
  path: string
  title?: string
  description?: string
  blocks: KbBlock[]
}

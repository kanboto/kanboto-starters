import type { ComputedRef, InjectionKey } from 'vue'
import { computed, inject } from 'vue'
import type { KbBlock } from './types'

/** Id of the block whose title is the page's `h1`, provided by `KbPage`. */
export const H1_BLOCK: InjectionKey<ComputedRef<string | undefined>> = Symbol('kb:h1')

/** Path of the page being rendered, provided by `KbPage`. */
export const PAGE_PATH: InjectionKey<ComputedRef<string>> = Symbol('kb:path')

/** Id of the first block that shows an image: the page's largest paint, loaded first and never lazily. */
export const LEAD_IMAGE: InjectionKey<ComputedRef<string | undefined>> = Symbol('kb:lead-image')

/** Whether this block carries the page's first image. */
export function useLeadImage(block: () => KbBlock): ComputedRef<boolean> {
  const lead = inject(LEAD_IMAGE, undefined)
  return computed(() => lead?.value === block().id)
}

/** `h1` for the one block that titles the page, `h2` for every other. */
export function useHeading(block: () => KbBlock): ComputedRef<'h1' | 'h2'> {
  const h1 = inject(H1_BLOCK, undefined)
  return computed(() => (h1?.value === block().id ? 'h1' : 'h2'))
}

/** Heading of an entry inside a block: one level under the block's title, with no level skipped when the block
 * has no title of its own or carries the page's `h1`. */
export function useItemHeading(block: () => KbBlock): ComputedRef<'h2' | 'h3'> {
  const h1 = inject(H1_BLOCK, undefined)
  return computed(() => {
    const title = block().props?.title
    return typeof title === 'string' && title !== '' && h1?.value !== block().id ? 'h3' : 'h2'
  })
}

/** The block's variant, or the section's first one when it is missing or unknown. */
export function useVariant<const T extends readonly [string, ...string[]]>(
  block: () => KbBlock,
  variants: T,
): ComputedRef<T[number]> {
  return computed(() => {
    const variant = block().variant
    return variant !== undefined && variants.includes(variant) ? variant : variants[0]
  })
}

const TONES: Record<string, string> = {
  default: '',
  surface: 'kb-tone-surface',
  accent: 'kb-tone-accent',
  inverse: 'kb-tone-inverse',
}

const BACKDROPS: Record<string, string> = {
  glow: 'kb-backdrop kb-backdrop-glow',
  grid: 'kb-backdrop kb-backdrop-grid',
  dots: 'kb-backdrop kb-backdrop-dots',
}

const DENSITIES: Record<string, string> = {
  compact: 'py-8 @3xl:py-10',
  normal: 'py-12 @3xl:py-20',
  spacious: 'py-16 @3xl:py-28',
}

const WIDTHS: Record<string, string> = {
  narrow: 'max-w-3xl',
  contained: 'max-w-(--content-width)',
  full: 'max-w-none',
}

export function toneClass(block: KbBlock): string {
  return TONES[block.settings?.tone ?? 'default'] ?? ''
}

/** The decoration drawn behind the content of a section, from the colours of the charter. */
export function backdropClass(block: KbBlock): string {
  return BACKDROPS[block.settings?.backdrop ?? 'none'] ?? ''
}

/** Whether the head of a section is centred: the author's choice, else the section's own. */
export function centred(block: KbBlock, byDefault: boolean): boolean {
  const align = block.settings?.align
  return align === 'center' || (align !== 'start' && byDefault)
}

export function densityClass(block: KbBlock): string {
  return DENSITIES[block.settings?.density ?? 'normal'] ?? DENSITIES.normal!
}

/** The centred column every section aligns on. */
export function containerClass(block: KbBlock): string {
  const width = WIDTHS[block.settings?.width ?? 'contained'] ?? WIDTHS.contained!
  return `mx-auto w-full px-(--gutter) @3xl:px-8 ${width}`
}

const COLUMNS: Record<string, string> = {
  2: '@2xl:grid-cols-2',
  3: '@2xl:grid-cols-2 @5xl:grid-cols-3',
  4: '@2xl:grid-cols-2 @5xl:grid-cols-4',
}

/** `options.columns` as a grid that stacks in a narrow container. */
export function columnsClass(block: KbBlock): string {
  return `grid gap-6 ${COLUMNS[block.options?.columns ?? '3'] ?? COLUMNS[3]!}`
}

import type { ComputedRef, InjectionKey } from 'vue'
import { computed, inject } from 'vue'
import type { KbBlock } from './types'

/** Id of the block whose title is the page's `h1`, provided by `KbPage`. */
export const H1_BLOCK: InjectionKey<ComputedRef<string | undefined>> = Symbol('kb:h1')

/** Path of the page being rendered, provided by `KbPage`. */
export const PAGE_PATH: InjectionKey<ComputedRef<string>> = Symbol('kb:path')

/** `h1` for the one block that titles the page, `h2` for every other. */
export function useHeading(block: () => KbBlock): ComputedRef<'h1' | 'h2'> {
  const h1 = inject(H1_BLOCK, undefined)
  return computed(() => (h1?.value === block().id ? 'h1' : 'h2'))
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
  inverse: 'kb-tone-inverse',
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

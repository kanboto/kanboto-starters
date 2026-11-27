import type { KbImageField, KbItem, KbLinkField } from './types'

type Source = KbItem | undefined

function record(value: unknown): Record<string, unknown> | undefined {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? value as Record<string, unknown>
    : undefined
}

/** A text field, trimmed; empty when missing, so `v-if` renders nothing. */
export function text(source: Source, key: string): string {
  const value = source?.[key]
  return typeof value === 'string' || typeof value === 'number' ? String(value).trim() : ''
}

export function flag(source: Source, key: string): boolean {
  return source?.[key] === true
}

/** A link field, only when it has a label to show. */
export function link(source: Source, key: string): KbLinkField | undefined {
  const value = record(source?.[key])
  return typeof value?.label === 'string' && value.label.trim() ? value as KbLinkField : undefined
}

/** An image field, only when it has something to show: a file, or a caption for its placeholder. */
export function image(source: Source, key: string): KbImageField | undefined {
  const value = record(source?.[key]) as KbImageField | undefined
  return value && (value.src || value.alt || value.prompt) ? value : undefined
}

export function items(source: Source, key: string): KbItem[] {
  const value = source?.[key]
  return Array.isArray(value) ? value.filter(item => record(item) !== undefined) : []
}

/** A long text as its non-empty lines: paragraphs, list entries, table rows. */
export function lines(value: string): string[] {
  return value.split('\n').map(line => line.trim()).filter(Boolean)
}

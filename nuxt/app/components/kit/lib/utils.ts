import type { ClassValue } from 'clsx'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

/** Visible keyboard focus, shared by every link and control of the kit. */
export const focusRing = 'outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring'

/** At least 44px under a finger; a mouse keeps the compact size. */
export const touchTarget = 'pointer-coarse:min-h-11 pointer-coarse:min-w-11'

/** A plain text link: underlined on hover, never by colour alone. */
export const textLink = `rounded-(--radius-sm) underline-offset-4 hover:underline ${focusRing}`

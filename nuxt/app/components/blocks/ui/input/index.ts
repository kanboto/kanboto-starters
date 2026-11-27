import { focusRing } from '../../lib/utils'

export { default as Input } from './Input.vue'

/** The look of a text control, shared by the input, the textarea and the native select. */
export const controlClass = `w-full min-w-0 rounded-(--radius-md) border border-input bg-background px-3 py-2 text-[length:max(1rem,var(--text-base))] text-foreground shadow-(--shadow-sm) transition-colors duration-(--duration-fast) ease-(--easing) placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50 user-invalid:border-destructive user-invalid:outline-destructive pointer-coarse:min-h-11 ${focusRing}`

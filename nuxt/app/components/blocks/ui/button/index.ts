import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'
import { focusRing, touchTarget } from '../../lib/utils'

export { default as Button } from './Button.vue'

export const buttonVariants = cva(
  `inline-flex shrink-0 items-center justify-center gap-2 rounded-(--radius-md) text-center text-sm font-medium transition-colors duration-(--duration-fast) ease-(--easing) disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 ${focusRing} ${touchTarget}`,
  {
    variants: {
      variant: {
        default: 'border border-transparent bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/80',
        outline: 'border border-border bg-background text-foreground hover:bg-muted active:bg-muted/70',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80 active:bg-secondary/60',
        ghost: 'text-foreground hover:bg-muted active:bg-muted/70',
        link: 'text-foreground underline-offset-4 hover:underline',
      },
      size: {
        default: 'min-h-9 px-4 py-2',
        sm: 'min-h-8 px-3 py-1.5',
        lg: 'min-h-11 px-6 py-2.5 text-base',
        icon: 'size-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>

<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import KbLink from './KbLink.vue'
import { icon } from './lib/icons'
import type { KbLinkField } from './lib/types'
import { cn } from './lib/utils'
import type { ButtonVariants } from './ui/button'
import { Button } from './ui/button'

// A link field shown as a button: renders nothing without a label. With an icon, the button shows it before
// its label. `compact` is for the actions of a bar (navigation, page header): where the container is as narrow
// as a phone, the button folds into a square with the icon alone, and keeps its label as its accessible name.
// Without an icon there is nothing to fold into: the label stays.
const props = defineProps<{
  link?: KbLinkField
  field: string
  variant?: ButtonVariants['variant']
  size?: ButtonVariants['size']
  compact?: boolean
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <Button
    v-if="link?.label"
    as-child
    :variant="variant"
    :size="size"
    :class="cn(compact && link.icon && '@max-xl:aspect-square @max-xl:px-0', props.class)"
  >
    <KbLink
      :href="link.href"
      :data-kb-field="field"
      :title="compact && link.icon ? link.label : undefined"
    >
      <component
        :is="icon(link.icon)"
        v-if="link.icon"
        aria-hidden="true"
      />
      <span :class="compact && link.icon && '@max-xl:sr-only'">{{ link.label }}</span>
    </KbLink>
  </Button>
</template>

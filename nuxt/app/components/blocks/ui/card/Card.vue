<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '../../lib/utils'

// `as`: a card is a look, not a meaning. The section picks the element (`article`, `li`, `figure`, `form`).
const props = withDefaults(defineProps<{
  as?: string
  class?: HTMLAttributes['class']
}>(), {
  as: 'div',
})
</script>

<template>
  <component
    :is="as"
    data-slot="card"
    :class="cn('flex flex-col gap-4 rounded-(--radius-lg) border border-border bg-card p-6 text-card-foreground shadow-(--shadow-sm)', props.class)"
  >
    <slot />
  </component>
</template>

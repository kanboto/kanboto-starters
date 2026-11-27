<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { containerClass, densityClass, toneClass } from '../lib/block'
import type { KbBlock } from '../lib/types'
import { cn } from '../lib/utils'

// The wrapper of every section: what the workshop reads (`data-kb-block`, `data-kb-type`) and the block's
// settings (tone, density, width). `bare` leaves spacing and width to the section (the navigation bars).
const props = withDefaults(defineProps<{
  block: KbBlock
  as?: string
  bare?: boolean
  class?: HTMLAttributes['class']
}>(), {
  as: 'section',
})
</script>

<template>
  <component
    :is="as"
    :data-kb-block="block.id"
    :data-kb-type="block.type"
    :class="cn('bg-background text-foreground', toneClass(block), !bare && densityClass(block), props.class)"
  >
    <slot v-if="bare" />
    <div
      v-else
      :class="containerClass(block)"
    >
      <slot />
    </div>
  </component>
</template>

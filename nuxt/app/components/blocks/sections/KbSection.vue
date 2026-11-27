<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import KbImage from '../KbImage.vue'
import { backdropClass, containerClass, densityClass, toneClass } from '../lib/block'
import { image } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { cn } from '../lib/utils'

// The wrapper of every section: what the workshop reads (`data-kb-block`, `data-kb-type`) and the block's
// settings (tone, decoration, density, width). A background image (`props.background`) lies under a veil of
// the tone's colour, so the text keeps its contrast whatever the picture. `bare` leaves spacing and width to
// the section (the navigation bars).
const props = withDefaults(defineProps<{
  block: KbBlock
  as?: string
  bare?: boolean
  class?: HTMLAttributes['class']
}>(), {
  as: 'section',
})

const background = computed(() => (props.bare ? undefined : image(props.block.props, 'background')))
</script>

<template>
  <component
    :is="as"
    :data-kb-block="block.id"
    :data-kb-type="block.type"
    :class="cn('bg-background text-foreground', toneClass(block), !bare && backdropClass(block), !bare && densityClass(block), background && 'relative isolate overflow-clip', props.class)"
  >
    <template v-if="background">
      <KbImage
        :image="{ ...background, alt: '' }"
        field="background"
        sizes="100vw"
        class="absolute inset-0 -z-20 aspect-auto h-full rounded-none border-0"
      />
      <span
        class="absolute inset-0 -z-10 bg-background/80"
        aria-hidden="true"
      />
    </template>
    <slot v-if="bare" />
    <div
      v-else
      :class="containerClass(block)"
    >
      <slot />
    </div>
  </component>
</template>

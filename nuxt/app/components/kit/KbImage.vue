<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { Image as ImageIcon } from 'lucide-vue-next'
import type { KbImageField } from './lib/types'
import { cn } from './lib/utils'

// An image always reserves its place (`width`, `height`, ratio). Without a file yet, a tinted placeholder of
// the same ratio says what will stand there.
const props = withDefaults(defineProps<{
  image: KbImageField
  /** The page's main image: loaded first, never lazily. */
  priority?: boolean
  field?: string
  class?: HTMLAttributes['class']
}>(), {
  field: 'image',
})

const RATIOS: Record<string, { class: string, value: number }> = {
  '1:1': { class: 'aspect-square', value: 1 },
  '4:3': { class: 'aspect-4/3', value: 4 / 3 },
  '3:2': { class: 'aspect-3/2', value: 3 / 2 },
  '16:9': { class: 'aspect-video', value: 16 / 9 },
  '3:4': { class: 'aspect-3/4', value: 3 / 4 },
  '21:9': { class: 'aspect-21/9', value: 21 / 9 },
}
const DEFAULT_WIDTH = 1200

const ratio = computed(() => RATIOS[props.image.ratio ?? ''] ?? RATIOS['4:3']!)
const width = computed(() => props.image.width ?? DEFAULT_WIDTH)
const height = computed(() => props.image.height ?? Math.round(width.value / ratio.value.value))
const caption = computed(() => props.image.alt || props.image.prompt || '')
</script>

<template>
  <img
    v-if="image.src"
    :src="image.src"
    :alt="image.alt ?? ''"
    :width="width"
    :height="height"
    :loading="priority ? 'eager' : 'lazy'"
    :fetchpriority="priority ? 'high' : undefined"
    decoding="async"
    :data-kb-field="field"
    :class="cn('h-auto w-full rounded-(--radius-lg) bg-muted object-cover', ratio.class, props.class)"
  >
  <div
    v-else
    role="img"
    :aria-label="caption"
    :data-kb-field="field"
    :class="cn('flex w-full flex-col items-center justify-center gap-3 rounded-(--radius-lg) border border-dashed border-border bg-muted p-6 text-center text-muted-foreground', ratio.class, props.class)"
  >
    <ImageIcon
      class="size-6"
      aria-hidden="true"
    />
    <span
      v-if="caption"
      class="line-clamp-3 max-w-prose text-sm"
    >{{ caption }}</span>
  </div>
</template>
